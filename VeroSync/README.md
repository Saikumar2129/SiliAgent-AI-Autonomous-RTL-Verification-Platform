# VeroSync

**V1 — Autonomous Syntax Verification Agent**

VeroSync generates an 8-bit synchronous FIFO from a natural language spec using Claude, compiles it with Icarus Verilog, and autonomously fixes all syntax errors in a repair loop.

---

## What It Does

```
Spec → Claude generates FIFO RTL
     → iverilog compiles
     → Syntax errors? → Claude reads error log → fixes RTL → recompile
     → Clean compile → vvp simulates → dump.vcd produced
```

---

## Key Achievement

Proved that Claude can fix its own Verilog syntax errors when given the exact compiler error message. The critical insight: AI for reasoning, Python for rules. LLMs wrap Verilog in markdown fences (```verilog ... ```) — VeroSync strips them deterministically before compilation.

---

## Files

| File | Purpose |
|------|---------|
| `agent_v1.py` | Main agent — generates, compiles, repairs |
| `fifo.v` | Generated 8-bit synchronous FIFO RTL |
| `fifo_tb.v` | Testbench with $dumpfile directives |

---

## Run

```bash
source venv/bin/activate
python3 agent_v1.py
```

---

## Verified Output

```
0xAA and 0xBB written to FIFO
0xAA and 0xBB read back correctly
VCD waveforms confirmed
```

---

*Part of the [SiliAgent AI](../) platform*
