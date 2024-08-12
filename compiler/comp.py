from typing import Optional, List, Tuple, Dict
from parser import Node, NodeType
from enum import Enum


class OpCode(Enum):
  MOV = "mov"
  GET_ENV = "get_env"
  SET_ENV = "set_env"
  SYSCALL = "syscall"
  CONST = "const"
  BINOP = "binop"
  NEG = "neg"
  NOT = "not"
  JMP = "jmp"
  JMPF = "jmpf"
  CALL = "call"
  RET = "ret"


class ReturnType(Enum):
  VOID = "void"
  INT = "int"
  BYTE = "byte"


class ReturnData:
  def __init__(self, tp: ReturnType, val: int) -> None:
    self.type = tp
    self.val = val


class ByteCode:
  def __init__(self, op: OpCode, *args) -> None:
    self.op = op
    self.args = args

  def __str__(self) -> str:
    return f"{self.op.value} {''.join(str(x) for x in self.args)}"


class Scope:
  def __init__(self, prev: Optional["Scope"]) -> None:
    self.prev = prev
    self.nlocal = 0
    self.names: Dict[str, ReturnData] = {}
    self.loop_start = prev.loop_start if prev else -1
    self.loop_end = prev.loop_end if prev else -1
    self.save = -1


def scope_get_var(scope: Optional[Scope], name: str) -> ReturnData:
  while scope:
    if name in scope.names:
      return scope.names[name]
    scope = scope.prev
  return ReturnData(None, -1)


class Func:
  def __init__(self, prev: Optional["Func"] = None) -> None:
    self.prev = prev
    self.level = (prev.level + 1) if prev else 0
    self.rtype: ReturnType = None
    self.funcs: List[Func] = prev.funcs if prev else []
    self.scope = Scope(None)
    # the output: a list of instructions
    self.code: List[ByteCode] = []
    # current number of local variable in the stack (non-temporary)
    self.nvar = 0
    # current number of variables (both locals and temporaries)
    self.stack = 0
    # label IDs to instruction locations
    self.labels: List[int] = []

  def tmp(self) -> int:
    dst = self.stack
    self.stack += 1
    return dst

  def add_var(self, name: str, tp: ReturnType) -> int:
    if name in self.scope.names:
      raise ValueError(f"variable {name} already exists")
    self.scope.names[name] = ReturnData(tp, self.nvar)
    self.scope.nlocal += 1
    assert self.stack == self.nvar
    dst = self.stack
    self.stack += 1
    self.nvar += 1
    return dst

  def get_var(self, name: str) -> Tuple[int, ReturnData]:
    var = scope_get_var(self.scope, name)
    if var.val >= 0:
      return self.level, var
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

  def new_label(self) -> int:
    label = len(self.labels)
    self.labels.append(None)
    return label

  def set_label(self, label):
    assert label < len(self.labels)
    self.labels[label] = len(self.code)

  def add_code(self, code: ByteCode):
    self.code.append(code)


def validate_type(tp: ReturnType) -> ReturnType:
  if ReturnType(tp) not in (ReturnType.INT, ReturnType.BYTE):
    raise ValueError("bad type")
  return ReturnType(tp)


