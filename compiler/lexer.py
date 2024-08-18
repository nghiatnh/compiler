from compiler.token import Token
from compiler.constants import TokenType
from compiler.constants import ErrorType
from compiler.constants import PUNCTUATIONS
from compiler.constants import KEYWORDS
from compiler.constants import OPERATORS1CHAR
from compiler.constants import OPERATORS2CHAR


class LexerError(Exception):
  """
  LexerError
  ==========
  The lexer error class is a custom exception class for lexer errors. It
  contains an error message with the error code and description.
  """


class Lexer:
  """
  Lexer
  ===========
  The lexer class is responsible for reading the source code and returning
  tokens. It reads the source code character by character and returns the next
  token. It skips whitespaces and comments.
  """

  def __init__(self, text: str):
    self._text = text
    self._pos = 0
    self._line = 1
    self._column = 1

  @property
  def _cur_char(self) -> str:
    return self._text[self._pos] if not self._is_eof else None

  @property
  def _is_eof(self) -> bool:
    return self._pos >= len(self._text)

  def _error(self, error_type: ErrorType):
    raise LexerError(
        f"Lexer error code {error_type.value}: {error_type.name} at line"
        f" {self._line}, column {self._column}"
    )

  def _move_next(self):
    if not self._is_eof:
      if self._cur_char == "\n":
        self._line += 1
        self._column = 1
        self._pos += 1
      else:
        self._pos += 1
        self._column += 1

  def _skip_whitespace(self):
    while self._cur_char is not None and self._cur_char.isspace():
      self._move_next()

  def _skip_comment(self):
    while self._cur_char is not None and self._cur_char != TokenType.RIGHT_BRACE.value:
      self._move_next()
    if self._cur_char is None:
      self._error(ErrorType.UNCLOSED_COMMENT)
    self._move_next()

  def _integer(self) -> int:
    cur = ""
    while not self._is_eof and self._cur_char.isdigit():
      cur += self._cur_char
      self._move_next()
    return int(cur)

  def _identifier(self) -> str:
    cur = ""
    while self._cur_char is not None and self._cur_char.isalnum():
      cur += self._cur_char
      self._move_next()
    return cur

  def _seek(self) -> str:
    return self._text[self._pos + 1] if self._pos + 1 < len(self._text) else None

  # ===========================================================================#
  # Public methods                                                            #
  # ===========================================================================#
  def next_token(self) -> Token:
    """
    Get the next token from the source code.
    """
    while self._cur_char is not None:
      if self._cur_char.isspace():
        self._skip_whitespace()
        continue

      if self._cur_char == TokenType.LEFT_BRACE.value:
        self._move_next()
        self._skip_comment()
        continue

      _cur_char = self._cur_char

      if _cur_char == TokenType.RIGHT_BRACE.value:
        self._error(ErrorType.UNMATCHED_COMMENT)

      # Must check 2 chars before punctuations to avoid ambiguity
      if self._seek() is not None and _cur_char + self._seek() in OPERATORS2CHAR:
        _cur_char += self._seek()
        self._move_next()
        self._move_next()
        return Token(
            self._line, self._column, OPERATORS2CHAR[_cur_char], _cur_char)

      if _cur_char in PUNCTUATIONS:
        self._move_next()
        return Token(
            self._line, self._column, PUNCTUATIONS[_cur_char], _cur_char)

      if _cur_char in OPERATORS1CHAR:
        self._move_next()
        return Token(
            self._line, self._column, OPERATORS1CHAR[_cur_char], _cur_char)

      if _cur_char.isalpha():
        _cur_char = self._identifier()
        if _cur_char in KEYWORDS:
          return Token(self._line, self._column, KEYWORDS[_cur_char])
        return Token(self._line, self._column, TokenType.ID, _cur_char)

      if self._cur_char.isdigit():
        return Token(
            self._line, self._column, TokenType.INTEGER, self._integer())

      self._error(ErrorType.UNEXPECTED_TOKEN)

    return Token(self._line, self._column, TokenType.EOF)
