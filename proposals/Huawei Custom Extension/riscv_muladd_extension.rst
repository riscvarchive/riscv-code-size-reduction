RISC-V 32-bit Multiply/Add Extension
====================================

The 32-bit version instruction is included in the Huawei custom RISCV extension, and is implemented on silicon.

Rationale
---------

For efficient indexing into array structures in C-code, such as this example from the Huawei IoT code (with the variable names changed)

.. code-block:: text

  uint32 get_element(uint8 index) {
    return array_base[index].element1.element2
  }

The RISC-V HCC toolchain is the internal Huawei branch of GCC including the Huawei custom instructions

The compiler needs to:

1.	Load the base address of the array (``array_base``)
2.	Multiply the size of the array element by the array index (``index``)
3.	Add the base address of array to the result of the multiply
4.	Load using the result of stage 3 as the base address and an immediate offset to access a specific field of the selected element (``element1.element2``)

HCC returns:

.. code-block:: text
  
  02002a96 <get_element>:
  02002a96      47d1          li          a5,20
  02002a98      02f50533      mul         a0,a0,a5
  02002a9c      010057b7      lui         a5,0x1005
  02002aa0      74478793      addi        a5,a5,1860 # 1005744 <array_base>
  02002aa4      953e          add         a0,a0,a5
  02002aa6      4548          lw          a0,12(a0)
  02002aa8      8082          ret


The function uses 20 bytes of code:

1.	``lui/addi`` can be combined into ``l.li`` saving 2 bytes (see load long immediate proposal - yet to be uploaded)
2.	``mul/add`` can be combined into muladd saving 2 bytes

 a.	this joins the ``mul`` and ``add`` into a single instruction

3.	``muladd`` can be converted to ``muliadd`` saving 2 bytes (remove the ``li``)

 a.	this multiplies by a constant, and then adds a register value

Note that: if the value in ``a5`` is a power-of-two then ``addshf`` can be used, as the shift is a power-of-two multiply.

Therefore we can save 6 bytes on this sequence using the proposed custom instructions. The optimised code sequence is:

.. code-block:: text

  l.li      a5,#0x1005744       #combine lui and addi   (48-bit encoding)
  muliadd   a0,a5,a0,#20        #combine li, mul, add   (32-bit encoding)
  lw        a0,12(a0)           #lw unchanged           (16-bit encoding)
  ret                           #ret unchanged          (16-bit encoding)

The range of the immediate supported by the ``muliadd`` instruction is important and has a significant impact upon its usefulness. Processing the assembly 
output from all of the Huawei IoT code and looking for sequences of multiply by constant, we get these results of how many immediate values can be encoded 
for different ranges of values:

=============== ============
Immediate range	Success rate
=============== ============
0 to 31	        0%
0 to 63	        34%
0 to 127	      52%
0 to 255	      83%
0 to 511	      87%
0 to 1023    	  93%
0 to 2047	      99.7%
=============== ============

*Note that the remaining 0.3% of offsets are negative.*

The 32-bit encoding has an *unsigned* 7-bit immediate, and so a 48-bit encoding is also available with a *signed* 16-bit immediate  
which covers *all* cases seen in the code.

The primary justification for ``muliadd`` is to efficiently encode the structure references above, however this instruction may 
also be useful in other areas. 

Opcode Assignment
-----------------

  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | 31 | 30 | 29:27        | 26:25   |24:23|    22:20| 19:15 | 14:12        | 11:9        | 8 | 7 | 6 : 0 | instruction            |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | uimm[7:1]\ :sup:`*`              | rs2           | rs1   | 111          |  rd                 |0101011| MULIADD                |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+

``muliadd`` is currently implemented in ``custom-1``

\ :sup:`*` uimm[0]=0

Assembler Syntax
----------------

.. code-block:: text

  muliadd   x4, x1, x2, #<imm>	// x4 = x1 + (x2 * imm)

48-bit encoding proposal
------------------------

It's possible that a version of ``muliadd`` with a longer immediate would be useful, although it's not beneficial for the IoT code.
Here is a proposal encoding, and the immediate is now signed to allow negative offsets. This instruction has not been implemented by Huawei.

  +-----+-----+-----+-------+-----+-----+--+--+-------+----+----+---+---+------------------------+
  |47:32            | 31:25 |24:20|19:17|16|15| 14:12 | 11 :7   | 6 : 0 | instruction            |
  +-----+-----+-----+-------+-----+-----+--+--+-------+----+----+---+---+------------------------+
  |imm[15:0]        |00...00|rs2  | rs1       | 001   | rd      |0011111| L.MULIADD              |
  +-----+-----+-----+-------+-----+-----+--+--+-------+----+----+---+---+------------------------+

The immediate value is signed for ``l.muliadd`` and unsigned for ``muladd``. In the NB-IoT code it is rare to need a negative immediate so 
``muliadd`` covers the common cases due to the restricted number of immediate bits available.

*Some RISCV instruction also have unsigned immediate in a smaller encoding and signed immediates in a larger encoding, for example ``C.FSD`` and ``FSD``*

.. code-block:: text

  muliadd   rd = rs1 + rs2 * zero_ext(imm)
  l.muliadd rd = rs1 + rs2 * sign_ext(imm)

Assembler Syntax
----------------

.. code-block:: text

  //the assembler will choose the 32-bit or 48-bit encoding depending on the immediate value only
  muliadd   x4, x1, x2, #<imm>	// x4 = x1 + (x2 * imm)





