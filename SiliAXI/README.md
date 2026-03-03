# SiliAXI

**V4 — AXI4-Lite Protocol Verification + Autonomous Repair**

SiliAXI verifies AXI4-Lite bus protocol correctness. Claude autonomously generates both the RTL slave and the testbench from a natural language spec. A human-written golden memory model checks handshake integrity, write-read data consistency, and response codes.

AXI4-Lite is used in virtually every ARM-based SoC in production — from Raspberry Pi to Qualcomm Snapdragon.

---

## Pipeline

```
Spec (Natural Language)
     ↓ generate_axi.py — Claude generates RTL + Testbench
axi4_lite_slave.v + axi4_lite_tb.v
     ↓ axi_agent.py
Compile → Simulate (with timeout) → Protocol Check → Repair if needed
```

---

## AXI4-Lite Protocol Rules Verified

| Rule | Channel | Check |
|------|---------|-------|
| Handshake integrity | AW, W, AR | VALID must not deassert before READY |
| Write correctness | W | Data written matches wdata |
| Read correctness | R | rdata matches previously written value |
| Write response | B | BRESP must be 2'b00 (OKAY) |
| Read response | R | RRESP must be 2'b00 (OKAY) |

---

## Files

| File | Purpose |
|------|---------|
| `generate_axi.py` | Generates RTL + Testbench from spec using Claude (streaming) |
| `axi4_lite_slave.v` | Claude-generated AXI4-Lite slave with 256×32 register file |
| `axi4_lite_tb.v` | Claude-generated testbench with timeout-safe handshake tasks |
| `golden_model_axi.py` | Human-written protocol checker + golden memory model |
| `axi_agent.py` | Full autonomous pipeline with timeout handling + streaming repair |

---

## Run

```bash
source venv/bin/activate

# Step 1: Generate RTL + Testbench from spec
python3 generate_axi.py

# Step 2: Full autonomous agent
python3 axi_agent.py
```

---

## Proven Results

**Clean run:**
```
✅ AXI4-LITE PROTOCOL VERIFIED CLEAN
   • Syntax:    Passed
   • Handshake: Passed (VALID/READY integrity)
   • Data:      Passed (Write→Read correctness)
   • Response:  Passed (BRESP/RRESP = OKAY)
🎉 AXI4-Lite Silicon Truth Confirmed — 10/10 transactions verified.
```

**Sabotage Test:** Changed `rdata <= mem[araddr]` to `rdata <= mem[araddr] ^ 32'hFFFFFFFF`
```
❌ t=106: expected 0xDEADBEEF, got 0x21524110
❌ t=326: expected 0xCAFEBABE, got 0x35014541
❌ t=366: expected 0x12345678, got 0xEDCBA987
❌ t=406: expected 0xAABBCCDD, got 0x55443322
❌ t=506: expected 0x11223344, got 0xEEDDCCBB
🔮 FAIL — 5 protocol violations in 10 transactions

🧠 Streaming logic fix...
✅ PASS — 10/10 transactions verified. No protocol violations.
```

---

## Engineering Notes

**Timeout handling:** Claude-generated testbenches can produce AXI handshake deadlocks if timing assumptions don't match the RTL. `axi_agent.py` uses a 30-second simulation timeout — if the simulation hangs, Claude automatically receives a precise deadlock diagnosis and repairs the RTL.

**Oracle timing:** AXI signals settle 1ns after posedge with `#1` delays. The golden model checks all `clk=1` timestamps rather than only rising edges to correctly capture handshake completions.

**Streaming:** All Claude repair calls stream output in real time — no silent 60-second waits.

---

## Why AXI4-Lite Matters

Every SoC uses AXI. ARM Cortex-M, RISC-V cores, custom accelerators — all communicate over AXI buses. Protocol violations in silicon cause system hangs, data corruption, and security vulnerabilities. Catching them in simulation before tape-out saves millions.

---

*Part of the [SiliAgent AI](../) platform*
