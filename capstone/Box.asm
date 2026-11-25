// ==========================================================================
//  Box.asm -- draw a black box on the Hack screen while a key is pressed
//  Nand to Tetris capstone, Part C
//
//  K = 93          (last two digits of the roll number)
//    start row      = K                       = 93
//    height         = 20 rows                 = 20
//    width          = 16 * ((K mod 4) + 1)    = 16 * 2 = 32 pixels = 2 words
//    left edge      = column 0 (word 0 of every row)
//
//  Screen map:  row r starts at address SCREEN + 32*r   (SCREEN = 16384)
//               writing -1 to a word paints its 16 pixels black
//               writing  0  to a word clears them
//
//  To move the box down for the viva, change the number on the
//  "START ROW" line below (for example 93 -> 103) and reassemble.
// ==========================================================================

(BOOT)
    @93                     // START ROW = K
    D=A
    @startRow
    M=D

    @2                      // WIDTH IN WORDS = (K mod 4) + 1
    D=A
    @width
    M=D

    @20                     // HEIGHT IN ROWS
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
