RISC-V 32-bit >±1Mbyte Offset Jump Extension
============================================

These instructions are included in the Huawei custom RISCV extension, and are implemented on silicon.

Rationale
---------

The standard RISC-V ISA allows ``JAL/J`` to jump ±1Mbyte from the current PC, this is usually sufficient when all the code is placed in a single 
continuous memory region. However in some SOCs the code is split between memory subsystems, for example, ROM, SRAM and/or Flash which are 
spaced widely in the address space. If there is frequent calling between regions (for example to access the shared save/restore routines 
associated with the ``–msave-restore`` or run-time library functions) significant code bloat can occur because each call requires an additional 
32-bit instruction to construct the target address.  

This proposal provides support for jumping ±16Mbytes from the current PC which matches the distance that can be achieved with the equivalent 
ARMv7-M instructions. However the benefit is highly dependent on memory map and code structuring and will be small if all code is occupies a single 
memory subsystem or the memory subsystems are so widely spaced that ±16Mbytes is insufficient to jump between them. 

These instructions are expensive in terms of encoding space and we therefore need to be confident that the number of jumps >±1MByte can’t be 
significantly reduced by other means (for example through address map changes).

Examining the Huawei IoT code we see that every ``JAL`` instruction expectedly uses one of the two link registers as specified by the RISC-V ABI, 
in the following proportions:

-	ra: 86.7%
-	t0:	13.3%

Therefore it is reasonable to only link to ra to cover the most common case.

*It would be useful to analyse the t0 link register cases……*

There are also many cases where jumps are issued with no link, these are usually caused by calls through function pointers.

This proposal increases the number of bits used for immediate offsets to increase the maximum jump distance at the cost of limiting the choice 
of destination register for the link address. It constrains the link address to being saved in ra/x1 or not being saved at all (effectively 
written to x0) to achieve a ±16Mbyte jump. If more encoding space was assigned or we chose only to implement link to ra then larger offsets 
could be achieved.

Which instructions are useful is very SoC specific, as the requirement is caused by the memory map.

These instructions are implemented in the RISC-V HCC toolchain, this is the internal Huawei branch of GCC including the Huawei custom instructions

- enabled with -Wl,--enjal16
- save 1.05% of Hiawei IoT code size

However, I don't recommend implementing them in the RISC-V extension as 96% of IoT cases are covered by ``JAL8`` i.e. the target of the jump is within ±8Mbyte. 
The additional range achieved by ``JAL16`` and the choice of excluding the link with ``J16`` make up the other 4%. 
``JAL8`` takes 1/4 of the encoding space of ``JAL16/J16`` so the cost/benefit is much higher.
Of course, the benefit is memory map dependant.

Opcode Assignment
-----------------

.. table:: encoding format for ``JAL16/J16``

  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | 31 | 30 | 29:27        | 26:25   |24:23|    22:20| 19:15 | 14:12        | 11:9        | 8 | 7 | 6 : 0 | instruction            |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | imm[20,10:1,11,19:12]                                                   | imm[24:21]      | 0 |1011011| JAL16                  |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+
  | imm[20,10:1,11,19:12]                                                   | imm[24:21]      | 1 |1011011| J16                    |
  +----+----+----+----+----+----+----+-----+----+----+-------+----+----+----+----+----+---+---+---+---+---+------------------------+

Supporting these two instructions is expensive in terms of encoding space as these two instructions fill the entire custom-3 encoding space (which is 
1/6 of the entire custom encoding space).

.. note:: 

Assembler Syntax
----------------
The assembler will use the standard syntax and the toolchain will target ``JAL16/J16`` opcodes only when ±1MByte limitations of the standard instructions 
is exceeded.

.. code-block:: text


  jal16	ra,	#<imm>	// jump to PC + sext(imm), link to ra

  j16		#<imm>	// jump to PC + sext(imm)




