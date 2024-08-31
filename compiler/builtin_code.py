WRITE = """
FUNCTION write(s: STRING; len: INTEGER): VOID;
BEGIN
  SYSCALL(1, 1, s, len);
END;
"""


BUILT_IN_CODES = [
    WRITE,
]
