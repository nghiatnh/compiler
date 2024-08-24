from typing import Optional, Union

from compiler.constants import TokenType


class Token:
  """
  Token
  =====
  The token class represents a token in the source code. It contains the token
  type, value, line, and column where the token was found in the source code.
  """
  def __init__(
      self,
      line: int,
      column: int,
      type: TokenType,
      value: Optional[Union[int, float, bool, str]] = None
  ):
    self.line = line
    self.column = column
    self.type = type
    self.value = value

  def __repr__(self) -> str:
    if self.value is None:
      return f"<Token {self.type.name}, {self.line}, {self.column}>"
    return f"<Token {self.type.name}, {self.line}, {self.column}>: {self.value}"

  def __str__(self) -> str:
    return self.__repr__()
