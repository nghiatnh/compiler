import os
import argparse
import logging
from dataclasses import dataclass

from compiler import Compiler
from compiler.logger import LOGGER


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
  MACHINE_CODE = Compiler().compile(text)
  LOGGER.info("Writing machine code to %s", args.output)
  if os.path.exists(args.output):
    os.unlink(args.output)
  fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o755)
  with os.fdopen(fd, "wb", closefd=True) as fp:
    fp.write(MACHINE_CODE)
  LOGGER.info("Compilation successful!")
