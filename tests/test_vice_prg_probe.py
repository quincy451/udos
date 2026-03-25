from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import vice_prg_probe as vp


class TestViceProbeArgNormalization(unittest.TestCase):
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

    def test_locate_x64sc_prefers_path_on_non_windows(self) -> None:
        with mock.patch.object(vp, "os") as os_mock:
            os_mock.name = "posix"
            os_mock.environ = {}
            with mock.patch.object(
                vp.shutil,
                "which",
                side_effect=lambda name: "/usr/bin/x64" if name == "x64" else "/usr/bin/x64sc",
            ):
                self.assertTrue(vp.locate_x64sc().as_posix().endswith("/usr/bin/x64"))

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

    def test_format_udos_launch_trace_reads_expected_bytes(self) -> None:
        client = mock.Mock()
        values = {
            0x03F0: b"\x01",
            0x03F1: b"\x00",
            0x03F2: b"\xF3",
            0x03F3: b"\xC3",
        }

        def fake_memory_get(start: int, end: int, *, memspace: int = 0, bank: int = 0) -> bytes:
            self.assertEqual(start, end)
            self.assertEqual(memspace, 0)
            self.assertEqual(bank, 0)
            return values[start]

        client.memory_get.side_effect = fake_memory_get
        self.assertEqual(
            vp.format_udos_launch_trace(client),
            "VICE debug bytes: "
            "LAUNCH_RESULT_FLAG=0x01@0x03F0 "
            "LAUNCH_EXIT_STATUS=0x00@0x03F1 "
            "LAUNCH_TRACE_STAGE=0xF3@0x03F2 "
            "LAUNCH_TRACE_CODE=0xC3@0x03F3",
        )

    def test_read_active_screen_text_falls_back_to_default_screen_when_vic_regs_invalid(self) -> None:
        client = mock.Mock()

        def fake_memory_get(start: int, end: int, *, memspace: int = 0, bank: int = 0) -> bytes:
            self.assertEqual(memspace, 0)
            self.assertEqual(bank, 0)
            if (start, end) == (0xD018, 0xD018):
                return b"\xFF"
            if (start, end) == (0xDD00, 0xDD00):
                return b"\xFF"
            if (start, end) == (0x0400, 0x07E7):
                data = bytearray(b"\x20" * 1000)
                data[0] = 1  # A
                data[1] = 2  # B
                return bytes(data)
            self.fail(f"unexpected memory_get range {(start, end)}")

        client.memory_get.side_effect = fake_memory_get
        text, d018, dd00 = vp.read_active_screen_text(client)
        self.assertEqual((d018, dd00), (0xFF, 0xFF))
        self.assertIn("AB", text)


if __name__ == "__main__":
    unittest.main()
