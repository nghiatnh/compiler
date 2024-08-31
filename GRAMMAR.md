
# Grammar (Pascal-like)

### Comment
- **comment**: `{` *any* `}`

### Program
- **program**: `PROGRAM` *prog_name* `;` *block* `.`
- **block**: *var_decl*? *func_decl** *body*
- **body**: `BEGIN` *statements*? `END`
- **prog_name**: **ID**

### Variables
- **var_decl**: `VAR` (*declaration* `;`)+
- **declaration**: *variable* (`,` *variable*)* `:` *var_type*
- **var_type**: `INTEGER` | `REAL` | `BOOLEAN` | `STRING`
- **assign**: *variable* `:=` *logic*
- **variable**: **ID**

### Functions
- **func_decl**: `FUNCTION` *func_name* `(` *params*? `)` `:` *func_type* `;` *block* `;`
- **params**: *declaration* (`;` *declaration*)*
- **func_type**: *var_type* | `VOID`
- **call**: *func_name* `(` *args*? `)`
- **args**: *logic* (`,` *logic*)*
- **return**: `RETURN` *logic*?
- **func_name**: **ID**

### Statements
- **statements**: (*statement* `;`)* *statement*
- **statement**: *body* | *assign* | *call* | *control_flow* | *loop* | *jump*
- **logic**: *expr* ((`AND` | `OR` | `=` | `<>` | `<` | `<=` | `>` | `>=`) *expr*)*
- **expr**: *term* ((`+` | `-`) *term*)*
- **term**: *factor* ((`*` | `/` | `DIV` | `MOD`) *factor*)*
- **factor**: (`+` | `-` | `NOT`) *factor* | `(` *logic* `)` | *value* | *variable* | *call*

### Control flow
- **control_flow**: `IF` *logic* `THEN` *statement* (`ELSE` *statement*)?

### Loop
- **loop**: `WHILE` *logic* `DO` *statement*
- **jump**: `BREAK` | `CONTINUE` | *return*

### Values
- **value**: *number* | *boolean* | *string*
- **number**:  ([0-9]*[.])?[0-9]+ 
- **boolean**: `TRUE` | `FALSE`
- **string**: `'` .*? `'`
