#!/usr/bin/env python3
"""
make_box.py -- writes Box.asm for your own personal number K.

The box is described in one place (three numbers at the top of Box.asm):
    start row = K
    height    = 20 rows
    width     = 16 * ((K mod 4) + 1) pixels = (K mod 4) + 1 words

Usage:
    python3 make_box.py 93          # K = 93 -> writes Box.asm
    python3 make_box.py 93 --asm Box.asm --hack Box.hack
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

TEMPLATE = """// ==========================================================================
//  Box.asm -- draw a black box on the Hack screen while a key is pressed
//  Nand to Tetris capstone, Part C
//
//  K = {K}          (last two digits of the roll number)
//    start row      = K                       = {K}
//    height         = 20 rows                 = {height}
//    width          = 16 * ((K mod 4) + 1)    = 16 * {words} = {pixels} pixels = {words} word{s}
//    left edge      = column 0 (word 0 of every row)
//
//  Screen map:  row r starts at address SCREEN + 32*r   (SCREEN = 16384)
//               writing -1 to a word paints its 16 pixels black
//               writing  0  to a word clears them
//
//  To move the box down for the viva, change the number on the
//  "START ROW" line below (for example {K} -> {moved}) and reassemble.
// ==========================================================================

(BOOT)
    @{K:<22} // START ROW = K
    D=A
    @startRow
    M=D

    @{words:<22} // WIDTH IN WORDS = (K mod 4) + 1
    D=A
    @width
    M=D

    @{height:<22} // HEIGHT IN ROWS
    D=A
    @height
    M=D

// --------------------------------------------------------------------------
//  MAIN: look at the keyboard, choose -1 (paint) or 0 (erase), then draw
// --------------------------------------------------------------------------
(MAIN)
    @KBD                    // RAM[24576] holds the code of the pressed key (0 = none)
    D=M
    @PRESSED
    D;JNE                   // a key is down -> paint with -1

    @fill                   // no key -> paint with 0, which erases the box
    M=0
    @PAINT
    0;JMP

(PRESSED)
    @fill
    M=-1

// --------------------------------------------------------------------------
//  PAINT: addr = SCREEN + 32 * startRow
// --------------------------------------------------------------------------
(PAINT)
    @SCREEN
    D=A
    @addr
    M=D
    @startRow
    D=M
    @rowsToSkip
    M=D

(SKIP_ROWS)
    @rowsToSkip
    D=M
    @ADDRESS_READY
    D;JEQ
    @addr
    D=M
    @32
    D=D+A
    @addr
    M=D
    @rowsToSkip
    M=M-1
    @SKIP_ROWS
    0;JMP

(ADDRESS_READY)
    @height
    D=M
    @rowsLeft
    M=D

// --------------------------------------------------------------------------
//  One row: write `width` words starting at addr
// --------------------------------------------------------------------------
(ROW)
    @addr
    D=M
    @ptr
    M=D
    @width
    D=M
    @wordsLeft
    M=D

(WORD)
    @fill
    D=M
    @ptr
    A=M
    M=D                     // RAM[ptr] = fill
    @ptr
    M=M+1
    @wordsLeft
    M=M-1
    D=M
    @ROW_DONE
    D;JEQ
    @WORD
    0;JMP

// --------------------------------------------------------------------------
//  Next row: addr = addr + 32
// --------------------------------------------------------------------------
(ROW_DONE)
    @addr
    D=M
    @32
    D=D+A
    @addr
    M=D
    @rowsLeft
    M=M-1
    D=M
    @DONE
    D;JEQ
    @ROW
    0;JMP

(DONE)
    @MAIN
    0;JMP                   // keep scanning the keyboard forever
"""


def main():
    parser = argparse.ArgumentParser(description="Write Box.asm for a given K.")
    parser.add_argument("k", type=int, help="your personal number (last two digits of the roll number)")
    parser.add_argument("--asm", default=os.path.join(HERE, "Box.asm"))
    parser.add_argument("--hack", default=os.path.join(HERE, "Box.hack"))
    parser.add_argument("--no-assemble", action="store_true")
    args = parser.parse_args()

    if not 0 <= args.k <= 99:
        sys.exit("K must be between 0 and 99 (the last two digits of the roll number)")

    words = (args.k % 4) + 1
    pixels = words * 16
    height = 20
    moved = min(args.k + 10, 235)      # a start row for the viva demo, still on screen

    source = TEMPLATE.format(
        K=args.k,
        words=words,
        pixels=pixels,
        height=height,
        moved=moved,
        s="s" if words > 1 else "",
    )

    with open(args.asm, "w") as handle:
        handle.write(source)
    print("K = %d -> start row %d, %d rows tall, %d pixels wide (%d words)"
          % (args.k, args.k, height, pixels, words))
    print("wrote", args.asm)

    if not args.no_assemble:
        subprocess.run(
            [sys.executable, os.path.join(HERE, "assembler.py"), args.asm, "-o", args.hack],
            check=True,
        )


if __name__ == "__main__":
    main()
