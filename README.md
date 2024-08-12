# Compiler
I want to build a simple compiler from scratch to know how the compiler works. This compiler use the S-expression as the grammar and the code will be compiled to the ELF format. This project is following the book [From Source Code To Machine Code](https://build-your-own.org/compiler/) of **James Smith**. I changed the code generating the ELF file because the author's code does not work for me. The code to generate ELF File is following the project [elf-from-scratch](https://github.com/statusfailed/elf-from-scratch) of **statusfailed**.

# How to run

```bash
python3 compiler/elf_gen.py -f compiler/fib.sexpr -o fib.elf -v
./fib.elf
echo $?
```


# Grammar

### Variable operators:

- (**var** [name] [value])
- (**set** [name] [value])


### Binary operators

- (**op** [value1] [value2])
- ***op**: +, -, *, /, %, eq, ne, lt, le, gt, ge

### Unary operators

- (**op** [value])
- ***op**: not, neg

### Flow control

- (**if** [condition] (**then** [value]))
- (**if** [condition] (**then** [value1]) (**else** [value2]))
- (**loop** [condition] [body]) 
- (**break**)/(**continue**)

### Functions

- (**def** ([name] [return_type]) ([arg_defs...]) [body])
- (**call** [name] [args...])
- ***arg_def**: ([name] [type])
- ***return_type**: int, str, void

### New Scope

- (**do** [body])


### Syscall

- (**syscall** [num] [args])
