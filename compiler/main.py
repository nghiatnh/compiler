#!/usr/bin/python3
import os
import mmap
import ctypes
import struct
import sys
from typing import Optional


class LoopBreak(Exception):
  pass


class LoopContinue(Exception):
  pass


class FuncReturn(Exception):
  def __init__(self, value):
    super().__init__("return")
    self.value = value


def parse_expr(s: str, idx: int):
  idx = skip_whitespace(s, idx)
  if s[idx] == "(":
    idx += 1
    l = []
    while True:
      idx = skip_whitespace(s, idx)
      if idx >= len(s):
        raise Exception("unbalanced parenthesis")
      if s[idx] == ")":
        idx += 1
        break
      idx, v = parse_expr(s, idx)
      l.append(v)
    return idx, l
  elif s[idx] == ")":
    raise Exception("bad parenthesis")
  else:
    start = idx
    while idx < len(s) and (not s[idx].isspace()) and s[idx] not in "()":
      idx += 1
    if start == idx:
      raise Exception("empty expression")
    return idx, parse_atom(s[start:idx])


def skip_whitespace(s: str, idx: int):
  while True:
    save = idx
    # skip whitespace
    while idx < len(s) and s[idx].isspace():
      idx += 1
    # skip comment
    if idx + 1 < len(s) and s[idx] == ";" and s[idx + 1] == ";":
      idx += 2
      while idx < len(s) and s[idx] != "\n":
        idx += 1
    # if no progress, break
    if idx == save:
      break
  return idx


def parse_atom(s):
  import json
  try:
    return ["val", json.loads(s)]
  except json.JSONDecodeError:
    return s


def pl_parse(s):
  idx, node = parse_expr(s, 0)
  idx = skip_whitespace(s, idx)
  if idx < len(s):
    raise ValueError("traling garbage")
  return node


class Scope:
  def __init__(self, prev: Optional["Scope"]) -> None:
    self.prev = prev
    self.nlocal = 0
    self.names = dict()
    self.loop_start = prev.loop_start if prev else -1
    self.loop_end = prev.loop_end if prev else -1


def scope_get_var(scope: Scope, name):
  while scope:
    if name in scope.names:
      return scope.names[name]
    scope = scope.prev
  return None, -1


class Func:
  def __init__(self, prev: Optional["Func"]) -> None:
    self.prev = prev
    self.level = (prev.level + 1) if prev else 0
    self.rtype = None
    self.funcs = prev.funcs if prev else []
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

  if node[0] == "syscall":
    return pl_comp_syscall(fenv, node)

  raise ValueError("unknown expression")


def pl_comp_syscall(fenv: Func, node):
  _, num, *args = node
  dsts = []

  # Compile the arguments
  arg_vars = []
  for kid in args:
    tp, var = pl_comp_expr(fenv, kid)
    move_to(fenv, var, fenv.tmp())
    arg_vars.append(fenv.stack - 1)

  # Adjust the stack
  fenv.stack -= len(arg_vars)

  # Generate the syscall instruction
  dst = fenv.tmp()
  fenv.code.append(("syscall", dst, num[1], *arg_vars))

  return ("int",), dst


def pl_comp_newvar(fenv: Func, node):
  _, name, kid = node
  tp, var = pl_comp_expr(fenv, kid)
  if var < 0:  # void
    raise ValueError("bad variable init type")
  dst = fenv.add_var(name, tp)
  return tp, move_to(fenv, var, dst)


def move_to(fenv: Func, var, dst):
  if dst != var:
    fenv.code.append(("mov", dst, var))
  return dst


def validate_type(tp):
  if len(tp) == 1 and tp[0] in {"int", "byte"}:
    return tuple(tp)
  raise ValueError("bad type")


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
  if t1 == t2 and t1 == ("byte",):
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
  fenv.scope.loop_start = fenv.new_label()
  fenv.scope.loop_end = fenv.new_label()
  fenv.enter_scope()
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


