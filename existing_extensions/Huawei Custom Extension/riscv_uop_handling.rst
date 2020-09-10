RISC-V UOP Handling for Sequenced Instructions
==============================================

This documents how Huawei implemented sequenced instructions. This is similar to the ``vstart`` approach taken in the vector extension.

Load/store multiple instructions and push/pop require execution over multiple UOPs (micro-ops).
Every UOP represents one step of the sequence required to complete execution of a sequenced instruction.
Every UOP is a standard 32-bit encoding of a RISCV instruction, and so the sequenced instruction can be 
expanded into a sequence of UOPs at the input to the instruction decoder, without changing the decode logic. 
Therefore UOPs always write results to standard X/F registers. A UOP must not be a sequenced instruction, i.e. no recursion is allowed.

The control logic needs to change to track the UOP number, and not to increment the PC until the final UOP has issued.

It is possible to implement instructions which require more than two register read ports as a sequence of UOPs, 
providing any intermediate results can be written to standard registers (not special temporary registers) as this
would prevent the UOP using a standard RISCV encoding.

Handling interrupts, exceptions etc.
------------------------------------

The simplest approach is to treat a sequenced instruction as a single uninterruptible entity. 
If there is an interrupt then either complete all of the instruction (every UOP), or none of it.
This is bad for interrupt latency, and also can cause problems if a UOP is a load or store instruction which causes a 
load/store access fault or fires a trigger (which either causes entry into debug mode or a handler). 
In these cases the sequence *should* be interrupted when the exception fires, so that the handler runs or debug mode is entered at the correct point. 
The UOP number which caused the exception must also be available (like ``vstart``)  in the handler/debug mode and also for restart.

Given that the sequence can be interrupted by an exception, it makes sense to allow interrupts at any UOP.
Also, given that a trigger can cause entry into debug mode on any load/store UOP it makes sense to allow external debug halt on *any* UOP, 
to keep the specification regular and remove special cases.

The proposal is to add a field to ``xstatus`` (i.e. ``[msu]status`` ) called ``step`` in bits [30:26] to allow up to 31 UOPs from a single instruction.
``xstatus.step`` says how many UOPs completed in ``x`` mode before the exception/interrupt, so 0 means none of the instruction executed 
(or the interrupted instruction was not a sequenced instruction). Why add a field to ``xstatus`` ? It was the most convenient place as it
already forms part of the context, so requires no software changes.

``xstatus.step`` is only updated by issuing sequenced instructions or software writes to the ``xstatus`` register. If handler or debug mode code
issue any sequenced instructions then they must save/restore the value of ``xstatus.step`` before returning to the interrupted sequenced instruction.

On debug mode entry, also update ``xstatus.step`` when debug mode is entered from ``x`` mode. This seems a bit strange, as it's not a D register but it avoided the need for a debug mode register
representing the UOP number. This seems irregular, but simple. Maybe there should be a ``dxxx.step`` field somewhere, TBD.

*In our implementation we only had U and M-mode,and no N-extension, and only added the step field to mstatus*

``xstatus.step`` says which UOP to execute first when executing the next sequenced instruction. If it is out of range (e.g. ``xstatus.step=5`` and the next sequenced instruction only has 3 UOPs) then take an illegal instruction exception.

Given that any UOP may be interrupted the question is how to restart. 

Restarting sequenced instructions
---------------------------------

This section can all be *implementation defined* but there are issues to raise.

These are all options for restarting sequenced instructions.

1. Issue the whole sequence again, which means that interrupts must be disabled and triggers are not possible if any UOP cannot be reissued 
   (e.g. the ``sp`` increment in a ``C.POPRET`` cannot be reissued, more on this below)
2. Rely on the handler to complete the sequence by emulating the remaining UOPs and setting ``xstatus.step=0``
3. Implement hardware restart, so that on an ``xret`` (i.e. ``[msu]ret`` ) or debug resume, if ``xstatus.step>0`` then continue the sequence, or take an exception if the 
   step value is out of range for the encoding.

An an example for ``C.POPRET`` which issues this sequence, instruction definition 
`here <https://github.com/riscv/riscv-code-size-reduction/blob/master/existing_extensions/Huawei%20Custom%20Extension/riscv_push_pop_extension.rst>`_

  - UOP 0 lw  x19, 12(sp);  
  - UOP 1 lw  x18, 16(sp);
  - UOP 2 lw   x9, 20(sp);  
  - UOP 3 lw   x8, 24(sp);
  - UOP 4 lw   x1, 28(sp);
  - UOP 5 addi sp, sp, 32; 
  - UOP 6 ret


Notes


  
  - UOPs 0-5 can be interrupted/debug halted. UOP 6 *can't* because UOP 5 cannot be issued more than once if restart option 1 above is implemented. Any UOP may be 
    interrupted/debug halted for restart ioptions 2 and 3
  - UOPs 0-4 can cause load alignment faults or watchpoint triggers
  - UOP 0 can cause a PC match trigger

However, it's possible that the interrupt handler will want to allocate space on the stack, in which case the stack pointer increment must be issued *first*
so that the the load to x19, x18 etc. don't get overwritten. In which case the sequence must be:

  - UOP 0 addi sp, sp, 32; 
  - UOP 1 lw  x19, -20(sp);  
  - UOP 2 lw  x18, -26(sp);
  - UOP 3 lw   x9, -12(sp);  
  - UOP 4 lw   x8,  -8(sp);
  - UOP 5 lw   x1,  -4(sp);
  - UOP 6 ret

Then restart option 1 no longer works as the stack pointer will be incremented more than once, so options 2 or 3 must be used.

For a load/store multiple style instruction without the complexity caused by ``addi/ret`` then restart option 1 can be implemented, 
assuming that the memory is idempotent.


