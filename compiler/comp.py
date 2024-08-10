from typing import Optional, List


class Scope:
  def __init__(self, prev: Optional["Scope"]) -> None:
    self.prev = prev
    self.nlocal = 0
    self.names = dict()
    self.loop_start = prev.loop_start if prev else -1
    self.loop_end = prev.loop_end if prev else -1
    self.save = -1


def scope_get_var(scope: Optional[Scope], name):
  while scope:
    if name in scope.names:
      return scope.names[name]
    scope = scope.prev
  return None, -1


class Func:
  def __init__(self, prev: Optional["Func"] = None) -> None:
    self.prev = prev
    self.level = (prev.level + 1) if prev else 0
    self.rtype = None
    self.funcs: List[Func] = prev.funcs if prev else []
    self.scope = Scope(None)
    # the output: a list of instructions
    self.code = []
    # current number of local variable in the stack (non-temporary)
    self.nvar = 0
    # current number of variables (both locals and temporaries)
    self.stack = 0
    # label IDs to instruction locations
    self.labels = []

  def syscall(self, dst, num, *args):
    self.code.append(("syscall", dst, num, *args))
    return dst

  def tmp(self):
    dst = self.stack
    self.stack += 1
    return dst

  def add_var(self, name, tp):
    if name in self.scope.names:
      raise ValueError(f"variable {name} already exists")
    self.scope.names[name] = (tp, self.nvar)  # type, index
    self.scope.nlocal += 1
    assert self.stack == self.nvar
    dst = self.stack
    self.stack += 1
    self.nvar += 1
    return dst

  def get_var(self, name):
    tp, var = scope_get_var(self.scope, name)
    if var >= 0:
      return self.level, tp, var
    if not self.prev:
      raise ValueError(f"variable {name} not found")
    return self.prev.get_var(name)

  def enter_scope(self):
    self.scope = Scope(self.scope)
    self.scope.save = self.stack

  def leave_scope(self):
    self.stack = self.scope.save
    self.nvar -= self.scope.nlocal
    self.scope = self.scope.prev

  def new_label(self):
    label = len(self.labels)
    self.labels.append(None)
    return label

  def set_label(self, label):
    assert label < len(self.labels)
    self.labels[label] = len(self.code)


def move_to(fenv: Func, var, dst):
  if dst != var:
    fenv.code.append(("mov", dst, var))
  return dst


def validate_type(tp):
  if len(tp) == 1 and tp[0] in {"int", "byte"}:
    return tuple(tp)
  raise ValueError("bad type")


def pl_comp_expr(fenv: Func, node, *, allow_var=False):
  if allow_var:
    assert fenv.stack == fenv.nvar
  save = fenv.stack
  tp, var = pl_comp_expr_temp(fenv, node, allow_var=allow_var)
  assert var < fenv.stack
  if allow_var:
    fenv.stack = fenv.nvar
  else:
    fenv.stack = save
  assert var <= fenv.stack
  return tp, var


def pl_comp_expr_temp(fenv: Func, node, *, allow_var=False):
  # read a variable
  if not isinstance(node, list):
    return pl_comp_getvar(fenv, node)

  # anything else
  if len(node) == 0:
    raise ValueError("empty expression")

  # constant
  if len(node) == 2 and node[0] in ("val", "val8", "str"):
    return pl_comp_const(fenv, node)

  # binary operator
  binops = {
      "%", "*", "/", "+", "-", "and", "or", "eq", "ne", "lt", "le", "gt", "ge",
  }
  if len(node) == 3 and node[0] in binops:
    return pl_comp_binop(fenv, node)

  # unary operator
  if len(node) == 2 and node[0] in {"not", "-"}:
    return pl_comp_unop(fenv, node)

  # new scope
  if node[0] in {"do", "then", "else"}:
    return pl_comp_scope(fenv, node)

  # new variable
  if node[0] == "var" and len(node) == 3:
    if not allow_var:
      raise ValueError("variable declaration not allowed here")
    return pl_comp_newvar(fenv, node)

  # update variable
  if node[0] == "set" and len(node) == 3:
    return pl_comp_setvar(fenv, node)

  # condition
  if node[0] == "if" and len(node) >= 3:
    return pl_comp_cond(fenv, node)

  # loop
  if node[0] == "loop" and len(node) == 3:
    return pl_comp_loop(fenv, node)

  # break/continue
  if node[0] == "break":
    if fenv.scope.loop_end < 0:
      raise ValueError("break outside loop")
    fenv.code.append(("jmp", fenv.scope.loop_end))
    return ("void",), -1

  if node[0] == "continue":
    if fenv.scope.loop_start < 0:
      raise ValueError("continue outside loop")
    fenv.code.append(("jmp", fenv.scope.loop_start))
    return ("void",), -1

  if node[0] == "call":
    return pl_comp_call(fenv, node)

  if node[0] == "return":
    return pl_comp_return(fenv, node)

  raise ValueError("unknown expression")


