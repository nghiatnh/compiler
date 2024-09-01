import sys

from compiler.logger import LOGGER
from compiler.error_reporter import ErrorReporter, CompileError
from compiler.precompile import MacroCompiler
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.byte_code_generator import ByteCodeGenerator
from compiler.code_generator import MachineCodeGenerator
from compiler.program_generator import ELF64Generator


class Compiler:
  """
  Compiler
  ========
  Compiler class is responsible for compiling source code into machine code. It orchestrates
  various stages of the compilation process, including macro compilation, lexical analysis, parsing,
  semantic analysis, and code generation.
  """

  def compile(self, text: str) -> bytes:
    """
    Compile the given source code to machine code.
    """
    LOGGER.info("Macro compiling code")
    mc = MacroCompiler()
    text = mc.compile(text)
    error_reporter = ErrorReporter(text)
    try:
      LOGGER.info("Parsing code")
      lexer = Lexer(text, error_reporter)
      parser = Parser(lexer, error_reporter)
      root = parser.parse()
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
