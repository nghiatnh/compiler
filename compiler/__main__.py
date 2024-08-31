import os
import sys
import argparse
import logging
from dataclasses import dataclass

from compiler.logger import LOGGER
from compiler.error_reporter import ErrorReporter, CompileError
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.byte_code_generator import ByteCodeGenerator
from compiler.code_generator import MachineCodeGenerator
from compiler.program_generator import ELF64Generator


@dataclass
class CompilerParams:
  filename: str
  output: str
  verbose: bool


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      prog="compiler", description="Compiler for the Pascal-like programming language")
  parser.add_argument("filename", help="Input file")
  parser.add_argument("-o", "--output", help="Output file", default="main.elf")
  parser.add_argument(
      "-v", "--verbose", help="Verbose logging",
      action="store_true", default=False
  )
  args = parser.parse_args(namespace=CompilerParams)
  if not args.verbose:
    LOGGER.setLevel(logging.ERROR)
  LOGGER.info("Reading code from %s", args.filename)
  with open(args.filename, "r", encoding="utf-8") as f:
    text = f.read()
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
    MACHINE_CODE = elf_gen.generate(mcg.generate())
    LOGGER.info("Writing output to %s", args.output)
    if os.path.exists(args.output):
      os.unlink(args.output)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o755)
    with os.fdopen(fd, "wb", closefd=True) as fp:
      fp.write(MACHINE_CODE)
    LOGGER.info("Compilation successful!")
  except CompileError as e:
    LOGGER.error(e)
    sys.exit(1)