def pl_comp_newvar(fenv: Func, node):
  _, name, kid = node
  tp, var = pl_comp_expr(fenv, kid)
  if var < 0:  # void
    raise ValueError("bad variable init type")
  dst = fenv.add_var(name, tp)
  return tp, move_to(fenv, var, dst)


def pl_comp_getvar(fenv: Func, node):
  assert isinstance(node, str)
  flevel, tp, var = fenv.get_var(node)
  if flevel == fenv.level:
    return tp, var
  else:
    dst = fenv.tmp()
    fenv.code.append(("get_env", flevel, var, dst))
    return tp, dst


def pl_comp_setvar(fenv: Func, node):
  _, name, kid = node
  flevel, dst_tp, dst = fenv.get_var(name)
  tp, var = pl_comp_expr(fenv, kid)
  if dst_tp != tp:
    raise ValueError("type mismatch")
  if flevel == fenv.level:
    return dst_tp, move_to(fenv, var, dst)
  fenv.code.append(("set_env", flevel, var, dst))
  return dst_tp, move_to(fenv, var, fenv.tmp())


def pl_comp_scope(fenv: Func, node):
  fenv.enter_scope()
  tp, var = ("void",), -1
  groups = [[]]
  for kid in node[1:]:
    groups[-1].append(kid)
    if kid[0] == "var":
      groups.append([])
  for g in groups:
    funcs = [
        pl_scan_func(fenv, kid)
        for kid in g if kid[0] == "def" and len(kid) == 4
    ]
    for kid in g:
      if kid[0] == "def" and len(kid) == 4:
        target, *funcs = funcs
        tp, var = pl_comp_func(target, kid)
      else:
        tp, var = pl_comp_expr(fenv, kid, allow_var=True)
  fenv.leave_scope()
  if var >= fenv.stack:
    var = move_to(fenv, var, fenv.tmp())
  return tp, var


def pl_comp_binop(fenv: Func, node):
  op, lhs, rhs = node
  save = fenv.stack
  t1, a1 = pl_comp_expr_temp(fenv, lhs)
  t2, a2 = pl_comp_expr_temp(fenv, rhs)
  fenv.stack = save
  # TODO: pointers
  if "ptr" in (t1[0], t2[0]):
    raise NotImplementedError("pointer arithmetic")
  if not (t1 == t2 and t1[0] in {"int", "byte"}):
    raise ValueError("bad binop types")
  rtype = t1
  if op in {"eq", "ne", "lt", "le", "gt", "ge"}:
    rtype = ("int",)
  suffix = ""
  if t1 == t2 == ("byte",):
    suffix = "8"
  dst = fenv.tmp()
  fenv.code.append(("binop" + suffix, op, a1, a2, dst))
  return rtype, dst


def pl_comp_unop(fenv: Func, node):
  op, kid = node
  tp, var = pl_comp_expr(fenv, kid)
  if op == "-":
    if tp != ("int",):
      raise ValueError("bad unop type")
    dst = fenv.tmp()
    fenv.code.append(("neg", var, dst))
    return tp, dst
  if op == "not":
    if tp != ("int",):
      raise ValueError("bad unop type")
    dst = fenv.tmp()
    fenv.code.append(("not", var, dst))
    return tp, dst
  raise ValueError("unknown unop")


