# Grammar

### Program
- **program**: `program` *prog_name* `;` *block* `.`
- **block**: *declarations* (*proc_decl* | *func_decl*)* *body*
- **body**: `BEGIN` *statements* `END`
- **prog_name**: **ID**

### Variables
- **declarations**: `var` (*declaration* `;`)+ | **EMPTY**
- **declaration**: *variable* (`,` *variable*)* `:` *type*
- **type**: `INTEGER` | `REAL`
- **assign**: *variable* `:=` *expr*
- **variable**: **ID**

### Functions/Procedures
- **func_decl**: `function` *func_name* `(` *params* `)` `:` *type* `;` *block* `;`
- **proc_decl**: `procedure` *func_name* `(` *params* `)` `;` *block* `;`
- **params**: *declaration* (`;` *declaration*)* | **EMPTY**
- **func_name**: **ID**

### Statements
- **statements**: (*statement* `;`)* *statement* | **EMPTY**
- **statement**: *body* | *assign* | *control_flow* | *loop*

- **expr**: *term* ((`+` | `-`) *term*)*
- **term**: *factor* ((`*` | `/` | `div` | `mod`) *factor*)*
- **factor**: `+` *factor* | `-` *factor* | `(` *expr* `)` | **VALUE** | *variable*

### Control flow
- **control_flow**: `if` *expr* `then` (*body* | *statement*) (`else` (*body* | *statement*))?

### Loop
- **loop**: `while` *expr* `do` (*body* | *statement*)