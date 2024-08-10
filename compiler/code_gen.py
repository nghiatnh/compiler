import struct
from comp import Func


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

  # compile the program to an ELF executable
  def output(self, root: Func):
    self.code_entry()
    for func in root.funcs:
      self.func(func)
    self.code_end()
    return self.buf

  def padding(self):
    while len(self.buf) % 16:
      self.buf.append(0)

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
