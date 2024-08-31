PROGRAM FIBONACCI;
VAR n: INTEGER;

FUNCTION fib(n: INTEGER): INTEGER;
VAR f1, f2, result, i: INTEGER;
BEGIN
  IF n <= 2 THEN RETURN 1;
  i := 3;
  WHILE i <= n DO
  BEGIN
    result := f1 + f2;
    f1 := f2;
    f2 := result;
    i := i + 1;
  END;
  RETURN result;
END;

BEGIN
  n := fib(5);
END.
