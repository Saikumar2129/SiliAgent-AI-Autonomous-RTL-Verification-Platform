import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

RTL_FILE = "counter.v"
TB_FILE  = "counter_tb.v"

SPEC = """
Design a 4-bit synchronous up/down counter with the following spec:

Module name: counter
Ports:
  - input clk
  - input rst (synchronous, active high, resets count to 0)
  - input up_en
  - input down_en
  - output reg [3:0] count

Behavior:
  - On rising clock edge:
  - If rst=1: count resets to 0
  - If up_en=1 and down_en=0: count increments by 1
  - If down_en=1 and up_en=0: count decrements by 1
  - If both or neither: count holds
  - Natural 4-bit wrap: 15+1=0 (overflow), 0-1=15 (underflow)
"""

TB_SPEC = """
Write a Verilog testbench for the 4-bit up/down counter.

Module name: tb_counter
DUT instance name: dut

Requirements:
  - Clock period: 10ns (always #5 clk = ~clk)
  - Include $dumpfile("dump.vcd") and $dumpvars(0, tb_counter)
  - This is a REGISTERED output — count updates on the NEXT rising edge after inputs change
  - Test sequence must cover ALL of these states:
      1. Reset (rst=1 then rst=0)
      2. Count up from 0 to 8 (up_en=1, down_en=0 for 8 cycles)
      3. Count down from 8 to 4 (down_en=1, up_en=0 for 4 cycles)
      4. Both enabled — count holds (up_en=1, down_en=1 for 2 cycles)
      5. Count up to 15 (max value)
      6. Overflow: count up one more step from 15 → wraps to 0
      7. Count up to 5
      8. Reset while count > 0
      9. Count up to 3
      10. Underflow: count down from 3 → 2 → 1 → 0 → wraps to 15
  - End with $finish
  - No SystemVerilog syntax (use reg/wire not logic)
  - No automatic checking inside testbench — verification is done externally
"""


def clean_verilog(text):
    lines = text.split("\n")
    lines = [l for l in lines if not l.strip().startswith("```")]
    return "\n".join(lines).strip()


def generate_rtl():
    print("🧠 Generating counter RTL from spec...")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"{SPEC}\n\nOutput ONLY the Verilog code. No markdown. No explanation."
        }]
    )
    rtl = clean_verilog(response.content[0].text.strip())
    with open(RTL_FILE, "w") as f:
        f.write(rtl)
    print(f"✅ RTL saved to {RTL_FILE}")
    return rtl


def generate_testbench():
    print("🧠 Generating counter testbench from spec...")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"{TB_SPEC}\n\nOutput ONLY the Verilog code. No markdown. No explanation."
        }]
    )
    tb = clean_verilog(response.content[0].text.strip())
    with open(TB_FILE, "w") as f:
        f.write(tb)
    print(f"✅ Testbench saved to {TB_FILE}")
    return tb


def preview(filepath, lines=15):
    print(f"\n📄 Preview of {filepath} (first {lines} lines):")
    with open(filepath) as f:
        for i, line in enumerate(f):
            if i >= lines:
                print("  ...")
                break
            print(f"  {line}", end="")
    print()


if __name__ == "__main__":
    print("=" * 55)
    print("  🔷 SiliCount: RTL + Testbench Generator")
    print("=" * 55)

    generate_rtl()
    preview(RTL_FILE)

    generate_testbench()
    preview(TB_FILE)

    print("=" * 55)
    print("✅ Generation complete.")
    print("   Next step: python3 counter_agent.py")
    print("=" * 55)