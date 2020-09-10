RISC-V 48-bit Load Long Immediate Extension
===========================================

This instruction is included in the Huawei custom RISCV extension, and is implemented on silicon.

Rationale
---------

The table below summarises the number of bytes of code required to load different sizes of immediate using the RV32IMC instruction set.

=============== =============================== ============================= =================
Immediate range	Size of signed immediate (bits)	Code sequence                 Code Size (bytes)
=============== =============================== ============================= =================
+/-32	          6                               c.li  rd, imm                 2
+/-2048         12                              addi  rd, zero, imm	          4
+/-256K         18                              c.lui rd, imm[17:12]+imm[11]  6
                                                
                                                addi  rd, rd, imm[11:0]
+/-2G           32                              lui   rd, imm[31:12]+imm[11]  8

                                                addi  rd, rd, imm[11:0]
=============== =============================== ============================= =================

Table 1: code size for different sizes of immediate

Note: The addition of imm[11] to the upper bits of the immediate in the lui instructions is required to counteract the effect of the sign bit 
in the addi instruction.

In the worst case a 32-bit immediate value can require 8 bytes of code to load. The frequency with which this occurs is highly dependent upon 
the application code and on the memory layout as the compiler will use these sequences when loading pointer values into registers.

ARMv7M code typically uses a 16-bit encoding of a PC relative load to access constant data from a constant pool which is placed at the end of a function.
Therefore we have seen a case where loading a constant representing a string in the OPUS decoder requires 8-bytes on RISC-V, and only 2-bytes on ARMv7M. Additionally the string was loaded many times so the extra 6-bytes of code was incurred many times.

This proposal encodes full 32-bit signed immediate data into a 48-bit encoding. The sign extension becomes visible if this instruction is implemented on an RV64 machine.
We have the instruction an ``l.`` prefix indicating a long encoding. This naming scheme may not scale to longer (64bit+) encodings, so may need to change.

``l.li`` is implemented in the RISC-V HCC toolchain, this is the internal Huawei branch of GCC including the Huawei custom instructions

- enabled with *–femit-lli*
- saves 0.79% of Huawei IoT code size

Note that the curent compiler implementation is sub-optimal, so I think that the code-size saving could increase a lot.

- ``l.li`` always requires 48-bits for large constants
- for certain values GCC can often use fewer instruction bytes to form the constant than is currently achieved in HCC

The advantage of encoding the constant in the instruction stream is that a load instruction is not required to read the data, therefore increasing performance and reducing power. The disadvantage is that if the constant value is needed multiple times it must be held in a register, so that the 48-bit instruction is not required to be issued again, whereas ARMv7M only requires an additional 16-bit instruction to load the data again.

Typical usage
-------------

Analysing the Huawei IoT code output from HCC, we see ~17000 ``l.li`` instructions, and the resulting values are used as follows:

=========== ======================= =========================================
percentage  l.li usage              comment
=========== ======================= =========================================
28.5%       function argument       set a0-a7 before a j or jal call
12.2%       LW address              load word from distant address
6.6%        LBU address             load unsigned byte from distant address
6.0%        SW address              store word to distant address
5.6%        ADD src/dst             the result is added to a register value
3.3%        SB address              store byte to distant address
3.1%        AND src/dst             the result is masked by a register value
2.4%        ADDSHF src or src/dst   source for fused add/shift, see below
2.0%        MULIADD src or src/dst  source for fused mul/add, see below
1.8%        LHU address             load unsigned half from distant address
1.0%        B* source               result feeds into a conditional branch
=========== ======================= =========================================

where the ``l.li`` is used as a load address, it is frequently held in a register and reused as a store address. I don't have exact statistics for how often the address is reused (the table above show the first use of the ``l.li`` result only).

``addshf`` is a custom instruction, not yet on github

``muliadd`` is a custom instruction, defined here: https://github.com/riscv/riscv-code-size-reduction/blob/master/proposals/Huawei%20Custom%20Extension/riscv_muladd_extension.rst

Opcode Assignment
-----------------

.. table:: encoding for load long immediate

  +-----+-----+-----+-------+-----+----+-------+----+----+---+---+------------------------+
  |47:43|42:38|       37:32 |31:17|16  | 15:12 | 11 :7   | 6 : 0 | instruction            |
  +-----+-----+-----+-------+-----+----+-------+----+----+---+---+------------------------+
  |imm[31:0]                           | 0000  | rd      |0011111| L.LI                   |
  +-----+-----+-----+-------+-----+----+-------+----+----+---+---+------------------------+

Assembler Syntax
----------------

The assembler will use the pseudo instruction mnemonic that is already defined for loading immediates (``li``) , but the compiler will only 
target the use of the 48-bit form when this extension is enabled and the immediate cannot be expressed in a shorter form. 

*Example*

``li x1, 0x80000024``






