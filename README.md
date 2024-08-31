# Compiler

I am building a simple compiler from scratch to understand how compilers work. This compiler uses Pascal as the [grammar](./GRAMMAR.md) (with some modifications), and the code will be compiled to the 64-bit ELF format. This project follows the book [From Source Code To Machine Code](https://build-your-own.org/compiler/) by **James Smith**. I modified the code for generating the ELF file because the author's code did not work for me. The code to generate the ELF file follows the project [elf-from-scratch](https://github.com/statusfailed/elf-from-scratch) by **statusfailed**. The way I separate the code modules follows the blog [Let’s Build A Simple Interpreter](https://ruslanspivak.com/lsbasi-part1/) by **Ruslan**.

# How to run?

```bash
python3 -m compiler <filename>
./main.elf
echo $?
```
