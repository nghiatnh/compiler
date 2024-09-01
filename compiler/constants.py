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
  SYSCALL = "SYSCALL"
  INTEGER = "INTEGER"
  REAL = "REAL"
  BOOLEAN = "BOOLEAN"
  STRING = "STRING"
  POINTER = "POINTER"
  VOID = "VOID"
  BREAK = "BREAK"
  CONTINUE = "CONTINUE"
  TRUE = "TRUE"
  FALSE = "FALSE"
  PEEK = "PEEK"
  POKE = "POKE"
  REF = "REF"

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
  SYSCALL = "SYSCALL"
  RETURN = "RETURN"

  # Statements
  MOV_PTR = "MOV_PTR"
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

  # Memory
  PEEK = "PEEK"
  POKE = "POKE"
  REF = "REF"


class ReturnType(Enum):
  INTEGER = "INTEGER"
  REAL = "REAL"
  BOOLEAN = "BOOLEAN"
  STRING = "STRING"
  POINTER = "POINTER"
  VOID = "VOID"


class OpCode(Enum):
  MOV = "MOV"
  LEA = "LEA"
  GET_ENV = "GET_ENV"
  SET_ENV = "SET_ENV"
  SYSCALL = "SYSCALL"
  CONST = "CONST"
  BINOP = "BINOP"
  NEG = "NEG"
  NOT = "NOT"
  JMP = "JMP"
  JMPF = "JMPF"
  CALL = "CALL"
  RET = "RET"
  PEEK = "PEEK"
  POKE = "POKE"
  REF = "REF"


class BinaryOp(Enum):
  ADD = "+"
  SUB = "-"
  MUL = "*"
  DIV = "/"
  INTEGER_DIV = "DIV"
  INTEGER_MOD = "MOD"
  EQ = "="
  NE = "<>"
  LT = "<"
  LE = "<="
  GT = ">"
  GE = ">="
  AND = "AND"
  OR = "OR"


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
    TokenType.SYSCALL.value: TokenType.SYSCALL,
    TokenType.INTEGER.value: TokenType.INTEGER,
    TokenType.REAL.value: TokenType.REAL,
    TokenType.BOOLEAN.value: TokenType.BOOLEAN,
    TokenType.STRING.value: TokenType.STRING,
    TokenType.POINTER.value: TokenType.POINTER,
    TokenType.VOID.value: TokenType.VOID,
    TokenType.RETURN.value: TokenType.RETURN,
    TokenType.BREAK.value: TokenType.BREAK,
    TokenType.CONTINUE.value: TokenType.CONTINUE,
    TokenType.PEEK.value: TokenType.PEEK,
    TokenType.POKE.value: TokenType.POKE,
    TokenType.REF.value: TokenType.REF,
}


ELF64_TYPE_SIZE = {
    "addr": 8,  # 8 unsigned program address
    "off": 8,  # 8 unsigned file offset
    "half": 2,  # 2 unsigned medium integer
    "word": 4,  # 4 unsigned integer
    "sword": 4,  # 4 signed integer
    "xword": 8,  # 8 unsigned long integer
    "sxword": 8,  # 8 signed long integer
    "double_xword": 16,  # 16 double unsigned long integer
    "s_double_xword": 16,  # 16 double signed long integer
    "unsigned_char": 1,  # 1 unsigned small integer
}

ELF64_EHDR = [
    ("e_ident", "double_xword"),  # ELF identification (actually 16-length array of unsigned char)
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
