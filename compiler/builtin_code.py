# =========================================================================== #
# STD LIBS                                                                    #
# =========================================================================== #

VAR_DECL = """
VAR BuiltInHeap: POINTER;
"""

EXIT = """
FUNCTION exit(code: INTEGER): VOID;
BEGIN
  SYSCALL(60, code);
END;
"""

MALLOC = """
FUNCTION malloc(n: INTEGER): POINTER;
VAR heapsz, prot, flags, fd, offset, tmp: INTEGER;
result: POINTER;
BEGIN
  IF BuiltInHeap = (CAST POINTER, 0) THEN
  BEGIN
    heapsz := 255;
    prot := 3;
    flags := 34;
    fd := -1;
    offset := 0;
    tmp := SYSCALL(9, 0, heapsz, prot, flags, fd, offset);
    BuiltInHeap := CAST POINTER, tmp;
  END;
  result := BuiltInHeap;
  BuiltInHeap := BuiltInHeap + n;
  RETURN result;
END;
"""

# =========================================================================== #
# STR LIBS                                                                    #
# =========================================================================== #

STRNEW = """
FUNCTION strnew(cap: INTEGER): POINTER;
VAR addr, iaddr: POINTER;
BEGIN
  addr := malloc(cap + 16);
  POKE addr, 0;
  addr := addr + 8;
  POKE addr, cap;
  RETURN addr + 8;
END;
"""

STRLEN = """
FUNCTION strlen(s: POINTER): INTEGER;
BEGIN
  s := s - 16;
  RETURN PEEK s;
END;
"""

STRCAP = """
FUNCTION strcap(s: POINTER): INTEGER;
BEGIN
  s := s - 8;
  RETURN PEEK s;
END;
"""

APPEND = """
FUNCTION strappend(s: POINTER; ch: INTEGER): POINTER;
VAR len: INTEGER;
start: POINTER;
BEGIN
  len := strlen(s);
  start := s + len;
  POKE start, ch;
  s := s - 16;
  POKE s, len + 1;
  RETURN s + 16;
END;
"""

STRREV = """
FUNCTION strrev(s: POINTER): POINTER;
VAR r, tmp: POINTER; i: INTEGER;
BEGIN
  r := strnew(strlen(s));
  i := strlen(s) - 1;
  WHILE i >= 0 DO
  BEGIN
    tmp := s + i;
    strappend(r, PEEK tmp);
    i := i - 1;
  END;
  RETURN r;
END;
"""

ITOA = """
FUNCTION itoa(i: INTEGER): POINTER;
VAR s: POINTER; d, tmp, l, tmp1: INTEGER;
BEGIN
  s := strnew(24);
  IF i = 0 THEN strappend(s, 48);
  tmp := i * 1;
  WHILE tmp > 0 DO
  BEGIN
    d := (tmp % 10) + 48;
    tmp := tmp / 10;
    strappend(s, d);
  END;
  return strrev(s);
END;
"""

ATOI = """
FUNCTION atoi(s: POINTER): INTEGER;
VAR result, i: INTEGER;
tmp: POINTER;
BEGIN
  result := 0;
  i := 0;
  WHILE i <= strlen(s) - 1 DO
  BEGIN
    tmp := s + i;
    result := result * 10 + (((PEEK tmp) % 256) - 48);
    i := i + 1;
  END;
  RETURN result;
END;
"""

# =========================================================================== #
# IO LIBS                                                                     #
# =========================================================================== #

WRITE = """
FUNCTION write(s: POINTER; len: INTEGER): VOID;
BEGIN
  SYSCALL(1, 1, s, len);
END;
"""

WRITELN = """
FUNCTION writeln(s: POINTER; len: INTEGER): VOID;
BEGIN
  SYSCALL(1, 1, s, len);
  s := strnew(1);
  strappend(s, 10);
  SYSCALL(1, 1, s, 1);
END;
"""

WRITE_STR = """
FUNCTION writestr(s: STRING; len: INTEGER): VOID;
BEGIN
  SYSCALL(1, 1, s, len);
END;
"""

WRITELN_STR = """
FUNCTION writelnstr(s: STRING; len: INTEGER): VOID;
VAR tmp: POINTER;
BEGIN
  SYSCALL(1, 1, s, len);
  tmp := strnew(1);
  strappend(s, 10);
  SYSCALL(1, 1, s, 1);
END;
"""

INPUT = """
FUNCTION input(len: INTEGER): POINTER;
VAR result, tmp: POINTER; nread, i: INTEGER;
BEGIN
  result := strnew(len);
  tmp := strnew(len);
  nread := SYSCALL(0, 0, tmp, len);
  i := 0;
  WHILE i < nread - 1 DO
  BEGIN
    strappend(result, PEEK tmp);
    tmp := tmp + 1;
    i := i + 1;
  END;
  RETURN result;
END;
"""

# =========================================================================== #
# BUILT-IN CODES                                                              #
# =========================================================================== #

STDLIBS = [VAR_DECL, EXIT, MALLOC]
STRLIBS = [*STDLIBS, STRNEW, STRLEN, STRCAP, APPEND, STRREV, ITOA, ATOI]
IOLIBS = [*STRLIBS, WRITE, WRITELN, INPUT]

BUILT_IN_CODES = {
    "STDLIBS": STDLIBS,
    "STRLIBS": STRLIBS,
    "IOLIBS": IOLIBS,
}
