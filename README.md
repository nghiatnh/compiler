# Grammar

### Program
- **program**: `program` *prog_name* `;` *block* `.`
- **block**: *declarations* *body*
- **prog_name**: **ID**

### Variables
- **declarations**: `var` (*declaration* `;`)+ | **EMPTY**
- **declaration**: *variable* (`,` *variable*)* `:` *type*
- **type**: `INTEGER` | `REAL`
- **assign**: *variable* `:=` *expr*
- **variable**: **ID**

### Functions/Procedures
- **function**: `function` *func_name* `(` *params* `)` `:` *type* `;` *body*
- **procedure**: `procedure` *func_name* `(` *params* `)` `;` *body*
- **params**: *param* (`,` *param*)* | **EMPTY**
- **param**: *variable* `:` *type*
- **body**: `BEGIN` *statements* `END`
- **func_name**: **ID**

### Statements
- **statements**: (*statement* `;`)* *statement* | **EMPTY**
- **statement**: *body* | *assign* | *control_flow* | *loop*

- **expr**: *term* ((`+` | `-`) *term*)*
- **term**: *factor* ((`*` | `/` | `div` | `mod`) *factor*)*
- **factor**: `+` *factor* | `-` *factor* | `(` *expr* `)` | **VALUE** | *variable*

### Control flow
- **control_flow**: `if` *expr* `then` (*body* | *statement*) | `if` *expr* `then` (*body* | *statement*) `else` (*body* | *statement*)

### Loop
- **loop**: `while` *expr* `do` (*body* | *statement*)