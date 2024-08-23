PROGRAM Example;

VAR
    x, y: INTEGER;
    result: BOOLEAN;

FUNCTION Add(a, b: INTEGER): INTEGER;
BEGIN
    RETURN a + b;
END;

FUNCTION IsEven(n: INTEGER): BOOLEAN;
BEGIN
    RETURN (n MOD 2) = 0;
END;

BEGIN
    x := 10;
    y := 20;
    result := FALSE;

    IF IsEven(x) THEN
        result := TRUE
    ELSE
        result := FALSE;

    WHILE x < y DO
    BEGIN
        x := x + 1;
        IF x = 15 THEN
            CONTINUE;
        IF x = 18 THEN
            BREAK;
    END;

    IF result AND (x = y) THEN
        x := Add(x, y)
    ELSE
        x := x - y;

    {WRITELN is a built-in function}
    WRITELN('Final value of x: ', x);
    WRITELN('Is x even? ', IsEven(x));
END.