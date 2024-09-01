WRITE = """
FUNCTION write(s: STRING; len: INTEGER): VOID;
BEGIN
  SYSCALL(1, 1, s, len);
END;
"""


INPUT = """
FUNCTION input(len: INTEGER): STRING;
VAR result: STRING;
BEGIN
  result := '';
  SYSCALL(0, 0, result, len);
  RETURN result;
END;
"""

EXIT = """
FUNCTION exit(code: INTEGER): VOID;
BEGIN
  SYSCALL(60, code);
END;
"""

BUILT_IN_CODES = [
    # WRITE,
    # INPUT,
    EXIT,
]
