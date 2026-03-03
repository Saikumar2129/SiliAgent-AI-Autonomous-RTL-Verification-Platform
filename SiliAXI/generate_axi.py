import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

RTL_FILE = "axi4_lite_slave.v"
TB_FILE  = "axi4_lite_tb.v"

SPEC = """
Design an AXI4-Lite slave module with the following spec:

Module name: axi4_lite_slave
Parameters: DATA_WIDTH=32, ADDR_WIDTH=8

Ports: clk, rst, awvalid, awready, awaddr[ADDR_WIDTH-1:0],
wvalid, wready, wdata[DATA_WIDTH-1:0], wstrb[DATA_WIDTH/8-1:0],
bvalid, bready, bresp[1:0], arvalid, arready, araddr[ADDR_WIDTH-1:0],
rvalid, rready, rdata[DATA_WIDTH-1:0], rresp[1:0]

Behavior:
- Internal memory: reg [DATA_WIDTH-1:0] mem [0:255]
- Synchronous reset — all outputs 0, memory cleared via integer loop
- Write: latch awaddr when awvalid, write wdata to mem[awaddr] when wvalid, send BRESP=OKAY
- Read: read mem[araddr] into rdata when arvalid, send RRESP=OKAY
- awready, wready, arready are single-cycle pulses
- Use reg/wire only (no logic keyword)
"""

TB_SPEC = """
Write a Verilog testbench for an AXI4-Lite slave.
Module: tb_axi4_lite, DUT instance: dut, DATA_WIDTH=32, ADDR_WIDTH=8.
Clock: always #5 clk = ~clk.
Include $dumpfile("dump.vcd") and $dumpvars(0, tb_axi4_lite).
No SystemVerilog (use reg/wire only).

Write task axi_write(input [7:0] addr, input [31:0] data):
  assert awvalid+awaddr, wait awready, deassert.
  assert wvalid+wdata+wstrb=4'hF, wait wready, deassert.
  assert bready, wait bvalid, deassert.

Write task axi_read(input [7:0] addr, output [31:0] data):
  assert arvalid+araddr, wait arready, deassert.
  assert rready, wait rvalid, capture rdata, deassert.

Test sequence:
  rst=1 for 2 cycles, rst=0.
  axi_write(0x04, 0xDEADBEEF)
  axi_read(0x04, read_data), $display result
  axi_write(0x08, 0xCAFEBABE)
  axi_write(0x0C, 0x12345678)
  axi_write(0x10, 0xAABBCCDD)
  axi_read(0x08, read_data), $display result
  axi_read(0x0C, read_data), $display result
  axi_read(0x10, read_data), $display result
  axi_write(0x04, 0x11223344)
  axi_read(0x04, read_data), $display result
  $finish

No pass/fail checking inside testbench.
"""


def clean_verilog(text):
    lines = text.split("\n")
    lines = [l for l in lines if not l.strip().startswith("```")]
    return "\n".join(lines).strip()


def generate_rtl():
    print("🧠 Generating AXI4-Lite slave RTL... ", end="", flush=True)
    tb_text = ""
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": f"{SPEC}\n\nOutput ONLY Verilog. No markdown. No explanation."}]
    ) as stream:
        for text in stream.text_stream:
            tb_text += text
            print(".", end="", flush=True)
    print(" done.")
    rtl = clean_verilog(tb_text.strip())
    with open(RTL_FILE, "w") as f:
        f.write(rtl)
    print(f"✅ RTL saved to {RTL_FILE}")
    return rtl


def fix_module_name():
    """Ensure testbench instantiates axi4_lite_slave not axi4_lite."""
    with open(TB_FILE) as f:
        content = f.read()
    # Fix bare module instantiation (without parameters)
    content = content.replace("axi4_lite dut", "axi4_lite_slave dut")
    # Fix module instantiation with parameters
    content = content.replace("axi4_lite #(", "axi4_lite_slave #(")
    with open(TB_FILE, "w") as f:
        f.write(content)
    print("  🔧 Module name verified: axi4_lite_slave")


def generate_testbench():
    print("🧠 Generating AXI4-Lite testbench... ", end="", flush=True)
    tb_text = ""
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": f"{TB_SPEC}\n\nOutput ONLY Verilog. No markdown. No explanation."}]
    ) as stream:
        for text in stream.text_stream:
            tb_text += text
            print(".", end="", flush=True)
    print(" done.")
    tb = clean_verilog(tb_text.strip())
    with open(TB_FILE, "w") as f:
        f.write(tb)
    print(f"✅ Testbench saved to {TB_FILE}")
    fix_module_name()
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
    print("  🔷 SiliAXI: RTL + Testbench Generator")
    print("=" * 55)

    generate_rtl()
    preview(RTL_FILE)

    generate_testbench()
    preview(TB_FILE)

    print("=" * 55)
    print("✅ Generation complete.")
    print("   Next step: python3 axi_agent.py")
    print("=" * 55)