def pl_comp_main(fenv: Func, node):
  assert node[:3] == ["def", ["main", "int"], []]
  func = pl_scan_func(fenv, node)
  return pl_comp_func(func, node)


def pl_parse_main(s):
  return pl_parse("(def (main int) () (do " + s + "))")


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


class CodeGen:
  # register encodings
  A = 0
  C = 1
  D = 2
  B = 3
  SP = 4
  BP = 5
  SI = 6
  DI = 7

  def __init__(self):
    self.buf = bytearray()
    self.jmps = dict()  # label -> offset list
    self.calls = dict()  # func index -> offset list
    self.strings = dict()  # string literal -> offset list
    self.func2off = []  # func index -> offset
    self.fields = dict()
    self.vaddr = 0x4

  def mov(self, dst, src):
    if src == dst:
      return
    self.load_rax(src)
    self.store_rax(dst)

  # mov reg, [rm + disp]
  def asm_load(self, reg, rm, disp):
    self.asm_disp(b"\x48\x8b", reg, rm, disp)

  # mov [rm + disp], reg
  def asm_store(self, rm, disp, reg):
    self.asm_disp(b"\x48\x89", reg, rm, disp)

  def store_rax(self, dst):
    # mov [rbx + dst * 8], rax
    self.asm_store(CodeGen.B, dst * 8, CodeGen.A)

  def load_rax(self, src):
    # mov rax, [rbx + src * 8]
    self.asm_load(CodeGen.A, CodeGen.B, src * 8)

  # instr reg, [rm + disp]
  # instr [rm + disp], reg
  def asm_disp(self, lead, reg, rm, disp):
    assert reg < 16 and rm < 16 and rm != CodeGen.SP
    lead = bytearray(lead)  # optional prefix + opcode
    if reg >= 8 or rm >= 8:
      assert (lead[0] >> 4) == 0b0100  # REX
      lead[0] |= (reg >> 3) << 2  # REX.R
      lead[0] |= (rm >> 3) << 0  # REX.B
      reg &= 0b111
      rm &= 0b111

    self.buf.extend(lead)
    if disp == 0:
      mod = 0  # [rm]
    elif -128 <= disp < 128:
      mod = 1  # [rm + disp8]
    else:
      mod = 2  # [rm + disp32]
    self.buf.append((mod << 6) | (reg << 3) | rm)  # ModR/M
    if mod == 1:
      self.i8(disp)
    if mod == 2:
      self.i32(disp)

  def i8(self, x):
    self.buf.append(x if x >= 0 else (x + 256))

  def i32(self, x):
    self.buf.extend(struct.pack("<i", x))

  def i64(self, x):
    self.buf.extend(struct.pack("<q", x))

  def const(self, val, dst):
    assert isinstance(val, (int, str))
    if isinstance(val, str):
      self.buf.extend(b"\x48\x8d\x05")  # lea rax, [rip + disp32]
      self.strings.setdefault(val, []).append(len(self.buf))
      self.buf.extend(b"\x00\x00\x00\x00")  # placeholder
    elif val == 0:
      self.buf.extend(b"\x31\xc0")  # xor eax, eax
    else:
      self.buf.extend(b"\x48\xb8")  # mov rax, imm64
      self.i64(val)
    self.store_rax(dst)

  def patch_addr(self, patch_off, dst_off):
    src_off = patch_off + 4  # rip
    relative = struct.pack("<i", dst_off - src_off)
    self.buf[patch_off:patch_off + 4] = relative

  def code_end(self):
    # fill in the call addresses
    for L, offsets in self.calls.items():
      dst_off = self.func2off[L]
      for patch_off in offsets:
        self.patch_addr(patch_off, dst_off)
    # strings
    for s, offsets in self.strings.items():
      off = len(self.buf)
      for patch_off in offsets:
        self.patch_addr(patch_off, off)
      self.buf.extend(s.encode("utf-8") + b"\0")
    self.strings.clear()

  def jmp(self, L):
    self.buf.extend(b"\xe9")  # jmp
    self.jmps.setdefault(L, []).append(len(self.buf))
    self.buf.extend(b"\x00\x00\x00\x00")  # placeholder

  def jmpf(self, a1, L):
    self.load_rax(a1)
    self.buf.extend(
        b"\x48\x85\xc0"
        b"\x0f\x84"  # je
    )  # test rax, rax
    self.jmps.setdefault(L, []).append(len(self.buf))
    self.buf.extend(b"\x00\x00\x00\x00")  # placeholder

  def asm_call(self, L):
    self.buf.extend(b"\xe8")  # call
    self.calls.setdefault(L, []).append(len(self.buf))
    self.buf.extend(b"\x00\x00\x00\x00")  # placeholder

  def func(self, func: Func):
    self.func2off.append(len(self.buf))
    pos2off = []
    for instr_name, *instr_args in func.code:
      pos2off.append(len(self.buf))
      method = getattr(self.__class__, instr_name)
      method(self, *instr_args)
    for L, offsets in self.jmps.items():
      dst_off = pos2off[func.labels[L]]
      for patch_off in offsets:
        self.patch_addr(patch_off, dst_off)
    self.jmps.clear()

  def call(self, func, arg_start, level_cur, level_new):
    assert 1 <= level_cur
    assert 1 <= level_new <= level_cur + 1
    if level_new > level_cur:
      self.buf.append(0x53)  # push rbx
    for _ in range(min(level_new, level_cur) - 1):
      self.buf.extend(b"\xff\xb4\x24")  # push [rsp + (level_new - 1) * 8]
      self.i32((level_new - 1) * 8)
    # make a new frame and call the target
    self.buf.extend(b"\x48\x81\xc3")
    self.i32(arg_start * 8)  # add rbx, arg_start*8
    self.asm_call(func)  # call func
    self.buf.extend(b"\x48\x81\xc3")
    self.i32(-arg_start * 8)

    self.buf.extend(b"\x48\x81\xc4")  # add rsp, (level_new - 1) * 8
    self.i32((level_new - 1) * 8)

  def ret(self, a1):
    if a1 > 0:
      self.load_rax(a1)
      self.store_rax(0)
    self.buf.append(0xc3)  # ret

  def load_env_addr(self, level_var):
    self.buf.extend(b"\x48\x8b\x84\x24")  # mov rax, [rsp + level_var * 8]
    self.i32(level_var * 8)

  def get_env(self, level_var, var, dst):
    self.load_env_addr(level_var)
    # mov rax, [rax + var * 8]
    self.asm_load(CodeGen.A, CodeGen.A, var * 8)
    # mov [rbx + dst * 8], rax
    self.store_rax(dst)

  def set_env(self, level_var, var, src):
    self.load_env_addr(level_var)
    # mov rdx, [rbx + src * 8]
    self.asm_load(CodeGen.D, CodeGen.B, src * 8)
    # mov [rax + var * 8], rdx
    self.asm_store(CodeGen.A, var * 8, CodeGen.D)

  def binop(self, op, a1, a2, dst):
    self.load_rax(a1)
    arith = {
        "+": b"\x48\x03",  # add reg, rm
        "-": b"\x48\x2b",  # sub reg, rm
        "*": b"\x48\x0f\xaf",  # imul reg, rm
    }
    if op in arith:
      # op rax, [rbx + a2 * 8]
      self.asm_disp(arith[op], CodeGen.A, CodeGen.B, a2 * 8)
    if op in {"/", "%"}:
      # xor edx, edx
      self.buf.extend(b"\x31\xd2")
      # idiv rax, [rbx + a2 * 8]
      self.buf.extend(b"\x48\xf7\xbb")
      self.i32(a2 * 8)
      if op == "%":
        # mov rax, rdx
        self.buf.extend(b"\x48\x89\xd0")
    cmp = {
        "eq": b"\x0f\x94\xc0",  # sete al
        "ne": b"\x0f\x95\xc0",  # setne al
        "ge": b"\x0f\x9d\xc0",  # setge al
        "gt": b"\x0f\x9f\xc0",  # setg al
        "le": b"\x0f\x9e\xc0",  # setle al
        "lt": b"\x0f\x9c\xc0",  # setl al
    }
    if op in cmp:
      # cmp rax, [rbx + a2 * 8]
      self.asm_disp(b"\x48\x3b", CodeGen.A, CodeGen.B, a2 * 8)
      # setcc al
      self.buf.extend(cmp[op])
      # movzx eax, al
      self.buf.extend(b"\x0f\xb6\xc0")
    self.store_rax(dst)

  # C function: int64_t (*)(void *stack)
  def mem_entry(self):
    # the first argument is the data stack
    self.buf.extend(b"\x53")  # push rbx
    self.buf.extend(b"\x48\x89\xFB")  # mov rbx, rdi
    # call the main function
    self.asm_call(0)
    # the return value
    self.buf.extend(b"\x48\x8b\x03")  # mov rax, [rbx]
    self.buf.extend(b"\x5b")  # pop rbx
    self.buf.extend(b"\xc3")  # ret

  def output_mem(self, root: Func):
    self.mem_entry()
    for func in root.funcs:
      self.func(func)
    self.code_end()

  def syscall(self, dst, num, *arg_list):
    self.buf.extend(b"\xb8")
    # mov eax, imm32
    self.i32(num)
    arg_regs = [CodeGen.DI, CodeGen.SI, CodeGen.D, 10, 8, 9]
    assert len(arg_list) <= len(arg_regs)
    for i, arg in enumerate(arg_list):
      # mov reg, [rbx + arg*8]
      self.asm_load(arg_regs[i], CodeGen.B, arg * 8)
    self.buf.extend(b"\x0f\x05")
    self.store_rax(dst)
    # syscall
    # mov [rbx + dst*8], rax

  # compile the program to an ELF executable
  def output_elf(self, root: Func):
    # ELF header + program header
    # self.elf_begin()
    # machine code
    start = len(self.buf)
    self.code_entry()
    for func in root.funcs:
      self.func(func)
    print(self.buf[start:])
    self.code_end()
    # fill in some ELF fields
    # self.elf_end()

  def padding(self):
    while len(self.buf) % 16:
      self.buf.append(0)

  def elf_begin(self):
    self.elf_header()

    phdr_start = len(self.buf)  # the program header starts here
    self.elf_program_header()
    # program header size
    self.setf('e_phentsize', len(self.buf) - phdr_start)
    # number of program headers: 1
    self.setf('e_phnum', 1)
    self.padding()
    # the entry point: the virtual address where the program start
    self.setf('e_entry', self.vaddr + len(self.buf))

  def elf_end(self):
    self.setf('p_filesz', len(self.buf))
    self.setf('p_memsz', len(self.buf))

  def code_entry(self):
    # create the data stack
    self.buf.extend(
        b"\xb8\x09\x00\x00\x00"  # mov eax, 9
        b"\x31\xff"  # xor edi, edi// addr = NULL
        b"\x48\xc7\xc6"  # mov rsi, xxx// len
    )
    self.i32(8 << 20)  # 8M
    self.buf.extend(
        # prot = PROT_READ|PROT_WRITE
        b"\xba\x03\x00\x00\x00"  # mov edx, 3
        # flags = MAP PRIVATE|MAP ANONYMOUS
        b"\x41\xba\x22\x00\x00\x00"  # mov r10d, 0x22
        b"\x49\x83\xc8\xff"  # or r8, -1// fd = -1
        b"\x4d\x31\xc9"  # xor r9, r9// offset = 0
        b"\x0f\x05"  # syscall
        b"\x48\x89\xc3"  # mov rbx, rax// the data stack
    )
    # call the main function
    self.asm_call(0)
    # exit
    self.buf.extend(
        b"\xb8\x3c\x00\x00\x00"  # mov eax, 60
        b"\x48\x8b\x3b"  # mov rdi, [rbx]
        b"\x0f\x05"  # syscall
    )

  def padding(self):
    while len(self.buf) % 16:
      self.buf.append(0)

  def elf_program_header(self):
    # p_type, p_flags
    self.buf.extend(bytes.fromhex('01 00 00 00 05 00 00 00'))
    # p_offset
    self.i64(0)
    # p_vaddr, p_paddr
    self.i64(self.vaddr)
    self.i64(self.vaddr)  # useless
    self.f64('p_filesz')
    self.f64('p_memsz')
    # p_align
    self.i64(0x1000)

  def elf_header(self):
    self.buf.extend(bytes.fromhex('7F 45 4C 46 02 01 01 00'))
    self.buf.extend(bytes.fromhex('00 00 00 00 00 00 00 00'))
    # e_type, e_machine, e_version
    self.buf.extend(bytes.fromhex('02 00 3E 00 01 00 00 00'))
    self.f64('e_entry')
    self.f64('e_phoff')
    self.f64('e_shoff')
    self.f32('e_flags')
    self.f16('e_ehsize')
    self.f16('e_phentsize')
    self.f16('e_phnum')
    self.f16('e_shentsize')
    self.f16('e_shnum')
    self.f16('e_shstrndx')
    self.setf('e_phoff', len(self.buf))  # offset of the program header
    self.setf('e_ehsize', len(self.buf))  # size of the ELF header

  def f16(self, name):
    self.fields[name] = (2, len(self.buf))
    self.buf.extend(b'\x00\x00')

  def f32(self, name):
    self.fields[name] = (4, len(self.buf))
    self.buf.extend(b'\x00\x00\x00\x00')

  def f64(self, name):
    self.fields[name] = (8, len(self.buf))
    self.buf.extend(b'\x00\x00\x00\x00\x00\x00\x00\x00')

  def setf(self, name, value):
    size, offset = self.fields[name]
    fmt = {2: '<H', 4: '<I', 8: '<Q'}[size]
    self.buf[offset:offset+size] = struct.pack(fmt, value)


