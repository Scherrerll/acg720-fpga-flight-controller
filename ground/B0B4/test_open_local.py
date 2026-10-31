"""Mock-only launcher tests: no services or serial devices are accessed."""
import sys
import types
import unittest
from unittest.mock import Mock, patch

import open_local as launcher


class LauncherTests(unittest.TestCase):
    def test_existing_receiver_is_reused_without_device_enumeration(self):
        with patch.object(launcher, 'probe', return_value='real') as probe, \
             patch.object(launcher, 'compatible_build', return_value='ok'), \
             patch.object(launcher, 'select_sik', side_effect=AssertionError), \
             patch.object(launcher.subprocess, 'Popen', side_effect=AssertionError):
            self.assertEqual(launcher.run(no_browser=True, connect_sik=True), 0)
            probe.assert_called_once_with(8765)

    def test_normal_mode_never_starts_preview(self):
        for state in ('free', 'preview', 'other'):
            with self.subTest(state=state), patch.object(launcher, 'probe', return_value=state), \
                 patch.object(launcher.subprocess, 'Popen', side_effect=AssertionError):
                self.assertEqual(launcher.run(no_browser=True), 2)

    def test_existing_disabled_receiver_is_not_restarted(self):
        with patch.object(launcher, 'probe', return_value='real'), \
             patch.object(launcher, 'compatible_build', return_value='disabled'), \
             patch.object(launcher.subprocess, 'Popen', side_effect=AssertionError):
            self.assertEqual(launcher.run(no_browser=True, connect_sik=True, enable_xy_pi=True), 2)

    def test_explicit_preview_uses_no_serial(self):
        child = Mock(); child.poll.return_value = None
        with patch.object(launcher, 'probe', side_effect=['free', 'preview']), \
             patch.object(launcher, 'compatible_build', return_value='ok'), \
             patch.object(launcher.subprocess, 'Popen', return_value=child) as popen, \
             patch.object(launcher, 'select_sik', side_effect=AssertionError):
            self.assertEqual(launcher.run(no_browser=True, preview=True), 0)
        command = popen.call_args.args[0]
        self.assertIn('--no-serial', command)
        self.assertNotIn('--enable-xy-pi', command)
        self.assertEqual(command[command.index('--http-port') + 1], '8874')

    def test_sik_enumeration_requires_one_exact_match(self):
        def device(name, vid, pid):
            return types.SimpleNamespace(device=name, vid=vid, pid=pid)
        list_ports = types.ModuleType('serial.tools.list_ports')
        serial = types.ModuleType('serial'); tools = types.ModuleType('serial.tools')
        tools.list_ports = list_ports; serial.tools = tools
        modules = {'serial': serial, 'serial.tools': tools, 'serial.tools.list_ports': list_ports}
        programmer = device('COM2', 0x0403, 0x6014)
        one = device('COM17', 0x0403, 0x6015)
        with patch.dict(sys.modules, modules):
            for ports in ([], [programmer], [one, device('COM18', 0x0403, 0x6015)]):
                list_ports.comports = lambda: ports
                with self.assertRaises(ValueError): launcher.select_sik()
            list_ports.comports = lambda: [programmer, one]
            self.assertEqual(launcher.select_sik(), 'COM17')

    def test_explicit_connect_forwards_build_and_optional_parameter_flag(self):
        for enabled, build in ((False, 'B0B4'), (True, 'B0B4'), (True, 'B0B5')):
            with self.subTest(enabled=enabled, build=build):
                child = Mock(); child.poll.return_value = None
                with patch.object(launcher, 'probe', side_effect=['free', 'real']), \
                     patch.object(launcher, 'select_sik', return_value='COM17'), \
                     patch.object(launcher, 'compatible_build', return_value='ok'), \
                     patch.object(launcher, 'get_json', return_value={'connected': True, 'source': {'port': 'COM17'}}), \
                     patch.object(launcher.subprocess, 'Popen', return_value=child) as popen:
                    self.assertEqual(launcher.run(no_browser=True, connect_sik=True, enable_xy_pi=enabled, xy_pi_build=build), 0)
                command = popen.call_args.args[0]
                self.assertEqual(command[command.index('--port') + 1], 'COM17')
                self.assertEqual(command[command.index('--xy-pi-build') + 1], build)
                self.assertEqual(command[command.index('--logs') + 1],
                                 str(launcher.HERE.parent/'runtime'/build))
                self.assertEqual(command[command.index('--http-port') + 1], '8765')
                self.assertEqual('--enable-xy-pi' in command, enabled)
                self.assertNotIn('--no-serial', command)

    def test_existing_wrong_build_is_refused_even_if_parameters_disabled(self):
        with patch.object(launcher, 'probe', return_value='real'), \
             patch.object(launcher, 'get_json', return_value={'expected_build': '0000B0B5', 'enabled': False}), \
             patch.object(launcher.subprocess, 'Popen', side_effect=AssertionError):
            self.assertEqual(launcher.run(no_browser=True, xy_pi_build='B0B4'), 2)

    def test_preview_forwards_selected_build(self):
        child = Mock(); child.poll.return_value = None
        with patch.object(launcher, 'probe', side_effect=['free', 'preview']), \
             patch.object(launcher, 'compatible_build', return_value='ok'), \
             patch.object(launcher.subprocess, 'Popen', return_value=child) as popen:
            self.assertEqual(launcher.run(no_browser=True, preview=True, xy_pi_build='B0B5'), 0)
        command = popen.call_args.args[0]
        self.assertEqual(command[command.index('--xy-pi-build') + 1], 'B0B5')

    def test_missing_or_ambiguous_sik_never_starts_a_child(self):
        for message in ('发现 0 个', '发现 2 个'):
            with self.subTest(message=message), patch.object(launcher, 'probe', return_value='free'), \
                 patch.object(launcher, 'select_sik', side_effect=ValueError(message)), \
                 patch.object(launcher.subprocess, 'Popen', side_effect=AssertionError):
                self.assertEqual(launcher.run(no_browser=True, connect_sik=True), 2)

    def test_probe_distinguishes_offline_and_real(self):
        state = dict(ui_version=launcher.UI_VERSION, receiver_profile=launcher.PROFILE)
        for port_name, expected in [('offline', 'preview'), ('COM17', 'real')]:
            with patch.object(launcher, 'get_json', return_value={**state, 'source': {'port': port_name}}):
                self.assertEqual(launcher.probe(1), expected)


if __name__ == '__main__':
    unittest.main()
