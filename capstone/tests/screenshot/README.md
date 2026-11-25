# Where to take the four screenshots

Each folder here is ready to open in the nand2tetris tools — the chips, the official test
file and the compare file are already side by side, so nothing has to be copied around.

The tools are the ones from the course (`nand2tetris/tools`): `HardwareSimulator`
(for the HDL tests) and `CPUEmulator` (for the box program).

## 1. CPU.tst — `01-cpu/`

1. Open **Hardware Simulator**.
2. **File → Load Test Script** (the page icon) → choose `tests/screenshot/01-cpu/CPU.tst`.
   The simulator loads `CPU.hdl` by itself because the script says `load CPU.hdl,`.
3. Click **Run** (the double arrow, or Ctrl+F6 / the `>>` button).
4. The bottom line turns green: *End of script - Comparison ended successfully*.
   Screenshot the whole window with that line visible.

## 2. ComputerRect.tst — `02-computerrect/`

Same idea: **File → Load Test Script** → `02-computerrect/ComputerRect.tst` → **Run** →
green *Comparison ended successfully* → screenshot.

This folder has no `PC.hdl` and no `RAM16K.hdl` on purpose: this test prints `RAM16K[0]`
and `PC[]`, and the simulator can only show those values for its own built-in versions of
those two chips. Your own `RAM16K` and `PC` are proven by `RAM16K.tst` and `PC.tst`, which
come free with the `run_tests.sh` run.

## 3. symbols.txt — `03-symbols/`

Open a terminal in the capstone folder and run:

```bash
python3 assembler.py Box.asm -s symbols.txt
```

It prints `symbols -> symbols.txt`. Screenshot the terminal with the command and that
line, plus the top of the file (`type symbols.txt` on Windows, `cat symbols.txt` on
Mac/Linux). `03-symbols/symbols.txt` is already the generated file.

## 4. The box in the CPU Emulator — `04-box/`

1. Open **CPU Emulator**.
2. Click the **folder icon** above the ROM list → choose `tests/screenshot/04-box/Box.hack`.
   The ROM now shows `@93, D=A, @16, M=D, @2, …`.
3. Drag the **Animate** slider all the way to **Fast**.
4. Press **F5** (Run), then **hold down any letter key** and wait a moment — the black box
   appears at row 93, 32 pixels wide, at the left edge.
5. Screenshot the window while the key is still held. Release the key and the box
   disappears (nice to have as a second picture).

If nothing appears after a few seconds, press F5 again — the emulator restarts the run from
the current ROM and picks the key up on the next pass.
