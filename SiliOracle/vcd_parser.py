from vcdvcd import VCDVCD

def parse_vcd(vcd_file="dump.vcd"):
    print(f"📂 SiliOracle: Reading {vcd_file}...")
    vcd = VCDVCD(vcd_file)

    print("📡 Signals found in VCD:")
    for signal in vcd.signals:
        print(f"   {signal}")

    signals_to_extract = [
        "tb_sync_fifo.clk",
        "tb_sync_fifo.dut.clk",
        "tb_sync_fifo.dut.wr_en",
        "tb_sync_fifo.dut.rd_en",
        "tb_sync_fifo.dut.din[7:0]",
        "tb_sync_fifo.dut.dout[7:0]",
        "tb_sync_fifo.dut.full",
        "tb_sync_fifo.dut.empty",
        "tb_sync_fifo.dut.rst",
        "tb_sync_fifo.dut.rd_ptr[3:0]",
        "tb_sync_fifo.dut.wr_ptr[3:0]",
    ]

    timeline = {}

    for sig_name in signals_to_extract:
        try:
            signal = vcd[sig_name]
            for timestamp, value in signal.tv:
                if timestamp not in timeline:
                    timeline[timestamp] = {}
                key = sig_name.split(".")[-1].replace("[7:0]", "").replace("[3:0]", "").replace("[2:0]", "")
                timeline[timestamp][key] = value
        except KeyError:
            print(f"   ⚠️  Signal not found: {sig_name}")

    sorted_timeline = dict(sorted(timeline.items()))
    print(f"✅ Parsed {len(sorted_timeline)} timestamps from VCD.")
    return sorted_timeline


def fill_gaps(timeline):
    filled = {}
    last_known = {}
    for timestamp, signals in timeline.items():
        last_known.update(signals)
        filled[timestamp] = dict(last_known)
    return filled


def to_int(value):
    if value is None:
        return None
    value = str(value).lower()
    if 'x' in value or 'z' in value:
        return None
    try:
        return int(value, 2)
    except ValueError:
        return None


if __name__ == "__main__":
    timeline = parse_vcd("../VeroSync/dump.vcd")
    filled = fill_gaps(timeline)

    print("\n📊 First 15 timestamps:")
    for i, (ts, signals) in enumerate(filled.items()):
        if i >= 15:
            break
        print(f"  t={ts}: {signals}")

    print("\n🔍 All timestamps with din or dout present:")
    for ts, signals in filled.items():
        if "din" in signals or "dout" in signals:
            print(f"  t={ts}: din={signals.get('din','?')} | dout={signals.get('dout','?')} | wr_en={signals.get('wr_en','?')} | rd_en={signals.get('rd_en','?')}")