PROGRAM fibonacci;
VAR heap, str: POINTER;
s: STRING;

{ INCLUDE IOLIBS }

FUNCTION fib(n: integer): integer;
BEGIN
  IF n <= 2 THEN RETURN 1;
  RETURN fib(n - 1) + fib(n - 2);
END;

BEGIN
  syscall(1, 1, 'Enter a number: ', 16);
  heap := CAST POINTER, 0;
  str := input(10);
  syscall(1, 1, 'The ', 4);
  write(str, strlen(str));
  syscall(1, 1, 'th fibonacci is: ', 17);
  str := itoa(fib(atoi(str)));
  writeln(str, strlen(str));
  exit(0);
END.
