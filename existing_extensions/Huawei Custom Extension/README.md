Huawei Custom Extension
-----------------------

Here are the specifications for instructions to reduce code size, which are currently available on silicon:

- [16-bit load/store byte/half](https://github.com/riscv/riscv-code-size-reduction/blob/master/existing_extensions/Huawei%20Custom%20Extension/riscv_ldst_bh_extension.rst)
- [16-bit push/pop](https://github.com/riscv/riscv-code-size-reduction/blob/master/proposals/Huawei%20Custom%20Extension/riscv_push_pop_extension.rst)
- [32-bit compare immediate branch](https://github.com/riscv/riscv-code-size-reduction/blob/master/proposals/Huawei%20Custom%20Extension/riscv_condbr_imm_extension.rst)
- [32-bit long jump](https://github.com/riscv/riscv-code-size-reduction/blob/master/proposals/Huawei%20Custom%20Extension/riscv_longjump_extension.rst)
- [32-bit multiply immediate add](https://github.com/riscv/riscv-code-size-reduction/blob/master/proposals/Huawei%20Custom%20Extension/riscv_muladd_extension.rst)
- [32-bit preshifted arithmetic](https://github.com/riscv/riscv-code-size-reduction/blob/master/proposals/Huawei%20Custom%20Extension/riscv_preshifted_arithmetic.rst)
- [48-bit load long immediate](https://github.com/riscv/riscv-code-size-reduction/blob/master/proposals/Huawei%20Custom%20Extension/riscv_LLI_extension.rst)

There are also 
- 32-bit load/store multiple (spec not included, I'll post a revised version for the new RISC-V extension)
- 16-bit byte/half zero extension (trivial to specify, and useful for compiling softfloat)

As noted in the documents, the 16-bit push/pop instructions and the 32-bit long jump instructions may need modification before being used as proposals for the new RISC-V extension.

Also refer to this [paper](https://github.com/riscv/riscv-code-size-reduction/blob/master/CARRV2020_final.pdf) for analysis. Unfortunately the code size results don't agree with the measurements in my proposal documents, so we need to standardise on a code size measurement methodology.

Load/store multiple and push/pop execute *multiple UOPs (micro-ops)*, proposed handling for these is documented [here](https://github.com/riscv/riscv-code-size-reduction/blob/master/existing_extensions/Huawei%20Custom%20Extension/riscv_uop_handling.rst)
