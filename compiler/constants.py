from enum import Enum


# =========================================================================== #
# Enumerations                                                                #
# =========================================================================== #

class TokenType(Enum):
  EMPTY = 0
  # Single-character tokens
  LEFT_PAREN = 1
  RIGHT_PAREN = 2
  LEFT_BRACE = 3
  RIGHT_BRACE = 4
  COMMA = 5
  SEMICOLON = 6
  COLON = 7
  DOT = 8

  # Binary operators
  PLUS = 20
  MINUS = 21
  STAR = 22
  SLASH = 23
  INTEGER_DIV = 24
  INTEGER_MOD = 25

  # Comparison operators
  EQ = 30
  NEQ = 31
  LT = 32
  LE = 33
  GT = 34
  GE = 35

  # Logical operators
  AND = 36
  OR = 37
  NOT = 38

  # Keywords
  VAR = 100
  BEGIN = 101
  END = 102
  IF = 103
  THEN = 104
  ELSE = 105
  WHILE = 106
  DO = 107
  PROGRAM = 108
  FUNCTION = 110
  INTEGER = 111
  REAL = 112
  BOOLEAN = 113
  STRING = 114
  VOID = 115

  # OTHERS
  ASSIGN = 120
  ID = 121
  VALUE = 122

  EOF = 200


class ASTNodeType(Enum):
  EMPTY = 0
  PROGRAM = 1
  VAR = 2
  ASSIGN = 3
  CONTROL_FLOW = 4
  LOOP = 5
  BLOCK = 6
  BINARY_OP = 7
  UNARY_OP = 8
  STATEMENTS = 9
  STATEMENT = 10
  ID = 11
  VALUE = 12
  DECLARATION = 13
  FUNC_DECL = 15
  PARAMS = 16
  CALL = 17
  TYPE = 18


class ErrorType(Enum):
  UNEXPECTED_TOKEN = 1
  UNMATCHED_COMMENT = 2
  UNCLOSED_COMMENT = 3
  EXPECT_TOKEN = 4


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
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
    ":": TokenType.COLON,
    ".": TokenType.DOT,
}

OPERATORS1CHAR = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "=": TokenType.EQ,
    "<": TokenType.LT,
    ">": TokenType.GT,
}

OPERATORS2CHAR = {
    "<>": TokenType.NEQ,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
    ":=": TokenType.ASSIGN,
}

KEYWORDS = {
    "VAR": TokenType.VAR,
    "BEGIN": TokenType.BEGIN,
    "END": TokenType.END,
    "IF": TokenType.IF,
    "THEN": TokenType.THEN,
    "ELSE": TokenType.ELSE,
    "WHILE": TokenType.WHILE,
    "DO": TokenType.DO,
    "PROGRAM": TokenType.PROGRAM,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "NOT": TokenType.NOT,
    "DIV": TokenType.INTEGER_DIV,
    "MOD": TokenType.INTEGER_MOD,
    "FUNCTION": TokenType.FUNCTION,
    "INTEGER": TokenType.INTEGER,
    "REAL": TokenType.REAL,
    "BOOLEAN": TokenType.BOOLEAN,
    "STRING": TokenType.STRING,
    "VOID": TokenType.VOID,
}
