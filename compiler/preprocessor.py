import re

from compiler.builtin_code import BUILT_IN_CODES


class PreprocessorError(Exception):
  """
  PreprocessorError
  ==================
  PreprocessorError is raised when an error occurs during the macro compilation process.
  """


class Preprocessor:
  """
  Preprocessor
  =============
  Preprocessor is a class that represents a compiler for macros.
  """

  def compile(self, text: str) -> str:
    """
    Compiles the given text.
    """
    changes = {}
    used_codes = {}
    for match in re.finditer(r"{\s+INCLUDE\s+(\w+)\s+}", text, re.IGNORECASE):
      name = match.groups()[0].upper()
      if name not in BUILT_IN_CODES:
        raise PreprocessorError("Invalid include name")
      changes[match.span()] = name
      used_codes[name] = "\n".join(BUILT_IN_CODES[name])
    new_text = ""
    cur = 0
    for (start, end), name in changes.items():
      new_text += text[cur:start]
      new_text += used_codes[name]
      cur = end
    new_text += text[cur:]
    return new_text
