from typing import Dict, List, Union
import struct

from compiler.symbol_table import SymbolTable
from compiler.constants import BinaryOp


class Registers:
  """
  Registers
  =========
  Registers class to represent the registers encoding.
  """
  A = 0
  C = 1
  D = 2
  B = 3
  SP = 4
  BP = 5
  SI = 6
  DI = 7


class MachineCodeGenerator:
  """
  MachineCodeGenerator
  ====================
  MachineCodeGenerator is a class that is used to generate machine code from the
  bytecodes.
  """

  def __init__(self, global_scope: SymbolTable):
    self._global_scope = global_scope
    self.code = bytearray()
    self.jmps: Dict[int, List[int]] = {}  # label -> offset list
    self.calls: Dict[int, List[int]] = {}  # func index -> offset list
    self.strings: Dict[str, List[int]] = {}  # string literal -> offset list
    self.scope2off = []  # func index -> offset
    self.fields = {}
    self.vaddr = 0x4

  # ========================================================================= #
  # Private methods                                                           #
  # ========================================================================= #

  # mov reg, [rm + disp]
  def _asm_load(self, reg: int, rm: int, disp: int):
    self._asm_disp(b"\x48\x8b", reg, rm, disp)

  # mov [rm + disp], reg
  def _asm_store(self, rm: int, disp: int, reg: int):
    self._asm_disp(b"\x48\x89", reg, rm, disp)

  def _store_rax(self, dst: int):
    # mov [rbx + dst * 8], rax
    self._asm_store(Registers.B, dst * 8, Registers.A)

  def _load_rax(self, src: int):
    # mov rax, [rbx + src * 8]
    self._asm_load(Registers.A, Registers.B, src * 8)

  # instr reg, [rm + disp]
  # instr [rm + disp], reg
  def _asm_disp(self, lead: int, reg: int, rm: int, disp: int):
    assert reg < 16 and rm < 16 and rm != Registers.SP
    lead = bytearray(lead)  # optional prefix + opcode
    if reg >= 8 or rm >= 8:
      assert (lead[0] >> 4) == 0b0100  # REX
      lead[0] |= (reg >> 3) << 2  # REX.R
      lead[0] |= (rm >> 3) << 0  # REX.B
      reg &= 0b111
      rm &= 0b111

    self.code.extend(lead)
    if disp == 0:
      mod = 0  # [rm]
    elif -128 <= disp < 128:
      mod = 1  # [rm + disp8]
    else:
      mod = 2  # [rm + disp32]
    self.code.append((mod << 6) | (reg << 3) | rm)  # ModR/M
    if mod == 1:
      self._i8(disp)
    if mod == 2:
      self._i32(disp)

  def _i8(self, x: int):
    self.code.append(x if x >= 0 else (x + 256))

  def _i32(self, x: int):
    self.code.extend(struct.pack("<i", x))

  def _i64(self, x: int):
    self.code.extend(struct.pack("<q", x))

  def _patch_addr(self, patch_off: int, dst_off: int):
    src_off = patch_off + 4  # rip
    relative = struct.pack("<i", dst_off - src_off)
    self.code[patch_off:patch_off + 4] = relative

  def _code_end(self):
    # fill in the call addresses
    for label, offsets in self.calls.items():
      dst_off = self.scope2off[label]
      for patch_off in offsets:
        self._patch_addr(patch_off, dst_off)
    # strings
    for s, offsets in self.strings.items():
      off = len(self.code)
      for patch_off in offsets:
        self._patch_addr(patch_off, off)
      self.code.extend(s.encode("utf-8") + b"\0")
    self.strings.clear()

  def _asm_call(self, label: int):
    self.code.extend(b"\xe8")  # call
    self.calls.setdefault(label, []).append(len(self.code))
    self.code.extend(b"\x00\x00\x00\x00")  # placeholder

  def _load_env_addr(self, level_var: int):
    self.code.extend(b"\x48\x8b\x84\x24")  # mov rax, [rsp + level_var * 8]
    self._i32(level_var * 8)

  def _padding(self):
    while len(self.code) % 16:
      self.code.append(0)

  def _code_entry(self):
    # create the data stack
    self.code.extend(
        b"\xb8\x09\x00\x00\x00"  # mov eax, 9
        b"\x31\xff"  # xor edi, edi// addr = NULL
        b"\x48\xc7\xc6"  # mov rsi, xxx// len
    )
    self._i32(8 << 20)  # 8M
    self.code.extend(
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
    self._asm_call(0)
    # exit
    self.code.extend(
        b"\xb8\x3c\x00\x00\x00"  # mov eax, 60
        b"\x48\x8b\x3b"  # mov rdi, [rbx]
        b"\x0f\x05"  # syscall
    )

  def _scope(self, scope: SymbolTable):
    self.scope2off.append(len(self.code))
    pos2off = []
    for code in scope.code:
      pos2off.append(len(self.code))
      method = getattr(self.__class__, f"_{code.opcode.name.lower()}_")
      method(self, *code.operands)
    for label, offsets in self.jmps.items():
      dst_off = pos2off[scope.labels[label]]
      for patch_off in offsets:
        self._patch_addr(patch_off, dst_off)
    self.code.append(0xc3)  # ret
    self.jmps.clear()
    for child in scope.children:
      self._scope(child)

  # ========================================================================= #
  # Generation methods                                                        #
  # ========================================================================= #

  def _mov_(self, dst: int, src: int):
    if src == dst:
      return
    self._load_rax(src)
    self._store_rax(dst)

  def _get_env_(self, level_var: int, var: int, dst: int):
    self._load_env_addr(level_var)
    # mov rax, [rax + var * 8]
    self._asm_load(Registers.A, Registers.A, var * 8)
    # mov [rbx + dst * 8], rax
    self._store_rax(dst)

  def _set_env_(self, level_var: int, var: int, src: int):
    self._load_env_addr(level_var)
    # mov rdx, [rbx + src * 8]
    self._asm_load(Registers.D, Registers.B, src * 8)
    # mov [rax + var * 8], rdx
    self._asm_store(Registers.A, var * 8, Registers.D)

  def _binop_(self, op: BinaryOp, a1: int, a2: int, dst: int):
    self._load_rax(a1)
    arith = {
        BinaryOp.ADD: b"\x48\x03",  # add reg, rm
        BinaryOp.SUB: b"\x48\x2b",  # sub reg, rm
        BinaryOp.MUL: b"\x48\x0f\xaf",  # imul reg, rm
    }
    if op in arith:
      # op rax, [rbx + a2 * 8]
      self._asm_disp(arith[op], Registers.A, Registers.B, a2 * 8)
    if op in {BinaryOp.INTEGER_DIV, BinaryOp.INTEGER_MOD}:
      # xor edx, edx
      self.code.extend(b"\x31\xd2")
      # idiv rax, [rbx + a2 * 8]
      self.code.extend(b"\x48\xf7\xbb")
      self._i32(a2 * 8)
      if op == BinaryOp.INTEGER_MOD:
        # mov rax, rdx
        self.code.extend(b"\x48\x89\xd0")
    cmp = {
        BinaryOp.EQ: b"\x0f\x94\xc0",  # sete al
        BinaryOp.NE: b"\x0f\x95\xc0",  # setne al
        BinaryOp.GE: b"\x0f\x9d\xc0",  # setge al
        BinaryOp.GT: b"\x0f\x9f\xc0",  # setg al
        BinaryOp.LE: b"\x0f\x9e\xc0",  # setle al
        BinaryOp.LT: b"\x0f\x9c\xc0",  # setl al
    }
    if op in cmp:
      # cmp rax, [rbx + a2 * 8]
      self._asm_disp(b"\x48\x3b", Registers.A, Registers.B, a2 * 8)
      # setcc al
      self.code.extend(cmp[op])
      # movzx eax, al
      self.code.extend(b"\x0f\xb6\xc0")
    self._store_rax(dst)

  def _jmp_(self, label: int):
    self.code.extend(b"\xe9")  # jmp
    self.jmps.setdefault(label, []).append(len(self.code))
    self.code.extend(b"\x00\x00\x00\x00")  # placeholder

  def _jmpf_(self, a1: int, label: int):
    self._load_rax(a1)
    self.code.extend(
        b"\x48\x85\xc0"
        b"\x0f\x84"  # je
    )  # test rax, rax
    self.jmps.setdefault(label, []).append(len(self.code))
    self.code.extend(b"\x00\x00\x00\x00")  # placeholder

  def _ret_(self, a1: int):
    if a1 > 0:
      self._load_rax(a1)
      self._store_rax(0)
    self.code.append(0xc3)  # ret

  def _call_(
      self,
      scope: int,
      arg_start: int,
      level_cur: int,
      level_new: int,
  ):
    assert 1 <= level_cur
    assert 1 <= level_new <= level_cur + 1
    if level_new > level_cur:
      self.code.append(0x53)  # push rbx
    for _ in range(min(level_new, level_cur) - 1):
      self.code.extend(b"\xff\xb4\x24")  # push [rsp + (level_new - 1) * 8]
      self._i32((level_new - 1) * 8)
    # make a new frame and call the target
    self.code.extend(b"\x48\x81\xc3")
    self._i32(arg_start * 8)  # add rbx, arg_start*8
    self._asm_call(scope)  # call func
    self.code.extend(b"\x48\x81\xc3")
    self._i32(-arg_start * 8)

    self.code.extend(b"\x48\x81\xc4")  # add rsp, (level_new - 1) * 8
    self._i32((level_new - 1) * 8)

  def _const_(self, val: int, dst: int):
    assert isinstance(val, (int, str))
    if isinstance(val, str):
      self.code.extend(b"\x48\x8d\x05")  # lea rax, [rip + disp32]
      self.strings.setdefault(val, []).append(len(self.code))
      self.code.extend(b"\x00\x00\x00\x00")  # placeholder
    elif val == 0:
      self.code.extend(b"\x31\xc0")  # xor eax, eax
    else:
      self.code.extend(b"\x48\xb8")  # mov rax, imm64
      self._i64(val)
    self._store_rax(dst)

  def _syscall_(self, *arg_list):
    dst, num, *arg_list = arg_list
    self.code.extend(b"\xb8")
    self._i32(0)
    self._asm_load(Registers.A, Registers.B, num * 8)  # mov eax, num
    arg_regs = [Registers.DI, Registers.SI, Registers.D, 10, 8, 9]
    assert len(arg_list) <= len(arg_regs)
    for i, arg in enumerate(arg_list):
      self._asm_load(arg_regs[i], Registers.B, arg * 8)  # mov reg, [rbx + arg*8]
    self.code.extend(b"\x0f\x05")  # syscall
    self._store_rax(dst)  # mov [rbx + dst*8], rax

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #

  def generate(self) -> bytes:
    """
    Compile the program to the machine code.
    """
    self._code_entry()
    self._scope(self._global_scope)
    self._code_end()
    return bytes(self.code)
