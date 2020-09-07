RISC-V 32-bit Conditional Branch Compare Immediate Extension
============================================================

These instructions are included in the Huawei custom RISCV extension, and are implemented on silicon.

Rationale
---------

When ARMv7-M code needs to take a conditional branch based upon a register value and a small constant, 
it requires 4-bytes of instructions. For example:

.. code-block:: text

  cmp r3, #2

  beq.n <offset>

because the cmp instruction implicitly sets the condition code flags the ``beq.n`` instruction does not need to 
specify a source register. 

The equivalent RISC-V code is like this:

.. code-block:: text

  c.li a2,#2

  beq a4, a2, <offset>

requiring 6-bytes of instructions.

This sequence occurs thousands of times in the Huawei IoT code, so the proposal is to add immediate forms of the 
32-bit condition branch instructions. For example:

``beqi a4, #2, <offset>``

which requires a single 32-bit encoding, and so is the same size as the ARMv7-M code.

According to code analysis, this sequence is by far most common for ``beq``, ``bne`` and is rare for other types of 
conditional branch instructions. There are 15 bits of immediate value available in the encoding space 
(bit 0 of the branch offset is not required). The optimum assignments are


1.	Allow an 8-bit immediate value

    a)	Compare register value against values -128 to +127 (signed) or 0 to +255 (unsigned)

2.	Allow a 10-bit branch offset (bit 0 isn’t stored)

    b)	Allows branches to PC-512 to PC+510

These instructions are implemented in the RISC-V HCC toolchain, this is the internal Huawei branch of GCC including the Huawei custom instructions

- enabled with -fimm-compare
- saves 0.89% of Huawei IoT code size

=========== =============
percentage  instruction
=========== =============
42.1%       BNEI
26.9%       BEQI
19.4%       BGEUI
9.5%        BLTUI
1.4%        BLTI
0.7%        BEGI
=========== =============

The full set needed to be implemented to allow HCC to infer the instructions, even though some are clearly of limited value.

Opcode Assignment
-----------------

.. table:: encoding for immediate conditional branches

  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  | 31 | 30 | 29 | 28 | 27 | 26 | 25 |24:23|    22:20| 19:15 | 14 | 13 | 12 | 11 | 10 | 9 | 8 | 7 | 6 : 0 | instruction  |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  | **custom-0 encoding group**                                                                                          |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  | cmpimm[7:0]                      |  offset[9:6]  | rs1   | 000          | offset[5:1]         |0001011| BEQI         |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  | cmpimm[7:0]                      |  offset[9:6]  | rs1   | 001          | offset[5:1]         |0001011| BNEI         |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  | cmpimm[7:0]                      |  offset[9:6]  | rs1   | 010          | offset[5:1]         |0001011| BLTI         |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  | cmpimm[7:0]                      |  offset[9:6]  | rs1   | 011          | offset[5:1]         |0001011| BGEI         |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  | cmpimm[7:0]                      |  offset[9:6]  | rs1   | 100          | offset[5:1]         |0001011| BLTUI        |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  | cmpimm[7:0]                      |  offset[9:6]  | rs1   | 101          | offset[5:1]         |0001011| BGEUI        |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+--------------+
  
LE(U) and GT(U) are not included as they can be achieved by modifying the immediate by 1.

For example 

-	a <= 2 can be transformed to a < 3 and use BLTI
-	a > 2 can be transformed to a >= 1 and use BGEI

Assembler Syntax
----------------

``beqi	r1, #1, <offset>	// if r1 == 	sign_ext(cmpimm) branch to PC+offset``

``bnei	r1, #1, <offset>	// if r1 != 	sign_ext(cmpimm) branch to PC+offset``

``blti	r1, #1, <offset>	// if r1 <  	sign_ext(cmpimm) branch to PC+offset``

``bgei	r1, #1, <offset>	// if r1 >= 	sign_ext(cmpimm) branch to PC+offset``

``bltui	r1, #1, <offset>	// if r1 <u  	zero_ext(cmpimm) branch to PC+offset``

``bgeui	r1, #1, <offset>	// if r1 >=u  zero_ext(cmpimm) branch to PC+offset``



