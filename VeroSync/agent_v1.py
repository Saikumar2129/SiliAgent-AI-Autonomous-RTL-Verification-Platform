import subprocess
import os
from generate_rtl import create_fifo
from build_tb import create_testbench
from auto_fixer import run_compilation, fix_code
from cleaner import clean_verilog_file

MAX_RETRIES = 5

def run_simulation():
    result = subprocess.run(
        ["vvp", "sim.out"],
        capture_output=True, text=True
    )
    return result.stdout

def agent_loop():
    print("🚀 VeroSync Agent v1 Starting...")
    print("=" * 50)

    # Step 1: Generate RTL
    print("\n📝 Step 1: Generating RTL...")
    create_fifo()

    # Step 2: Generate Testbench
    print("\n🧪 Step 2: Generating Testbench...")
    create_testbench()

    # Step 3: Clean → Compile → Fix loop
    print("\n🔄 Step 3: Clean → Compile → Auto-Fix Loop...")
    
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n  Attempt {attempt}/{MAX_RETRIES}: Cleaning & Compiling...")
        
        # Deterministic cleaner first
        clean_verilog_file("fifo.v")
        clean_verilog_file("fifo_tb.v")
        
        errors = run_compilation()
        
        if not errors:
            print("  ✅ Compilation successful!")
            break
        else:
            print(f"  ❌ Errors found. Sending to AI fixer...")
            fix_code(errors)
    else:
        print("\n❌ Max retries reached. Manual intervention needed.")
        return

    # Step 4: Run simulation
    print("\n▶️  Step 4: Running Simulation...")
    output = run_simulation()
    print(output)

    print("\n" + "=" * 50)
    print("✅ VeroSync Agent v1 Complete!")
    print("📊 Check dump.vcd for waveforms.")

if __name__ == "__main__":
    agent_loop()
