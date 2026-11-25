#!/usr/bin/env python3
"""
assembler.py -- a two-pass Hack assembler (Nand to Tetris capstone, Part B).

Reads a Hack assembly program (.asm) and writes 16-bit machine code (.hack),
exactly like the official nand2tetris assembler.

Usage:
    python3 assembler.py Add.asm                 # writes Add.hack
    python3 assembler.py Add.asm Max.asm Rect.asm Pong.asm
    python3 assembler.py Box.asm -o out/Box.hack --symbols symbols.txt
    python3 assembler.py --k 41 Box.asm          # show which extra feature K selects

Extra feature (K mod 3) -- all three are implemented, the one selected by your
own K is reported when you pass --k:
    K mod 3 = 0 : every label and variable is saved with its address in symbols.txt
    K mod 3 = 1 : a bad line prints "Line N: ..." instead of crashing
    K mod 3 = 2 : writing the same label twice prints a warning
"""

import argparse
import os
import re
import sys

# --------------------------------------------------------------------------
# Hack instruction tables
# --------------------------------------------------------------------------

PREDEFINED = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5, "R6": 6, "R7": 7,
    "R8": 8, "R9": 9, "R10": 10, "R11": 11, "R12": 12, "R13": 13, "R14": 14, "R15": 15,
    "SCREEN": 16384,
    "KBD": 24576,
}

FIRST_VARIABLE_ADDRESS = 16

# comp field, with a=0 (A) and a=1 (M)
COMP_A0 = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "!D": "0001101", "!A": "0110001",
    "-D": "0001111", "-A": "0110011",
    "D+1": "0011111", "A+1": "0110111", "D-1": "0001110", "A-1": "0110010",
    "D+A": "0000010", "D-A": "0010011", "A-D": "0000111",
    "D&A": "0000000", "D|A": "0010101",
}
COMP_A1_ONLY = {
    "M": "1110000", "!M": "1110001", "-M": "1110011",
    "M+1": "1110111", "M-1": "1110010",
    "D+M": "1000010", "D-M": "1010011", "M-D": "1000111",
    "D&M": "1000000", "D|M": "1010101",
}

DEST = {
    "": "000", "M": "001", "D": "010", "DM": "011",
    "A": "100", "AM": "101", "AD": "110", "AMD": "111",
}

JUMP = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}

LABEL_RE = re.compile(r"^\(([^()]*)\)$")
SYMBOL_RE = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")


class AsmError(Exception):
    """A problem in the user's source file (reported with a line number)."""


# --------------------------------------------------------------------------
# Pass 0: clean the source
# --------------------------------------------------------------------------

