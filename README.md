# Compiler Project

## Overview

This project is a simple compiler designed to translate source code into executable machine code. It currently supports a limited set of operations and data types, and is intended as a learning tool for understanding the basics of compiler construction.

## How to Run

To compile and run a program using this compiler, follow these steps:

1. **Compile the Source Code:**

    Use the following command to compile your source code file (replace `<filename>` with the name of your source file):

    ```bash
    python3 -m compiler <filename>
    ```

    This command will generate an ELF executable file named `main.elf`.

2. **Run the Executable**:

    After compiling, you can run the generated executable with:
    ```
    ./main.elf
    ```

## Features

See the [GRAMMAR](./GRAMMAR.md) for the details of the grammar.
- **Basic Arithmetic Operations**: The compiler supports basic arithmetic operations such as addition, subtraction, multiplication, division and modulo.
- **Control Flow**: Basic control flow constructs like `IF` statements and `WHILE` loop are supported.
- **Function Calls**: You can define and call functions with the `FUNCTION` keyword.


## Limitations and Areas for Improvement
This compiler project is a work in progress and has several limitations:

1. **Memory Usage Optimization**:

    The current implementation does not include optimizations for memory usage. Future improvements could focus on optimizing memory allocation and deallocation to enhance performance.

2. **NOT Operator Implementation**:

    The implementation of the `NOT` operator may not be correct. Currently, it uses the expression `1 - (x != 0)` instead of a proper bitwise `NOT` operation. This is a temporary workaround and needs to be replaced with a correct implementation.

3. **BYTE Type Support**:

    There is no support for a `BYTE` data type. Adding support for `BYTE` would allow for more efficient memory usage and operations on smaller data units.

4. **Builtin Code and Preprocessors**:

    There is no method to include builtin code or preprocessors. Adding support for preprocessors would allow for more flexible and powerful code transformations before the actual compilation process.


## Contributing
Contributions to this project are welcome. If you have ideas for improvements or new features, feel free to open an issue or submit a pull request.

## Acknowledgments
I would like to thank the following authors:

- **James Smith**, for his book [From Source Code To Machine Code](https://build-your-own.org/compiler/), which provided the foundational knowledge for this project.
- **statusfailed**, for the project [elf-from-scratch](https://github.com/statusfailed/elf-from-scratch), which guided the ELF file generation process, as the code of **James Smith** did not work for me.
- **Ruslan**, for his blog [Let’s Build A Simple Interpreter](https://ruslanspivak.com/lsbasi-part1/), which inspried this project.


## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE.txt) file for more details.

## Contact
For any questions or inquiries, please contact the project maintainer at nghiatnh02@gmail.com.