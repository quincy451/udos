from __future__ import annotations

import os
import inspect
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import vice_prg_probe as vp
import run_action_command_probe as command_probe
import run_action_alink_seeded_runtime_probe as seeded_alink_probe


class TestViceProbeArgNormalization(unittest.TestCase):
    def test_seeded_alink_probe_allows_slow_host_completion(self) -> None:
        self.assertGreaterEqual(seeded_alink_probe.FINAL_TIMEOUT, 90.0)
        self.assertIn("final_timeout", inspect.signature(seeded_alink_probe.run_once).parameters)
        makefile = (ROOT / "Makefile").read_text(encoding="ascii")
        target = makefile.split("vice-action-alink:", 1)[1].split("vice-action-alink-prg:", 1)[0]
        self.assertIn("--final-timeout 120", target)

    def test_direct_tool_workflow_allows_slow_compile_link_chain(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="ascii")
        target = makefile.split("vice-action-tool-workflow:", 1)[1].split(
            "vice-action-actedit-overlay:", 1
        )[0]
        self.assertIn("--shell-timeout 300", target)

    def test_command_probe_allows_transient_ready_during_autostart(self) -> None:
        client = mock.Mock()
        screens = ["READY.\n", "A:D64/>\n"]
        with mock.patch.object(command_probe, "screen_text_for_fragment", side_effect=screens):
            with mock.patch.object(command_probe.time, "monotonic", side_effect=(0.0, 0.0, 0.1)):
                with mock.patch.object(command_probe.time, "sleep"):
                    screen = command_probe.wait_for_active_prompt(
                        client,
                        "A:D64/>",
                        1.0,
                        allow_transient_ready=True,
                    )

        self.assertEqual(screen, "A:D64/>\n")

    def test_command_probe_still_rejects_ready_after_launch(self) -> None:
        client = mock.Mock()
        with mock.patch.object(command_probe, "screen_text_for_fragment", return_value="READY.\n"):
            with mock.patch.object(command_probe.time, "monotonic", side_effect=(0.0, 0.0)):
                with self.assertRaisesRegex(vp.ViceError, "escaped to READY"):
                    command_probe.wait_for_active_prompt(client, "A:D64/>", 1.0)

    def test_command_probe_waits_for_live_prompt_with_reused_fragment(self) -> None:
        client = mock.Mock()
        screens = [
            "COPIED\n  B:DNP/> COPY MAIN.ACT BIG1.ACT\n",
            "COPIED\n  B:DNP/>\n",
        ]
        with mock.patch.object(command_probe, "screen_text_for_fragment", side_effect=screens):
            with mock.patch.object(command_probe.time, "monotonic", side_effect=(0.0, 0.0, 0.1)):
                with mock.patch.object(command_probe.time, "sleep"):
                    screen = command_probe.wait_for_active_prompt_and_fragments(
                        client,
                        "B:DNP/>",
                        ["COPIED"],
                        1.0,
                    )

        self.assertEqual(screen, screens[-1])

    def test_command_probe_parses_raw_key_code_sequences(self) -> None:
        self.assertEqual(
            command_probe.parse_key_codes("0x58, 0x11, 0x85, 3"),
            [0x58, 0x11, 0x85, 0x03],
        )

    def test_command_probe_sends_high_raw_key_codes_without_ascii_encoding(self) -> None:
        client = mock.Mock()
        with mock.patch.object(command_probe, "wait_for_keyboard_idle"):
            with mock.patch.object(command_probe.time, "sleep"):
                command_probe.send_key_codes(client, [0x58, 0x85, 0x03], 1.0)

        self.assertIn(mock.call(vp.KEYBUF_DATA, b"\x85"), client.memory_set.call_args_list)
        self.assertEqual(client.memory_set.call_args_list[-2:], [
            mock.call(vp.KEYBUF_DATA, b"\x03"),
            mock.call(vp.KEYBUF_COUNT, b"\x01"),
        ])

    def write_probe_binary(self, text: str) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "x64sc-probe.bin"
        path.write_bytes(text.encode("ascii"))
        return path

    def test_keeps_legacy_options_for_legacy_binary(self) -> None:
        executable = self.write_probe_binary("-iecdevice9\n-device9\n-virtualdev9\n")
        args = ["-iecdevice9", "-device9", "1", "-virtualdev9"]
        self.assertEqual(vp.normalize_vice_args_for_executable(executable, args), args)

    def test_rewrites_renamed_windows_vice_options(self) -> None:
        executable = self.write_probe_binary("-busdevice9\n-devicebackend9\n-trapdevice9\n")
        args = [
            "-iecdevice8",
            "-device8",
            "1",
            "+iecdevice9",
            "+device9",
            "-virtualdev9",
            "-fs9",
            "C:\\VICEFS",
        ]
        self.assertEqual(
            vp.normalize_vice_args_for_executable(executable, args),
            [
                "-busdevice8",
                "-devicebackend8",
                "1",
                "+busdevice9",
                "+devicebackend9",
                "-trapdevice9",
                "-fs9",
                "C:\\VICEFS",
            ],
        )

    def test_enables_virtual_device_for_legacy_filesystem_backend(self) -> None:
        executable = self.write_probe_binary("-iecdevice9\n-device9\n-virtualdev9\n")
        args = ["-iecdevice9", "-device9", "1", "-fs9", "C:\\VICEFS"]
        self.assertEqual(
            vp.normalize_vice_args_for_executable(
                executable,
                vp.enable_virtual_devices_for_filesystem_args(args),
            ),
            ["-iecdevice9", "-device9", "1", "-fs9", "C:\\VICEFS", "-virtualdev9"],
        )

    def test_enables_trap_device_for_windows_filesystem_backend(self) -> None:
        executable = self.write_probe_binary("-busdevice9\n-devicebackend9\n-trapdevice9\n")
        args = ["-iecdevice9", "-device9", "1", "-fs9", "C:\\VICEFS"]
        self.assertEqual(
            vp.normalize_vice_args_for_executable(
                executable,
                vp.enable_virtual_devices_for_filesystem_args(args),
            ),
            ["-busdevice9", "-devicebackend9", "1", "-fs9", "C:\\VICEFS", "-trapdevice9"],
        )

    def test_locate_x64sc_honors_env_override(self) -> None:
        executable = self.write_probe_binary("vice-probe")
        with mock.patch.dict(os.environ, {"VICE_X64SC": str(executable)}):
            self.assertEqual(vp.locate_x64sc(), executable.resolve())

    def test_locate_x64sc_prefers_native_windows_candidate(self) -> None:
        native = Path(r"C:\c64\vice\GTK3VICE-3.10-win64\bin\x64sc.exe")

        def fake_is_file(path: Path) -> bool:
            return path == native

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(Path, "is_file", autospec=True, side_effect=fake_is_file):
                with mock.patch.object(vp.shutil, "which", return_value=None):
                    self.assertEqual(vp.locate_x64sc(), native.resolve())

    def test_default_connect_delay_uses_windows_binary(self) -> None:
        with mock.patch.object(vp, "locate_x64sc", return_value=Path("C:/VICE/x64sc.exe")):
            self.assertEqual(vp.default_connect_delays(), (8.0, 10.0, 12.0, 15.0))
            self.assertEqual(vp.default_connect_delay(), 8.0)
            self.assertEqual(vp.default_attempt_delay(), 5.0)

    def test_default_connect_delay_uses_linux_binary(self) -> None:
        with mock.patch.object(vp, "locate_x64sc", return_value=Path("/usr/bin/x64")):
            with mock.patch.object(vp, "display_is_usable", return_value=True):
                self.assertEqual(vp.default_connect_delays(), (11.0, 9.0, 13.0, 10.0, 14.0, 12.0))
                self.assertEqual(vp.default_connect_delay(), 11.0)
                self.assertEqual(vp.default_attempt_delay(), 2.0)

    def test_default_connect_delay_uses_headless_linux_xvfb(self) -> None:
        with mock.patch.object(vp, "locate_x64sc", return_value=Path("/usr/bin/x64")):
            with mock.patch.object(vp, "display_is_usable", return_value=False):
                with mock.patch.object(vp, "locate_xvfb_run", return_value=Path("/usr/bin/xvfb-run")):
                    self.assertEqual(vp.default_connect_delays(), (20.0, 24.0, 28.0, 32.0))
                    self.assertEqual(vp.default_connect_delay(), 20.0)
                    self.assertEqual(vp.default_attempt_delay(), 4.0)

    def test_launch_vice_uses_xvfb_run_for_headless_linux(self) -> None:
        popen = mock.Mock()
        with mock.patch.object(vp, "locate_x64sc", return_value=Path("/usr/bin/x64sc")):
            with mock.patch.object(vp, "locate_xvfb_run", return_value=Path("/usr/bin/xvfb-run")):
                with mock.patch.object(vp, "display_is_usable", return_value=False):
                    with mock.patch.object(vp.subprocess, "Popen", return_value=popen) as popen_mock:
                        vp.launch_vice(Path("/tmp/test.d64"), 6502)
        cmd = popen_mock.call_args.args[0]
        self.assertEqual(Path(cmd[0]).as_posix(), "/usr/bin/xvfb-run")
        self.assertEqual(cmd[1:4], ["-a", "-s", "-screen 0 1024x768x24"])
        self.assertIn(Path("/usr/bin/x64sc").as_posix(), [Path(part).as_posix() for part in cmd])

    def test_locate_x64sc_prefers_x64sc_path_on_non_windows(self) -> None:
        with mock.patch.object(vp, "os") as os_mock:
            os_mock.name = "posix"
            os_mock.environ = {}
            with mock.patch.object(
                vp.shutil,
                "which",
                side_effect=lambda name: "/usr/bin/x64" if name == "x64" else "/usr/bin/x64sc",
            ):
                self.assertTrue(vp.locate_x64sc().as_posix().endswith("/usr/bin/x64sc"))

    def test_main_cleans_up_stale_vice_before_probe_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            disk = Path(tmpdir) / "test.d64"
            disk.write_bytes(b"disk")
            with mock.patch.object(vp, "cleanup_stale_vice") as cleanup_mock:
                with mock.patch.object(vp, "default_connect_delays", return_value=(0.0,)):
                    with mock.patch.object(vp, "run_probe", return_value="A:D64/>"):
                        rc = vp.main(["--disk", str(disk), "--expected", "A:D64/>", "--attempt-delay", "2.5"])
        self.assertEqual(rc, 0)
        cleanup_mock.assert_called_once_with(settle_seconds=2.5)

    def test_wait_for_screen_reports_fragment_and_last_screen_on_early_exit(self) -> None:
        process = mock.Mock()
        process.poll.side_effect = [None, 1]
        process.communicate.return_value = ("out text", "err text")
        client = mock.Mock()

        with mock.patch.object(
            vp,
            "read_screen_text_for_fragment",
            return_value=("last visible screen", 0x18, 0x17),
        ):
            with mock.patch.object(vp.time, "sleep", return_value=None):
                with self.assertRaises(vp.ViceError) as raised:
                    vp.wait_for_screen_and_state(
                        client,
                        process,
                        "READY>",
                        marker_addr=None,
                        marker_value=None,
                        extra_checks=[],
                        timeout=1.0,
                    )

        message = str(raised.exception)
        self.assertIn("screen text 'READY>'", message)
        self.assertIn("last VIC state: D018=0x18 DD00=0x17", message)
        self.assertIn("last visible screen", message)
        self.assertIn("out text", message)
        self.assertIn("err text", message)

    def test_wait_for_screen_reports_state_byte_mismatches_on_timeout(self) -> None:
        process = mock.Mock()
        process.poll.return_value = None
        client = mock.Mock()
        client.memory_get.return_value = b"\x03"
        client.registers_get.return_value = {}

        with mock.patch.object(
            vp,
            "read_screen_text_for_fragment",
            return_value=("READY>", 0x18, 0x17),
        ):
            with mock.patch.object(vp.time, "monotonic", side_effect=(0.0, 0.0, 2.0)):
                with mock.patch.object(vp.time, "sleep", return_value=None):
                    with self.assertRaises(vp.ViceError) as raised:
                        vp.wait_for_screen_and_state(
                            client,
                            process,
                            "READY>",
                            marker_addr=None,
                            marker_value=None,
                            extra_checks=[(0x1234, 0x02)],
                            timeout=1.0,
                        )

        self.assertIn(
            "State mismatches: 0x1234: expected 0x02, got 0x03",
            str(raised.exception),
        )

    def test_format_udos_launch_trace_reads_expected_bytes(self) -> None:
        client = mock.Mock()
        values = {addr: b"\x00" for _label, addr in vp.UDOS_LAUNCH_DEBUG_BYTES}
        values.update(
            {
                0x03F0: b"\x01",
                0x03F1: b"\x00",
                0x03F2: b"\xF3",
                0x03F3: b"\xC3",
            }
        )

        def fake_memory_get(start: int, end: int, *, memspace: int = 0, bank: int = 0) -> bytes:
            self.assertEqual(start, end)
            self.assertEqual(memspace, 0)
            self.assertEqual(bank, 0)
            return values[start]

        client.memory_get.side_effect = fake_memory_get
        text = vp.format_udos_launch_trace(client)
        self.assertIn("TOOL_DEBUG0=0x00@0x03D0", text)
        self.assertIn("LAUNCH_RESULT_FLAG=0x01@0x03F0", text)
        self.assertIn("LAUNCH_EXIT_STATUS=0x00@0x03F1", text)
        self.assertIn("LAUNCH_TRACE_STAGE=0xF3@0x03F2", text)
        self.assertIn("LAUNCH_TRACE_CODE=0xC3@0x03F3", text)

    def test_read_active_screen_text_falls_back_to_default_screen_when_vic_regs_invalid(self) -> None:
        client = mock.Mock()

        def fake_memory_get(start: int, end: int, *, memspace: int = 0, bank: int = 0) -> bytes:
            if (start, end) == (0xD018, 0xD018):
                self.assertEqual((memspace, bank), (vp.MAIN_MEMSPACE, vp.MAIN_BANK_IO))
                return b"\xFF"
            if (start, end) == (0xDD00, 0xDD00):
                self.assertEqual((memspace, bank), (vp.MAIN_MEMSPACE, vp.MAIN_BANK_IO))
                return b"\xFF"
            if (start, end) == (0x0400, 0x07E7):
                self.assertEqual((memspace, bank), (vp.MAIN_MEMSPACE, vp.MAIN_BANK_RAM))
                data = bytearray(b"\x20" * 1000)
                data[0] = 1  # a
                data[1] = 2  # b
                return bytes(data)
            self.fail(f"unexpected memory_get range {(start, end)}")

        client.memory_get.side_effect = fake_memory_get
        text, d018, dd00 = vp.read_active_screen_text(client)
        self.assertEqual((d018, dd00), (0xFF, 0xFF))
        self.assertIn("ab", text)


if __name__ == "__main__":
    unittest.main()
