# SiliCount

**V3 — Counter Verification + Repair + Functional Coverage**

SiliCount proves that SiliAgent's architecture generalizes beyond memory modules. Claude autonomously generates both the RTL and testbench from a natural language spec. A human-written golden model verifies correctness. A coverage tracker proves completeness.

---

## What's New in V3

**Claude generates RTL + Testbench** — not just the RTL. The spec is passed to Claude which produces both `counter.v` and `counter_tb.v` autonomously.

**Functional Coverage Tracking** — Passing a test does not mean a design is correct. Coverage answers: *Did we test every possible state?*

---

## Pipeline

```
Spec (Natural Language)
     ↓ generate_counter.py — Claude generates RTL + Testbench
counter.v + counter_tb.v
     ↓ counter_agent.py
Compile → Simulate → Golden Model → Coverage
```

---

## Coverage Bins (11 total)

| Bin | Description |
|-----|-------------|
| `count_zero` | Counter reached 0 |
| `count_max` | Counter reached 15 (max) |
| `count_mid` | Counter reached 8 (midpoint) |
| `overflow` | Counter wrapped: 15 → 0 |
| `underflow` | Counter wrapped: 0 → 15 |
| `up_only` | up_en=1, down_en=0 |
| `down_only` | down_en=1, up_en=0 |
| `both_enabled` | Both high — count holds |
| `neither_enabled` | Both low — count holds |
| `reset_active` | Reset asserted |
| `reset_mid_count` | Reset while count > 0 |

---

## Files

| File | Purpose |
|------|---------|
| `generate_counter.py` | Generates counter.v + counter_tb.v from spec using Claude |
| `counter.v` | Claude-generated 4-bit up/down counter RTL |
| `counter_tb.v` | Claude-generated testbench |
| `golden_model_counter.py` | Human-written Python counter behavioral model |
| `coverage_tracker.py` | 11-bin functional coverage tracker |
| `counter_agent.py` | Full autonomous pipeline |

---

## Run

```bash
source venv/bin/activate

# Step 1: Generate RTL + Testbench from spec
python3 generate_counter.py

# Step 2: Full verification pipeline
python3 counter_agent.py
```

---

## Proven Results

**Clean run:**
```
✅ COUNTER VERIFIED CLEAN
   • Syntax:   Passed
   • Logic:    Passed — 44 cycles verified
   • Coverage: 100.0% (11/11 bins)
🎉 SiliCount Complete — 100% Silicon Truth Confirmed.
```

**Sabotage Test:** Changed `count + 1` to `count + 2`
```
❌ 21 mismatches detected
🧠 Claude repairs autonomously
✅ PASS — 44 cycles verified
```

---

*Part of the [SiliAgent AI](../) platform*
