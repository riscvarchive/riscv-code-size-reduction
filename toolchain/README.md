RISC-V GNU Compiler Toolchain with zc* support
==============================================

This is the RISC-V C and C++ cross-compiler. It supports a variety of zc extensions for RISC-V 32

## Getting the sources

This repository uses submodules for Newlib, GCC and Binutils. 

    $ git submodule update --init --recursive

## Building

There is a script provided which will build all of the required elements for the toolchain, along with standard libraries

    $ ./gcc.sh

This script uses the following default paths:

* `INSTALLPREFIX`: prefix/
* `BUILDPREFIX`: build/
* `SRCPREFIX`: .

These paths can be overridden as follows:

    $ INSTALLPREFIX=/usr/local ./gcc.sh

## Install

The script will install the toolchain in `./install` where it can be used as normal. 

### Extensions

The base extensions which are supported is rv32ima with ilp32 abi, and any combination of the following can be added:
* zca
* zcb
* zcmb
* zcmp
* zcmt

### Example usage

Compiling a basic c program with zc extensions:

```
<path to toolchain>/install/bin/riscv32-unknown-elf-gcc -march=rv32ima_zca_zcb_zcmb_zcmp_zcmt -mabi=ilp32 <path to program>/main.c
```