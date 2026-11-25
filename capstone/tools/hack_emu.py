#!/usr/bin/env python3
"""
hack_emu.py -- a small Hack computer emulator used to CHECK the capstone work.

It runs a .hack program the way the nand2tetris CPU Emulator does (same
instruction set, same memory map) but from the command line, so the box
program can be tested automatically: the script presses and releases a key,
then reports the bounding box of the black pixels it found on the screen.

Usage:
    python3 hack_emu.py Box.hack --key 65 --cycles 300000
    python3 hack_emu.py Box.hack --script press,0 --png shot.png
"""

import argparse

SCREEN_BASE = 16384
SCREEN_WORDS = 8192          # 256 rows * 32 words
KBD = 24576
RAM_SIZE = 32768


def load(path):
    """Load a .hack file into a 32K ROM image (unused words stay 0)."""
    with open(path) as handle:
        words = [int(line.strip(), 2) for line in handle if line.strip()]
    if len(words) > 32768:
        raise ValueError("%s is larger than the Hack ROM" % path)
    return words + [0] * (32768 - len(words))


class Hack:
    def __init__(self, rom):
        self.rom = rom
        self.ram = [0] * RAM_SIZE
        self.a = 0
        self.d = 0
        self.pc = 0
        self.reset()

    def reset(self):
        self.a = 0
        self.d = 0
        self.pc = 0

    # -- one instruction ---------------------------------------------------
    def step(self):
        instruction = self.rom[self.pc]
        if instruction & 0x8000 == 0:                 # @value  (A-instruction)
            self.a = instruction
            self.pc = (self.pc + 1) & 0x7FFF
            return

        bits = format(instruction, "016b")
        a_bit = bits[3]
        comp = bits[4:10]
        dest = bits[10:13]
        jump = bits[13:16]

        x = self.d
        y = self.ram[self.a & 0x7FFF] if a_bit == "1" else (self.a & 0xFFFF)

        zx, nx, zy, ny, f, no = (int(b) for b in comp)
        if zx:
            x = 0
        if nx:
            x = ~x & 0xFFFF
        if zy:
            y = 0
        if ny:
            y = ~y & 0xFFFF
        out = (x + y) & 0xFFFF if f else (x & y)
        if no:
            out = ~out & 0xFFFF

        if dest[0] == "1":                 # d1 = A
            self.a = out
        if dest[1] == "1":                 # d2 = D
            self.d = out
        if dest[2] == "1":                 # d3 = M
            address = self.a & 0x7FFF
            if address < KBD:
                self.ram[address] = out

        do_jump = False
        if jump != "000":
            negative = out & 0x8000 != 0
            zero = out == 0
            do_jump = (
                (jump == "001" and not negative and not zero) or   # JGT
                (jump == "010" and zero) or                        # JEQ
                (jump == "011" and (zero or negative)) or          # JGE
                (jump == "100" and negative) or                    # JLT
                (jump == "101" and not zero) or                    # JNE
                (jump == "110" and (negative or zero)) or          # JLE
                (jump == "111")                                    # JMP
            )
        self.pc = (self.a if do_jump else self.pc + 1) & 0x7FFF

    # -- screen helpers ----------------------------------------------------
    def pixels(self):
        rows = []
        for row in range(256):
            line = []
            for word in range(32):
                value = self.ram[SCREEN_BASE + row * 32 + word]
                for bit in range(16):
                    line.append((value >> (15 - bit)) & 1)
            rows.append(line)
        return rows

    def black_box(self):
        """Bounding box of the black pixels: (top, bottom, left, right) or None."""
        rows = self.pixels()
        top = bottom = left = right = None
        for r, line in enumerate(rows):
            if any(line):
                top = r if top is None else top
                bottom = r
                first = line.index(1)
                last = len(line) - 1 - line[::-1].index(1)
                left = first if left is None else min(left, first)
                right = last if right is None else max(right, last)
        if top is None:
            return None
        return top, bottom, left, right

    def black_pixels(self):
        return sum(sum(line) for line in self.pixels())


def render(emulator, path, scale=2):
    from PIL import Image

    image = Image.new("L", (512, 256), 255)
    pixels = image.load()
    rows = emulator.pixels()
    for r, line in enumerate(rows):
        for c, value in enumerate(line):
            if value:
                pixels[c, r] = 0
    image = image.resize((512 * scale, 256 * scale), Image.NEAREST)
    image.save(path)


def run(emulator, cycles, key):
    emulator.ram[KBD] = key
    for _ in range(cycles):
        emulator.step()


def main():
    parser = argparse.ArgumentParser(description="Run a .hack program and report the screen.")
    parser.add_argument("program")
    parser.add_argument("--cycles", type=int, default=200000)
    parser.add_argument("--key", type=int, default=0, help="keyboard code (0 = no key)")
    parser.add_argument("--png", help="save the 512x256 screen to this PNG")
    parser.add_argument("--script", help="comma separated keys, e.g. press,0,press")
    args = parser.parse_args()

    emulator = Hack(load(args.program))
    emulator.reset()

    if args.script:
        for token in args.script.split(","):
            key = 65 if token.strip() == "press" else int(token)
            run(emulator, args.cycles, key)
            box = emulator.black_box()
            print("key=%-5d box=%s black_pixels=%d"
                  % (key, box, emulator.black_pixels()))
            if args.png:
                name = args.png.replace(".png", "_key%d.png" % key)
                render(emulator, name)
                print("  screenshot ->", name)
        return

    run(emulator, args.cycles, args.key)
    box = emulator.black_box()
    print("key=%d box=%s black_pixels=%d" % (args.key, box, emulator.black_pixels()))
    if args.png:
        render(emulator, args.png)
        print("screenshot ->", args.png)


if __name__ == "__main__":
    main()
