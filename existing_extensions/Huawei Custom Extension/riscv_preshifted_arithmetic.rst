
RISC-V 32-bit Pre-shifted Arithmetic Extension
==============================================

These instructions are included in the Huawei custom RISCV extension, and are implemented on silicon.

Rationale
---------

ARMv7-M code is very efficient for data processing, making heavy use of an arithmetic or logical operation with a shifted/rotated register operand. 
For example:

``add.w r2, r3, r4, lsl #3``

takes one 4-byte instruction

RISC-V requires

``c.slli x4, x4, #3``

``add x2, x3, x4``

6-bytes of instructions. These sequences are very common when compiling softfloat with GCC.

The proposal is to define instructions which specify a shift type and immediate operand which 
allows one source register to be shifted prior to performing the operation.

The shift types are:

•	``sll`` #1-31 logical shift left
•	``srl`` #1-31 logical shift right
•	``sra`` #1-31 arithmetic shift right
•	``ror`` #1-31 rotate right 

A shift distance of zero is illegal

Including ``ror`` is useful because there is no native rotate instruction in risc-v, it is only present if the B-extension is implemented.

The instructions are:

•	``ADDSHF  rd, rs1, rs2, <shift_type> # shift_amount``
•	``SUBSHF  rd, rs1, rs2, <shift_type> # shift_amount``
•	``ORSHF   rd, rs1, rs2, <shift_type> # shift_amount``
•	``XORSHF  rd, rs1, rs2, <shift_type> # shift_amount``
•	``ANDSHF  rd, rs1, rs2, <shift_type> # shift_amount``
•	3 encodings are reserved for future use

These are the most common instructions of this type in the Huawei IoT code:

=============== ================ ========== 
Percentage      Base instruction Shift type 
=============== ================ ========== 
59.4%           OR               SLL 
27.5%           ADD              SLL
4.9%            ADD              SRL
1.8%            OR               SRL
1.4%            XOR              ROR
1.0%            ADD              ROR
1.0%            AND              SLL
=============== ================ ========== 

=============== ================  
Percentage      Shift distance
=============== ================  
29.0%           8
16.4%           2
14.9%           16
6.5%            3
4.5%            1
3.9%            4
1.3%            5
1.1%            6
1.0%            7
0.9%            31
=============== ================  

=============== ================  
Percentage      Shift range
=============== ================  
64.0%           1-8
17.5%           9-16
15.5%           17-24
2.5%            25-31
=============== ================  


Therefore a limited shift distance of 1-16 would cover the majority of cases, but more code bases need to be analysed.

These instructions are implemented in the RISC-V HCC toolchain, this is the internal Huawei branch of GCC including the Huawei custom instructions

- enabled with -fmerge-immshf
- save 0.3% of Huawei IoT code size but also give performance improvement


Opcode Assignment
-----------------

.. table:: encoding for preshifted arithmetic operations

  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | 31 | 30 | 29 | 28 | 27 | 26 | 25 |24:23|    22:20| 19:15 | 14 | 13 | 12 | 11 | 10 | 9 | 8 | 7 | 6 : 0 | instruction            |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | **custom-1 encoding group**                                                                                                    |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | shtype  | shamt                  | rs2           | rs1   | 000          |  rd                 |0101011| ADDSHF                 |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | shtype  | shamt                  | rs2           | rs1   | 001          |  rd                 |0101011| SUBSHF                 |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | shtype  | shamt                  | rs2           | rs1   | 010          |  rd                 |0101011| ORSHF                  |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | shtype  | shamt                  | rs2           | rs1   | 011          |  rd                 |0101011| XORSHF                 |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | shtype  | shamt                  | rs2           | rs1   | 100          |  rd                 |0101011| ANDSHF                 |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+

- shtype = 00: SLL

- shtype = 01: SRL

- shtype = 10: SRA

- shtype = 11: ROR


Assembler Syntax
----------------

.. code-block:: text

  add x1, x2, x3, sll  #1// x1 = x2 + (x3 << 1)``
  sub x1, x2, x3, ror #30// x1 = x2 – ror(x3, 30)``
  or  x1, x2, x3, srl #30// x1 = x2 | (x3 >> 30)``
  xor x1, x2, x3, sra #30// x1 = x2 ^ asr(x3, 30)``
  and x1, x2, x3, sll #30// x1 = x2 & (x3 << 30)``

This pseudo instruction is also defined

.. code-block:: text

  ror       x1, x2, #shamt // expands to r x1, zero, x2, ror #shamt