class Compiler:
  def _move_to(self, fenv: Func, var: int, dst: int):
    if dst != var:
      fenv.add_code(ByteCode(OpCode.MOV, dst, var))
    return dst

  def comp_expr(self, fenv: Func, node: Node, *, allow_var=False) -> ReturnData:
    if allow_var:
      assert fenv.stack == fenv.nvar
    save = fenv.stack
    var = self.comp_expr_temp(fenv, node, allow_var=allow_var)
    assert var.val < fenv.stack
    fenv.stack = fenv.nvar if allow_var else save
    assert var.val <= fenv.stack
    return var

  def comp_expr_temp(
      self,
      fenv: Func,
      node: Node,
      *,
      allow_var=False
  ) -> ReturnData:
    # anything else
    if node.type == NodeType.EMPTY or node.type == NodeType.UNINIT:
      raise ValueError("empty expression")

    # read a variable
    if node.type == NodeType.SYM:
      return self.comp_getvar(fenv, node)

    # constant
    if node.type == NodeType.VAL:
      return self.comp_const(fenv, node)

    # binary operator
    binops = [
        NodeType.AND, NodeType.OR, NodeType.EQ, NodeType.NE, NodeType.LT,
        NodeType.LE, NodeType.GT, NodeType.GE, NodeType.ADD, NodeType.SUB,
        NodeType.MUL, NodeType.DIV, NodeType.MOD
    ]
    if node.type in binops:
      return self.comp_binop(fenv, node)

    # unary operator
    if node.type in [NodeType.NEG, NodeType.NOT]:
      return self.comp_unop(fenv, node)

    # new scope
    if node.type in [NodeType.DO, NodeType.THEN, NodeType.ELSE]:
      return self.comp_scope(fenv, node)

    # new variable
    if node.type == NodeType.VAR:
      if not allow_var:
        raise ValueError("variable declaration not allowed here")
      return self.comp_newvar(fenv, node)

    # update variable
    if node.type == NodeType.SET:
      return self.comp_setvar(fenv, node)

    # condition
    if node.type == NodeType.IF:
      return self.comp_cond(fenv, node)

    # loop
    if node.type == NodeType.LOOP:
      return self.comp_loop(fenv, node)

    # break/continue
    if node.type == NodeType.BREAK:
      if fenv.scope.loop_end < 0:
        raise ValueError("break outside loop")
      fenv.add_code(ByteCode(OpCode.JMP, fenv.scope.loop_end))
      return ReturnData(ReturnType.VOID, -1)

    if node.type == NodeType.CONTINUE:
      if fenv.scope.loop_start < 0:
        raise ValueError("continue outside loop")
      fenv.add_code(ByteCode(OpCode.JMP, fenv.scope.loop_start))
      return ReturnData(ReturnType.VOID, -1)

    if node.type == NodeType.CALL:
      return self.comp_call(fenv, node)

    if node.type == NodeType.RETURN:
      return self.comp_return(fenv, node)

    raise ValueError("unknown expression")

  def comp_newvar(self, fenv: Func, node: Node) -> ReturnData:
    # var <name> <value>
    if len(node.children) != 2:
      raise ValueError("bad variable declaration")
    name, val = node.children
    rd = self.comp_expr(fenv, val)
    if rd.val < 0:  # void
      raise ValueError("bad variable init type")
    dst = fenv.add_var(name.value, rd.type)
    return ReturnData(rd.type, self._move_to(fenv, rd.val, dst))

  def comp_getvar(self, fenv: Func, node: Node) -> ReturnData:
    assert node.type == NodeType.SYM
    flevel, rd = fenv.get_var(node.value)
    if flevel == fenv.level:
      return rd
    else:
      dst = fenv.tmp()
      fenv.code.append(ByteCode(OpCode.GET_ENV, flevel, rd.val, dst))
      return ReturnData(rd.type, dst)

  def comp_setvar(self, fenv: Func, node: Node):
    # set <name> <value>
    if len(node.children) != 2:
      raise ValueError("bad variable assignment")
    name, val = node.children
    flevel, dst = fenv.get_var(name.value)
    expr = self.comp_expr(fenv, val)
    if dst.type != expr.type:
      raise ValueError("type mismatch")
    if flevel == fenv.level:
      return ReturnData(dst.type, self._move_to(fenv, expr.val, dst.val))
    fenv.code.append(ByteCode(OpCode.SET_ENV, flevel, expr.val, dst.val))
    return ReturnData(dst.type, self._move_to(fenv, expr.val, fenv.tmp()))

  def comp_scope(self, fenv: Func, node: Node) -> ReturnData:
    fenv.enter_scope()
    rd = ReturnData(ReturnType.VOID, -1)
    # split children into groups separated by variable declarations
    groups: List[List[Node]] = [[]]
    for child in node.children:
      groups[-1].append(child)
      if child.type == NodeType.VAR:
        groups.append([])
    # Functions are visible before they are defined,
    # as long as they don"t cross a variable declaration.
    # This allows adjacent functions to call each other mutually.
    for g in groups:
      # preprocess functions
      funcs = [
          self.scan_func(fenv, child)
          for child in g if child.type == NodeType.DEF
      ]
      # compile subexpressions
      for child in g:
        if child.type == NodeType.DEF:
          if len(child.children) != 3:
            raise ValueError("bad function definition")
          target = funcs.pop(0)
          rd = self.comp_func(target, child)
        else:
          rd = self.comp_expr(fenv, child, allow_var=True)
    fenv.leave_scope()
    # the return is either a local variable or a new temporary
    if rd.val >= fenv.stack:
      rd.val = self._move_to(fenv, rd.val, fenv.tmp())
    return rd

  def comp_binop(self, fenv: Func, node: Node) -> ReturnData:
    if len(node.children) != 2:
      raise ValueError("bad binary operator")
    lhs, rhs = node.children
    save = fenv.stack
    rd1 = self.comp_expr_temp(fenv, lhs)
    rd2 = self.comp_expr_temp(fenv, rhs)
    fenv.stack = save
    # TODO: pointers
    if not (rd1.type == rd2.type and rd1.type in
            [ReturnType.INT, ReturnType.BYTE]):
      raise ValueError("bad binop types")
    rtype = rd1.type
    if node.type in [NodeType.EQ, NodeType.NE, NodeType.LT, NodeType.LE,
                     NodeType.GT, NodeType.GE]:
      rtype = ReturnType.INT
    dst = fenv.tmp()
    fenv.add_code(ByteCode(OpCode.BINOP, node.type, rd1.val, rd2.val, dst))
    return ReturnData(rtype, dst)

  def comp_unop(self, fenv: Func, node: Node) -> ReturnData:
    if len(node.children) != 1:
      raise ValueError("bad unary operator")
    child = node.children[0]
    rd = self.comp_expr(fenv, child)
    if rd.type != ReturnType.INT:
      raise ValueError("bad unop type")
    dst = fenv.tmp()
    if node.type == NodeType.NEG:
      fenv.add_code(ByteCode(OpCode.NEG, rd.val, dst))
      return ReturnData(ReturnType.INT, dst)
    if node.type == NodeType.NOT:
      fenv.add_code(ByteCode(OpCode.NOT, rd.val, dst))
      return ReturnData(ReturnType.INT, dst)
    raise ValueError("unknown unop")

  def comp_const(self, fenv: Func, node: Node) -> ReturnData:
    if node.type != NodeType.VAL:
      raise ValueError("unknown const")
    dst = fenv.tmp()
    fenv.add_code(ByteCode(OpCode.CONST, node.value, dst))
    return ReturnData(ReturnType.INT, dst)

  def comp_cond(self, fenv: Func, node: Node) -> ReturnData:
    if len(node.children) < 2:
      raise ValueError("bad condition expression")
    cond, yes, *no = node.children
    l_true = fenv.new_label()
    f_false = fenv.new_label()
    fenv.enter_scope()
    rd = self.comp_expr(fenv, cond, allow_var=True)
    if rd.type == ReturnType.VOID:
      raise ValueError("bad condition type")
    fenv.code.append(ByteCode(OpCode.JMPF, rd.val, f_false))
    rd1 = self.comp_expr(fenv, yes)
    if rd1.val >= 0:
      self._move_to(fenv, rd1.val, fenv.stack)
    rd2 = ReturnData(ReturnType.VOID, -1)
    if no:
      fenv.add_code(ByteCode(OpCode.JMP, l_true))
    fenv.set_label(f_false)
    if no:
      rd2 = self.comp_expr(fenv, no[0])
      if rd2.val >= 0:
        self._move_to(fenv, rd2.val, fenv.stack)
    fenv.set_label(l_true)
    fenv.leave_scope()
    if rd1.val < 0 or rd2.val < 0 or rd1.type != rd2.type:
      return ReturnData(ReturnType.VOID, -1)
    return ReturnData(rd1.type, fenv.tmp())

  def comp_loop(self, fenv: Func, node: Node) -> ReturnData:
    if len(node.children) != 2:
      raise ValueError("bad loop expression")
    cond, body = node.children
    fenv.enter_scope()
    fenv.scope.loop_start = fenv.new_label()
    fenv.scope.loop_end = fenv.new_label()
    fenv.set_label(fenv.scope.loop_start)
    expr = self.comp_expr(fenv, cond, allow_var=True)
    if expr.val < 0:
      raise ValueError("bad condition type")
    fenv.code.append(ByteCode(OpCode.JMPF, expr.val, fenv.scope.loop_end))
    self.comp_expr(fenv, body)
    fenv.code.append(ByteCode(OpCode.JMP, fenv.scope.loop_start))
    fenv.set_label(fenv.scope.loop_end)
    fenv.leave_scope()
    return ReturnData(ReturnType.VOID, -1)

  def scan_func(self, fenv: Func, node: Node) -> Func:
    name_def, args_def, _ = node.children
    rtype = validate_type(name_def.children[0].value)
    arg_type_list = tuple(validate_type(
        x.children[0].value) for x in args_def.children)
    key = (name_def.value, arg_type_list)
    if key in fenv.scope.names:
      raise ValueError(f"function {name_def.value} already defined")
    fenv.scope.names[key] = ReturnData(rtype, len(fenv.funcs))
    func = Func(prev=fenv)
    func.rtype = rtype
    fenv.funcs.append(func)
    return func

  def comp_func(self, fenv: Func, node: Node) -> ReturnData:
    if len(node.children) != 3:
      raise ValueError("bad function definition")
    _, args_def, body = node.children
    for arg in args_def.children:
      if not isinstance(arg.value, str):
        raise ValueError("bad argument name")
      arg_type = validate_type(arg.children[0].value)
      if arg_type == ReturnType.VOID:
        raise ValueError("bad argument type")
      fenv.add_var(arg.value, arg_type)
    assert fenv.stack == len(args_def.children)
    rd = self.comp_expr(fenv, body)
    if fenv.rtype != ReturnType.VOID and fenv.rtype != rd.type:
      raise ValueError("bad body type")
    if fenv.rtype == ReturnType.VOID:
      rd.val = -1
    fenv.add_code(ByteCode(OpCode.RET, rd.val))
    return ReturnData(ReturnType.VOID, -1)

  def comp_call(self, fenv: Func, node: Node) -> ReturnData:
    name, *args = node.children
    arg_types = []
    for child in args:
      expr = self.comp_expr(fenv, child)
      arg_types.append(expr.type)
      self._move_to(fenv, expr.val, fenv.tmp())
    fenv.stack -= len(args)
    key = (name.value, tuple(arg_types))
    _, var = fenv.get_var(key)
    func = fenv.funcs[var.val]
    fenv.add_code(ByteCode(OpCode.CALL, var.val,
                  fenv.stack, fenv.level, func.level))
    if func.rtype != ReturnType.VOID:
      dst = fenv.tmp()
    return ReturnData(func.rtype, dst)

  def comp_return(self, fenv: Func, node: Node) -> ReturnData:
    if len(node.children) > 1:
      raise ValueError("bad return expression")
    rd = ReturnData(ReturnType.VOID, -1)
    if len(node.children) == 1:
      rd = self.comp_expr_temp(fenv, node.children[0])
    if rd.type != fenv.rtype:
      raise ValueError("bad return type")
    fenv.add_code(ByteCode(OpCode.RET, rd.val))
    return rd

  def comp_main(self, fenv: Func, node: Node):
    assert node.type == NodeType.DEF and node.children[
        0].value == "main" and node.children[0].children[0].value == "int"
    func = self.scan_func(fenv, node)
    return self.comp_func(func, node)
