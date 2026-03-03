import os
import subprocess
import anthropic
from dotenv import load_dotenv
from golden_model_axi import verify_axi_protocol

load_dotenv()

MAX_SYNTAX_RETRIES = 5
MAX_LOGIC_RETRIES  = 3

RTL_FILE = "axi4_lite_slave.v"
TB_FILE  = "axi4_lite_tb.v"
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
    try:
        result = subprocess.run(
            ["vvp", SIM_OUT],
            capture_output=True, text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, None
    except subprocess.TimeoutExpired:
        timeout_msg = (
            "TIMEOUT: Simulation hung after 30s.\n"
            "Root cause: AXI handshake deadlock.\n"
            "The testbench is stuck in a while(!wready) or while(!awready) loop.\n"
            "Most likely: write_addr_valid is not set before wvalid arrives.\n"
            "Fix: ensure wready is asserted when wvalid=1 regardless of "
            "write_addr_valid timing, or accept awvalid and wvalid on same cycle."
        )
        return False, "", timeout_msg


def stream_claude(prompt, max_tokens=4096):
    full_text = ""
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            print(".", end="", flush=True)
    print(" done.")
    return full_text


def clean(text):
    lines = text.split("\n")
    lines = [l for l in lines if not l.strip().startswith("```")]
    return "\n".join(lines).strip()


def fix_syntax(errors):
    with open(RTL_FILE) as f: rtl = f.read()
    with open(TB_FILE)  as f: tb  = f.read()

    prompt = f"""Fix these Verilog compiler errors.

ERRORS:
{errors}

RTL (axi4_lite_slave.v):
{rtl}

TESTBENCH (axi4_lite_tb.v):
{tb}

Rules: fix all errors, keep module names/ports, use reg/wire only, no markdown.

Output format:
===AXI4_LITE_SLAVE.V===
<fixed rtl>
===AXI4_LITE_TB.V===
<fixed testbench>"""

    print("  🧠 Streaming syntax fix... ", end="", flush=True)
    text = stream_claude(prompt)

    try:
        rtl_fixed = text.split("===AXI4_LITE_SLAVE.V===")[1].split("===AXI4_LITE_TB.V===")[0].strip()
        tb_fixed  = text.split("===AXI4_LITE_TB.V===")[1].strip()
    except IndexError:
        rtl_fixed = rtl
        tb_fixed  = tb

    with open(RTL_FILE, "w") as f: f.write(clean(rtl_fixed))
    with open(TB_FILE,  "w") as f: f.write(clean(tb_fixed))


def fix_timeout(timeout_msg):
    with open(RTL_FILE) as f: rtl = f.read()

    prompt = f"""This AXI4-Lite slave RTL caused a simulation timeout (handshake deadlock).

DIAGNOSIS:
{timeout_msg}

AXI4-LITE WRITE SEQUENCE:
1. Master asserts awvalid=1 with awaddr
2. Slave asserts awready=1 — address latched
3. Master deasserts awvalid, asserts wvalid=1 with wdata
4. Slave asserts wready=1 — data written to memory
5. Slave asserts bvalid=1 with bresp=OKAY
6. Master asserts bready=1 — transaction complete

CRITICAL FIX REQUIRED:
The write data channel (wvalid/wready) must not depend on write_addr_valid
being set in the SAME clock cycle as awvalid. Non-blocking assignments mean
write_addr_valid won't be 1 until the NEXT cycle after awvalid.
Solution: latch write_addr combinatorially or accept wvalid one cycle after awready.

BUGGY RTL:
{rtl}

Fix the handshake deadlock. Keep module name and ports. Output ONLY Verilog. No markdown."""

    print("  🧠 Streaming timeout fix... ", end="", flush=True)
    fixed = stream_claude(prompt, max_tokens=4096)
    with open(RTL_FILE, "w") as f: f.write(clean(fixed))
    print("  ✅ Fixed RTL saved.")


def fix_logic(violations):
    with open(RTL_FILE) as f: rtl = f.read()

    error_lines = [f"  - [{v['rule']}] t={v['time']}: {v['error']}" for v in violations[:10]]

    prompt = f"""Fix this AXI4-Lite slave RTL protocol bug.

VIOLATIONS:
{chr(10).join(error_lines)}

SPEC:
- BRESP/RRESP must be 2'b00 (OKAY)
- RDATA must return exactly the data written to that address
- VALID must never deassert before READY

BUGGY RTL:
{rtl}

Fix ONLY the bug. Keep module name and ports. Output ONLY Verilog. No markdown."""

    print("  🧠 Streaming logic fix... ", end="", flush=True)
    fixed = stream_claude(prompt, max_tokens=2048)
    with open(RTL_FILE, "w") as f: f.write(clean(fixed))
    print("  ✅ Repaired RTL saved.")


def run():
    banner("🚀 SiliAXI Agent Starting")
    print("   AXI4-Lite Protocol Verification + Autonomous Repair")

    # ── Step 1: Compile ───────────────────────────────────────
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
            fix_syntax(errors)

    if not compiled:
        print("❌ Max syntax retries reached. Exiting.")
        return False

    # ── Step 2: Simulate with timeout ─────────────────────────
    banner("🔷 Step 2: Running Simulation")

    sim_passed = False
    for attempt in range(1, MAX_LOGIC_RETRIES + 1):
        print(f"\n  Simulation attempt {attempt}/{MAX_LOGIC_RETRIES}...")
        success, output, timeout_msg = simulate()

        if timeout_msg:
            print(f"  ⏱️  {timeout_msg.splitlines()[0]}")
            print("  🧠 Sending timeout diagnosis to Claude...")
            fix_timeout(timeout_msg)
            success, errors = compile_design()
            if not success:
                print(f"  ❌ Recompilation failed:\n{errors}")
                continue
        else:
            print(output)
            print("  ✅ Simulation complete.")
            sim_passed = True
            break

    if not sim_passed:
        print("❌ Simulation failed after max retries. Exiting.")
        return False

    # ── Step 3: Protocol Verification + Fix Loop ──────────────
    banner("🔷 Step 3: SiliAXI Protocol Verification")

    passed = False
    for attempt in range(1, MAX_LOGIC_RETRIES + 1):
        print(f"\n  Protocol check attempt {attempt}/{MAX_LOGIC_RETRIES}...")
        passed, violations, report = verify_axi_protocol(VCD_FILE)

        if passed:
            break
        else:
            print(f"\n  🚨 {len(violations)} violation(s) found. Engaging Claude repair...")
            fix_logic(violations)
            success, errors = compile_design()
            if not success:
                print(f"  ❌ Recompilation failed:\n{errors}")
                continue
            _, _, timeout_msg = simulate()
            if timeout_msg:
                print(f"  ⏱️  Simulation hung again. Sending to Claude...")
                fix_timeout(timeout_msg)
                compile_design()
                simulate()

    # ── Final Verdict ──────────────────────────────────────────
    banner("🏁 SiliAXI Final Verdict")

    if passed:
        print("✅ AXI4-LITE PROTOCOL VERIFIED CLEAN")
        print("   • Syntax:    Passed")
        print("   • Handshake: Passed (VALID/READY integrity)")
        print("   • Data:      Passed (Write→Read correctness)")
        print("   • Response:  Passed (BRESP/RRESP = OKAY)")
        print(f"   • Waveforms: {VCD_FILE}")
        print("\n🎉 SiliAXI Complete — AXI4-Lite Silicon Truth Confirmed.")
    else:
        print("❌ PROTOCOL VERIFICATION FAILED after max retries.")
        print("   Manual review required.")

    return passed


if __name__ == "__main__":
    run()