# execute the program as a ctype function
class MemProgram:
  def __init__(self, code):
    # copy the code to an executable memory buffer
    flags = mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS
    prot = mmap.PROT_EXEC | mmap.PROT_READ | mmap.PROT_WRITE
    self.code = mmap.mmap(-1, len(code), flags=flags, prot=prot)
    self.code[:] = code
    # ctype function: int64_t (*)(void *stack)
    func_type = ctypes.CFUNCTYPE(ctypes.c_int64, ctypes.c_void_p)
    cbuf = ctypes.c_void_p.from_buffer(self.code)
    self.cfunc = func_type(ctypes.addressof(cbuf))

    prot = mmap.PROT_READ | mmap.PROT_WRITE
    self.stack = mmap.mmap(-1, 8 << 20, flags=flags, prot=prot)
    cbuf = ctypes.c_void_p.from_buffer(self.stack)
    self.stack_addr = ctypes.addressof(cbuf)

  def invoke(self):
    return self.cfunc(self.stack_addr)


def main():
  file = sys.argv[1]
  # output = sys.argv[2]
  # source text
  with open(file, 'rt', encoding='utf-8') as fp:
    text = fp.read()
  # parse & compile
  node = pl_parse_main(text)
  root = Func(None)
  _ = pl_comp_main(root, node)
  print(root.funcs[0].code)
  # generate output
  gen = CodeGen()
  gen.output_mem(root)
  # gen.output_elf(root)
  print(gen.buf)
  prog = MemProgram(gen.buf)
  sys.exit(prog.invoke())
  # print(gen.buf)
  fd = os.open("test.out", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o755)
  with os.fdopen(fd, 'wb', closefd=True) as fp:
    fp.write(gen.buf)


if __name__ == "__main__":
  main()
