RISC-V 32-bit Multiply by Immediate and Add Extension
=====================================================

The 32-bit version of this instruction is included in the Huawei custom RISCV extension, and is implemented on silicon.

Rationale
---------

For efficient indexing into array structures in C-code, such as this example from the Huawei IoT code (with the variable and function names changed)

.. code-block:: text

  uint32 get_element(uint8 index) {
    return array_base[index].element1.element2
  }

``muliadd`` is implemented in the RISC-V HCC toolchain, this is the internal Huawei branch of GCC including the Huawei custom instructions

- enabled with *–femit-muliadd*
- saves 0.32% of Huawei IoT code size

To compiler the ``get_element`` function the compiler needs to:

1.	Load the base address of the array (``array_base``)
2.	Multiply the size of the array element by the array index (``index``)
3.	Add the base address of array to the result of the multiply
4.	Load using the result of stage 3 as the base address and add an immediate offset to access a specific field of the selected element (``element1.element2``)

HCC returns:

.. code-block:: text
  
  02002a96 <get_element>:
  02002a96      47d1          li          a5,20      ;;//load the element size
  02002a98      02f50533      mul         a0,a0,a5   ;;//multiply by the index
  02002a9c      010057b7      lui         a5,0x1005  ;;//build up array_base
  02002aa0      74478793      addi        a5,a5,1860 # 1005744 <array_base>
  02002aa4      953e          add         a0,a0,a5   ;;//add it to the element_size*index
  02002aa6      4548          lw          a0,12(a0)  ;;//load the final result
  02002aa8      8082          ret


The function uses 20 bytes of code:

1.	``lui/addi`` can be combined into ``l.li`` saving 2 bytes: see the `load long immediate proposal <https://github.com/riscv/riscv-code-size-reduction/blob/master/proposals/Huawei%20Custom%20Extension/riscv_LLI_extension.rst>`_
2.	``l.li, mul, add`` can be converted to ``muliadd`` saving 4 bytes.	``muliadd`` multiplies a register value by a constant, and then adds a register value

Therefore we can save 6 bytes on this sequence using the proposed custom instructions ``muliadd`` and ``l.li``. The optimised code sequence is:

.. code-block:: text

  l.li      a5,#0x1005744       #combine lui and addi   (48-bit encoding)
  muliadd   a0,a5,a0,#20        #combine li, mul, add   (32-bit encoding)
  lw        a0,12(a0)           #lw unchanged           (16-bit encoding)
  ret                           #ret unchanged          (16-bit encoding)

The range of the immediate supported by the ``muliadd`` instruction is important and has a significant impact upon its usefulness. 
The 32-bit encoding has an *unsigned* 7-bit immediate representing bits [7:1].
The value of different lengths of the immediate are shown in the table:

================ =================
immediate range  code-size saving
================ =================
uimm[7:1]        0.32%
uimm[6:1]        0.29%
uimm[5:1]        0.23%
uimm[4:1]        0.18%
uimm[3:1]        0.10%
uimm[2:1]        0.02%
uimm[1]          0.01%
================ =================

The primary justification for ``muliadd`` is to efficiently encode the structure references above, however this instruction may 
also be useful in other areas. 

Opcode Assignment
-----------------

  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | 31 | 30 | 29:27        | 26:25   |24:23|    22:20| 19:15 | 14:12        | 11:9        | 8 | 7 | 6 : 0 | instruction            |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | uimm[7:1]\ :sup:`*`              | rs2           | rs1   | 111          |  rd                 |0101011| MULIADD                |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
\ :sup:`*` uimm[0]=0

``muliadd`` is currently implemented in ``custom-1``


Assembler Syntax
----------------

.. code-block:: text

  muliadd   x4, x1, x2, #<imm>	// x4 = x1 + (x2 * zero_ext(imm))

48-bit encoding proposal
------------------------

It's possible that a version of ``muliadd`` with a longer immediate would be useful, although it's not beneficial for the IoT code.
Here is a proposal encoding, and the immediate is now signed to allow negative offsets. This instruction has *not* been implemented in the Huawei custom extension.

  +-----+-----+-----+-------+-----+-----+--+--+-------+----+----+---+---+------------------------+
  |47:32            | 31:25 |24:20|19:17|16|15| 14:12 | 11 :7   | 6 : 0 | instruction            |
  +-----+-----+-----+-------+-----+-----+--+--+-------+----+----+---+---+------------------------+
  |imm[15:0]        |00...00|rs2  | rs1       | 001   | rd      |0011111| L.MULIADD              |
  +-----+-----+-----+-------+-----+-----+--+--+-------+----+----+---+---+------------------------+

The immediate value is signed for ``l.muliadd`` and unsigned for ``muladd``. In the NB-IoT code it is rare to need a negative immediate so 
``muliadd`` covers the common cases due to the restricted number of immediate bits available.

Note that some RISCV instructions also have unsigned immediate in a smaller encoding and signed immediates in a larger encoding, for example ``C.FSD`` and ``FSD``

.. code-block:: text

  l.muliadd rd = rs1 + rs2 * sign_ext(imm)

Assembler Syntax
----------------

.. code-block:: text

  //the assembler will choose the 32-bit or 48-bit encoding depending on the immediate value only
  muliadd   x4, x1, x2, #<imm>	// x4 = x1 + (x2 * imm)





