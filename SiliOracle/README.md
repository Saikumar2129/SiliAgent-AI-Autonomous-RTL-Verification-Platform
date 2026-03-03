# SiliOracle

**V2 — Logic Verification + Autonomous Repair Agent**

SiliOracle catches logic hallucinations in LLM-generated Verilog that pass compilation but produce wrong output. It uses a Python golden reference model as the source of truth and autonomously repairs detected bugs using Claude.

---

## The Core Insight

A FIFO that compiles is not a FIFO that works.

The VCD (Value Change Dump) from simulation is silicon truth — a timestamped record of every signal transition. SiliOracle parses this file and compares it against a Python `deque`-based behavioral model that cannot hallucinate.

---

## Architecture

```
dump.vcd (Silicon Truth)
     ↓ vcd_parser.py
Timeline {timestamp: {signal: value}}
     ↓ golden_model.py
Python deque = ground truth FIFO
Compare dout against expected at every read
     ↓ mismatch found
logic_fixer.py → Claude repairs RTL (streaming)
     ↓ recompile + resimulate
Re-run golden model → PASS
```

---

## Files

| File | Purpose |
|------|---------|
| `vcd_parser.py` | Parses VCD into timeline, fills gaps, converts binary strings |
| `golden_model.py` | Python FIFO behavioral model, compares against VCD |
| `logic_fixer.py` | Sends mismatches to Claude, saves repaired RTL, re-verifies |

---

## Proven Results

**Sabotage Test:** Changed `dout <= memory[rd_ptr]` to `dout <= 8'hFF`

```
❌ t=145: Expected 0xAA, got 0xFF
❌ t=155: Expected 0xBB, got 0xFF
... 7 hallucinations detected
```

**Autonomous Repair:**
```
🧠 Streaming repair...
✅ Claude returned repaired RTL
✅ PASS — 8 reads verified. No hallucinations detected.
```

---

## Why Timestamp-Precise Diagnostics Matter

Vague: *"The FIFO is broken"* — Claude cannot reliably fix this.

Precise: *"At t=145, expected 0xAA, got 0xFF. rd_en=1, wr_ptr=2, rd_ptr=0"* — Claude fixes this on the first attempt.

---

## Run

```bash
source venv/bin/activate
python3 golden_model.py    # verify only
python3 logic_fixer.py     # detect + repair
```

---

*Part of the [SiliAgent AI](../) platform*
