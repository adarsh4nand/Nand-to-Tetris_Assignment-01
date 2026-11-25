#!/bin/sh
# ==========================================================================
#  run_tests.sh -- one command that re-checks the whole capstone
#
#  Usage:
#      sh tests/run_tests.sh /path/to/nand2tetris/tools
#      NAND2TETRIS=/path/to/nand2tetris sh tests/run_tests.sh
#
#  It runs, in order:
#    1. every chip test of projects 1-3 with OUR chips
#    2. CPU.tst with OUR CPU
#    3. Memory (quick version of the official Memory.tst) and the three Computer tests
#    4. our assembler against the official assembler on Add/Max/Rect/Pong
#    5. the box program in the small Hack emulator (press / release / press)
#
#  Note on step 3: the official Computer tests read the internal state of
#  RAM16K and PC (their output lines say RAM16K[0] and PC[]). The standard
#  simulator only reports that for its BUILT-IN RAM16K and PC, so for those
#  three tests only, those two chips are taken from the built-in library.
#  Our own RAM16K and PC are proven by RAM16K.tst and PC.tst in step 1.
#
#  The official Memory.tst is very slow in command-line mode with a student
#  RAM16K (around 20 minutes). Add --slow to run it as well.
# ==========================================================================

set -u

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
HDL="$ROOT/hdl"
OFFICIAL="$HERE/official"

TOOLS=${1:-${NAND2TETRIS:-}/tools}
if [ ! -f "$TOOLS/HardwareSimulator.sh" ]; then
    echo "Cannot find the nand2tetris tools."
    echo "Usage: sh tests/run_tests.sh /path/to/nand2tetris/tools"
    exit 1
fi
TOOLS=$(cd "$TOOLS" && pwd)
JAVA_CP=":bin/classes:BuiltIn:bin/lib/Hack.jar:bin/lib/HackGUI.jar:bin/lib/Simulators.jar:bin/lib/SimulatorsGUI.jar:bin/lib/Compilers.jar"
JAVA_CP_ABS="$TOOLS/bin/classes:$TOOLS/bin/lib/Hack.jar:$TOOLS/bin/lib/HackGUI.jar:$TOOLS/bin/lib/Simulators.jar:$TOOLS/bin/lib/SimulatorsGUI.jar:$TOOLS/bin/lib/Compilers.jar"

PASS=0
FAIL=0
FAILED=""

ok()   { PASS=$((PASS + 1)); printf "  PASS  %s\n" "$1"; }
bad()  { FAIL=$((FAIL + 1)); FAILED="$FAILED $1"; printf "  FAIL  %s\n" "$1"; }

run_test() {                 # run_test <dir> <name>
    out=$(cd "$TOOLS" && java -Xmx4g -classpath "$JAVA_CP" HardwareSimulatorMain "$1/$2.tst" 2>&1)
    case "$out" in
        *"Comparison ended successfully"*) ok "$2" ;;
        *) bad "$2"; printf "        %s\n" "$(printf '%s' "$out" | tail -2 | tr '\n' ' ')" ;;
    esac
}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/capstone.XXXXXX")

echo
echo "=== 1. chips of projects 1-3 (our HDL) ==="
FULL="$WORK/full"
mkdir -p "$FULL"
cp "$HDL"/*.hdl "$FULL"/
cp "$OFFICIAL"/*.tst "$OFFICIAL"/*.cmp "$OFFICIAL"/*.hack "$FULL"/
for chip in Not And Or Xor Mux DMux Not16 And16 Or16 Mux16 Or8Way Mux4Way16 Mux8Way16 \
            DMux4Way DMux8Way HalfAdder FullAdder Add16 Inc16 ALU Bit Register \
            RAM8 RAM64 RAM512 RAM4K RAM16K PC; do
    run_test "$FULL" "$chip"
done

echo
echo "=== 2. the CPU (our CPU.hdl) ==="
run_test "$FULL" CPU

echo
echo "=== 3. Memory and the Computer ==="
BUILTIN="$WORK/builtin"
mkdir -p "$BUILTIN"
cp "$HDL"/*.hdl "$BUILTIN"/
cp "$OFFICIAL"/*.tst "$OFFICIAL"/*.cmp "$OFFICIAL"/*.hack "$BUILTIN"/
rm -f "$BUILTIN/PC.hdl" "$BUILTIN/RAM16K.hdl"     # see the note at the top
run_test "$FULL" Memory-quick                # RAM / screen / keyboard addressing, quick version
run_test "$BUILTIN" ComputerAdd
run_test "$BUILTIN" ComputerMax
run_test "$BUILTIN" ComputerRect

if [ "${1:-}" = "--slow" ] || [ "${SLOW:-}" = "1" ]; then
    echo "  (running the full official Memory.tst -- this one is slow)"
    run_test "$FULL" Memory
fi

echo
echo "=== 4. our assembler against the official assembler ==="
ASM="$WORK/asm"
mkdir -p "$ASM"
for program in Add Max Rect Pong; do
    cp "$OFFICIAL/$program.asm" "$ASM/"
    ( cd "$ASM" && python3 "$ROOT/assembler.py" "$program.asm" -o "$program.mine.hack" >/dev/null 2>&1 )
    ( cd "$ASM" && java -classpath "$JAVA_CP_ABS" HackAssemblerMain "$program.asm" >/dev/null 2>&1 )
    mv "$ASM/$program.hack" "$ASM/$program.official.hack"
    if cmp -s "$ASM/$program.mine.hack" "$ASM/$program.official.hack"; then
        ok "assembler $program ($(wc -l < "$ASM/$program.mine.hack" | tr -d ' ') instructions, identical)"
    else
        bad "assembler $program"
    fi
done

echo
echo "=== 5. the box program (emulator check) ==="
K=$(sed -n 's/^ *@\([0-9][0-9]*\).*START ROW = K.*/\1/p' "$ROOT/Box.asm" | head -1)
WORDS=$(sed -n 's/^ *@\([0-9][0-9]*\).*WIDTH IN WORDS.*/\1/p' "$ROOT/Box.asm" | head -1)
EXPECTED="box=($K,$((K + 19)),0,$((WORDS * 16 - 1)))"
echo "  Box.asm says: K=$K, width=$WORDS word(s), height=20"
python3 "$ROOT/tools/hack_emu.py" "$ROOT/Box.hack" --script "press,0,press" --cycles 300000 | sed 's/^/  /'
SEEN=$(python3 "$ROOT/tools/hack_emu.py" "$ROOT/Box.hack" --script "press,0,press" --cycles 300000 \
    | grep -o 'box=([^)]*)' | sort -u | tr '\n' ' ')
if [ "$(printf '%s' "$SEEN" | tr -d ' ')" = "$(printf '%s' "$EXPECTED" | tr -d ' ')" ]; then
    ok "box: rows $K-$((K + 19)), $((WORDS * 16)) pixels wide, appears and disappears"
else
    bad "box dimensions (got $SEEN expected $EXPECTED)"
fi

echo
echo "-------------------------------------------------------------"
echo "  $PASS passed, $FAIL failed${FAILED:+ -- failed:$FAILED}"
echo "-------------------------------------------------------------"
[ "$FAIL" -eq 0 ]
