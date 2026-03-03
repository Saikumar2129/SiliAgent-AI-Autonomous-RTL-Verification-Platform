import os
import anthropic
from dotenv import load_dotenv

load_dotenv()


def fix_logic_bug(mismatches, rtl_file="../VeroSync/fifo.v"):
    print("🧠 SiliOracle: Sending logic bug to Claude for repair...")
    print("=" * 50)

    with open(rtl_file, "r") as f:
        rtl_code = f.read()

    error_lines = []
    for m in mismatches:
        error_lines.append(
            f"  - dout checked at t={m['time']}: "
            f"Expected {m['expected']}, got {m['got']}. {m['error']}"
        )

    mismatch_report = "\n".join(error_lines)

    prompt = f"""You are a senior Verilog verification engineer.

The following RTL code has a LOGIC BUG. It compiles and simulates successfully,
but the SiliOracle Golden Reference Model detected functional mismatches.

=== MISMATCH REPORT ===
{mismatch_report}

=== BUGGY RTL CODE ===
{rtl_code}

=== YOUR TASK ===
1. Analyze the mismatch report carefully
2. Identify the root cause of the logic bug
3. Fix ONLY the logic bug — do not change module name, port names, or interface
4. Output ONLY the corrected Verilog code
5. No markdown backticks, no explanation, no comments about what you changed

Output the fixed Verilog now:"""

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    fixed_code = response.content[0].text.strip()

    if fixed_code.startswith("```"):
        lines = fixed_code.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        fixed_code = "\n".join(lines)

    print("✅ Claude returned repaired RTL.")
    return fixed_code


def save_and_verify(fixed_code, rtl_file="../VeroSync/fifo.v"):
    import subprocess
    from golden_model import verify_fifo_logic

    with open(rtl_file, "w") as f:
        f.write(fixed_code)
    print(f"💾 Fixed RTL saved to {rtl_file}")

    print("🔨 Recompiling...")
    result = subprocess.run(
        ["iverilog", "-o", "../VeroSync/sim.out",
         "../VeroSync/fifo.v", "../VeroSync/fifo_tb.v"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"❌ Compilation failed after fix:\n{result.stderr}")
        return False

    print("✅ Compilation successful!")

    print("▶️  Running simulation...")
    sim = subprocess.run(
        ["vvp", "../VeroSync/sim.out"],
        capture_output=True, text=True,
        cwd="../VeroSync"
    )
    print("✅ Simulation complete.")

    print("\n🔮 Re-running SiliOracle to verify fix...")
    passed, mismatches, report = verify_fifo_logic()
    return passed


if __name__ == "__main__":
    from golden_model import verify_fifo_logic

    passed, mismatches, report = verify_fifo_logic()

    if passed:
        print("\n✅ No logic bugs found. Nothing to fix.")
    else:
        print(f"\n🚨 {len(mismatches)} logic bug(s) detected. Engaging Claude repair...")

        fixed_code = fix_logic_bug(mismatches)

        print("\n📄 Fixed RTL Preview (first 20 lines):")
        for line in fixed_code.split("\n")[:20]:
            print(f"  {line}")

        success = save_and_verify(fixed_code)

        if success:
            print("\n🎉 SiliOracle Logic Fix Complete — RTL verified clean!")
        else:
            print("\n❌ Fix attempt failed. Manual review required.")