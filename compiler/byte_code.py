from dataclasses import dataclass
from compiler.constants import OpCode


@dataclass
class ByteCode:
  """
  ByteCode
  ========
  ByteCode class to represent a byte code instruction. It has an opcode and a 
  list of operands.
  """
  opcode: OpCode
  operands: list

  def __repr__(self) -> str:
    return f"<ByteCode {self.opcode.name} {', '.join(map(str, self.operands))}>"

  def __str__(self) -> str:
    return self.__repr__()
