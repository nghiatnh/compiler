from compiler.token import Token
from compiler.constants import TokenType
from compiler.constants import ErrorType
from compiler.constants import PUNCTUATIONS
from compiler.constants import KEYWORDS
from compiler.constants import OPERATORS1CHAR
from compiler.constants import OPERATORS2CHAR


class Lexer:
  """
  Lexer class
  ===========
  The lexer class is responsible for reading the source code and returning
  tokens. It reads the source code character by character and returns the next
  token. It skips whitespaces and comments.
  """
  def __init__(self, text: str):
    self._text = text
    self._pos = 0
    self._line = 0
    self._column = 0

  @property
  def cur_char(self) -> str:
    return self._text[self._pos] if self._pos < len(self._text) else None

  def error(self, error_type: ErrorType):
    raise Exception(
        f"Lexer error code {error_type.value}: {error_type.name} at line"
        f" {self._line + 1}, column {self._column + 1}"
    )

  def move_next(self):
    if self._pos < len(self._text):
      if self.cur_char == "\n":
        self._line += 1
        self._column = 0
        self._pos += 1
      else:
        self._pos += 1
        self._column += 1

  def skip_whitespace(self):
    while self.cur_char is not None and self.cur_char.isspace():
      self.move_next()

  def skip_comment(self):
    while self.cur_char is not None and self.cur_char != TokenType.RIGHT_BRACE.value:
      self.move_next()
    if self.cur_char is None:
      self.error(ErrorType.UNCLOSED_COMMENT)
    self.move_next()

  def integer(self) -> int:
    cur = ""
    while self._pos < len(self._text) and self.cur_char.isdigit():
      cur += self.cur_char
      self.move_next()
    return int(cur)

  def identifier(self) -> str:
    cur = ""
    while self.cur_char is not None and self.cur_char.isalnum():
      cur += self.cur_char
      self.move_next()
    return cur

  def seek(self) -> str:
    return self._text[self._pos + 1] if self._pos + 1 < len(self._text) else None

  def get_next_token(self) -> Token:
    while self.cur_char is not None:
      if self.cur_char.isspace():
        self.skip_whitespace()
        continue

      if self.cur_char == TokenType.LEFT_BRACE.value:
        self.move_next()
        self.skip_comment()
        continue

      cur_char = self.cur_char

      if cur_char == TokenType.RIGHT_BRACE.value:
        self.error(ErrorType.UNMATCHED_COMMENT)

      if self.seek() is not None and cur_char + self.seek() in OPERATORS2CHAR:
        cur_char += self.seek()
        self.move_next()
        self.move_next()
        return Token(OPERATORS2CHAR[cur_char])

      if cur_char in PUNCTUATIONS:
        self.move_next()
        return Token(PUNCTUATIONS[cur_char])

      if cur_char in OPERATORS1CHAR:
        self.move_next()
        return Token(OPERATORS1CHAR[cur_char])

      if cur_char.isalpha():
        cur_char = self.identifier()
        if cur_char in KEYWORDS:
          return Token(KEYWORDS[cur_char])
        return Token(TokenType.ID, cur_char)

      if self.cur_char.isdigit():
        return Token(TokenType.INTEGER, self.integer())

      self.error(ErrorType.UNEXPECTED_TOKEN)

    return Token(TokenType.EOF, None)
