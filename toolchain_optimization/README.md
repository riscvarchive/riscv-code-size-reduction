# Toolchain Optimization

## Reference Toolchains

- [GNU Arm Embedded Toolchain](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm/downloads) / LLVM? Version / download link?
- [ARC](https://github.com/foss-for-synopsys-dwc-arc-processors/toolchain/releases)

## Toolchain optimisation suggestions
1. Recognising similar/same constants in the linker and simplifying them

2. fix -mno-strict-align

3. Reported by Matteo: https://github.com/riscv/riscv-gcc/issues/193

4. Use C.SWSP instead of SB/SH when zeroing stack variables, so can use 16-bit encodings and if possible group variables together to allow fewer stores to cover them all

5. Library support
	- Optimized library functions can make the difference for two reasons:
 		- Code tailored for embedded application
 		- Smaller + Faster code, assembly-optimized in the critical parts
 		- No intricate inter-dependencies, which call a lot of different functions even if they are not fundamental

	- Different libraries to optimize:
 		- Low-level runtime library (e.g. libgcc)
  		- Optimize the FP functions, which bloat the code especially when linked to small programs
 		- Other _external_ libraries, like newlib
  		- picolibc by Keith Packard (https://keithp.com/blogs/picolibc/, https://github.com/picolibc/picolibc) is the evolution of newlib-nano, a shrunk version of newlib. Citing the GitHub description: _"Picolibc is library offering standard C library APIs that targets small embedded systems with limited RAM. Picolibc was formed by blending code from Newlib and AVR Libc."_

6. runtime library optimisation
7. link time optimisation
	- including dead code elimination
	- outlining
8. function prologue/epilogue optimisation in software, to close the gap with the PUSH/POP ISA extension proposal


## Linker script and Global Pointer optimization

The position of the Global Pointer (GP) is fundamental for the code size problem since memory operations exploit it as a base register for the addressing without the need to pre-load an immediate (the base for the addressing) in a register. Given the 12-bit signed-immediate encoding of the memory operations, the GP is effective when the memory address falls within the interval [GP-2KiB, GP+2KiB), so frequently accessed data should be placed in this range to maximize the code-size/performance benefit. This operation can be done inside the linker script.

