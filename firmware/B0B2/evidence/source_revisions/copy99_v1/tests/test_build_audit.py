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
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("b0b2_build_audit_tested", ROOT / "tools/build.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)
TOP = builder.TOP

# Shared, deliberately nonprogrammable donor fixture for installer integration.
MOCK_BOOT_RTL = """module acg720_ano_port(input clk50, input pose_valid);
reg [7:0] boot=0;always @(posedge clk50) if(boot!=255) boot<=boot+1'b1;
wire rst_n=boot==255;
reg previous_pose_valid=0;
always @(posedge clk50) if(!rst_n) previous_pose_valid<=0;else previous_pose_valid<=pose_valid;
wire observer_reset=!pose_valid || !previous_pose_valid;
endmodule
"""
MOCK_RESET_VG = """// MOCK STRUCTURE ONLY; NO COMPLETE OR PROGRAMMABLE DESIGN
module acg720_ano_port(input clk50);
LUT4 boot_hi (.F(reset_hi),.I0(boot[4]),.I1(boot[5]),.I2(boot[6]),.I3(boot[7]));
defparam boot_hi.INIT=16'h8000;
LUT4 boot_lo (.F(reset_lo),.I0(boot[0]),.I1(boot[1]),.I2(boot[2]),.I3(boot[3]));
defparam boot_lo.INIT=16'h8000;
LUT4 observer_gate (.F(observer_mock_42),.I0(reset_hi),.I1(reset_lo),.I2(previous_pose_valid),.I3(pose_valid));
defparam observer_gate.INIT=16'h7FFF;
endmodule
"""


def make_mock_donor(build_module, output):
    """Caller supplies a temporary ROOT/source, REPO/baseline and mocked tools."""
    (build_module.ROOT / 'source' / (TOP + '.v')).write_text(MOCK_BOOT_RTL)
    fixture, manifest = build_module.prepare(output, 2, 2, 1)
    netlist = fixture / ('impl/gwsynthesis/' + TOP + '.vg')
    netlist.parent.mkdir(parents=True)
    netlist.write_text(MOCK_RESET_VG)
    (output / 'console.log').write_text('MOCK synthesis\nGowinSynthesis finish\nMOCK later PNR failed\n')
    return fixture, manifest


class BuildAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="b0b2_mock_build_audit_")
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve()
        self.root = self.repo / "firmware/B0B2"
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
        (self.pnr / f"{TOP}.fs").write_text("// UserCode: 0x0000B0B2\nMOCK ONLY -- NOT PROGRAMMABLE\n")
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
        image.write_text('// UserCode: 0x0000B0B20\nMOCK ONLY\n')
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
        self.edit(self.pnr / f"{TOP}.fs", "0x0000B0B2", "0x0000B0B0")
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

    def test_prepare_only_cli_omitted_replicate_defaults_to_zero(self):
        output = self.repo / 'mock_cli_default_replication'
        arguments = ['build.py', '--output', str(output), '--prepare-only']
        with mock.patch.object(sys, 'argv', arguments), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 0)
        manifest = json.loads((output / 'inputs.json').read_text())
        self.assertEqual(manifest['options']['replicate_resources'], 0)
        tcl = (output / 'fixture/build.tcl').read_text()
        self.assertIn('set_option -replicate_resources 0\n', tcl)
        self.assertNotIn('set_option -replicate_resources 1\n', tcl)

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

    def synthesis(self, output=None, boot=False):
        output = output or self.repo / 'mock_synthesis'
        if boot:
            (self.source / (TOP + '.v')).write_text(MOCK_BOOT_RTL)
        fixture, manifest = builder.prepare(output, 2, 2, 0, synthesis_only=True)
        vg = fixture / ('impl/gwsynthesis/' + TOP + '.vg')
        vg.parent.mkdir(parents=True)
        vg.write_text(MOCK_RESET_VG if boot else '// MOCK ONLY; NOT PROGRAMMABLE\n')
        (output / 'console.log').write_text('MOCK synthesis\nGowinSynthesis finish\n')
        builder.write_json(output / 'vendor_exit_code.json', dict(returncode=0))
        return output, fixture, manifest

    def collect_synthesis(self, output, returncode=0):
        with redirect_stdout(io.StringIO()):
            return builder.collect_synthesis(output, returncode)

    def derived(self, synthesis_only=False):
        donor = self.repo / 'mock_donor'
        if synthesis_only:
            self.synthesis(donor, boot=True)
            self.collect_synthesis(donor)
        else:
            make_mock_donor(builder, donor)
        previous_pnr = self.pnr
        self.output = self.repo / 'mock_derived'
        self.fixture, self.inputs = builder.prepare(self.output, 2, 2, 1, donor, True)
        self.pnr = self.fixture / 'impl/pnr'
        shutil.copytree(previous_pnr, self.pnr)
        (self.output / 'console.log').write_text('Placement and routing completed\nBitstream generation completed\n')
        with (self.pnr / (TOP + '.rpt.txt')).open('a') as stream:
            stream.write('6. Global Clock Signals\n observer_mock_42 | LW | -\n')
        (self.pnr / 'cmd.do').write_text(
            f'-d {self.fixture / ("impl/gwsynthesis/" + TOP + ".vg")}\n'
            f'-cst {self.fixture / (TOP + ".cst")}\n-sdc {self.fixture / (TOP + ".sdc")}\n')
        return donor

    def save_manifest(self):
        builder.write_json(self.output / 'inputs.json', self.inputs)

    def rebind_file(self, name):
        self.inputs['source_sha256'][name] = builder.sha(self.fixture / name)
        self.save_manifest()

    def test_failed_routing_proof_is_not_established(self):
        result = self.collect(7)
        self.assertFalse(result['routing_passed'])
        self.assertIn('not established', result['routing_status_proof'])

    def test_derived_complete_chain_preserves_logical_source_and_requires_global(self):
        donor = self.derived()
        result = self.collect()
        self.assertTrue(result['passed'])
        self.assertEqual(result['observer_global_assignment'], 'LW')
        self.assertEqual(self.inputs['derived_netlist']['observer_reset']['net'], 'observer_mock_42')
        self.assertEqual(self.inputs['logical_source_sha256'], builder.source_hashes(self.source))
        differences = {k for k,v in self.inputs['source_sha256'].items() if v != self.inputs['logical_source_sha256'][k]}
        self.assertEqual(differences, {'build.tcl', TOP + '.cst', TOP + '.gprj'})
        self.assertEqual(builder.sha(self.fixture / ('impl/gwsynthesis/' + TOP + '.vg')),
                         builder.sha(donor / ('fixture/impl/gwsynthesis/' + TOP + '.vg')))
        self.assertNotIn('CLOCK_LOC', (self.source / (TOP + '.cst')).read_text())
        self.assertEqual((self.fixture / (TOP + '.gprj')).read_bytes(), builder.netlist_project(self.source))
        refs = builder.ET.parse(self.fixture / (TOP + '.gprj')).findall('.//File')
        self.assertEqual([(x.attrib['path'],x.attrib['type'],x.attrib['enable']) for x in refs],
                         [('impl/gwsynthesis/' + TOP + '.vg','file.netlist','1'),
                          (TOP + '.cst','file.cst','1'),(TOP + '.sdc','file.sdc','1')])

    def test_derived_missing_actual_global_assignment_fails(self):
        self.derived()
        self.edit(self.pnr / (TOP + '.rpt.txt'), ' observer_mock_42 | LW | -\n', '')
        result = self.collect()
        self.assertFalse(result['passed'])
        self.assertFalse(result['observer_global_contract_passed'])

    def test_pnr_donor_and_global_flags_must_be_paired(self):
        for donor, glob in ((None, True), (self.output, False)):
            with self.subTest(donor=donor, glob=glob), self.assertRaises(ValueError):
                builder.prepare(self.repo / 'bad_flags', 2, 2, 1, donor, glob)

    def test_donor_requires_completed_synthesis(self):
        donor = self.repo / 'mock_donor'
        make_mock_donor(builder, donor)
        (donor / 'console.log').write_text('MOCK synthesis still running\n')
        with self.assertRaisesRegex(ValueError, 'completed donor synthesis'):
            builder.prepare(self.repo / 'mock_derived', 2, 2, 1, donor, True)

    def test_wrong_and_nand_boot_bits_or_ambiguous_structure_fail(self):
        donor = self.repo / 'mock_donor'
        make_mock_donor(builder, donor)
        vg = donor / ('fixture/impl/gwsynthesis/' + TOP + '.vg')
        cases = [MOCK_RESET_VG.replace("boot_hi.INIT=16'h8000", "boot_hi.INIT=16'h8001"),
                 MOCK_RESET_VG.replace("observer_gate.INIT=16'h7FFF", "observer_gate.INIT=16'h7FFE"),
                 MOCK_RESET_VG.replace('.I3(boot[7])', '.I3(boot[6])'),
                 MOCK_RESET_VG.replace('endmodule', 'LUT4 second_gate (.F(other_net),.I0(reset_hi),.I1(reset_lo),.I2(previous_pose_valid),.I3(pose_valid));\ndefparam second_gate.INIT=16\'h7FFF;\nendmodule')]
        for index, text in enumerate(cases):
            with self.subTest(index=index):
                vg.write_text(text)
                with self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
                    builder.prepare(self.repo / ('bad_structure_' + str(index)), 2, 2, 1, donor, True)

    def test_unexpected_logical_boot_definition_fails(self):
        donor = self.repo / 'mock_donor'
        make_mock_donor(builder, donor)
        self.edit(self.source / (TOP + '.v'), 'boot!=255', 'boot!=254')
        with self.assertRaisesRegex(ValueError, 'logical boot'):
            builder.observer_reset(donor / ('fixture/impl/gwsynthesis/' + TOP + '.vg'), self.source)

    def test_changed_donor_source_or_runner_fails(self):
        donor = self.derived()
        self.edit(donor / 'build_runner.py', 'import argparse', 'import argparse # MOCK TAMPER')
        self.rejected()

    def test_changed_donor_input_receipt_fails(self):
        donor = self.derived()
        path = donor / 'inputs.json'
        value = json.loads(path.read_text());value['created_utc'] = 'changed'
        builder.write_json(path, value)
        self.rejected()

    def test_changed_donor_or_copied_vg_fails(self):
        donor = self.derived()
        copy = self.fixture / ('impl/gwsynthesis/' + TOP + '.vg')
        original = copy.read_bytes()
        copy.write_bytes(original + b'// changed copied VG\n')
        self.rejected()
        copy.write_bytes(original)
        (donor / ('fixture/impl/gwsynthesis/' + TOP + '.vg')).write_bytes(original + b'// changed donor VG\n')
        self.rejected()

    def test_changed_synthesis_prefix_fails(self):
        self.derived()
        path = self.output / 'donor_synthesis.log'
        path.write_bytes(path.read_bytes() + b'changed\n')
        self.rejected()

    def test_unknown_schema_missing_logical_map_or_chained_provenance_fail(self):
        donor = self.derived()
        original = json.loads(json.dumps(self.inputs))
        for field in ('schema', 'unknown_key', 'logical_map'):
            with self.subTest(field=field):
                self.inputs = json.loads(json.dumps(original))
                if field == 'schema':self.inputs['derived_netlist']['schema'] = 'unknown'
                elif field == 'unknown_key':self.inputs['derived_netlist']['arbitrary_exception'] = True
                else:self.inputs.pop('logical_source_sha256')
                self.save_manifest();self.rejected()
        value = json.loads((donor / 'inputs.json').read_text());value['derived_netlist'] = {'schema':'unknown'}
        builder.write_json(donor / 'inputs.json', value)
        with self.assertRaisesRegex(ValueError, 'Chained'):
            builder.prepare(self.repo / 'chained', 2, 2, 1, donor, True)

    def test_tampered_proof_cannot_allow_arbitrary_global(self):
        self.derived()
        self.inputs['derived_netlist']['observer_reset']['net'] = 'arbitrary'
        self.save_manifest()
        self.rejected()

    def test_extra_or_wrong_global_or_pin_with_rebound_physical_hash_fails(self):
        self.derived()
        path = self.fixture / (TOP + '.cst');original = path.read_bytes()
        cases = [original + b'CLOCK_LOC "other_net" BUFG = CE|SR|LOGIC;\n',
                 original.replace(b'"observer_mock_42"', b'"other_net"'),
                 original.replace(b'"clk50" MOCK0;', b'"clk50" OTHER;')]
        for index, data in enumerate(cases):
            with self.subTest(index=index):
                path.write_bytes(data);self.rebind_file(TOP + '.cst');self.rejected()

    def test_run_all_or_arbitrary_tcl_with_rebound_hash_fails(self):
        self.derived()
        path = self.fixture / 'build.tcl';original = path.read_text()
        for text in (original.replace('run pnr', 'run all'), original + 'set_option -retime 1\n'):
            with self.subTest(text=text):
                path.write_text(text);self.rebind_file('build.tcl');self.rejected()

    def test_derived_rtl_or_extra_include_project_with_rebound_hash_fails(self):
        self.derived()
        path = self.fixture / (TOP + '.gprj');original = path.read_text()
        cases = [original.replace('file.netlist', 'file.verilog'),
                 original.replace('</FileList>', '<File path="extra.v" type="file.verilog" enable="1"/></FileList>'),
                 original.replace('</FileList>', '<File path="extra.vh" type="file.include" enable="1"/></FileList>')]
        for index, text in enumerate(cases):
            with self.subTest(index=index):
                path.write_text(text);self.rebind_file(TOP + '.gprj');self.rejected()

    def test_netlist_project_preserves_device_and_other_metadata(self):
        path = self.source / (TOP + '.gprj')
        self.edit(path, '<Project>', '<Project><Template>FPGA</Template><Version>5</Version><Device name="MOCK" pn="MOCK-PART">mock-id</Device>')
        project = builder.ET.fromstring(builder.netlist_project(self.source))
        self.assertEqual(project.find('Template').text, 'FPGA')
        self.assertEqual(project.find('Version').text, '5')
        self.assertEqual(project.find('Device').attrib, dict(name='MOCK',pn='MOCK-PART'))
        self.assertEqual(project.find('Device').text, 'mock-id')

    def test_derived_console_synthesis_evidence_prevents_acceptance(self):
        self.derived()
        path = self.output / 'console.log';original = path.read_text()
        for marker in ('GowinSynthesis start', 'GowinSynthesis finish', "Compiling module 'MOCK'", 'Running netlist conversion'):
            with self.subTest(marker=marker):
                path.write_text(original + marker + '\n')
                result = self.collect()
                self.assertFalse(result['passed'])
                self.assertFalse(result['pnr_only_synthesis_absent'])

    def test_cancelled_build_never_accepted(self):
        (self.output / 'CANCELLED.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Cancelled'):
            self.collect()

    def test_synthesis_only_prepare_cli_has_explicit_mode_and_only_run_syn(self):
        output = self.repo / 'mock_cli_syn'
        arguments = ['build.py', '--output', str(output), '--prepare-only', '--synthesis-only']
        with mock.patch.object(sys, 'argv', arguments), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 0)
        manifest = json.loads((output / 'inputs.json').read_text())
        self.assertEqual(manifest['build_mode'], 'synthesis-only')
        tcl = (output / 'fixture/build.tcl').read_text()
        self.assertEqual([x for x in tcl.splitlines() if x.startswith('run ')], ['run syn'])
        self.assertEqual(builder.verify_current_source(output / 'fixture', manifest), self.pins)
        self.assertFalse((output / 'result.json').exists())
        self.assertFalse((output / 'synthesis_result.json').exists())

    def test_synthesis_only_and_each_derived_flag_reject_before_copy(self):
        for index, (donor, glob) in enumerate(((self.output, False), (None, True), (self.output, True))):
            with self.subTest(donor=donor, glob=glob):
                output = self.repo / ('bad_syn_flags_' + str(index))
                with self.assertRaisesRegex(ValueError, 'mutually exclusive'):
                    builder.prepare(output, 2, 2, 0, donor, glob, True)
                self.assertFalse(output.exists())
        for extra in (['--pnr-only-from', str(self.output)], ['--global-observer-reset']):
            arguments = ['build.py', '--synthesis-only', '--prepare-only', *extra]
            with mock.patch.object(sys, 'argv', arguments), self.assertRaisesRegex(ValueError, 'mutually exclusive'):
                builder.main()

    def test_missing_none_full_modes_compatible_unknown_modes_rejected(self):
        for mode in (None, 'full'):
            with self.subTest(mode=mode):
                self.inputs['build_mode'] = mode
                self.save_manifest()
                self.assertTrue(self.collect()['passed'])
        for mode in ('pnr-only', 'syn', '', 0, False, ['full']):
            with self.subTest(mode=mode):
                self.inputs['build_mode'] = mode
                self.save_manifest()
                with self.assertRaisesRegex(ValueError, 'Unknown build mode'):
                    self.collect()

    def test_mode_must_match_exact_tcl_even_with_rebound_hash(self):
        output, fixture, manifest = self.synthesis()
        tcl = fixture / 'build.tcl'
        original = tcl.read_text()
        for run in ('all', 'pnr'):
            with self.subTest(run=run):
                tcl.write_text(original.replace('run syn', 'run ' + run))
                manifest['source_sha256']['build.tcl'] = builder.sha(tcl)
                with self.assertRaisesRegex(ValueError, 'Build Tcl'):
                    builder.verify_current_source(fixture, manifest)
        self.inputs['build_mode'] = 'synthesis-only'
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'Build Tcl'):
            builder.verify_current_source(self.fixture, self.inputs)

    def test_synthesis_only_never_receives_physical_acceptance_with_complete_pnr(self):
        self.inputs['build_mode'] = 'synthesis-only'
        tcl = self.fixture / 'build.tcl'
        tcl.write_text(builder.build_tcl(self.inputs['options'], synthesis_only=True))
        self.rebind_file('build.tcl')
        builder.verify_current_source(self.fixture, self.inputs)
        with self.assertRaisesRegex(ValueError, 'cannot receive physical acceptance'):
            self.collect()
        self.assertFalse((self.output / 'result.json').exists())

    def test_synthesis_receipt_success_binds_all_artifacts_without_physical_result(self):
        output, fixture, manifest = self.synthesis()
        result = self.collect_synthesis(output)
        self.assertIs(result['synthesis_passed'], True)
        self.assertIs(result['physical_acceptance'], False)
        self.assertNotIn('passed', result)
        self.assertEqual(result['source_sha256'], manifest['source_sha256'])
        self.assertEqual(result['runner_sha256'], builder.sha(output / 'build_runner.py'))
        self.assertEqual(result['console_sha256'], builder.sha(output / 'console.log'))
        self.assertEqual(result['inputs_sha256'], builder.sha(output / 'inputs.json'))
        self.assertEqual(result['vendor_exit_sha256'], builder.sha(output / 'vendor_exit_code.json'))
        self.assertEqual(result['netlist']['sha256'], builder.sha(fixture / result['netlist']['path']))
        self.assertEqual(builder.verify_synthesis_result(output), result)
        for name in ('result.json', 'offline_acceptance.json'):
            self.assertFalse((output / name).exists())

    def test_synthesis_vendor_exit_requires_matching_real_integer(self):
        output, _, _ = self.synthesis()
        for value in (False, None, 0.0, '0'):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'integer'):
                    self.collect_synthesis(output, value)
        builder.write_json(output / 'vendor_exit_code.json', dict(returncode=False))
        with self.assertRaisesRegex(ValueError, 'integer'):
            self.collect_synthesis(output)
        builder.write_json(output / 'vendor_exit_code.json', dict(returncode=8))
        with self.assertRaisesRegex(ValueError, 'actual integer'):
            self.collect_synthesis(output)
        self.assertFalse(self.collect_synthesis(output, 8)['synthesis_passed'])
        with self.assertRaisesRegex(ValueError, 'unsuccessful'):
            builder.verify_synthesis_result(output)

    def test_synthesis_error_missing_duplicate_finish_or_empty_vg_never_succeed(self):
        cases = [('MOCK ERROR before finish\nGowinSynthesis finish\n', 'VG'),
                 ('GowinSynthesis finish\nERROR after finish\n', 'VG'),
                 ('GowinSynthesis start\n', 'VG'),
                 ('GowinSynthesis finish\nGowinSynthesis finish\n', 'VG'),
                 ('MOCK GowinSynthesis finish suffix\n', 'VG'),
                 ('GowinSynthesis finish\n', '')]
        for index, (console, vg) in enumerate(cases):
            with self.subTest(index=index):
                output, fixture, _ = self.synthesis(self.repo / ('bad_syn_' + str(index)))
                (output / 'console.log').write_text(console)
                (fixture / ('impl/gwsynthesis/' + TOP + '.vg')).write_text(vg)
                self.assertIs(self.collect_synthesis(output)['synthesis_passed'], False)
                with self.assertRaisesRegex(ValueError, 'unsuccessful'):
                    builder.verify_synthesis_result(output)

    def test_synthesis_missing_vg_fails(self):
        output, fixture, _ = self.synthesis()
        (fixture / ('impl/gwsynthesis/' + TOP + '.vg')).unlink()
        self.assertIs(self.collect_synthesis(output)['synthesis_passed'], False)

    def test_synthesis_receipt_detects_each_bound_artifact_drift(self):
        names = ['inputs.json', 'build_runner.py', 'vendor_exit_code.json', 'console.log',
                 'fixture/impl/gwsynthesis/' + TOP + '.vg', 'fixture/' + TOP + '.v']
        for index, name in enumerate(names):
            with self.subTest(name=name):
                output, _, _ = self.synthesis(self.repo / ('drift_syn_' + str(index)))
                self.collect_synthesis(output)
                path = output / name
                path.write_bytes(path.read_bytes() + b'\n ')
                with self.assertRaises((ValueError, OSError)):
                    builder.verify_synthesis_result(output)

    def test_synthesis_receipt_rejects_unknown_fields_and_boolean_number_substitution(self):
        output, _, _ = self.synthesis()
        result = self.collect_synthesis(output)
        for key, value in (('unknown', True), ('physical_acceptance', 0), ('synthesis_passed', 1)):
            with self.subTest(key=key):
                changed = dict(result)
                changed[key] = value
                builder.write_json(output / 'synthesis_result.json', changed)
                with self.assertRaisesRegex(ValueError, 'Invalid'):
                    builder.verify_synthesis_result(output)

    def test_collect_synthesis_rejects_full_derived_and_cancelled_modes(self):
        with self.assertRaisesRegex(ValueError, 'requires synthesis-only'):
            self.collect_synthesis(self.output)
        output, _, _ = self.synthesis()
        (output / 'CANCELLED.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Cancelled'):
            self.collect_synthesis(output)
        self.derived()
        self.inputs['build_mode'] = 'synthesis-only'
        with self.assertRaisesRegex(ValueError, 'cannot use a derived'):
            builder.verify_current_source(self.fixture, self.inputs)

    def test_collect_cli_synthesis_only_uses_separate_receipt(self):
        output, _, _ = self.synthesis()
        arguments = ['build.py', '--collect', str(output)]
        with mock.patch.object(sys, 'argv', arguments), redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(), 0)
        self.assertTrue(json.loads((output / 'synthesis_result.json').read_text())['synthesis_passed'])
        self.assertFalse((output / 'result.json').exists())

    def test_collect_cli_synthesis_requires_actual_exit_even_with_physical_result(self):
        output, _, _ = self.synthesis()
        (output / 'vendor_exit_code.json').unlink()
        builder.write_json(output / 'result.json', dict(passed=True, vendor_returncode=0))
        with mock.patch.object(sys, 'argv', ['build.py', '--collect', str(output)]):
            with self.assertRaisesRegex(ValueError, 'actual vendor process exits'):
                builder.main()

    def test_synthesis_only_mocked_vendor_path_collects_without_physical_result(self):
        output = self.repo / 'mock_vendor_syn'
        def mock_vendor(arguments, cwd, stdout, stderr):
            self.assertEqual(arguments, [str(builder.GOWIN), 'build.tcl'])
            self.assertTrue((cwd / 'build.tcl').read_text().endswith('run syn\nexit\n'))
            vg = cwd / ('impl/gwsynthesis/' + TOP + '.vg')
            vg.parent.mkdir(parents=True)
            vg.write_text('// MOCK NETLIST ONLY\n')
            stdout.write('MOCK synthesis\nGowinSynthesis finish\n')
            return mock.Mock(returncode=0)
        arguments = ['build.py', '--output', str(output), '--synthesis-only']
        with mock.patch.object(builder.subprocess, 'run', side_effect=mock_vendor) as run:
            with mock.patch.object(sys, 'argv', arguments), redirect_stdout(io.StringIO()):
                self.assertEqual(builder.main(), 0)
        run.assert_called_once()
        self.assertTrue(builder.verify_synthesis_result(output)['synthesis_passed'])
        self.assertFalse((output / 'result.json').exists())

    def test_completed_synthesis_only_donor_supports_strict_physical_derived(self):
        donor = self.derived(synthesis_only=True)
        self.assertEqual(self.inputs['derived_netlist']['donor_synthesis_result_sha256'],
                         builder.sha(donor / 'synthesis_result.json'))
        self.assertTrue(self.collect()['passed'])

    def test_synthesis_only_donor_requires_successful_bound_receipt(self):
        donor, _, _ = self.synthesis(self.repo / 'mock_syn_donor', boot=True)
        with self.assertRaises(FileNotFoundError):
            builder.prepare(self.repo / 'derived_without_syn_receipt', 2, 2, 0, donor, True)
        self.collect_synthesis(donor)
        path = donor / 'synthesis_result.json'
        result = json.loads(path.read_text())
        result['synthesis_passed'] = False
        builder.write_json(path, result)
        with self.assertRaisesRegex(ValueError, 'unsuccessful'):
            builder.prepare(self.repo / 'derived_failed_syn_receipt', 2, 2, 0, donor, True)

    def test_derived_synthesis_only_donor_receipt_binding_is_required_and_immutable(self):
        donor = self.derived(synthesis_only=True)
        digest = self.inputs['derived_netlist'].pop('donor_synthesis_result_sha256')
        self.save_manifest()
        self.rejected()
        self.inputs['derived_netlist']['donor_synthesis_result_sha256'] = digest
        self.save_manifest()
        path = donor / 'synthesis_result.json'
        path.write_bytes(path.read_bytes() + b'\n')
        self.rejected()

    def test_full_donor_cannot_claim_synthesis_only_receipt_exception(self):
        self.derived()
        self.inputs['derived_netlist']['donor_synthesis_result_sha256'] = '0' * 64
        self.save_manifest()
        self.rejected()


if __name__ == "__main__":
    unittest.main(verbosity=2)
