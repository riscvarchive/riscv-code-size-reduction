RISC-V 16-bit Load/Store Byte/Half Extension Proposal
=====================================================

These instructions are included in the Huawei custom RISCV extension

Rationale
---------

The RISC-V C extension supports ``c.lw``, ``c.sw`` but it does not support 16-bit encodings of smaller data types. 
Analysis has shown that ``c.lbu`` , ``c.sb`` (load byte unsigned, store byte), and ``c.lhu`` , ``c.sh`` give a significant benefit to code size.
In the Huawei IoT code base the benefit of the byte instructions is roughly double the benefit of the half-word instructions.

Signed byte / half loads give minimal benefit and so are not proposed.

``c.lbu`` , ``c.sb`` are implemented in the RISC-V HCC toolchain, this is the internal Huawei branch of GCC including the Huawei custom instructions

-  enabled with *–Wa,-enable-c-lbu-sb*
-  save 1.5% of NB-IoT code size

``c.lhu`` , ``c.sh`` are implemented in the RISC-V HCC toolchain

-  enabled with *-Wa,-enable-c-lhu-sh*
-  save 0.7% of NB-IoT code size

Opcode Assignment
-----------------

..table:: encodings for load/store byte/half

  +----+----+----+----+----+----+---+---+---+----+----+---+---+---+---+---+-----------------+
  | 15 | 14 | 13 | 12 | 11 | 10 | 9 | 8 | 7 | 6  | 5  | 4 | 3 | 2 | 1 | 0 |instruction      |
  +----+----+----+----+----+----+---+---+---+----+----+---+---+---+---+---+-----------------+
  |  1 |  0 |  1 |  uimm[0,4:3] | rs1’      |uimm[2:1]| rs2’      | 0 | 0 | C.SB            |
  +----+----+----+----+----+----+---+---+---+----+----+---+---+---+---+---+-----------------+
  |  0 |  0 |  1 |  uimm[0,4:3] | rs1’      |uimm[2:1]| rd’       | 0 | 0 | C.LBU           |
  +----+----+----+----+----+----+---+---+---+----+----+---+---+---+---+---+-----------------+
  |  1 |  0 |  1 |  uimm[5:3]   | rs1’      |uimm[2:1]| rs2’      | 1 | 0 | C.SH            |
  +----+----+----+----+----+----+---+---+---+----+----+---+---+---+---+---+-----------------+
  |  0 |  0 |  1 |  uimm[5:3]   | rs1’      |uimm[2:1]| rd’       | 1 | 0 | C.LHU           |
  +----+----+----+----+----+----+---+---+---+----+----+---+---+---+---+---+-----------------+

These encodings replace double precision floating point load/stores in the compressed encoding space.
Other encodings are difficult to find as the immediate is quite long for the instructions to be useful.

.. code-block:: text

  c.lbu: 	x[8+rd’] = zero_extend(M[x[8+rs1’] + uimm][7:0])
  c.lhu: 	x[8+rd’] = zero_extend(M[x[8+rs1’] + uimm][15:0])
  c.sb :	M[x[8+rs1’] + uimm][7:0] 	= x[8+rs2’]
  c.sh :	M[x[8+rs1’] + uimm][15:0] 	= x[8+rs2’]

``uimm[0]`` is implicitly zero for ``c.lhu`` / ``c.sh``.

Note that the registers are all in the range x8-x15 (s0-1, a0-5). The compiler should be aware of this restriction and optimise the register allocation 
to allow for these registers to be selected, so that the 16-bit encodings are selected more often.

Assembler Syntax
----------------

.. code-block:: text

  c.lbu  s0,5(a1)  // load zero extended byte from address a1+5
  c.sb   s1,6(a1)  // store s1[7:0] to address a1+6
  c.lhu  s0,10(a1) // load zero extended half-word from address a1+10
  c.sh   s1,12(a1) // store s1[15:0] to address a1+12

