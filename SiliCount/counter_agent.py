import os
import subprocess
import anthropic
from dotenv import load_dotenv
from golden_model_counter import verify_counter_logic
from coverage_tracker import CoverageTracker

load_dotenv()

MAX_SYNTAX_RETRIES = 5
MAX_LOGIC_RETRIES  = 3

RTL_FILE = "counter.v"
TB_FILE  = "counter_tb.v"
SIM_OUT  = "sim.out"
VCD_FILE = "dump.vcd"

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def banner(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def compile_design():
    result = subprocess.run(
        ["iverilog", "-o", SIM_OUT, RTL_FILE, TB_FILE],
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stderr


def simulate():
    result = subprocess.run(
        ["vvp", SIM_OUT],
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stdout


def fix_syntax(errors):
    with open(RTL_FILE) as f: rtl = f.read()
    with open(TB_FILE)  as f: tb  = f.read()

    prompt = f"""You are a Verilog expert. Fix the compiler errors below.

=== COMPILER ERRORS ===
{errors}

=== RTL FILE (counter.v) ===
{rtl}

=== TESTBENCH FILE (counter_tb.v) ===
{tb}

Rules:
1. Fix ALL errors
2. Do not change module names or port interfaces
3. Use only Icarus Verilog compatible syntax (reg/wire, not logic)
4. No markdown

Output in this exact format:
===COUNTER.V===
<fixed rtl code here>
===COUNTER_TB.V===
<fixed testbench code here>"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text

    try:
        rtl_fixed = text.split("===COUNTER.V===")[1].split("===COUNTER_TB.V===")[0].strip()
        tb_fixed  = text.split("===COUNTER_TB.V===")[1].strip()
    except IndexError:
        rtl_fixed = rtl
        tb_fixed  = tb

    # Clean markdown
    for code, path in [(rtl_fixed, RTL_FILE), (tb_fixed, TB_FILE)]:
        lines = code.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
        with open(path, "w") as f: f.write(cleaned)


def fix_logic(mismatches):
    with open(RTL_FILE) as f:
        rtl_code = f.read()

    error_lines = []
    for m in mismatches[:10]:
        error_lines.append(
            f"  - t={m['time']}: Expected count={m['expected']}, got {m['got']}. {m['error']}"
        )

    prompt = f"""You are a senior Verilog verification engineer.

The following 4-bit up/down counter RTL has a LOGIC BUG.
It compiles and simulates, but the SiliCount Golden Reference Model detected errors.

=== MISMATCH REPORT ===
{chr(10).join(error_lines)}

=== COUNTER SPEC ===
- up_en=1, down_en=0: increment count by 1
- down_en=1, up_en=0: decrement count by 1
- both or neither: count stays same
- wraps at 15→0 (up) and 0→15 (down)
- synchronous reset to 0

=== BUGGY RTL ===
{rtl_code}

Fix ONLY the logic bug. Do not change module name or ports.
Output ONLY corrected Verilog. No markdown. No explanation."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    fixed = response.content[0].text.strip()
    if fixed.startswith("```"):
        lines = fixed.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        fixed = "\n".join(lines)

    with open(RTL_FILE, "w") as f:
        f.write(fixed)

    print("✅ Claude returned repaired RTL.")


def run():
    banner("🚀 SiliCount Agent Starting")

    # ── Step 1: Compile ──────────────────────────────────────
    banner("🔷 Step 1: Compile → Syntax Fix Loop")

    compiled = False
    for attempt in range(1, MAX_SYNTAX_RETRIES + 1):
        print(f"\n  Attempt {attempt}/{MAX_SYNTAX_RETRIES}: Compiling...")
        success, errors = compile_design()

        if success:
            print("  ✅ Compilation successful!")
            compiled = True
            break
        else:
            print(f"  ❌ Errors:\n{errors}")
            print("  🧠 Sending to Claude for syntax repair...")
            fix_syntax(errors)

    if not compiled:
        print("❌ Max syntax retries reached. Exiting.")
        return False

    # ── Step 2: Simulate ─────────────────────────────────────
    banner("🔷 Step 2: Running Simulation")
    success, output = simulate()
    print(output)
    print("✅ Simulation complete.")

    # ── Step 3: Logic Verification + Fix Loop ────────────────
    banner("🔷 Step 3: SiliCount Logic Verification")

    passed = False
    for attempt in range(1, MAX_LOGIC_RETRIES + 1):
        print(f"\n  Logic check attempt {attempt}/{MAX_LOGIC_RETRIES}...")

        passed, mismatches, report = verify_counter_logic(VCD_FILE)

        if passed:
            break
        else:
            print(f"\n  🚨 {len(mismatches)} logic bug(s) found. Engaging Claude repair...")
            fix_logic(mismatches)

            success, errors = compile_design()
            if not success:
                print(f"  ❌ Recompilation failed:\n{errors}")
                continue

            simulate()

    # ── Step 4: Coverage Report ───────────────────────────────
    banner("🔷 Step 4: Functional Coverage Analysis")
    tracker = CoverageTracker()
    tracker.analyze(VCD_FILE)
    hit, total, pct = tracker.report()

    # ── Final Verdict ─────────────────────────────────────────
    banner("🏁 SiliCount Final Verdict")

    if passed:
        print("✅ COUNTER VERIFIED CLEAN")
        print("   • Syntax:   Passed")
        print("   • Logic:    Passed (Golden Reference Model)")
        print(f"   • Coverage: {pct:.1f}% ({hit}/{total} bins)")
        print(f"   • Waveforms: {VCD_FILE}")
        if pct == 100.0:
            print("\n🎉 SiliCount Complete — 100% Silicon Truth Confirmed.")
        else:
            print(f"\n⚠️  SiliCount Complete — {total - hit} coverage hole(s) remain.")
    else:
        print("❌ VERIFICATION FAILED after max retries.")
        print("   Manual review required.")

    return passed


if __name__ == "__main__":
    run()