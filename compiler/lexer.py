from compiler.token import Token
from compiler.error_reporter import ErrorType, ErrorReporter, CompileError
from compiler.constants import TokenType
from compiler.constants import PUNCTUATIONS
from compiler.constants import KEYWORDS
from compiler.constants import OPERATORS1CHAR
from compiler.constants import OPERATORS2CHAR


class Lexer:
  """
  Lexer
  ===========
  The lexer class is responsible for reading the source code and returning
  tokens. It reads the source code character by character and returns the next
  token. It skips whitespaces and comments.
  """

  def __init__(
      self,
      text: str,
      error_reporter: ErrorReporter,
      *,
      case_sentitive: bool = False,
  ):
    self._text = text
    self._pos = 0
    self._line = 1
    self._column = 1
    self._case_sensitive = case_sentitive
    self._error_reporter = error_reporter

  @property
  def _is_eof(self) -> bool:
    return self._pos >= len(self._text)

  def _error(
      self,
      error_type: ErrorType,
      line: int,
      column: int,
      message: str = "",
  ) -> CompileError:
    return self._error_reporter.error(error_type, line, column, message)

  def _move_next(self):
    if not self._is_eof:
      if self.cur_char == "\n":
        self._line += 1
        self._column = 1
        self._pos += 1
      else:
        self._pos += 1
        self._column += 1

  def _skip_whitespace(self):
    while self.cur_char is not None and self.cur_char.isspace():
      self._move_next()

  def _skip_comment(self):
    save = (self._line, self._column - 1)
    while self.cur_char is not None and self.cur_char != TokenType.RIGHT_BRACE.value:
      self._move_next()
    if self.cur_char is None:
      raise self._error(ErrorType.UNCLOSED_COMMENT, *save, "Unclosed comment")
    self._move_next()

  def _number(self) -> int:
    cur = ""
    is_real = False
    while self.cur_char is not None and (self.cur_char.isdigit() or (
            self.cur_char == TokenType.DOT.value and not is_real)):
      if self.cur_char == TokenType.DOT.value:
        is_real = True
      cur += self.cur_char
      self._move_next()
    return float(cur) if is_real else int(cur)

  def _string(self) -> str:
    cur = ""
    save = (self._line, self._column - 1)
    while not self._is_eof and self.cur_char != TokenType.SINGLE_QUOTE.value:
      cur += self.cur_char
      self._move_next()
    if self.cur_char is None:
      raise self._error(ErrorType.UNCLOSED_QUOTE, *save, "Unclosed quote")
    self._move_next()
    return cur

  def _identifier(self) -> str:
    cur = ""
    while self.cur_char is not None and self.cur_char.isalnum():
      cur += self.cur_char
      self._move_next()
    return cur

  def _seek(self) -> str:
    return self._text[self._pos + 1] if self._pos + 1 < len(self._text) else None

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #
  @property
  def cur_char(self) -> str:
    """
    Get the current character from the source code.
    """
    if self._is_eof:
      return None
    cur_char = self._text[self._pos]
    return cur_char if self._case_sensitive else cur_char.upper()

  def next_token(self) -> Token:
    """
    Get the next token from the source code.
    """
    while self.cur_char is not None:
      if self.cur_char.isspace():
        self._skip_whitespace()
        continue

      if self.cur_char == TokenType.LEFT_BRACE.value:
        self._move_next()
        self._skip_comment()
        continue

      cur_char = self.cur_char
      line, column = self._line, self._column

      if cur_char == TokenType.RIGHT_BRACE.value:
        raise self._error(
            ErrorType.UNMATCHED_COMMENT, self._line, self._column, "Unmatched comment"
        )

      if cur_char == TokenType.SINGLE_QUOTE.value:
        self._move_next()
        return Token(line, column, TokenType.VALUE, self._string())

      if self.cur_char.isdigit():
        return Token(line, column, TokenType.VALUE, self._number())

      # Must check 2 chars before punctuations to avoid ambiguity
      if self._seek() is not None and cur_char + self._seek() in OPERATORS2CHAR:
        cur_char += self._seek()
        self._move_next()
        self._move_next()
        return Token(line, column, OPERATORS2CHAR[cur_char], cur_char)

      if cur_char in PUNCTUATIONS:
        self._move_next()
        return Token(line, column, PUNCTUATIONS[cur_char], cur_char)

      if cur_char in OPERATORS1CHAR:
        self._move_next()
        return Token(line, column, OPERATORS1CHAR[cur_char], cur_char)

      if cur_char.isalpha():
        _id = self._identifier()
        if _id in [TokenType.TRUE.value, TokenType.FALSE.value]:
          value = _id == TokenType.TRUE.value
          return Token(line, column, TokenType.VALUE, value)
        if _id in KEYWORDS:
          return Token(line, column, KEYWORDS[_id], _id)
        return Token(line, column, TokenType.ID, _id)

      raise self._error(
          ErrorType.INVALID_CHARACTER, self._line, self._column, f"Invalid character {cur_char}"
      )

    return Token(self._line, self._column, TokenType.EOF)
