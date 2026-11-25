// A short version of the official Memory.tst: RAM, screen and keyboard addressing.
load Memory.hdl,
compare-to Memory-quick.cmp,
output-file Memory-quick.out,
output-list in%D1.6.1 load%B2.1.2 address%B1.15.1 out%D1.6.1;

set in -1,           // RAM[0] = -1
set load 1,
set address 0,
tick, output, tock, output;

set load 0,
set in 9999,
set address 0, eval, output;        // RAM[0] still -1
set address %X2000, eval, output;   // RAM[8192] is empty (must NOT read the keyboard)
set address %X4000, eval, output;   // screen[0] is empty
set address %X6000, eval, output;   // keyboard, no key pressed

set in -1,           // screen[0] = -1
set load 1,
set address %X4000,
tick, output, tock, output;

set in 0,
set load 0,
set address %X4000, eval, output;   // screen[0] reads back -1
set address 0, eval, output;        // RAM[0] untouched by the screen write
