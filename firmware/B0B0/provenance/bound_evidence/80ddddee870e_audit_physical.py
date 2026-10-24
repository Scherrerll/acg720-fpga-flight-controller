"""Independent read-only STA audit; writes only the requested audit JSON."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(fixture):
    top = "acg720_ano_port"
    pnr = fixture / "impl/pnr"
    report = pnr / (top + ".tr")
    text = report.read_text(errors="replace")
    text = text[text.index("Note:Core Timing Report"):]
    sdc = (fixture / (top + ".sdc")).read_text()
    frequency = re.search(r"clk50\s+([\d.]+)\(MHz\)\s+([\d.]+)\(MHz\)", text)
    summaries = {}
    for kind in ["setup", "hold"]:
        m = re.search(r"clk50\s+" + kind + r"\s+(-?[\d.]+)\s+(\d+)", text)
        summaries[kind] = dict(tns_ns=float(m[1]), violated_endpoints=int(m[2])) if m else None
    minima = {}
    for section, stop, kind in [("3.1.1 Setup Paths Table", "3.1.2 Hold Paths Table", "setup"),
            ("3.1.2 Hold Paths Table", "3.1.3 Recovery Paths Table", "hold"),
            ("3.1.3 Recovery Paths Table", "3.1.4 Removal Paths Table", "recovery"),
            ("3.1.4 Removal Paths Table", "3.2 Minimum Pulse Width Table", "removal"),
            ("3.2 Minimum Pulse Width Table", "3.3 Timing Report By Analysis Type", "minimum_pulse_width")]:
        begin = text.index(section)
        end = text.find(stop, begin + len(section))
        if end < 0:
            end = text.find("3.3.1 Setup Analysis Report", begin + len(section))
        block = text[begin:end]
        values = re.findall(r"^\s+\d+\s+(-?[\d.]+)\s+", block, re.M)
        minima[kind] = min(map(float, values)) if values else None
    pin_text = (pnr / (top + ".rpt.txt")).read_text(errors="replace")
    errors = re.findall(r"ERROR[^\r\n]*", pin_text)
    un = re.search(r"total\s+(\d+)\s+unrouted nets", pin_text)
    console = (fixture / "console.txt").read_text(errors="replace")
    routed = not errors and not (un and int(un[1])) and "Placement and routing completed" in console
    constraints = [line.strip() for line in sdc.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    clock = re.fullmatch(r"create_clock -name clk50 -period ([0-9.]+) \[get_ports \{clk50\}\]", constraints[0]) if len(constraints) == 1 else None
    period = float(clock[1]) if clock else None
    exact_clock_only = bool(clock and 18 <= period <= 20 and frequency and abs(float(frequency[1])-1000/period)<.002)
    clean = (routed and exact_clock_only and frequency is not None and float(frequency[2]) >= 50
        and all(summaries.get(k) == dict(tns_ns=0.0, violated_endpoints=0) for k in ["setup", "hold"])
        and all(value is not None and value >= 0 for value in minima.values()))
    result = dict(passed=bool(clean), routing_passed=routed, fmax_mhz=float(frequency[2]) if frequency else None, constraint_period_ns=period,
        summaries=summaries, worst_reported_slack_ns=minima, clock_20ns_or_stricter_only=exact_clock_only,
        timing_exceptions_added=False if exact_clock_only else None, hardware_accessed=False, flight_ready=False,
        evidence_sha256={str(p): sha(p) for p in [report, pnr / (top + ".rpt.txt"), fixture / (top + ".sdc"), fixture / (top + ".cst"), fixture / "console.txt"]},
        scope="Physical timing audit only; does not establish RTL equivalence, electrical health or flight acceptance.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.fixture.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "evidence_sha256"}))