def strip_comments(text):
    """Remove // comments and /* ... */ blocks. Returns a list of source lines.

    Kept 1:1 with the original file so error messages can name the real line.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    lines = []
    for raw in text.splitlines():
        line = raw.split("//", 1)[0]
        lines.append(line.strip())
    return lines


def clean_code_lines(lines):
    """Pair every real instruction line with its original line number."""
    result = []
    for number, line in enumerate(lines, start=1):
        if not line:
            continue
        result.append((number, line.replace(" ", "").replace("\t", "")))
    return result


# --------------------------------------------------------------------------
# Pass 1: labels
# --------------------------------------------------------------------------

def first_pass(code, symbols, warnings):
    """Record the ROM address of every (LABEL). Returns the code without labels."""
    instructions = []
    rom_address = 0
    for number, line in code:
        match = LABEL_RE.match(line)
        if match:
            name = match.group(1)
            if not SYMBOL_RE.match(name):
                raise AsmError("Line %d: invalid label name (%s)" % (number, name))
            if name in symbols:
                # Extra feature for K mod 3 == 2
                warnings.append(
                    "Line %d: warning: label (%s) is already defined at address %d; "
                    "the new definition at address %d is ignored"
                    % (number, name, symbols[name], rom_address)
                )
            else:
                symbols[name] = rom_address
            # a label does not take a ROM address of its own
            continue
        instructions.append((number, line))
        rom_address += 1
    return instructions


# --------------------------------------------------------------------------
# Pass 2: binary conversion
# --------------------------------------------------------------------------

def parse_a_instruction(number, body, symbols, variables, warnings):
    value = body[1:]
    if value == "":
        raise AsmError("Line %d: invalid instruction (@ with no value)" % number)
    if value.isdigit():
        address = int(value)
        if address > 32767:
            raise AsmError(
                "Line %d: constant %d is out of range (0..32767)" % (number, address)
            )
        return format(address, "016b")

    if not SYMBOL_RE.match(value):
        raise AsmError("Line %d: invalid symbol (%s)" % (number, value))

    if value not in symbols:
        # a new variable: RAM[16], RAM[17], ...
        symbols[value] = variables["next"]
        variables["list"].append((value, variables["next"]))
        variables["next"] += 1
        if variables["next"] > 16383:
            raise AsmError("Line %d: out of RAM for new variables" % number)
    return format(symbols[value], "016b")


def parse_c_instruction(number, body):
    dest_text, comp_text, jump_text = "", body, ""

    if "=" in body:
        dest_text, comp_text = body.split("=", 1)
        if "=" in comp_text:
            raise AsmError("Line %d: invalid instruction (%s)" % (number, body))

    if ";" in comp_text:
        comp_text, jump_text = comp_text.split(";", 1)
        if ";" in jump_text or "=" in jump_text:
            raise AsmError("Line %d: invalid instruction (%s)" % (number, body))

    if not comp_text:
        raise AsmError("Line %d: invalid instruction (%s)" % (number, body))

    dest_key = "".join(sorted(dest_text))
    if dest_key not in DEST:
        raise AsmError("Line %d: invalid destination (%s)" % (number, dest_text))

    if comp_text in COMP_A0:
        comp_bits = COMP_A0[comp_text]
    elif comp_text in COMP_A1_ONLY:
        comp_bits = COMP_A1_ONLY[comp_text]
    else:
        raise AsmError("Line %d: invalid computation (%s)" % (number, comp_text))

    jump = jump_text.upper()
    if jump not in JUMP:
        raise AsmError("Line %d: invalid jump (%s)" % (number, jump_text))

    return "111" + comp_bits + DEST[dest_key] + JUMP[jump]


def second_pass(instructions, symbols, warnings):
    """Translate every instruction; collect (do not crash on) bad lines."""
    variables = {"next": FIRST_VARIABLE_ADDRESS, "list": []}
    words = []
    errors = []
    for number, line in instructions:
        try:
            if line.startswith("@"):
                words.append(parse_a_instruction(number, line, symbols, variables, warnings))
            else:
                words.append(parse_c_instruction(number, line))
        except AsmError as error:
            errors.append(str(error))
    return words, variables["list"], errors


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def assemble_file(path, output_path=None, symbols_path=None, k=None):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        source = handle.read()

    code = clean_code_lines(strip_comments(source))

    symbols = dict(PREDEFINED)
    warnings = []

    print("Assembling %s" % os.path.basename(path))
    instructions = first_pass(code, symbols, warnings)
    words, variables, errors = second_pass(instructions, symbols, warnings)

    for message in warnings:
        print("  " + message)

    if errors:
        # Extra feature for K mod 3 == 1: every bad line is named, nothing crashes
        for message in errors:
            print("  " + message)
        print("  %d bad line(s) -- no .hack file written" % len(errors))
        return None

    if output_path is None:
        output_path = os.path.splitext(path)[0] + ".hack"
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(words) + "\n")

    print("  %d instructions -> %s" % (len(words), output_path))

    # Extra feature for K mod 3 == 0 (also useful for the other two)
    if symbols_path:
        variable_names = {name for name, _ in variables}
        labels = [(n, a) for n, a in symbols.items()
                  if n not in PREDEFINED and n not in variable_names]
        labels.sort(key=lambda item: item[1])
        with open(symbols_path, "w", encoding="utf-8") as handle:
            handle.write("# Hack symbol table generated by assembler.py\n")
            handle.write("\n# predefined symbols\n")
            for name in sorted(PREDEFINED, key=lambda n: PREDEFINED[n]):
                handle.write("%-24s %d\n" % (name, PREDEFINED[name]))
            handle.write("\n# labels (%d)\n" % len(labels))
            for name, address in labels:
                handle.write("%-24s %d\n" % (name, address))
            handle.write("\n# new variables (%d, from RAM[%d])\n"
                         % (len(variables), FIRST_VARIABLE_ADDRESS))
            for name, address in variables:
                handle.write("%-24s %d\n" % (name, address))
        print("  symbols -> %s" % symbols_path)

    return len(words)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Two-pass Hack assembler (.asm -> .hack).",
    )
    parser.add_argument("files", nargs="+", help="assembly files to translate")
    parser.add_argument("-o", "--output", help="output file (only with a single input)")
    parser.add_argument("-s", "--symbols", help="write the symbol table to this file")
    parser.add_argument("--k", type=int, help="your personal number K (selects the extra feature)")
    args = parser.parse_args(argv)

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with one input file")

    if args.k is not None:
        features = {
            0: "save every label and variable in symbols.txt",
            1: "print a clear error message with the line number",
            2: "warn when the same label is written twice",
        }
        print("K = %d  ->  K mod 3 = %d  ->  extra feature: %s"
              % (args.k, args.k % 3, features[args.k % 3]))

    exit_code = 0
    for path in args.files:
        try:
            written = assemble_file(
                path,
                output_path=args.output,
                symbols_path=args.symbols,
                k=args.k,
            )
            if written is None:
                exit_code = 1
        except AsmError as error:
            # Extra feature for K mod 3 == 1: a clear message, no crash, no traceback
            print("  %s" % error)
            print("  assembly stopped; no .hack file written")
            exit_code = 1
        except FileNotFoundError:
            print("  cannot open %s" % path)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
