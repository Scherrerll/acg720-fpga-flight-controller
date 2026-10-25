"""Build-auditor fail-closed tests using tiny, deliberately nonprogrammable mocks.

No Gowin, programmer, serial port or hardware API is called. All source,
reports and mock .fs files live inside a TemporaryDirectory and disappear.
These results are not an offline acceptance receipt for a real FPGA image.
"""
from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("b0b1_build_audit_tested", ROOT / "tools/build.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)
TOP = builder.TOP


class BuildAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="b0b1_mock_build_audit_")
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve()
        self.root = self.repo / "firmware/B0B1"
        self.source = self.root / "source"
        self.source.mkdir(parents=True)
        self.baseline = self.repo / "firmware/B0B0/source_snapshot"
        self.baseline.mkdir(parents=True)
        # A fake package and fake design: these can never program real hardware.
        self.pins = {"clk50": "MOCK0", **{f"mock_port_{i}": f"MOCK{i+1}" for i in range(16)}}
        cst = "\n".join(f'IO_LOC "{name}" {pin};' for name, pin in self.pins.items()) + "\n"
        (self.source / f"{TOP}.cst").write_text(cst)
        (self.baseline / f"{TOP}.cst").write_text(cst)
        (self.source / f"{TOP}.sdc").write_text("create_clock -name clk50 -period 19.500 [get_ports {clk50}]\n")
        (self.source / f"{TOP}.v").write_text("// MOCK ONLY\nmodule mock_only; endmodule\n")
        (self.source / "build.tcl").write_text(f"open_project {TOP}.gprj\nrun all\nexit\n")
        (self.source / f"{TOP}.gprj").write_text(
            '<Project><FileList>'
            f'<File path="{TOP}.v" type="file.verilog" enable="1"/>'
            f'<File path="{TOP}.sdc" type="file.sdc" enable="1"/>'
            f'<File path="{TOP}.cst" type="file.cst" enable="1"/>'
            '</FileList></Project>')
        for attribute, value in (("ROOT", self.root), ("REPO", self.repo)):
            patch = mock.patch.object(builder, attribute, value)
            patch.start()
            self.addCleanup(patch.stop)
        patch = mock.patch.object(builder.subprocess, "run", side_effect=AssertionError("No vendor/hardware process allowed"))
        patch.start()
        self.addCleanup(patch.stop)
        self.output = self.repo / "mock_build"
        self.fixture, self.inputs = builder.prepare(self.output, 2, 2, 0)
        self.pnr = self.fixture / "impl/pnr"
        self.pnr.mkdir(parents=True)
        netlist = self.fixture / f"impl/gwsynthesis/{TOP}.vg"
        netlist.parent.mkdir(parents=True)
        netlist.write_text("// MOCK NETLIST; NOT A HARDWARE DESIGN\n")
        (self.output / "console.log").write_text("Placement and routing completed\nBitstream generation completed\n")
        (self.pnr / f"{TOP}.rpt.txt").write_text(
            "Running routing:\nTotal Routing: MOCK\n" +
            "\n".join(f"{name} | - | {pin}/0 | MOCK" for name, pin in self.pins.items()) + "\n")
        (self.pnr / f"{TOP}.tr").write_text(self.timing())
        (self.pnr / f"{TOP}.fs").write_text("// UserCode: 0x0000B0B1\nMOCK ONLY -- NOT PROGRAMMABLE\n")
        (self.pnr / "cmd.do").write_text(
            f"-d {netlist}\n-cst {self.fixture / (TOP + '.cst')}\n-sdc {self.fixture / (TOP + '.sdc')}\n")

    @staticmethod
    def timing():
        return ("Note:Core Timing Report\n"
                "2.2 Clock Summary\n 1 clk50 Base 19.500 MOCK\n"
                "2.3 Max Frequency Summary\n clk50 51.282(MHz) 55.000(MHz)\n"
                " clk50 setup 0.000 0\n clk50 hold 0.000 0\n"
                "3.1.1 Setup Paths Table\n 1 0.100 MOCK\n"
                "3.1.2 Hold Paths Table\n 1 0.200 MOCK\n"
                "3.1.3 Recovery Paths Table\n 1 0.300 MOCK\n"
                "3.1.4 Removal Paths Table\n 1 0.400 MOCK\n"
                "3.2 Minimum Pulse Width Table\n 1 0.500 MOCK\n"
                "3.3 Timing Report By Analysis Type\n")

    def edit(self, path, old, new):
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new))

    def collect(self, returncode=0):
        with redirect_stdout(io.StringIO()):
            return builder.collect(self.output, returncode)

    def rejected(self, returncode=0):
        try:
            result = self.collect(returncode)
        except (ValueError, OSError, KeyError):
            return
        self.assertIs(result["passed"], False, "malformed audit inputs passed")

    def prepare_rejected(self):
        with self.assertRaises((ValueError, OSError)):
            builder.prepare(self.repo / "second_mock_build", 2, 2, 0)

    def test_normal_complete_chain_without_unrouted_line_passes(self):
        result = self.collect()
        self.assertIs(result["passed"], True)
        self.assertIsNone(result["unrouted_nets"])
        self.assertTrue(result["routing_status_proof"])
        self.assertEqual(len(result["worst_reported_slack_ns"]), 5)
        self.assertIs(result["hardware_accessed"], False)
        self.assertIs(result["flight_ready"], False)
        self.assertFalse((self.output / "offline_acceptance.json").exists())

    def test_bitstream_identity_prefix_is_not_a_match(self):
        image = self.pnr / (TOP + '.fs')
        image.write_text('// UserCode: 0x0000B0B10\nMOCK ONLY\n')
        self.rejected()

    def test_explicit_nonzero_unrouted_fails(self):
        path = self.pnr / f"{TOP}.rpt.txt"
        path.write_text(path.read_text() + "total 2 unrouted nets\n")
        self.rejected()

    def test_missing_full_timing_report_fails(self):
        (self.pnr / f"{TOP}.tr").unlink()
        self.rejected()

    def test_missing_each_sta_kind_fails(self):
        path = self.pnr / f"{TOP}.tr"
        for value in ("0.100", "0.200", "0.300", "0.400", "0.500"):
            with self.subTest(value=value):
                path.write_text(self.timing().replace(f" 1 {value} MOCK\n", ""))
                self.rejected()

    def test_negative_recovery_removal_minpulse_fail(self):
        path = self.pnr / f"{TOP}.tr"
        for value in ("0.300", "0.400", "0.500"):
            with self.subTest(value=value):
                path.write_text(self.timing().replace(value, "-0.001"))
                self.rejected()

    def test_negative_setup_or_hold_summary_fails(self):
        path = self.pnr / f"{TOP}.tr"
        for kind in ("setup", "hold"):
            with self.subTest(kind=kind):
                path.write_text(self.timing().replace(f"clk50 {kind} 0.000 0", f"clk50 {kind} -0.001 1"))
                self.rejected()

    def test_insufficient_fmax_fails(self):
        self.edit(self.pnr / f"{TOP}.tr", "55.000(MHz)", "50.000(MHz)")
        self.rejected()

    def test_additional_clock_fails(self):
        self.edit(self.pnr / f"{TOP}.tr", "2.3 Max Frequency Summary", " 2 other_clock Base 20.000 MOCK\n2.3 Max Frequency Summary")
        self.rejected()

    def test_wrong_report_clock_period_fails(self):
        self.edit(self.pnr / f"{TOP}.tr", "clk50 Base 19.500", "clk50 Base 20.000")
        self.rejected()

    def test_each_wrong_actual_command_input_fails(self):
        path = self.pnr / "cmd.do"
        original = path.read_text()
        for key in ("d", "cst", "sdc"):
            with self.subTest(key=key):
                lines = original.splitlines()
                path.write_text("\n".join(f"-{key} {self.repo / 'wrong_mock_input'}" if x.startswith(f"-{key} ") else x for x in lines) + "\n")
                self.rejected()

    def test_vendor_nonzero_exit_fails(self):
        self.rejected(returncode=7)

    def test_missing_router_or_bitstream_completion_fails(self):
        path = self.output / "console.log"
        for text in ("Placement and routing completed\n", "Bitstream generation completed\n"):
            with self.subTest(text=text):
                path.write_text(text)
                self.rejected()

    def test_incomplete_physical_report_fails(self):
        path = self.pnr / f"{TOP}.rpt.txt"
        self.edit(path, "Total Routing: MOCK\n", "")
        self.rejected()

    def test_actual_pin_mismatch_fails(self):
        self.edit(self.pnr / f"{TOP}.rpt.txt", "clk50 | - | MOCK0/0", "clk50 | - | WRONG/0")
        self.rejected()

    def test_wrong_usercode_fails(self):
        self.edit(self.pnr / f"{TOP}.fs", "0x0000B0B1", "0x0000B0B0")
        self.rejected()

    def test_missing_bitstream_fails(self):
        (self.pnr / f"{TOP}.fs").unlink()
        self.rejected()

    def test_duplicate_io_loc_fails_prepare(self):
        path = self.source / f"{TOP}.cst"
        path.write_text(path.read_text() + 'IO_LOC "clk50" MOCK0;\n')
        self.prepare_rejected()

    def test_duplicate_io_loc_fails_even_if_mock_baseline_matches(self):
        for root in (self.source, self.baseline):
            path = root / f"{TOP}.cst"
            path.write_text(path.read_text() + 'IO_LOC "clk50" MOCK0;\n')
        self.prepare_rejected()

    def test_gprj_extra_enabled_sdc_fails_prepare(self):
        (self.source / "extra.sdc").write_text("# MOCK\n")
        self.edit(self.source / f"{TOP}.gprj", "</FileList>", '<File path="extra.sdc" type="file.sdc" enable="1"/></FileList>')
        self.prepare_rejected()

    def test_sdc_exceptions_fail_prepare(self):
        path = self.source / f"{TOP}.sdc"
        original = path.read_text()
        for exception in ("set_false_path -from [all_registers]", "set_multicycle_path 2 -setup [all_registers]"):
            with self.subTest(exception=exception):
                path.write_text(original + exception + "\n")
                self.assertRaises(ValueError, builder.constraints, self.source)

    def test_wrong_sdc_period_fails_prepare(self):
        self.edit(self.source / f"{TOP}.sdc", "19.500", "20.000")
        self.prepare_rejected()

    def test_archived_builder_hash_change_fails(self):
        path = self.output / "build_runner.py"
        path.write_text(path.read_text() + "\n# modified mock archive\n")
        self.rejected()

    def test_fixture_input_change_fails(self):
        path = self.fixture / f"{TOP}.v"
        path.write_text(path.read_text() + "// modified fixture input\n")
        self.rejected()

    def test_input_hash_map_change_fails(self):
        path = self.output / "inputs.json"
        manifest = json.loads(path.read_text())
        manifest["source_sha256"][f"{TOP}.v"] = "0" * 64
        path.write_text(json.dumps(manifest))
        self.rejected()

    def test_missing_source_binding_cannot_hide_changed_fixture(self):
        path = self.output / "inputs.json"
        manifest = json.loads(path.read_text())
        manifest["source_sha256"].pop(f"{TOP}.v")
        path.write_text(json.dumps(manifest))
        (self.fixture / f"{TOP}.v").write_text("// CHANGED UNBOUND MOCK SOURCE\n")
        self.rejected()

    def test_empty_pin_manifest_cannot_hide_missing_report_pins(self):
        path = self.output / "inputs.json"
        manifest = json.loads(path.read_text())
        manifest["pins"] = {}
        path.write_text(json.dumps(manifest))
        (self.pnr / f"{TOP}.rpt.txt").write_text("Running routing:\nTotal Routing: MOCK\n")
        self.rejected()

    def test_boolean_vendor_returncode_is_not_integer_zero(self):
        self.rejected(returncode=False)

    def test_empty_source_hash_set_fails(self):
        path = self.output / "inputs.json"
        manifest = json.loads(path.read_text())
        manifest["source_sha256"] = {}
        path.write_text(json.dumps(manifest))
        self.rejected()

    def test_wrong_manifest_source_root_fails(self):
        path = self.output / "inputs.json"
        manifest = json.loads(path.read_text())
        manifest["source_root"] = str(self.repo / "unrelated_mock_source")
        path.write_text(json.dumps(manifest))
        self.rejected()

    def test_collect_cli_boolean_exit_is_not_success(self):
        (self.output / "vendor_exit_code.json").write_text('{"returncode": false}')
        with mock.patch.object(sys, "argv", ["build.py", "--collect", str(self.output)]), redirect_stdout(io.StringIO()):
            try:
                code = builder.main()
            except (ValueError, TypeError):
                return
        self.assertNotEqual(code, 0)

    def test_collect_cli_without_exit_or_prior_result_rejects(self):
        with mock.patch.object(sys, "argv", ["build.py", "--collect", str(self.output)]):
            with self.assertRaisesRegex(ValueError, "actual vendor process exits"):
                builder.main()

    def test_collect_cli_uses_actual_nonzero_exit(self):
        (self.output / "vendor_exit_code.json").write_text('{"returncode": 9}')
        with mock.patch.object(sys, "argv", ["build.py", "--collect", str(self.output)]), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 1)
        self.assertEqual(json.loads((self.output / "result.json").read_text())["vendor_returncode"], 9)

    def test_collect_cli_preserves_legacy_result_exit(self):
        (self.output / "result.json").write_text('{"vendor_returncode": 8}')
        with mock.patch.object(sys, "argv", ["build.py", "--collect", str(self.output)]), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 1)
        self.assertEqual(json.loads((self.output / "initial_vendor_result.json").read_text())["vendor_returncode"], 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
