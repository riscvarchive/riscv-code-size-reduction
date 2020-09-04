RISC-V 48-bit Load Long Immediate Extension
===========================================

This instruction is included in the Huawei custom RISCV extension, and is implemented on silicon.

*This proposal needs a lot of updating don't read it yet :-)*

Rationale
---------

Comparative analysis has shown that the space-optimized (-Os) code produced by gcc for the RISC-V compressed instruction set (rv32imc)
is not as dense as other target architectures with support for compressed encodings. One contributor to this is the relative inefficiency 
of loading long immediates. 

The table below summarises the number of bytes of code required to load different sizes of immediate using the rv32imc instruction set.

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

Denser coding could be achieved through the use of pc-relative loads from a constant pool. Constant pools are typically placed so that they are
accessible using a relatively small immediate offset that can be encoded in a 16-bit instruction. The total cost is therefore the 2-bytes of 
code plus XLEN/8 bytes of data. Further saving are also possible as the same constant can be loaded at multiple places at an additional cost of 
2 bytes of code. Although constant pools give good code density savings there are some disadvantages as they are accessed through the d-side of 
the machine at a cost of increased d-side bandwidth, d-cache utilization and load-use latency.

This extension reduces the cost of encoding these larger immediate values through the use of a 48-bit encoding, the maximum number of bytes 
needed to encode a 32-bit immediate then becomes 6 bytes.


Opcode Assignment
-----------------

The RISC-V Unprivileged ISA specification already defines the opcode prefix required to identify a 48-bit instruction 
(see Chapter 23 RV32/64G Instruction Set Listings). Bits [1:0] are 11 to indicate a uncompressed instruction 
(all other values are allocated to the 16-bit opcodes), bits[4:2] are 111 to indicate a long opcode (>32bits), 
and bits [6:5] are 00 for a 48-bit instruction. Therefore all 48-bit opcodes share the same 7 bit prefix (bits[6:0]) 
of 00.111.11 (0x1f). In addition the standard RISC-V encoding always uses bits[11:7] to identify the destination register, 
source operands when present start at bit 15. This leaves bits[14:12] available to specify the function (0 for this). 
The immediate is placed in the upper 32-bits of the 48-bit opcode, leaving bit 15 spare (set to 0).

Thus the opcode format is:

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

Note that this is supported in the HCC linker with ``–Wl,--enllui``


*Example*

``li x1, 0x80000024``

``Opcode: 0x80000024009f``






