# SiliAgent AI

**Autonomous RTL Verification Platform**

SiliAgent detects and repairs logic hallucinations in LLM-generated Verilog using VCD waveform analysis, Python golden reference models, and the Claude API.

> *"We don't trust the AI. We trust the Simulation."*

>Checkout at: https://saikumar2129.github.io/SiliAgent-AI-Autonomous-RTL-Verification-Platform/
---

## The Problem

When LLMs generate Verilog RTL, two types of failures occur:

- **Syntax errors** — caught by the compiler. Easy to fix.
- **Logic errors** — the code compiles and simulates, but produces wrong output. Invisible to the compiler. Dangerous.

SiliAgent catches both — and autonomously repairs them.

---

## Platform Architecture

```
Spec (Natural Language)
     ↓ generate_*.py — Claude generates RTL + Testbench
RTL Code (Verilog) + Testbench (Verilog)
     ↓ iverilog compile
Syntax Check → errors → Claude repairs → recompile
     ↓ vvp simulate
dump.vcd  ←  Silicon Truth
     ↓ VCD Parser
Timeline {timestamp: {signal: value}}
     ↓ Golden Reference Model (Python — human written)
Compare against behavioral truth
     ↓ mismatch detected
Claude repairs RTL → re-simulate → re-verify
     ↓ pass
Coverage Report
```

---

## Projects

| Project | Module | RTL Source | Verification Layer | Key Achievement |
|---------|--------|------------|-------------------|-----------------|
| [VeroSync](./VeroSync/) | 8-bit FIFO | Claude generated | Syntax repair loop | Compiler as guardrail |
| [SiliOracle](./SiliOracle/) | 8-bit FIFO | Claude generated | Logic verification + repair | Golden Reference Model |
| [SiliCount](./SiliCount/) | 4-bit Counter | Claude generated | Coverage tracking | 100% functional coverage |
| [SiliAXI](./SiliAXI/) | AXI4-Lite Slave | Claude generated | Protocol verification + repair | Handshake + data integrity |

---

## Results

| Metric | Result |
|--------|--------|
| Modules verified | 4 |
| RTL + Testbench generation | Fully autonomous (Claude API) |
| Functional coverage | 100% (11/11 bins) |
| AXI transactions verified | 10/10 |
| Logic hallucinations detected | Timestamp-precise |
| Autonomous repair | Single Claude API call |
| Human intervention in design | Zero — golden model only |

---

## Key Concepts

**Golden Reference Model** — A parallel Python simulation of expected behavior. Written by a human, never hallucinates. If the RTL disagrees with the Python model at any timestamp — the LLM hallucinated.

**VCD Oracle** — The VCD (Value Change Dump) is the timestamped record of every signal during simulation. It is silicon truth — what the hardware actually did.

**Timestamp-Precise Diagnostics** — Not "FIFO is broken" but "At t=145ns, expected 0xAA, got 0xFF." This precision enables Claude to repair bugs on the first attempt.

**Streaming Repair** — All Claude API calls use streaming so repair progress is visible in real time rather than blocking silently.

---

## Human vs AI Boundary

```
Claude generates:   RTL (Verilog) + Testbench (Verilog)
Human writes:       Golden Reference Model (Python)
Oracle verifies:    Claude's output against human truth
Claude repairs:     When Oracle detects violations
```

This separation is the architecture. The golden model cannot hallucinate. The AI output is always validated against it.

---

## Tech Stack

- **Python 3.14** — VCD parsing, golden models, coverage tracking, agents
- **Icarus Verilog** — RTL compilation and simulation
- **vcdvcd** — VCD file parsing library
- **Claude API** (claude-sonnet-4-5) — RTL generation, testbench generation, autonomous repair
- **python-dotenv** — API key management

---

## Setup

```bash
git clone https://github.com/yourusername/SiliAgent-AI
cd SiliAgent-AI

# Each project has its own venv
cd SiliCount
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Generate RTL + Testbench from spec
python3 generate_counter.py

# Run full verification pipeline
python3 counter_agent.py
```

---

## Design Decisions

**Why separate agents per module instead of one unified orchestrator?**

An early attempt at a unified orchestrator failed because Claude-generated testbenches had timing assumptions incompatible with the golden model. The cleaner architectural decision was separate, focused agents per module — each with controlled timing contracts.

**Why is the golden model human-written?**

The golden model is the source of truth. If the AI generates it, there is no independent oracle — you are asking the AI to verify itself. Auto-generating golden models from specs is the V2 research direction.

**Why streaming for Claude API calls?**

AXI4-Lite RTL repair can take 30-60 seconds. Streaming shows progress immediately (dots printing) rather than blocking silently, making the repair loop usable in practice.

---

## Roadmap

| Version | Target | Status |
|---------|--------|--------|
| V1 | Syntax verification (VeroSync) | ✅ Done |
| V2 | Logic verification + repair (SiliOracle) | ✅ Done |
| V3 | Coverage tracking (SiliCount) | ✅ Done |
| V4 | Protocol verification + repair (SiliAXI) | ✅ Done |
| V5 | Auto-generate golden model from spec | 🔜 Next |
| V6 | Multi-agent: Design-Agent + DV-Agent | 🔜 Planned |
| V7 | SVA assertion generation | 🔜 Planned |

---

## Inspired By

VLSID 2026 Tutorial on LLM-based RTL Generation — Dr. Soumya Joshi, BITS Hyderabad.
Research reference: arXiv:2410.20285

Conceptually aligned with Cadence Verisium WaveMiner and ChipStack AI Super Agent — built independently as a student project with zero EDA licensing cost.

---

*Built by Saikumar Swarnapudi | B.E. CSE Final Year | March 2026*
