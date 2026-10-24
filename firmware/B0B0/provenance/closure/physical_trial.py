"""Isolated, source-bound Gowin netlist physical experiment. Never programs hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parent
TOP = "acg720_ano_port"
GOWIN = "C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding="utf8"))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def save(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


def prepare(args):
    baseline = Path(args.baseline).resolve()
    old = read(baseline / "feasibility_contract.json")
    study_path = Path(old["study_manifest"])
    study = read(study_path)
    require(sha(study_path) == old["study_manifest_sha256"] and study["passed"], "Unbound synthesis study")
    folder = Path(study["folder"])
    for name, digest in study["source_sha256"].items():
        require(sha(folder / name) == digest, "Changed source: " + name)
    for name, digest in study["evidence_sha256"].items():
        require(sha(folder / name) == digest, "Changed synthesis evidence: " + name)
    vg = baseline / "fixture/impl/gwsynthesis" / (TOP + ".vg")
    require(sha(vg) == old["vg_sha256"] == study["proposed_vg_sha256"], "Changed input netlist")
    trial = ROOT / args.name
    trial.mkdir()
    fixture = trial / "fixture"
    (fixture / "impl/gwsynthesis").mkdir(parents=True)
    shutil.copyfile(vg, fixture / "impl/gwsynthesis" / vg.name)
    amendment = "".join('CLOCK_LOC "' + n + '" BUFG = CE|SR|LOGIC;\n' for n in args.global_net)
    base_cst = (folder / (TOP + ".cst")).read_bytes()
    (fixture / (TOP + ".cst")).write_bytes(base_cst + (b"" if base_cst.endswith(b"\n") else b"\n") + amendment.encode())
    for name in [TOP + ".gprj", TOP + ".sdc", "pnr_only.tcl"]:
        shutil.copyfile(baseline / "fixture" / name, fixture / name)
    (trial / "DO_NOT_PROGRAM").write_text("Unqualified physical experiment. Hardware and flight qualification pending.\n")
    save(trial / "contract.json", dict(baseline=str(baseline), baseline_contract_sha256=sha(baseline / "feasibility_contract.json"),
        study_manifest=str(study_path), study_manifest_sha256=sha(study_path),
        vg_sha256=sha(vg), source_sha256=study["source_sha256"], pins=old["pins"],
        amendment=amendment, global_nets=args.global_net,
        inputs_sha256={str(p.relative_to(fixture)): sha(p) for p in fixture.rglob("*") if p.is_file()},
        runner_sha256=sha(__file__), hardware_accessed=False, flight_ready=False))
    preflight(trial)
    print(json.dumps(dict(prepared=str(trial), vg_sha256=sha(vg), global_nets=args.global_net)))


def preflight(trial):
    c = read(trial / "contract.json")
    require(sha(__file__) == c["runner_sha256"], "Changed runner")
    require(sha(Path(c["baseline"]) / "feasibility_contract.json") == c["baseline_contract_sha256"], "Changed baseline contract")
    require(sha(c["study_manifest"]) == c["study_manifest_sha256"], "Changed study")
    study = read(c["study_manifest"])
    folder = Path(study["folder"])
    require(study["source_sha256"] == c["source_sha256"], "Changed source family")
    for n, h in {**study["source_sha256"], **study["evidence_sha256"]}.items():
        require(sha(folder / n) == h, "Changed baseline input/evidence: " + n)
    for n, h in c["inputs_sha256"].items():
        require(sha(trial / "fixture" / n) == h, "Changed physical input: " + n)
    fixture = trial / "fixture"
    require(sha(fixture / (TOP + ".sdc")) == study["source_sha256"][TOP + ".sdc"], "Changed timing constraints")
    require('create_clock -name clk50 -period 20.000' in (fixture / (TOP + ".sdc")).read_text(), "Missing 50 MHz clock")
    base = (folder / (TOP + ".cst")).read_bytes()
    require((fixture / (TOP + ".cst")).read_bytes() == base + (b"" if base.endswith(b"\n") else b"\n") + c["amendment"].encode(), "Unexpected physical amendment")
    require((trial / "DO_NOT_PROGRAM").is_file(), "Missing programming block")
    return c


def collect(trial, start, returncode):
    c = preflight(trial)
    fixture = trial / "fixture"
    pnr = fixture / "impl/pnr"
    console = (fixture / "console.txt").read_text(errors="replace")
    result = dict(routing_passed=False, timing_passed=False, feasibility_passed=False,
        functional_qualification_pending=True, hardware_accessed=False, flight_ready=False,
        programming_authorized=False, release_eligible=False, vendor_returncode=returncode,
        contract_sha256=sha(trial / "contract.json"), vg_sha256=c["vg_sha256"],
        actual_outputs_sha256={str(p.relative_to(fixture)): sha(p) for p in pnr.glob("*") if p.is_file()})
    try:
        require("Skip synthesis" in console and not re.search(r"GowinSynthesis|Running synthesis", console), "Unexpected synthesis")
        cmd = (pnr / "cmd.do").read_text()
        actual = dict(re.findall(r"^-(\w+)[ \t]+(.+?)[ \t]*$", cmd, re.M))
        for k, n in [("d", "impl/gwsynthesis/" + TOP + ".vg"), ("cst", TOP + ".cst"), ("sdc", TOP + ".sdc")]:
            require(Path(actual[k]).resolve() == (fixture / n).resolve(), "Wrong actual input: " + k)
        require(actual["p"] == "GW5AT-60B-PBGA484A-1" and actual["pn"] == "GW5AT-LV60PG484AC1/I0", "Wrong device")
        require(actual["place_option"] == "2" and actual["route_option"] == "2" and actual["route_maxfan"] == "23", "Wrong physical policy")
        require(not re.search(r"^-replicate\s*$", cmd, re.M) and re.search(r"^-timing\s*$", cmd, re.M), "Replication/timing policy changed")
        rpt = pnr / (TOP + ".rpt.txt")
        require(rpt.stat().st_mtime >= start, "Stale report")
        text = rpt.read_text(errors="replace")
        result["errors"] = re.findall(r"ERROR[^\r\n]*", console + "\n" + text)
        un = re.search(r"total\s+(\d+)\s+unrouted nets", text)
        result["unrouted_nets"] = int(un[1]) if un else None
        pins = dict(re.findall(r"^(\w+)\s+\|\s*-\s*\|\s*(\w+)/\d+\s*\|", text, re.M))
        require(pins == c["pins"], "Wrong physical pins")
        result["pins"] = pins
        result["routing_passed"] = not result["errors"] and not (un and int(un[1])) and "Placement and routing completed" in console
        if result["routing_passed"]:
            result["unrouted_nets"] = 0
        tr = pnr / (TOP + ".tr")
        if tr.exists():
            require(tr.stat().st_mtime >= start, "Stale timing report")
            text = tr.read_text(errors="replace")
            fm = re.search(r"clk50\s+50\.000\(MHz\)\s+([0-9.]+)\(MHz\)", text)
            slack = {}
            for kind in ["setup", "hold"]:
                m = re.search(r"clk50\s+" + kind + r"\s+(-?[0-9.]+)\s+(\d+)", text)
                if m:
                    slack[kind] = dict(tns_ns=float(m[1]), violated_endpoints=int(m[2]))
            result.update(fmax_mhz=float(fm[1]) if fm else None, slack=slack)
            result["timing_passed"] = bool(fm and float(fm[1]) >= 50 and all(slack.get(k) == dict(tns_ns=0.0, violated_endpoints=0) for k in ["setup", "hold"]))
        fs = pnr / (TOP + ".fs")
        if fs.exists():
            require(fs.stat().st_mtime >= start, "Stale bitstream")
            with fs.open() as stream:
                header = "".join(next(stream, "") for _ in range(15))
            require(re.search(r"UserCode:\s*0x0000b0b0", header, re.I), "Wrong bitstream identity")
            result["bitstream"] = dict(path=str(fs), sha256=sha(fs))
        result["feasibility_passed"] = bool(result["routing_passed"] and result["timing_passed"] and result.get("bitstream") and "Bitstream generation completed" in console)
    except (ValueError, KeyError, OSError) as error:
        result["acceptance_error"] = str(error)
    save(trial / "result.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "actual_outputs_sha256"}), flush=True)


def run(trial):
    preflight(trial)
    fixture = trial / "fixture"
    require(not (fixture / "impl/pnr").exists(), "Refuse existing physical outputs")
    state = dict(started_epoch=time.time(), hardware_accessed=False)
    with (fixture / "console.txt").open("w") as log:
        p = subprocess.Popen([GOWIN, "pnr_only.tcl"], cwd=fixture, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        state["owned_pid"] = p.pid
        save(trial / "run_state.json", state)
        print(json.dumps(state), flush=True)
        try:
            p.wait(timeout=5400)
        except subprocess.TimeoutExpired:
            p.terminate()
            p.wait(timeout=15)
            state["timed_out"] = True
        state.update(returncode=p.returncode, finished_epoch=time.time())
        save(trial / "run_state.json", state)
    collect(trial, state["started_epoch"], p.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "run", "verify"])
    parser.add_argument("name")
    parser.add_argument("--baseline")
    parser.add_argument("--global-net", action="append", default=[])
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z0-9_]+", args.name), "Invalid trial name")
    if args.action == "prepare":
        prepare(args)
    elif args.action == "run":
        run(ROOT / args.name)
    else:
        preflight(ROOT / args.name)
        print("PASS immutable source/netlist/constraint binding; no hardware access")
