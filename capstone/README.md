# Capstone — Make the Computer Draw a Box

Nand to Tetris – I (ETCNTC301) · School of Engineering & Technology, K.R. Mangalam University
Individual work — **K = 93** (last two digits of roll number 2501730393)

| What K decides | Rule | Value |
|---|---|---|
| Box start row | row = K | 93 |
| Box height | 20 rows | 93 – 112 |
| Box width | 16 × ((K mod 4) + 1) pixels | 93 mod 4 = 1 → 32 px = 2 words |
| Extra assembler feature | K mod 3 | 93 mod 3 = 0 → symbol table saved in `symbols.txt` |

## What is in this folder

```
capstone/
├── hdl/                 the Hack computer, built from Nand up (31 chips)
│   ├── CPU.hdl          A/D registers, ALU control, jump logic, PC
│   ├── Memory.hdl       RAM16K / Screen / Keyboard address decoding
│   ├── Computer.hdl     ROM32K + CPU + Memory
│   └── ...              projects 1–3 chips these three are built from
├── assembler.py         two-pass Hack assembler (no third-party libraries)
├── symbols.txt          labels and variables of Box.asm with their addresses
├── make_box.py          writes Box.asm for any K and assembles it
├── Box.asm              the box program for K = 93
├── Box.hack             Box.asm assembled with assembler.py
├── tools/hack_emu.py    small Hack emulator used to check the box program
├── tests/run_tests.sh   one command that re-checks everything
├── tests/official/      the official .tst / .cmp files and Add/Max/Rect/Pong
└── screenshots/         screen dumps of the box (pressed / released / moved)
```

## Check everything in one command

```bash
sh tests/run_tests.sh /path/to/nand2tetris/tools
```

It prints one line per check and ends with `38 passed, 0 failed`:

1. the project 1–3 chip tests with our own HDL
2. `CPU.tst` with our CPU
3. `Memory-quick.tst` (a short version of the official `Memory.tst`) and the three Computer tests
4. our assembler against the official assembler on Add, Max, Rect and Pong — byte for byte
5. `Box.hack` in a small Hack emulator: key pressed → box, released → empty, pressed again → box

The full official `Memory.tst` is very slow in command-line mode with a student-built
RAM16K (about 20 minutes); add `--slow` to include it. Running it in the Hardware
Simulator GUI is the normal way to take that screenshot.

### Note on the three Computer tests

`ComputerAdd.tst`, `ComputerMax.tst` and `ComputerRect.tst` print the internal state of
`RAM16K` and `PC` (`RAM16K[0]`, `PC[]`). The standard simulator reports those values only
for its **built-in** `RAM16K` and `PC`, so for those three scripts the built-in versions of
those two chips are used. The `RAM16K.hdl` and `PC.hdl` written here pass `RAM16K.tst` and
`PC.tst` on their own. `ARegister`, `DRegister`, `ROM32K`, `Screen` and `Keyboard` are
course built-ins (as intended in project 5).

## The assembler

```bash
python3 assembler.py Add.asm Max.asm Rect.asm Pong.asm   # writes .hack files
python3 assembler.py Box.asm -s symbols.txt              # also saves the symbol table
python3 assembler.py --k 93 Box.asm                      # shows which extra feature K selects
```

Extra feature for K = 93 (`K mod 3 = 0`): every successful run can write `symbols.txt`
with the predefined symbols, every label with its ROM address and every new variable with
its RAM address. For Box.asm that is BOOT 0, MAIN 12, PAINT 22 … and the variables
startRow 16, width 17, height 18, fill 19, addr 20, rowsToSkip 21, rowsLeft 22, ptr 23,
wordsLeft 24. The other two features of the assignment are switched on as well — a clear
`Line N: ...` message for a bad instruction (no traceback) and a warning when the same
label is written twice.

## The box program

```bash
python3 make_box.py 93        # writes Box.asm for K = 93 and assembles it to Box.hack
python3 tools/hack_emu.py Box.hack --script press,0,press --cycles 300000 --png shot.png
```

Measured for K = 93: box at rows 93–112, columns 0–31 (32 pixels wide), 640 black pixels,
empty after the key is released, back when it is pressed again.

To move the box down during the viva, change the number on the line marked
`START ROW = K` in `Box.asm` (93 → 120), then run `python3 assembler.py Box.asm` and load
the new `Box.hack`.

## Screenshots to take in the official tools

The report has four marked places; take these in the nand2tetris tools:

1. `CPU.tst` in the Hardware Simulator
2. `ComputerRect.tst` in the Hardware Simulator
3. the `symbols.txt` that the assembler writes
4. the CPU Emulator running `Box.hack` with a key held — the box on screen
