import sys

from compiler.ast_node import ASTNode
from compiler.logger import LOGGER
from compiler.error_reporter import ErrorReporter, CompileError
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.byte_code_generator import ByteCodeGenerator
from compiler.code_generator import MachineCodeGenerator
from compiler.program_generator import ELF64Generator
from compiler.builtin_code import BUILT_IN_CODES


def _parse_built_in(built_in_code: str) -> ASTNode:
  error_reporter = ErrorReporter(built_in_code)
  lexer = Lexer(built_in_code, error_reporter)
  parser = Parser(lexer, error_reporter)
  parser.cur_token = lexer.next_token()
  return parser.parse_func()


def compile_code(text: str) -> bytes:
  """
  Compile the given source code to machine code.
  """
  error_reporter = ErrorReporter(text)
  try:
    LOGGER.info("Parsing code")
    lexer = Lexer(text, error_reporter)
    parser = Parser(lexer, error_reporter)
    root = parser.parse()
    for code in BUILT_IN_CODES:
      root.children[0].children.insert(-1, _parse_built_in(code))
    LOGGER.info("Compiling code")
    sa = SemanticAnalyzer(error_reporter)
    scope = sa.analyze(root)
    LOGGER.info("Generating byte code")
    bcg = ByteCodeGenerator(scope)
    scope = bcg.generate(root)
    LOGGER.info("Generating machine code")
    mcg = MachineCodeGenerator(scope.children[0])
    elf_gen = ELF64Generator()
    machine_code = elf_gen.generate(mcg.generate())
    LOGGER.info("Compilation successful!")
    return machine_code
  except CompileError as e:
    LOGGER.error(e)
    sys.exit(1)
