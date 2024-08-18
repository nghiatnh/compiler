from typing import Optional

from compiler.constants import TokenType


class Token:
  def __init__(self, type: TokenType, value: Optional[str] = None):
    self.type = type
    self.value = value

  def __repr__(self) -> str:
    return f"Token({self.type.name}: {self.value})"

  def __str__(self) -> str:
    return self.__repr__()
