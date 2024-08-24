from enum import Enum


# =========================================================================== #
# Enumerations                                                                #
# =========================================================================== #

class TokenType(Enum):
  EMPTY = ""
  # Single-character tokens
  LEFT_PAREN = "("
  RIGHT_PAREN = ")"
  LEFT_BRACE = "{"
  RIGHT_BRACE = "}"
  COMMA = ","
  SEMICOLON = ";"
  COLON = ":"
  DOT = "."
  SINGLE_QUOTE = "'"

  # Binary operators
  PLUS = "+"
  MINUS = "-"
  STAR = "*"
  SLASH = "/"
  INTEGER_DIV = "DIV"
  INTEGER_MOD = "MOD"

  # Comparison operators
  EQ = "="
  NEQ = "<>"
  LT = "<"
  LE = "<="
  GT = ">"
  GE = ">="

  # Logical operators
  AND = "AND"
  OR = "OR"
  NOT = "NOT"

  # Keywords
  VAR = "VAR"
  BEGIN = "BEGIN"
  END = "END"
  IF = "IF"
  THEN = "THEN"
  ELSE = "ELSE"
  WHILE = "WHILE"
  DO = "DO"
  PROGRAM = "PROGRAM"
  RETURN = "RETURN"
  FUNCTION = "FUNCTION"
  INTEGER = "INTEGER"
  REAL = "REAL"
  BOOLEAN = "BOOLEAN"
  STRING = "STRING"
  VOID = "VOID"
  BREAK = "BREAK"
  CONTINUE = "CONTINUE"
  TRUE = "TRUE"
  FALSE = "FALSE"

  # OTHERS
  ASSIGN = ":="
  ID = "ID"
  VALUE = "VALUE"

  EOF = "EOF"


class ASTNodeType(Enum):
  EMPTY = "EMPTY"

  # Program
  PROGRAM = "PROGRAM"
  BLOCK = "BLOCK"

  # Variables
  VAR = "VAR"
  DECLARATION = "DECLARATION"
  TYPE = "TYPE"
  ASSIGN = "ASSIGN"

  # Functions
  FUNC_DECL = "FUNC_DECL"
  FUNC_PARAMS = "PARAMS"
  CALL = "CALL"
  RETURN = "RETURN"

  # Statements
  BINARY_OP = "BINARY_OP"
  UNARY_OP = "UNARY_OP"
  STATEMENTS = "STATEMENTS"
  STATEMENT = "STATEMENT"
  ID = "ID"
  VALUE = "VALUE"

  # Loop/Control flow
  LOOP = "LOOP"
  BREAK = "BREAK"
  CONTINUE = "CONTINUE"
  CONTROL_FLOW = "CONTROL_FLOW"


class ErrorType(Enum):
  UNEXPECTED_TOKEN = 1
  UNMATCHED_COMMENT = 2
  UNCLOSED_COMMENT = 3
  EXPECT_TOKEN = 4
  UNCLOSED_STRING = 5


class VariableType(Enum):
  INTEGER = "INTEGER"
  REAL = "REAL"
  BOOLEAN = "BOOLEAN"
  STRING = "STRING"
  VOID = "VOID"


# =========================================================================== #
# Constants                                                                   #
# =========================================================================== #

PUNCTUATIONS = {
    TokenType.LEFT_PAREN.value: TokenType.LEFT_PAREN,
    TokenType.RIGHT_PAREN.value: TokenType.RIGHT_PAREN,
    TokenType.LEFT_BRACE.value: TokenType.LEFT_BRACE,
    TokenType.RIGHT_BRACE.value: TokenType.RIGHT_BRACE,
    TokenType.COMMA.value: TokenType.COMMA,
    TokenType.SEMICOLON.value: TokenType.SEMICOLON,
    TokenType.COLON.value: TokenType.COLON,
    TokenType.DOT.value: TokenType.DOT,
    TokenType.SINGLE_QUOTE.value: TokenType.SINGLE_QUOTE,
}

OPERATORS1CHAR = {
    TokenType.PLUS.value: TokenType.PLUS,
    TokenType.MINUS.value: TokenType.MINUS,
    TokenType.STAR.value: TokenType.STAR,
    TokenType.SLASH.value: TokenType.SLASH,
    TokenType.EQ.value: TokenType.EQ,
    TokenType.LT.value: TokenType.LT,
    TokenType.GT.value: TokenType.GT,
}

OPERATORS2CHAR = {
    TokenType.NEQ.value: TokenType.NEQ,
    TokenType.LE.value: TokenType.LE,
    TokenType.GE.value: TokenType.GE,
    TokenType.ASSIGN.value: TokenType.ASSIGN,
}

KEYWORDS = {
    TokenType.VAR.value: TokenType.VAR,
    TokenType.BEGIN.value: TokenType.BEGIN,
    TokenType.END.value: TokenType.END,
    TokenType.IF.value: TokenType.IF,
    TokenType.THEN.value: TokenType.THEN,
    TokenType.ELSE.value: TokenType.ELSE,
    TokenType.WHILE.value: TokenType.WHILE,
    TokenType.DO.value: TokenType.DO,
    TokenType.PROGRAM.value: TokenType.PROGRAM,
    TokenType.AND.value: TokenType.AND,
    TokenType.OR.value: TokenType.OR,
    TokenType.NOT.value: TokenType.NOT,
    TokenType.INTEGER_DIV.value: TokenType.INTEGER_DIV,
    TokenType.INTEGER_MOD.value: TokenType.INTEGER_MOD,
    TokenType.FUNCTION.value: TokenType.FUNCTION,
    TokenType.INTEGER.value: TokenType.INTEGER,
    TokenType.REAL.value: TokenType.REAL,
    TokenType.BOOLEAN.value: TokenType.BOOLEAN,
    TokenType.STRING.value: TokenType.STRING,
    TokenType.VOID.value: TokenType.VOID,
    TokenType.RETURN.value: TokenType.RETURN,
    TokenType.BREAK.value: TokenType.BREAK,
    TokenType.CONTINUE.value: TokenType.CONTINUE,
}
