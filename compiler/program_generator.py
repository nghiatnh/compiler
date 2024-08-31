from typing import Union
import numbers


class ELF64GeneratorError(Exception):
  """
  ELF64GeneratorError
  ===================
  ELF64GeneratorError is a class that represents an error in the ELF64Generator.
  """


""" A definitely-not-complete list of some useful constants for generating an
    ELF64 file
"""

ET_EXEC = 2

EV_CURRENT = 1

# see https://software.intel.com/sites/default/files/article/402129/mpx-linux64-abi.pdf
EM_X86_64 = 62

SHN_UNDEF = 0

PT_LOAD = 1

PF_X = 0x1
PF_W = 0x2
PF_R = 0x4


DEFAULT_ENTRY_POINT = 0x400000

#    ELF HEADER
# ----------------
#  Prog Hdr table
# ----------------
#     Segment
# ----------------
#       ...
# ----------------
# Section Hdr Tbl


def uint(n, x):
  return x.to_bytes(n, "little")


ELF64_TYPE_SIZE = {
    "addr": 8,  # 8 unsigned program address
    "off": 8,  # 8 unsigned file offset
    "half": 2,  # 2 unsigned medium integer
    "word": 4,  # 4 unsigned integer
    "sword": 4,  # 4 signed integer
    "xword": 8,  # 8 unsigned long integer
    "sxword": 8,  # 8 signed long integer
    "unsigned_char": 1,  # 1 unsigned small integer
    "16": 16,  # 16 bytes
}

ELF64_EHDR = [
    ("e_ident", "16"),  # ELF identification (actually 16-length array of unsigned char)
    ("e_type", "half"),  # Object file type
    ("e_machine", "half"),  # Machine type
    ("e_version", "word"),  # Object file version
    ("e_entry", "addr"),  # Entry point address
    ("e_phoff", "off"),  # Program header offset
    ("e_shoff", "off"),  # Section header offset
    ("e_flags", "word"),  # Processor-specific flags
    ("e_ehsize", "half"),  # ELF header size
    ("e_phentsize", "half"),  # Size of program header entry
    ("e_phnum", "half"),  # Number of program header entries
    ("e_shentsize", "half"),  # Size of section header entry
    ("e_shnum", "half"),  # Number of section header entries
    ("e_shstrndx", "half"),  # Section name string table index
]


ELF64_PHDR = [
    ("p_type", "word"),  # Type of segment
    ("p_flags", "word"),  # Segment attributes
    ("p_offset", "off"),  # Offset in file
    ("p_vaddr", "addr"),  # Virtual address in memory
    ("p_paddr", "addr"),  # Reserved
    ("p_filesz", "xword"),  # Size of segment in file
    ("p_memsz", "xword"),  # Size of segment in memory
    ("p_align", "xword"),  # Alignment of segment
]


class ELF64Generator:
  """
  ELF64Generator
  ==============
  ELF64Generator is a class that generates an ELF64 file from a given code.
  """

  # ===================== #
  #        ELF FILE       #
  # ===================== #
  #       ELF HEADER      #
  # --------------------- #
  # Program Header Table  #
  # --------------------- #
  #         Segment       #
  # --------------------- #
  #           ...         #
  # --------------------- #
  # Section Header Table  #
  # ===================== #

  def _error(self, msg: str) -> ELF64GeneratorError:
    return ELF64GeneratorError(msg)

  def _to_size(self, elf64_type: str):
    result = ELF64_TYPE_SIZE.get(elf64_type, None)
    if result is None:
      self._error(f"{elf64_type} is not a size")
    return result

  def _serialize(self, x: Union[int, bytes], elf64_type: str) -> bytes:
    size = self._to_size(elf64_type)
    if isinstance(x, numbers.Number):
      return x.to_bytes(size, "little")
    if isinstance(x, bytes):
      if len(x) != size:
        self._error(f"data length {len(x)} != type {elf64_type} length of {size}")
      return x
    raise self._error(f"can't _serialize {x} of type {elf64_type}")

  def _serialize_struct(self, layout, values):
    result = b""
    for key, field_type in layout:
      result += self._serialize(values[key], field_type)
    return result

  def _struct_len(self, layout: list) -> int:
    return sum(self._to_size(t) for _, t in layout)

  @property
  def _e_ident(self) -> bytes:
    return b"".join([
        b"\x7FELF",  #  magic
        b"\x02",  # ELF64
        b"\x01",  # Little-endian
        b"\x01",  # EI_ABIVERSION
        b"\x00",  # ELFOSABI_HPUX ?? # ELFOSABI_SYSV (TODO: \x04 instead? LINUX?)
        b"\x00",  #  epends on EI_ABIVERSION
        b"\x00" * 6,  #  Padding
        b"\x00",  #  size of e_ident ??
    ])

  @property
  def _elf64_ehdr(self) -> bytes:
    prefix_size = self._struct_len(ELF64_EHDR) + self._struct_len(ELF64_PHDR)
    entry_point = DEFAULT_ENTRY_POINT + prefix_size  # virtual addr

    phlen = len(self._program_header(0))  # quick check
    e_ehsize = self._struct_len(ELF64_EHDR)  # size of ELF64 header
    e_phoff = self._struct_len(ELF64_EHDR)  # prog header offset
    e_shoff = 0  # no sections

    return self._serialize_struct(
        ELF64_EHDR,
        {
            "e_ident": self._e_ident,  # ELF identification
            "e_type": ET_EXEC,       # Object file type
            "e_machine": EM_X86_64,  # Machine type
            "e_version": EV_CURRENT,  # Object file version
            "e_entry": entry_point,  # virtual addr entry point
            "e_phoff": e_phoff,      # file offset for program header
            "e_shoff": e_shoff,  #  File offset for section header
            "e_flags": 0,            # processor specific flags
            "e_ehsize": e_ehsize,    # size in bytes of ELF header. (constant!)
            "e_phentsize": phlen,  #  size in bytes of prog header table entry
            "e_phnum": 1,            # num entries in prog header
            "e_shentsize": 0,  #  size in bytes of section header table entry
            "e_shnum": 0,  #  num entries in section header
            "e_shstrndx": SHN_UNDEF  # no section name strings table
        }
    )

  def _program_header(self, code_size: int) -> bytes:
    p_vaddr = DEFAULT_ENTRY_POINT
    p_paddr = p_vaddr
    p_offset = 0  # load whole ELF file.
    p_filesz = code_size
    p_memsz = code_size
    return self._serialize_struct(
        ELF64_PHDR,
        {
            "p_type": PT_LOAD,              # loadable segment
            "p_flags": PF_R | PF_W | PF_X,  # readable, writable, executable
            "p_offset": p_offset,           # offset in bytes from start of file
            "p_vaddr": p_vaddr,             # virtual address in memory
            "p_paddr": p_paddr,             # unused? reserved for physical addressing
            "p_filesz": p_filesz,           # size in bytes of *file image* of segment
            "p_memsz": p_memsz,             # size in bytes of *memory image* of segment
            "p_align": 0x4,                 # alignment (136/4)
        }
    )

  # ============================================================================================= #
  # Public methods                                                                                #
  # ============================================================================================= #

  def generate(self, code: bytes) -> bytes:
    return b"".join([self._elf64_ehdr, self._program_header(len(code)), code])
