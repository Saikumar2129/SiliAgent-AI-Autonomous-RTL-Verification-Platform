from golden_model_counter import parse_vcd, fill_gaps, to_int


class CoverageBin:
    """
    A single coverage point — one state we want to verify was hit.
    """
    def __init__(self, name, description):
        self.name        = name
        self.description = description
        self.hit         = False
        self.hit_at      = None  # timestamp when first hit

    def mark_hit(self, timestamp):
        if not self.hit:
            self.hit    = True
            self.hit_at = timestamp


class CoverageTracker:
    """
    Walks the VCD timeline and checks which coverage bins were hit.
    """
    def __init__(self):
        self.bins = {
            # Value coverage
            "count_zero":     CoverageBin("count_zero",     "Counter reached 0"),
            "count_max":      CoverageBin("count_max",      "Counter reached 15 (max)"),
            "count_mid":      CoverageBin("count_mid",      "Counter reached 8 (midpoint)"),

            # Transition coverage
            "overflow":       CoverageBin("overflow",       "Counter overflowed: 15 → 0"),
            "underflow":      CoverageBin("underflow",      "Counter underflowed: 0 → 15"),

            # Control signal coverage
            "up_only":        CoverageBin("up_only",        "up_en=1, down_en=0 (count up)"),
            "down_only":      CoverageBin("down_only",      "down_en=1, up_en=0 (count down)"),
            "both_enabled":   CoverageBin("both_enabled",   "up_en=1, down_en=1 (hold)"),
            "neither_enabled":CoverageBin("neither_enabled","up_en=0, down_en=0 (hold)"),

            # Reset coverage
            "reset_active":   CoverageBin("reset_active",   "Reset was asserted"),
            "reset_mid_count":CoverageBin("reset_mid_count","Reset while count > 0"),
        }

    def analyze(self, vcd_file="dump.vcd"):
        print(f"📊 CoverageTracker: Analyzing {vcd_file}...")

        timeline = parse_vcd(vcd_file)
        filled   = fill_gaps(timeline)

        last_clk   = None
        last_count = None

        for timestamp, signals in filled.items():
            clk     = to_int(signals.get("clk",     "0"))
            rst     = to_int(signals.get("rst",     "0"))
            up_en   = to_int(signals.get("up_en",   "0"))
            down_en = to_int(signals.get("down_en", "0"))
            count   = to_int(signals.get("count",   "0"))

            is_rising_edge = (clk == 1 and last_clk == 0)
            last_clk = clk

            if not is_rising_edge:
                continue

            if count is None:
                continue

            # ── Value Coverage ─────────────────────────────────
            if count == 0:
                self.bins["count_zero"].mark_hit(timestamp)
            if count == 15:
                self.bins["count_max"].mark_hit(timestamp)
            if count == 8:
                self.bins["count_mid"].mark_hit(timestamp)

            # ── Transition Coverage ────────────────────────────
            if last_count is not None:
                if last_count == 15 and count == 0:
                    self.bins["overflow"].mark_hit(timestamp)
                if last_count == 0 and count == 15:
                    self.bins["underflow"].mark_hit(timestamp)

            # ── Control Signal Coverage ────────────────────────
            if up_en == 1 and down_en == 0:
                self.bins["up_only"].mark_hit(timestamp)
            if down_en == 1 and up_en == 0:
                self.bins["down_only"].mark_hit(timestamp)
            if up_en == 1 and down_en == 1:
                self.bins["both_enabled"].mark_hit(timestamp)
            if up_en == 0 and down_en == 0:
                self.bins["neither_enabled"].mark_hit(timestamp)

            # ── Reset Coverage ─────────────────────────────────
            if rst == 1:
                self.bins["reset_active"].mark_hit(timestamp)
                if last_count is not None and last_count > 0:
                    self.bins["reset_mid_count"].mark_hit(timestamp)

            last_count = count

        return self


    def report(self):
        """Print a formatted coverage report."""
        total  = len(self.bins)
        hit    = sum(1 for b in self.bins.values() if b.hit)
        missed = total - hit
        pct    = (hit / total) * 100

        print("\n" + "=" * 60)
        print("  📊 SiliCount Functional Coverage Report")
        print("=" * 60)

        print(f"\n  {'BIN':<20} {'STATUS':<10} {'FIRST HIT'}")
        print(f"  {'-'*20} {'-'*10} {'-'*15}")

        for name, b in self.bins.items():
            status   = "✅ HIT"   if b.hit else "❌ MISSED"
            hit_time = f"t={b.hit_at}" if b.hit_at is not None else "—"
            print(f"  {name:<20} {status:<10} {hit_time}")

        print(f"\n  {'─'*50}")
        print(f"  Total Bins   : {total}")
        print(f"  Bins Hit     : {hit}")
        print(f"  Bins Missed  : {missed}")
        print(f"  Coverage     : {pct:.1f}%")
        print("=" * 60)

        if missed > 0:
            print("\n  ⚠️  Coverage Holes (untested states):")
            for name, b in self.bins.items():
                if not b.hit:
                    print(f"     • {b.description}")

        if pct == 100.0:
            print("\n  🎉 100% Functional Coverage Achieved!")
        elif pct >= 80.0:
            print(f"\n  ⚠️  Good coverage but {missed} state(s) untested.")
        else:
            print(f"\n  🚨 Low coverage — {missed} state(s) never exercised.")

        return hit, total, pct


if __name__ == "__main__":
    tracker = CoverageTracker()
    tracker.analyze("dump.vcd")
    tracker.report()