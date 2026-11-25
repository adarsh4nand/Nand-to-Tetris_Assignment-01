# Capstone — Make the Computer Draw a Box

Nand to Tetris – I (ETCNTC301) · School of Engineering & Technology
Adarsh Anand — **K = 93** (last two digits of roll number 2501730393)

| What K decides | Rule | Value |
|---|---|---|
| Box start row | row = K | 41 |
| Box height | 20 rows | 41 – 60 |
| Box width | 16 × ((K mod 4) + 1) pixels | 41 mod 4 = 1 → 32 px = 2 words |
| Extra assembler feature | K mod 3 | 41 mod 3 = 2 → duplicate-label warning |

## What is in this folder

```
capstone/
├── hdl/                 the Hack computer, built from Nand up (31 chips)
│   ├── CPU.hdl          A/D registers, ALU control, jump logic, PC
│   ├── Memory.hdl       RAM16K / Screen / Keyboard address decoding
│   ├── Computer.hdl     ROM32K + CPU + Memory
│   └── ...              projects 1–3 chips these three are built from
├── assembler.py         two-pass Hack assembler (no third-party libraries)
├── make_box.py          writes Box.asm for any K and assembles it
├── Box.asm              the box program for K = 41
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
python3 assembler.py Rect.asm -s symbols.txt             # also saves the symbol table
python3 assembler.py --k 41 Box.asm                      # shows which extra feature K selects
```

Extra feature for K = 41 (`K mod 3 = 2`): writing the same label twice prints a warning
with the line number and both addresses instead of silently overwriting it. The other two
features of the assignment are switched on as well — a clear `Line N: ...` message for a
bad instruction (no traceback), and `-s symbols.txt` with every label and variable.

## The box program

```bash
python3 make_box.py 41        # writes Box.asm for K = 41 and assembles it to Box.hack
python3 tools/hack_emu.py Box.hack --script press,0,press --cycles 300000 --png shot.png
```

Measured for K = 41: box at rows 41–60, columns 0–31 (32 pixels wide), 640 black pixels,
empty after the key is released, back when it is pressed again.


