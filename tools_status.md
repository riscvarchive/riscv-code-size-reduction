# GCC

## Build instructions:

-	Clone https://github.com/plctlab/corev-gcc into a folder called gcc
-	Clone https://github.com/plctlab/corev-binutils-gdb into a folder called binutils-gdb
-	Download this helpful script from embecosm  https://github.com/embecosm/embecosm-toolchain-releases/blob/master/stages/build-riscv32-gcc.sh and execute it in the same folder you cloned gcc and binutils, this should and build gcc, binutils and libs.
-	One could change the flags in the script to build the std lib with Zc* enabled
## known Issues:

- Introducing unnecessary unimps after functions possibly due to alignment issue : https://github.com/plctlab/corev-gcc/issues/2
* The note about c.zext.b is wrong really because it maps to andi 255

# LLVM:

## Build instructions:

-	Clone https://github.com/plctlab/llvm-project/tree/riscv-zce-llvm14
-	cd llvm-project
-	mkdir build
-	cd build
-	cmake -DLLVM_TARGETS_TO_BUILD="RISCV" -DLLVM_ENABLE_PROJECTS="clang;lld;libcxx;libcxxabi" -DCMAKE_BUILD_TYPE=Release -G "Unix Makefiles"  ../llvm 
-	make –j$(nproc)
	
## Known Issues:

- Compiler crashing in some cases with push/pop enabled: https://github.com/plctlab/llvm-project/issues/40 (Fixed)
- Linker relaxation not working https://github.com/plctlab/llvm-project/issues/41 (Fixed)

# Spike

- https://github.com/plctlab/plct-spike/tree/plct-zce-dev-0.70.0