def pl_comp_const(fenv: Func, node):
  if node[0] == "val":
    tp = ("int",)
  elif node[0] == "val8":
    tp = ("byte",)
  elif node[0] == "str":
    tp = ("ptr", "byte")
  else:
    raise ValueError("unknown const")
  dst = fenv.tmp()
  fenv.code.append(("const", node[1], dst))
  return tp, dst


def pl_comp_cond(fenv: Func, node):
  _, cond, yes, *no = node
  l_true = fenv.new_label()
  f_false = fenv.new_label()
  fenv.enter_scope()
  tp, var = pl_comp_expr(fenv, cond, allow_var=True)
  if tp == ("void",):
    raise ValueError("bad condition type")
  fenv.code.append(("jmpf", var, f_false))
  t1, a1 = pl_comp_expr(fenv, yes)
  if a1 >= 0:
    move_to(fenv, a1, fenv.stack)
  t2, a2 = ("void",), -1
  if no:
    fenv.code.append(("jmp", l_true))
  fenv.set_label(f_false)
  if no:
    t2, a2 = pl_comp_expr(fenv, no[0])
    if a2 >= 0:
      move_to(fenv, a2, fenv.stack)
  fenv.set_label(l_true)
  fenv.leave_scope()
  if a1 < 0 or a2 < 0 or t1 != t2:
    return ("void",), -1
  return t1, fenv.tmp()


def pl_comp_loop(fenv: Func, node):
  _, cond, body = node
  fenv.enter_scope()
  fenv.scope.loop_start = fenv.new_label()
  fenv.scope.loop_end = fenv.new_label()
  fenv.set_label(fenv.scope.loop_start)
  _, var = pl_comp_expr(fenv, cond, allow_var=True)
  if var < 0:
    raise ValueError("bad condition type")
  fenv.code.append(("jmpf", var, fenv.scope.loop_end))
  _, _ = pl_comp_expr(fenv, body)
  fenv.code.append(("jmp", fenv.scope.loop_start))
  fenv.set_label(fenv.scope.loop_end)
  fenv.leave_scope()
  return ("void",), -1


def pl_scan_func(fenv: Func, node):
  _, (name, *rtype), args, _ = node
  rtype = validate_type(rtype)
  arg_type_list = tuple(validate_type(x) for _, *x in args)
  key = (name, arg_type_list)
  if key in fenv.scope.names:
    raise ValueError(f"function {name} already defined")
  fenv.scope.names[key] = (rtype, len(fenv.funcs))
  func = Func(fenv)
  func.rtype = rtype
  fenv.funcs.append(func)
  return func


def pl_comp_func(fenv: Func, node):
  _, _, args, body = node
  for arg_name, *arg_type in args:
    if not isinstance(arg_name, str):
      raise ValueError("bad argument name")
    arg_type = validate_type(arg_type)
    if arg_type == ("void",):
      raise ValueError("bad argument type")
    fenv.add_var(arg_name, arg_type)
  assert fenv.stack == len(args)
  body_type, var = pl_comp_expr(fenv, body)
  if fenv.rtype != ("void",) and fenv.rtype != body_type:
    raise ValueError("bad body type")
  if fenv.rtype == ("void",):
    var = -1
  fenv.code.append(("ret", var))
  return ("void",), -1


def pl_comp_call(fenv: Func, node):
  _, name, *args = node
  arg_types = []
  for kid in args:
    tp, var = pl_comp_expr(fenv, kid)
    arg_types.append(tp)
    move_to(fenv, var, fenv.tmp())
  fenv.stack -= len(args)
  key = (name, tuple(arg_types))
  _, _, idx = fenv.get_var(key)
  func = fenv.funcs[idx]
  fenv.code.append(("call", idx, fenv.stack, fenv.level, func.level))
  dst = -1
  if func.rtype != ("void",):
    dst = fenv.tmp()
  return func.rtype, dst


def pl_comp_return(fenv: Func, node):
  _, *kid = node
  tp, var = ("void",), -1
  if kid:
    tp, var = pl_comp_expr_temp(fenv, kid[0])
  if tp != fenv.rtype:
    raise ValueError("bad return type")
  fenv.code.append(("ret", var))
  return tp, var


def pl_comp_main(fenv: Func, node):
  assert node[:3] == ["def", ["main", "int"], []]
  func = pl_scan_func(fenv, node)
  return pl_comp_func(func, node)
