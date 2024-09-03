PROGRAM fibonacci;
VAR str, ref: POINTER;
s: STRING;

{ INCLUDE IOLIBS }

FUNCTION fib(n: INTEGER): INTEGER;
BEGIN
  IF n <= 2 THEN write(itoa(n), strlen(itoa(n)));
  IF NOT (n > 2) THEN RETURN 1;
  RETURN fib(n - 1) + fib(n - 2);
END;

BEGIN
  writestr('Enter a number: ', 16);
  str := input(10);
  ref := @atoi(str);
  ^ref := (^ref) + 1;
  writestr('The ', 4);
  write(itoa(^ref), strlen(itoa(^ref)));
  writestr('th fibonacci is: ', 17);
  str := itoa(fib(^ref));
  writeln(str, strlen(str));
  exit(0);
END.
