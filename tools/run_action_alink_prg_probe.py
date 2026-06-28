#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import run_action_alink_probe as rap
import run_action_probe_fs as pfs
import run_action_command_probe as avp
import vice_prg_probe as vp


ROOT = Path(__file__).resolve().parent
ACTION_ROOT = ROOT.parent.parent / "actionc64u"
ACTION_ALINK_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ALINK.PRG"
ACTION_ACTC_HARNESS_BUILD = ROOT.parent.parent / "actionc64u" / "build" / "udos_tools" / "ACTC_HARNESS.PRG"
TOOL_ABI_HARNESS = ACTION_ROOT / "build" / "udos_tools" / "tool_abi_harness"
UDOS_SERVICES_INC = ACTION_ROOT / "build" / "udos_tools" / "udos_services.inc"
ACTION_ALINK_LABELS = ACTION_ROOT / "build" / "udos_tools" / "alink.current.labels"
ACTION_ACTC_HARNESS_LABELS = ACTION_ROOT / "build" / "udos_tools" / "actc_harness.current.labels"
UDOS_RUNTIME_MODULES = ACTION_ROOT / "src" / "runtime" / "udos_modules"
CONNECT_DELAYS = rap.CONNECT_DELAYS

DIRECT_PRG_LOAD_ADDR = 0x1000
DIRECT_PRG_STUB_SIZE = 32
INITIAL_SETTLE = 3.0
ALINK_PHASE_TIMEOUT = 60.0
PRG_PHASE_TIMEOUT = 8.0
DIRECT_PRG_EXIT_MARKER_ADDR = 0x03D0
DIRECT_PRG_EXIT_MARKER_VALUE = 0xA5
DBF_FIXTURE_NAME_ADDR = 0x3000
DBF_FIXTURE_NAME = "!TEST.DBF"
DBF_CREATE_NAME = "!CREATE.DBF"
DBF_MISSING_NAME = "!MISSING.DBF"
DBF_FIXTURE_STAGE_PATH = "BIN/TEST.DBF"

_DIRECT_PRG_EXIT_MARKER = bytes.fromhex("A9A58DD003A90085028503A2024C0FCF")
_EXTERNAL_STRING_INT_HELPER_CODE = (
    "A9 95 85 02 A9 10 85 03 A2 02 20 03 CF A9 2A 8D 91 10 A9 00 8D 92 10 "
    "A2 00 AD 91 10 C9 64 90 09 38 E9 64 8D 91 10 E8 D0 F0 E0 00 F0 0C "
    "8A 18 69 30 20 7B 10 A9 01 8D 92 10 A2 00 AD 91 10 C9 0A 90 09 38 "
    "E9 0A 8D 91 10 E8 D0 F0 E0 00 D0 05 AD 92 10 F0 07 8A 18 69 30 20 "
    "7B 10 AD 91 10 18 69 30 20 7B 10 20 06 CF 60 8D 93 10 A9 00 8D 94 "
    "10 A9 93 85 02 A9 10 85 03 A2 02 20 03 CF 60 00 00 00 00 54 4F 4F "
    "4C 00"
)


def _pre_run_memory_bytes(addr: int, data: bytes) -> list[dict[str, int]]:
    return [{"addr": addr + index, "value": byte} for index, byte in enumerate(data)]


def _dbf_fixture_bytes(record_count: int = 3, deleted_records: set[int] | None = None) -> bytes:
    header = bytearray(32)
    header[0] = 0x03
    header[1:4] = bytes([26, 6, 13])
    header[4:8] = record_count.to_bytes(4, "little")
    header[8:10] = (65).to_bytes(2, "little")
    header[10:12] = (2).to_bytes(2, "little")
    field = bytearray(32)
    field[0:5] = b"VALUE"
    field[11] = ord("C")
    field[16] = 1
    deleted_records = deleted_records or set()
    records = bytearray()
    for index in range(record_count):
        record_no = index + 1
        records.append(ord("*") if record_no in deleted_records else ord(" "))
        records.append(ord("A") + index)
    return bytes(header) + bytes(field) + b"\x0d" + records
_TRANSITIVE_EXTERNAL_STRING_INT_HELPER_CODE = (
    "A9 99 85 02 A9 10 85 03 A2 02 20 03 CF A9 2A 8D 95 10 A9 00 8D 96 10 "
    "A2 00 AD 95 10 C9 64 90 09 38 E9 64 8D 95 10 E8 D0 F0 E0 00 F0 0C "
    "8A 18 69 30 20 7F 10 A9 01 8D 96 10 A2 00 AD 95 10 C9 0A 90 09 38 "
    "E9 0A 8D 95 10 E8 D0 F0 E0 00 D0 05 AD 96 10 F0 07 8A 18 69 30 20 "
    "7F 10 AD 95 10 18 69 30 20 7F 10 20 06 CF 60 8D 97 10 A9 00 8D 98 "
    "10 A9 97 85 02 A9 10 85 03 A2 02 20 03 CF 60 00 00 00 00 54 4F 4F "
    "4C 00"
)


def _hex_bytes(data: bytes | bytearray) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def _object_code_lowercase_z_import_call_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b uzM\n"
            + "".join(f"u {name}\n" for name in import_names)
            + "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 uz\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [f"LIB/{name.upper()}.OBJ" for name in dummy_names],
    }


def _object_code_project_lowercase_z_import_call_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b uzM\n"
            + "".join(f"u {name}\n" for name in import_names)
            + "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 uz\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_project_second_export_lowercase_z_import_library_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm EA\nn a\n"
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b uzM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 uz\n"
                "n a\n"
            ),
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_project_second_export_lowercase_z_import_project_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm EA\nn a\n"
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b uzM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 uz\n"
                "n a\n"
            ),
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_library_second_export_lowercase_z_import_project_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x unused 0 4\n"
        "x a 4 4\n"
        "b u0M\n"
        "b uzM\n"
        + "".join(f"u {name}\n" for name in import_names)
        + "m 20 00 00 60 20 00 00 60\n"
        "r 1 u0\n"
        "r 5 uz\n"
        "n a\n"
    )
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_library_second_export_lowercase_z_import_library_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x unused 0 4\n"
        "x a 4 4\n"
        "b u0M\n"
        "b uzM\n"
        + "".join(f"u {name}\n" for name in import_names)
        + "m 20 00 00 60 20 00 00 60\n"
        "r 1 u0\n"
        "r 5 uz\n"
        "n a\n"
    )
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_project_lettered_import_call_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b uAM\n"
            + "".join(f"u {name}\n" for name in import_names)
            + "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 uA\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_project_dependency_lettered_import_project_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm EA\nn a\n"
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uAM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 60\n"
                "r 1 uA\n"
                "n a\n"
            ),
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_project_dependency_lettered_import_library_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm EA\nn a\n"
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uAM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 60\n"
                "r 1 uA\n"
                "n a\n"
            ),
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_root_second_export_dependency_dual_lettered_import_mixed_helpers_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["projhelper", "libhelper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects.update(
        {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "PROJHELPER.OBJ": "OBJ1\nx projhelper 0 1\nb M\nm EA\nn projhelper\n",
            "LIBHELPER.OBJ": "OBJ1\nx libhelper 0 1\nb M\nm 60\nn libhelper\n",
        }
    )
    return {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 7\n"
                "b uAuBM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 20 00 00 60\n"
                "r 1 uA\n"
                "r 4 uB\n"
                "n a\n"
            ),
            "PROJHELPER.OBJ": "OBJ1\nx projhelper 0 1\nb M\nm 60\nn projhelper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "201A10201B10606060"
        ),
        "expected_alink_loads": [
            "OBJ/A.OBJ",
            "OBJ/PROJHELPER.OBJ",
            "LIB/LIBHELPER.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/PROJHELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_root_second_export_dependency_lowercase_z_import_project_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm EA\nn a\n"
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uzM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 60\n"
                "r 1 uz\n"
                "n a\n"
            ),
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_root_second_export_dependency_lowercase_z_import_library_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm EA\nn a\n"
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uzM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 60\n"
                "r 1 uz\n"
                "n a\n"
            ),
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_root_second_export_library_dependency_lowercase_z_import_project_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x a 0 4\n"
        "b uzM\n"
        + "".join(f"u {name}\n" for name in import_names)
        + "m 20 00 00 60\n"
        "r 1 uz\n"
        "n a\n"
    )
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_root_second_export_library_dependency_lowercase_z_import_library_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x a 0 4\n"
        "b uzM\n"
        + "".join(f"u {name}\n" for name in import_names)
        + "m 20 00 00 60\n"
        "r 1 uz\n"
        "n a\n"
    )
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [f"LIB/{name.upper()}.OBJ" for name in dummy_names],
    }


def _object_code_library_second_export_dependency_dual_lettered_import_mixed_helpers_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["projhelper", "libhelper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects.update(
        {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 1\n"
                "x a 1 4\n"
                "b M\n"
                "b u0M\n"
                "u dep\n"
                "m EA 20 00 00 60\n"
                "r 2 u0\n"
                "n a\n"
            ),
            "DEP.OBJ": "OBJ1\nx dep 0 1\nb M\nm EA\nn dep\n",
            "PROJHELPER.OBJ": "OBJ1\nx projhelper 0 1\nb M\nm EA\nn projhelper\n",
            "LIBHELPER.OBJ": "OBJ1\nx libhelper 0 1\nb M\nm 60\nn libhelper\n",
        }
    )
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "DEP.OBJ": (
                "OBJ1\n"
                "x dep 0 7\n"
                "b uAuBM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 20 00 00 60\n"
                "r 1 uA\n"
                "r 4 uB\n"
                "n dep\n"
            ),
            "PROJHELPER.OBJ": "OBJ1\nx projhelper 0 1\nb M\nm 60\nn projhelper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "20171060"
            "201E10201F1060"
            "6060"
        ),
        "expected_alink_loads": [
            "LIB/A.OBJ",
            "OBJ/DEP.OBJ",
            "OBJ/PROJHELPER.OBJ",
            "LIB/LIBHELPER.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/DEP.OBJ",
            "LIB/PROJHELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_project_second_export_dependency_dual_lettered_import_mixed_helpers_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["projhelper", "libhelper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects.update(
        {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "DEP.OBJ": "OBJ1\nx dep 0 1\nb M\nm EA\nn dep\n",
            "PROJHELPER.OBJ": "OBJ1\nx projhelper 0 1\nb M\nm EA\nn projhelper\n",
            "LIBHELPER.OBJ": "OBJ1\nx libhelper 0 1\nb M\nm 60\nn libhelper\n",
        }
    )
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u dep\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "DEP.OBJ": (
                "OBJ1\n"
                "x dep 0 7\n"
                "b uAuBM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 20 00 00 60\n"
                "r 1 uA\n"
                "r 4 uB\n"
                "n dep\n"
            ),
            "PROJHELPER.OBJ": "OBJ1\nx projhelper 0 1\nb M\nm 60\nn projhelper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "20171060"
            "201E10201F1060"
            "6060"
        ),
        "expected_alink_loads": [
            "OBJ/A.OBJ",
            "OBJ/DEP.OBJ",
            "OBJ/PROJHELPER.OBJ",
            "LIB/LIBHELPER.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/DEP.OBJ",
            "LIB/PROJHELPER.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_library_dependency_lettered_import_project_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x a 0 4\n"
        "b uAM\n"
        + "".join(f"u {name}\n" for name in import_names)
        + "m 20 00 00 60\n"
        "r 1 uA\n"
        "n a\n"
    )
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_library_dependency_lettered_import_library_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x a 0 4\n"
        "b uAM\n"
        + "".join(f"u {name}\n" for name in import_names)
        + "m 20 00 00 60\n"
        "r 1 uA\n"
        "n a\n"
    )
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_library_dependency_lowercase_z_import_project_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x a 0 4\n"
        "b uzM\n"
        + "".join(f"u {name}\n" for name in import_names)
        + "m 20 00 00 60\n"
        "r 1 uz\n"
        "n a\n"
    )
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_dependency_lowercase_z_import_pruned_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x a 0 4\n"
        "b uzM\n"
        + "".join(f"u {name}\n" for name in import_names)
        + "m 20 00 00 60\n"
        "r 1 uz\n"
        "n a\n"
    )
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [f"LIB/{name.upper()}.OBJ" for name in dummy_names],
    }


def _object_code_project_dependency_lowercase_z_import_pruned_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm EA\nn a\n"
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uzM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 60\n"
                "r 1 uz\n"
                "n a\n"
            ),
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_project_dependency_lowercase_z_import_project_helper_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    import_names = dummy_names + ["helper"]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm EA\nn a\n"
    extra_library_objects["HELPER.OBJ"] = "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uzM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 60\n"
                "r 1 uz\n"
                "n a\n"
            ),
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/HELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_dependency_unknown_lowercase_import_index_rejects_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = (
        "OBJ1\n"
        "x a 0 4\n"
        "b uzM\n"
        + "".join(f"u {name}\n" for name in dummy_names)
        + "m 20 00 00 60\n"
        "r 1 uz\n"
        "n a\n"
    )
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": extra_library_objects,
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["LIB/A.OBJ"],
        "unexpected_alink_loads": [f"LIB/{name.upper()}.OBJ" for name in dummy_names],
    }


def _object_code_project_unknown_lowercase_import_index_blocks_library_fallback_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(35)]
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects["A.OBJ"] = "OBJ1\nx a 0 1\nb M\nm 60\nn a\n"
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uzM\n"
                + "".join(f"u {name}\n" for name in dummy_names)
                + "m 20 00 00 60\n"
                "r 1 uz\n"
                "n a\n"
            ),
        },
        "extra_library_objects": extra_library_objects,
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _object_code_large_dependency_page_crossing_case() -> dict[str, object]:
    root = bytearray(bytes.fromhex("20 00 00") + _DIRECT_PRG_EXIT_MARKER)
    large_size = 272
    a_addr = DIRECT_PRG_LOAD_ADDR + len(root)
    b_addr = a_addr + large_size
    root[1] = a_addr & 0xFF
    root[2] = a_addr >> 8
    a_seed = bytearray([0x20, 0x00, 0x00])
    a_seed.extend([0xEA] * (large_size - len(a_seed) - 1))
    a_seed.append(0x60)
    a_expected = bytearray(a_seed)
    a_expected[1] = b_addr & 0xFF
    a_expected[2] = b_addr >> 8
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                f"x a 0 {large_size}\n"
                "b u0M\n"
                "u b\n"
                f"m {_hex_bytes(a_seed)}\n"
                "r 1 u0\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes(root) + bytes(a_expected) + bytes([0x60]),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    }


def _object_code_project_large_dependency_page_crossing_case() -> dict[str, object]:
    root = bytearray(bytes.fromhex("20 00 00") + _DIRECT_PRG_EXIT_MARKER)
    large_size = 272
    a_addr = DIRECT_PRG_LOAD_ADDR + len(root)
    b_addr = a_addr + large_size
    root[1] = a_addr & 0xFF
    root[2] = a_addr >> 8
    a_seed = bytearray([0x20, 0x00, 0x00])
    a_seed.extend([0xEA] * (large_size - len(a_seed) - 1))
    a_seed.append(0x60)
    a_expected = bytearray(a_seed)
    a_expected[1] = b_addr & 0xFF
    a_expected[2] = b_addr >> 8
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                f"x a 0 {large_size}\n"
                "b u0M\n"
                "u b\n"
                f"m {_hex_bytes(a_seed)}\n"
                "r 1 u0\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes(root) + bytes(a_expected) + bytes([0x60]),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    }


def _object_code_project_large_dependency_library_tail_page_crossing_case() -> dict[str, object]:
    root = bytearray(bytes.fromhex("20 00 00") + _DIRECT_PRG_EXIT_MARKER)
    large_size = 272
    a_addr = DIRECT_PRG_LOAD_ADDR + len(root)
    b_addr = a_addr + large_size
    root[1] = a_addr & 0xFF
    root[2] = a_addr >> 8
    a_seed = bytearray([0x20, 0x00, 0x00])
    a_seed.extend([0xEA] * (large_size - len(a_seed) - 1))
    a_seed.append(0x60)
    a_expected = bytearray(a_seed)
    a_expected[1] = b_addr & 0xFF
    a_expected[2] = b_addr >> 8
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                f"x a 0 {large_size}\n"
                "b u0M\n"
                "u b\n"
                f"m {_hex_bytes(a_seed)}\n"
                "r 1 u0\n"
                "n a\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes(root) + bytes(a_expected) + bytes([0x60]),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    }


def _object_code_large_root_page_crossing_case() -> dict[str, object]:
    large_size = 272
    helper_addr = DIRECT_PRG_LOAD_ADDR + large_size
    root_seed = bytearray([0x20, 0x00, 0x00])
    root_seed.extend([0xEA] * (large_size - len(root_seed) - len(_DIRECT_PRG_EXIT_MARKER)))
    root_seed.extend(_DIRECT_PRG_EXIT_MARKER)
    root_expected = bytearray(root_seed)
    root_expected[1] = helper_addr & 0xFF
    root_expected[2] = helper_addr >> 8
    return {
        "seed_object": (
            "OBJ1\n"
            f"x main 0 {large_size}\n"
            "b u0M\n"
            "u helper\n"
            f"m {_hex_bytes(root_seed)}\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes(root_expected) + bytes([0x60]),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    }


def _object_code_large_root_multi_reloc_page_crossing_case() -> dict[str, object]:
    large_size = 288
    second_jsr_offset = 257
    a_addr = DIRECT_PRG_LOAD_ADDR + large_size
    b_addr = a_addr + 1
    root_seed = bytearray([0xEA] * large_size)
    root_seed[0:3] = bytes([0x20, 0x00, 0x00])
    root_seed[second_jsr_offset : second_jsr_offset + 3] = bytes([0x20, 0x00, 0x00])
    root_seed[-len(_DIRECT_PRG_EXIT_MARKER) :] = _DIRECT_PRG_EXIT_MARKER
    root_expected = bytearray(root_seed)
    root_expected[1] = a_addr & 0xFF
    root_expected[2] = a_addr >> 8
    root_expected[second_jsr_offset + 1] = b_addr & 0xFF
    root_expected[second_jsr_offset + 2] = b_addr >> 8
    return {
        "seed_object": (
            "OBJ1\n"
            f"x main 0 {large_size}\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            f"m {_hex_bytes(root_seed)}\n"
            "r 1 u0\n"
            f"r {second_jsr_offset + 1} u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes(root_expected) + bytes([0x60, 0x60]),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    }


def _object_code_reloc_scan_windowed_imports_case() -> dict[str, object]:
    helper_names = [
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
        "india",
        "juliet",
        "kilo",
    ]
    selectors = "0123456789A"
    body = bytearray()
    for _ in helper_names:
        body.extend(bytes([0x20, 0x00, 0x00]))
    body.extend(_DIRECT_PRG_EXIT_MARKER)
    expected = bytearray(body)
    for index in range(len(helper_names)):
        addr = DIRECT_PRG_LOAD_ADDR + len(body) + index
        offset = index * 3
        expected[offset + 1] = addr & 0xFF
        expected[offset + 2] = addr >> 8
    debug_lines = "".join(f"l 0 {index} 0 {index + 3} 1\n" for index in range(12))
    relocs = "".join(
        f"r {1 + (index * 3)} u{selectors[index]}\n"
        for index in range(len(helper_names))
    )
    imports = "".join(f"u {name}\n" for name in helper_names)
    return {
        "seed_object": (
            "OBJ1\n"
            "f 0 src/main.act\n"
            "q 0 0 2 6\n"
            f"{debug_lines}"
            f"x main 0 {len(body)}\n"
            "b u0u1u2u3u4u5u6u7u8u9uAM\n"
            f"m {_hex_bytes(body)}\n"
            f"{relocs}"
            f"{imports}"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
            for name in helper_names
        },
        "expected_tail": bytes(expected) + bytes([0x60] * len(helper_names)),
        "expected_alink_loads": [f"LIB/{name.upper()}.OBJ" for name in helper_names],
    }


def _object_code_dependency_reloc_scan_windowed_imports_case() -> dict[str, object]:
    helper_names = [
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
        "india",
        "juliet",
        "kilo",
    ]
    selectors = "0123456789A"
    root = bytearray(bytes.fromhex("20 00 00") + _DIRECT_PRG_EXIT_MARKER)
    a_addr = DIRECT_PRG_LOAD_ADDR + len(root)
    root[1] = a_addr & 0xFF
    root[2] = a_addr >> 8
    a_body = bytearray()
    for _ in helper_names:
        a_body.extend(bytes([0x20, 0x00, 0x00]))
    a_body.append(0x60)
    helper_addr = a_addr + len(a_body)
    a_expected = bytearray(a_body)
    for index in range(len(helper_names)):
        addr = helper_addr + index
        offset = index * 3
        a_expected[offset + 1] = addr & 0xFF
        a_expected[offset + 2] = addr >> 8
    debug_lines = "".join(f"l 0 {index} 0 {index + 3} 1\n" for index in range(16))
    relocs = "".join(
        f"r {1 + (index * 3)} u{selectors[index]}\n"
        for index in range(len(helper_names))
    )
    imports = "".join(f"u {name}\n" for name in helper_names)
    return {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "f 0 lib/a.obj\n"
                "q 0 0 2 6\n"
                f"{debug_lines}"
                f"x a 0 {len(a_body)}\n"
                "b u0u1u2u3u4u5u6u7u8u9uAM\n"
                f"m {_hex_bytes(a_body)}\n"
                f"{relocs}"
                f"{imports}"
                "n a\n"
            ),
            **{
                f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
                for name in helper_names
            },
        },
        "expected_tail": bytes(root) + bytes(a_expected) + bytes([0x60] * len(helper_names)),
        "expected_alink_loads": [
            "LIB/A.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in helper_names],
        ],
    }


def _external_dependency_windowed_lettered_import_call_case() -> dict[str, object]:
    helper_names = [
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
        "india",
        "juliet",
        "kilo",
    ]
    selectors = "0123456789A"
    root = bytearray(bytes.fromhex("20 00 00") + _DIRECT_PRG_EXIT_MARKER)
    wrap_addr = DIRECT_PRG_LOAD_ADDR + len(root)
    root[1] = wrap_addr & 0xFF
    root[2] = wrap_addr >> 8
    wrap_body = bytearray()
    for _ in helper_names:
        wrap_body.extend(bytes([0x20, 0x00, 0x00]))
    wrap_body.append(0x60)
    helper_addr = wrap_addr + len(wrap_body)
    wrap_expected = bytearray(wrap_body)
    for index in range(len(helper_names)):
        addr = helper_addr + index
        offset = index * 3
        wrap_expected[offset + 1] = addr & 0xFF
        wrap_expected[offset + 2] = addr >> 8
    debug_lines = "".join(f"l 0 {index} 0 {index + 3} 1\n" for index in range(16))
    relocs = "".join(
        f"r {1 + (index * 3)} u{selectors[index]}\n"
        for index in range(len(helper_names))
    )
    imports = "".join(f"u {name}\n" for name in helper_names)
    return {
        "source": "MODULE MAIN\rPROC MAIN()\rWrap()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 19\n",
            "b u0M\n",
            "u wrap\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
        ],
        "extra_library_objects": {
            "WRAP.OBJ": (
                "OBJ1\n"
                "f 0 lib/wrap.obj\n"
                "q 0 0 2 6\n"
                f"{debug_lines}"
                f"x wrap 0 {len(wrap_body)}\n"
                "b u0u1u2u3u4u5u6u7u8u9uAM\n"
                f"m {_hex_bytes(wrap_body)}\n"
                f"{relocs}"
                f"{imports}"
                "n wrap\n"
            ),
            **{
                f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm 60\nn {name}\n"
                for name in helper_names
            },
        },
        "expected_tail": bytes(root) + bytes(wrap_expected) + bytes([0x60] * len(helper_names)),
        "expected_alink_loads": [
            "LIB/WRAP.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in helper_names],
        ],
    }


def _local_external_project_dependency_windowed_lettered_import_call_case() -> dict[str, object]:
    case = _external_dependency_windowed_lettered_import_call_case()
    extra_library_objects = case.get("extra_library_objects")
    if not isinstance(extra_library_objects, dict):
        raise RuntimeError("windowed dependency case missing library objects")
    wrap_obj = extra_library_objects.pop("WRAP.OBJ", None)
    if not isinstance(wrap_obj, str):
        raise RuntimeError("windowed dependency case missing WRAP.OBJ")
    case["extra_objects"] = {"WRAP.OBJ": wrap_obj}
    expected_loads = case.get("expected_alink_loads", [])
    case["expected_alink_loads"] = [
        "OBJ/WRAP.OBJ",
        *[
            path
            for path in expected_loads
            if isinstance(path, str) and path.upper() != "LIB/WRAP.OBJ"
        ],
    ]
    case["unexpected_alink_loads"] = ["LIB/WRAP.OBJ"]
    return case


def _local_external_project_dependency_windowed_lettered_mixed_helper_call_case() -> dict[str, object]:
    dummy_names = [f"d{i}" for i in range(10)]
    import_names = dummy_names + ["projhelper", "libhelper"]
    root = bytearray(bytes.fromhex("20 00 00") + _DIRECT_PRG_EXIT_MARKER)
    wrap_addr = DIRECT_PRG_LOAD_ADDR + len(root)
    root[1] = wrap_addr & 0xFF
    root[2] = wrap_addr >> 8
    wrap_body = bytearray(bytes.fromhex("20 00 00 20 00 00 60"))
    projhelper_addr = wrap_addr + len(wrap_body)
    libhelper_addr = projhelper_addr + 1
    wrap_expected = bytearray(wrap_body)
    wrap_expected[1] = projhelper_addr & 0xFF
    wrap_expected[2] = projhelper_addr >> 8
    wrap_expected[4] = libhelper_addr & 0xFF
    wrap_expected[5] = libhelper_addr >> 8
    extra_library_objects = {
        f"{name.upper()}.OBJ": f"OBJ1\nx {name} 0 1\nb M\nm EA\nn {name}\n"
        for name in dummy_names
    }
    extra_library_objects.update(
        {
            "WRAP.OBJ": "OBJ1\nx wrap 0 1\nb M\nm EA\nn wrap\n",
            "PROJHELPER.OBJ": "OBJ1\nx projhelper 0 1\nb M\nm EA\nn projhelper\n",
            "LIBHELPER.OBJ": "OBJ1\nx libhelper 0 1\nb M\nm 60\nn libhelper\n",
        }
    )
    return {
        "source": "MODULE MAIN\rPROC MAIN()\rWrap()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 19\n",
            "b u0M\n",
            "u wrap\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
        ],
        "extra_objects": {
            "WRAP.OBJ": (
                "OBJ1\n"
                "x wrap 0 7\n"
                "b uAuBM\n"
                + "".join(f"u {name}\n" for name in import_names)
                + "m 20 00 00 20 00 00 60\n"
                "r 1 uA\n"
                "r 4 uB\n"
                "n wrap\n"
            ),
            "PROJHELPER.OBJ": "OBJ1\nx projhelper 0 1\nb M\nm 60\nn projhelper\n",
        },
        "extra_library_objects": extra_library_objects,
        "expected_tail": bytes(root) + bytes(wrap_expected) + b"\x60\x60",
        "expected_alink_loads": [
            "OBJ/WRAP.OBJ",
            "OBJ/PROJHELPER.OBJ",
            "LIB/LIBHELPER.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/WRAP.OBJ",
            "LIB/PROJHELPER.OBJ",
            *[f"LIB/{name.upper()}.OBJ" for name in dummy_names],
        ],
    }


def _runtime_obj_text(name: str) -> str:
    return (UDOS_RUNTIME_MODULES / f"{name}.obj").read_text(encoding="ascii")


def _runtime_obj_machine_code(name: str) -> bytes:
    for line in _runtime_obj_text(name).splitlines():
        if line.startswith("m "):
            return bytes.fromhex(line[2:])
    raise RuntimeError(f"runtime OBJ module has no machine-code record: {name}")


def _runtime_obj_imports(name: str) -> list[str]:
    imports: list[str] = []
    for line in _runtime_obj_text(name).splitlines():
        if line.startswith("u "):
            imports.append(line[2:].strip().lower())
    return imports


def _runtime_obj_relocs(name: str) -> list[tuple[int, int]]:
    relocs: list[tuple[int, int]] = []
    for line in _runtime_obj_text(name).splitlines():
        if not line.startswith("r "):
            continue
        parts = line.split()
        if len(parts) != 3 or not parts[2].startswith("u"):
            raise RuntimeError(f"unsupported relocation record in {name}: {line}")
        relocs.append((int(parts[1]), int(parts[2][1:])))
    return relocs


def _linked_runtime_module_bytes(name: str, module_addrs: dict[str, int]) -> bytes:
    code = bytearray(_runtime_obj_machine_code(name))
    imports = _runtime_obj_imports(name)
    for offset, import_index in _runtime_obj_relocs(name):
        if import_index >= len(imports):
            raise RuntimeError(f"relocation import index out of range in {name}: {import_index}")
        target_name = imports[import_index]
        target_addr = module_addrs[target_name]
        code[offset] = target_addr & 0xFF
        code[offset + 1] = target_addr >> 8
    return bytes(code)


def _runtime_module_addrs(module_names: list[str], first_addr: int) -> dict[str, int]:
    addrs: dict[str, int] = {}
    cursor = first_addr
    for name in module_names:
        addrs[name] = cursor
        cursor += len(_runtime_obj_machine_code(name))
    return addrs


def _runtime_module_closure(module_names: list[str]) -> list[str]:
    ordered: list[str] = []
    queued: set[str] = set()
    for name in module_names:
        if name not in queued:
            ordered.append(name)
            queued.add(name)
    index = 0
    while index < len(ordered):
        for import_name in _runtime_obj_imports(ordered[index]):
            if import_name not in queued:
                ordered.append(import_name)
                queued.add(import_name)
        index += 1
    return ordered


def _set_zp_word(zp_addr: int, value: int) -> bytes:
    return bytes(
        [
            0xA9,
            value & 0xFF,
            0x85,
            zp_addr,
            0xA9,
            value >> 8,
            0x85,
            zp_addr + 1,
        ]
    )


def _jsr(addr: int) -> bytes:
    return bytes([0x20, addr & 0xFF, addr >> 8])


def _actc_selective_hardware_runtime_tail() -> bytes:
    modules = ["rt_sprite_data", "rt_sprite_pos", "rt_gfx_bgcolor", "rt_sid_freq"]
    root_len = 49
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02, 0xA2, 0x00, 0xA0, 0x20])
        + _jsr(module_addrs["rt_sprite_data"])
        + bytes([0xA9, 0x02, 0xA2, 0x34, 0xA0, 0x56, 0x38])
        + _jsr(module_addrs["rt_sprite_pos"])
        + bytes([0xA9, 0x06])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + bytes([0xA9, 0x01, 0xA2, 0x34, 0xA0, 0x12])
        + _jsr(module_addrs["rt_sid_freq"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected selective hardware root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_reordered_hardware_runtime_tail() -> bytes:
    modules = ["rt_gfx_bgcolor", "rt_sid_freq", "rt_sprite_data"]
    root_len = 39
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x03])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + bytes([0xA9, 0x01, 0xA2, 0x34, 0xA0, 0x12])
        + _jsr(module_addrs["rt_sid_freq"])
        + bytes([0xA9, 0x02, 0xA2, 0x00, 0xA0, 0x20])
        + _jsr(module_addrs["rt_sprite_data"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected reordered hardware root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_repeated_bgcolor_runtime_tail() -> bytes:
    modules = ["rt_gfx_bgcolor"]
    root_len = 26
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + bytes([0xA9, 0x06])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected repeated BgColor root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_named_hardware_constants_runtime_tail() -> bytes:
    call_specs: list[tuple[str, str, int, int | None]] = [
        ("ay", "rt_sid_wave", 1, 0xF0),
        ("a", "rt_sid_mode", 0x70, None),
        ("ay", "rt_sprite_prio", 2, 1),
        ("ay", "rt_sprite_prio", 3, 0),
    ]
    root_len = len(_DIRECT_PRG_EXIT_MARKER) + sum(
        7 if kind == "ay" else 5 for kind, _, _, _ in call_specs
    )
    modules = _runtime_module_closure([name for _, name, _, _ in call_specs])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for kind, name, arg0, arg1 in call_specs:
        if kind == "ay":
            if arg1 is None:
                raise RuntimeError(f"missing AY helper second argument for {name}")
            code.extend([0xA9, arg0 & 0xFF, 0xA0, arg1 & 0xFF])
        else:
            code.extend([0xA9, arg0 & 0xFF])
        code.extend(_jsr(module_addrs[name]))
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    if len(code) != root_len:
        raise RuntimeError(f"unexpected named hardware constants root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_sidspr1_sid_wave_mask_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_wave"])
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01, 0xA0, 0xF0])
        + _jsr(module_addrs["rt_sid_wave"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected SIDSPR1 SidWave mask root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_sidspr1_sid_mode_mask_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_mode"])
    root_len = 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER)
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x70])
        + _jsr(module_addrs["rt_sid_mode"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected SIDSPR1 SidMode mask root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_sidspr1_sprite_prio_back_runtime_tail() -> bytes:
    modules = ["rt_sprite_prio"]
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02, 0xA0, 0x01])
        + _jsr(module_addrs["rt_sprite_prio"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected SIDSPR1 SpritePrio constant root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_named_constant_mixed_runtime_expr_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_mode"])
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x70])
        + _jsr(module_addrs["rt_sid_mode"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected named constant mixed runtime root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_joystick_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_joy", "rt_jp"])
    root_len = 26
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_joy"])
        + bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_jp"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected input joystick runtime root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_joystick_condition_gfx_runtime_tail(
    compare_value: int = 0,
    skip_opcode: int = 0xD0,
    helper_name: str = "rt_joy",
    helper_arg: int = 2,
    side_arg: int = 6,
) -> bytes:
    modules = _runtime_module_closure([helper_name, "rt_gfx_bgcolor"])
    root_len = 30
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, helper_arg & 0xFF])
        + _jsr(module_addrs[helper_name])
        + bytes([0xC9, compare_value & 0xFF, skip_opcode & 0xFF, 0x05, 0xA9, side_arg & 0xFF])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected input joystick condition runtime root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_mouse_condition_gfx_runtime_tail(
    compare_value: int = 0,
    skip_opcode: int = 0xD0,
    helper_name: str = "rt_mb",
    side_arg: int = 6,
) -> bytes:
    modules = _runtime_module_closure([helper_name, "rt_gfx_bgcolor"])
    root_len = 28
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        _jsr(module_addrs[helper_name])
        + bytes([0xC9, compare_value & 0xFF, skip_opcode & 0xFF, 0x05, 0xA9, side_arg & 0xFF])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected input mouse condition runtime root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_mouse_runtime_tail() -> bytes:
    modules = _runtime_module_closure(
        [
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_mb",
        ]
    )
    root_len = 33
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01])
        + _jsr(module_addrs["rt_mp"])
        + _jsr(module_addrs["rt_mseen"])
        + _jsr(module_addrs["rt_mx"])
        + _jsr(module_addrs["rt_my"])
        + _jsr(module_addrs["rt_mb"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected input mouse runtime root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_joystick_two_button_mask_runtime_tail() -> bytes:
    # The mask assignment is retained in the object metadata for layout, but the
    # generated root code only needs to store the Joy() result.
    variable_count = 2
    root_len = 13 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    state_store = store_base + 2
    modules = _runtime_module_closure(["rt_joy"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_joy"])
        + bytes(
            [
                0x8D,
                state_store & 0xFF,
                state_store >> 8,
                0xA9,
                0x00,
                0x8D,
                (state_store + 1) & 0xFF,
                (state_store + 1) >> 8,
            ]
        )
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2 * variable_count)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected INPUT joystick mask runtime root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_single_store_runtime_tail(helper_name: str, arg: int | None) -> bytes:
    variable_count = 1
    root_len = (2 if arg is not None else 0) + 3 + 8 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    modules = _runtime_module_closure([helper_name])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    if arg is not None:
        code.extend([0xA9, arg & 0xFF])
    code.extend(_jsr(module_addrs[helper_name]))
    code.extend(
        [
            0x8D,
            store_addr & 0xFF,
            store_addr >> 8,
            0xA9,
            0x00,
            0x8D,
            (store_addr + 1) & 0xFF,
            (store_addr + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected INPUT single-store runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_dual_store_runtime_tail(helper_names: tuple[str, str], args: tuple[int | None, int | None]) -> bytes:
    variable_count = 2
    call_bytes = sum((2 if arg is not None else 0) + 3 + 8 for arg in args)
    root_len = call_bytes + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    modules = _runtime_module_closure(list(helper_names))
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for index, (helper_name, arg) in enumerate(zip(helper_names, args)):
        if arg is not None:
            code.extend([0xA9, arg & 0xFF])
        code.extend(_jsr(module_addrs[helper_name]))
        store_addr = store_base + (2 * index)
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected INPUT dual-store runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_a_byte_side_effect_runtime_tail(helper_name: str, arg: int) -> bytes:
    root_len = 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER)
    modules = _runtime_module_closure([helper_name])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytes([0xA9, arg & 0xFF]) + _jsr(module_addrs[helper_name]) + _DIRECT_PRG_EXIT_MARKER
    if len(code) != root_len:
        raise RuntimeError(f"unexpected A-byte side-effect runtime root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_xy_word_readback_store_runtime_tail(
    helper_name: str, arg: int, variable_count: int = 1, store_index: int = 0
) -> bytes:
    root_len = 4 + 3 + 8 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    store_addr = store_base + (2 * store_index)
    modules = _runtime_module_closure([helper_name])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray([0xA2, arg & 0xFF, 0xA0, (arg >> 8) & 0xFF])
    code.extend(_jsr(module_addrs[helper_name]))
    code.extend(
        [
            0x8D,
            store_addr & 0xFF,
            store_addr >> 8,
            0xA9,
            0x00,
            0x8D,
            (store_addr + 1) & 0xFF,
            (store_addr + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected XY-word readback runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_export_sample_runtime_tail() -> bytes:
    variable_count = 10
    root_len = (
        15
        + 14
        + 16
        + 16
        + 14
        + 14
        + 14
        + 14
        + 14
        + 6
        + len(_DIRECT_PRG_EXIT_MARKER)
        + (2 * variable_count)
    )
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    filename_addr = DBF_FIXTURE_NAME_ADDR
    handle_store = store_base + 2
    fields_store = store_base + 4
    fieldlen_store = store_base + 6
    moved_store = store_base + 8
    deleted_store = store_base + 10
    headerlen_store = store_base + 12
    recordlen_store = store_base + 14
    total_store = store_base + 16
    recno_store = store_base + 18
    modules = _runtime_module_closure(
        [
            "rt_dbf_open",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_go",
            "rt_dbf_deleted",
            "rt_dbf_headerlen",
            "rt_dbf_recordlen",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_close",
        ]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
        ]
    )
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_fieldcount"]))
    code.extend(
        [
            0x8D,
            fields_store & 0xFF,
            fields_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (fields_store + 1) & 0xFF,
            (fields_store + 1) >> 8,
        ]
    )
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8, 0xA0, 0x01])
    code.extend(_jsr(module_addrs["rt_dbf_fieldlen"]))
    code.extend(
        [
            0x8D,
            fieldlen_store & 0xFF,
            fieldlen_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (fieldlen_store + 1) & 0xFF,
            (fieldlen_store + 1) >> 8,
        ]
    )
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8, 0xA0, 0x02])
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
        ]
    )
    for helper_name, store_addr in [
        ("rt_dbf_deleted", deleted_store),
        ("rt_dbf_headerlen", headerlen_store),
        ("rt_dbf_recordlen", recordlen_store),
    ]:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    for helper_name, store_addr in [
        ("rt_dbf_totalrecs", total_store),
        ("rt_dbf_currrecno", recno_store),
    ]:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_close"]))
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 export sample runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_go_runtime_tail() -> bytes:
    variable_count = 3
    root_len = 15 + 16 + 14 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    recno_store = store_base + 4
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(["rt_dbf_open", "rt_dbf_go", "rt_dbf_currrecno"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_currrecno"]))
    code.extend(
        [
            0x8D,
            recno_store & 0xFF,
            recno_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (recno_store + 1) & 0xFF,
            (recno_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Go runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_field_count_runtime_tail() -> bytes:
    variable_count = 2
    root_len = 15 + 14 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    fields_store = store_base + 2
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(["rt_dbf_open", "rt_dbf_fieldcount"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_fieldcount"]))
    code.extend(
        [
            0x8D,
            fields_store & 0xFF,
            fields_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (fields_store + 1) & 0xFF,
            (fields_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 FieldCount runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_field_len_runtime_tail() -> bytes:
    variable_count = 2
    root_len = 15 + 16 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    fieldlen_store = store_base + 2
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(["rt_dbf_open", "rt_dbf_fieldlen"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x01,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_fieldlen"]))
    code.extend(
        [
            0x8D,
            fieldlen_store & 0xFF,
            fieldlen_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (fieldlen_store + 1) & 0xFF,
            (fieldlen_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 FieldLen runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_read_byte_runtime_tail(
    go_record: int = 2, read_offset: int = 1, read_handle: int | None = None
) -> bytes:
    variable_count = 3
    read_call_len = (5 if read_handle is None else 4) + 3 + 8
    root_len = 15 + 16 + read_call_len + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    value_store = store_base + 4
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(["rt_dbf_open", "rt_dbf_go", "rt_dbf_readbyte"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            go_record & 0xFF,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
        ]
    )
    if read_handle is None:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
    else:
        code.extend([0xA9, read_handle & 0xFF])
    code.extend([0xA0, read_offset & 0xFF])
    code.extend(_jsr(module_addrs["rt_dbf_readbyte"]))
    code.extend(
        [
            0x8D,
            value_store & 0xFF,
            value_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (value_store + 1) & 0xFF,
            (value_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 ReadByte runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_read_field_byte_runtime_tail() -> bytes:
    variable_count = 3
    root_len = 15 + 16 + 19 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    value_store = store_base + 4
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        ["rt_dbf_open", "rt_dbf_go", "rt_dbf_readfieldbyte"]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA2,
            0x01,
            0xA0,
            0x00,
            0x18,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_readfieldbyte"]))
    code.extend(
        [
            0x8D,
            value_store & 0xFF,
            value_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (value_store + 1) & 0xFF,
            (value_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 ReadFieldByte runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_write_field_byte_runtime_tail() -> bytes:
    variable_count = 4
    root_len = 15 + 16 + 23 + 19 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    wrote_store = store_base + 4
    value_store = store_base + 6
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        ["rt_dbf_open", "rt_dbf_go", "rt_dbf_writefieldbyte", "rt_dbf_readfieldbyte"]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
            0xA9,
            0x5A,
            0x85,
            0xE0,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA2,
            0x01,
            0xA0,
            0x00,
            0x18,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_writefieldbyte"]))
    code.extend(
        [
            0x8D,
            wrote_store & 0xFF,
            wrote_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (wrote_store + 1) & 0xFF,
            (wrote_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA2,
            0x01,
            0xA0,
            0x00,
            0x18,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_readfieldbyte"]))
    code.extend(
        [
            0x8D,
            value_store & 0xFF,
            value_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (value_store + 1) & 0xFF,
            (value_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 WriteFieldByte runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_write_byte_runtime_tail() -> bytes:
    variable_count = 4
    root_len = 15 + 16 + 19 + 16 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    wrote_store = store_base + 4
    value_store = store_base + 6
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        ["rt_dbf_open", "rt_dbf_go", "rt_dbf_writebyte", "rt_dbf_readbyte"]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA2,
            0x01,
            0xA0,
            0x5A,
            0x18,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_writebyte"]))
    code.extend(
        [
            0x8D,
            wrote_store & 0xFF,
            wrote_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (wrote_store + 1) & 0xFF,
            (wrote_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x01,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_readbyte"]))
    code.extend(
        [
            0x8D,
            value_store & 0xFF,
            value_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (value_store + 1) & 0xFF,
            (value_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 WriteByte runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_save_runtime_tail(go_record: int = 2) -> bytes:
    variable_count = 7
    root_len = (
        15
        + 16
        + 19
        + 14
        + 6
        + 15
        + 16
        + 16
        + len(_DIRECT_PRG_EXIT_MARKER)
        + (2 * variable_count)
    )
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    wrote_store = store_base + 4
    saved_store = store_base + 6
    handle2_store = store_base + 8
    moved2_store = store_base + 10
    value_store = store_base + 12
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_writebyte",
            "rt_dbf_save",
            "rt_dbf_close",
            "rt_dbf_readbyte",
        ]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            go_record & 0xFF,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA2,
            0x01,
            0xA0,
            0x5A,
            0x18,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_writebyte"]))
    code.extend(
        [
            0x8D,
            wrote_store & 0xFF,
            wrote_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (wrote_store + 1) & 0xFF,
            (wrote_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_save"]))
    code.extend(
        [
            0x8D,
            saved_store & 0xFF,
            saved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (saved_store + 1) & 0xFF,
            (saved_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_close"]))
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle2_store & 0xFF,
            handle2_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle2_store + 1) & 0xFF,
            (handle2_store + 1) >> 8,
            0xAD,
            handle2_store & 0xFF,
            handle2_store >> 8,
            0xA0,
            go_record & 0xFF,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved2_store & 0xFF,
            moved2_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved2_store + 1) & 0xFF,
            (moved2_store + 1) >> 8,
            0xAD,
            handle2_store & 0xFF,
            handle2_store >> 8,
            0xA0,
            0x01,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_readbyte"]))
    code.extend(
        [
            0x8D,
            value_store & 0xFF,
            value_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (value_store + 1) & 0xFF,
            (value_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Save runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_deleted_runtime_tail() -> bytes:
    variable_count = 3
    root_len = 15 + 16 + 14 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    deleted_store = store_base + 4
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(["rt_dbf_open", "rt_dbf_go", "rt_dbf_deleted"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_deleted"]))
    code.extend(
        [
            0x8D,
            deleted_store & 0xFF,
            deleted_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (deleted_store + 1) & 0xFF,
            (deleted_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Deleted runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_delete_undelete_runtime_tail() -> bytes:
    variable_count = 6
    root_len = 15 + 16 + (14 * 4) + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    delok_store = store_base + 4
    deleted_store = store_base + 6
    undelok_store = store_base + 8
    deleted2_store = store_base + 10
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_delete",
            "rt_dbf_deleted",
            "rt_dbf_undelete",
        ]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()

    def store_a_as_word(store_addr: int) -> None:
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )

    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    store_a_as_word(handle_store)
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8, 0xA0, 0x02])
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    store_a_as_word(moved_store)
    for helper_name, store_addr in [
        ("rt_dbf_delete", delok_store),
        ("rt_dbf_deleted", deleted_store),
        ("rt_dbf_undelete", undelok_store),
        ("rt_dbf_deleted", deleted2_store),
    ]:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
        code.extend(_jsr(module_addrs[helper_name]))
        store_a_as_word(store_addr)
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Delete/Undelete runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_append_runtime_tail() -> bytes:
    variable_count = 5
    root_len = 15 + (14 * 3) + 16 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    appended_store = store_base + 2
    total_store = store_base + 4
    recno_store = store_base + 6
    value_store = store_base + 8
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        [
            "rt_dbf_open",
            "rt_dbf_append",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_readbyte",
        ]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()

    def store_a_as_word(store_addr: int) -> None:
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )

    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    store_a_as_word(handle_store)
    for helper_name, store_addr in [
        ("rt_dbf_append", appended_store),
        ("rt_dbf_totalrecs", total_store),
        ("rt_dbf_currrecno", recno_store),
    ]:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
        code.extend(_jsr(module_addrs[helper_name]))
        store_a_as_word(store_addr)
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8, 0xA0, 0x01])
    code.extend(_jsr(module_addrs["rt_dbf_readbyte"]))
    store_a_as_word(value_store)
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Append runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_create_runtime_tail() -> bytes:
    variable_count = 6
    root_len = (
        15
        + 14
        + 14
        + 6
        + 15
        + 14
        + 16
        + len(_DIRECT_PRG_EXIT_MARKER)
        + (2 * variable_count)
    )
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    appended_store = store_base + 2
    saved_store = store_base + 4
    reopened_store = store_base + 6
    total_store = store_base + 8
    value_store = store_base + 10
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        [
            "rt_dbf_create",
            "rt_dbf_append",
            "rt_dbf_save",
            "rt_dbf_close",
            "rt_dbf_open",
            "rt_dbf_totalrecs",
            "rt_dbf_readbyte",
        ]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()

    def store_a_as_word(store_addr: int) -> None:
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )

    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_create"]))
    store_a_as_word(handle_store)
    for helper_name, store_addr in [
        ("rt_dbf_append", appended_store),
        ("rt_dbf_save", saved_store),
    ]:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
        code.extend(_jsr(module_addrs[helper_name]))
        store_a_as_word(store_addr)
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_close"]))
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    store_a_as_word(reopened_store)
    code.extend([0xAD, reopened_store & 0xFF, reopened_store >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_totalrecs"]))
    store_a_as_word(total_store)
    code.extend([0xAD, reopened_store & 0xFF, reopened_store >> 8, 0xA0, 0x00])
    code.extend(_jsr(module_addrs["rt_dbf_readbyte"]))
    store_a_as_word(value_store)
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Create runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_pack_runtime_tail() -> bytes:
    variable_count = 10
    root_len = (
        15
        + 16
        + (14 * 4)
        + 16
        + 16
        + 16
        + 14
        + len(_DIRECT_PRG_EXIT_MARKER)
        + (2 * variable_count)
    )
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    delok_store = store_base + 4
    packed_store = store_base + 6
    total_store = store_base + 8
    recno_store = store_base + 10
    moved2_store = store_base + 12
    value_store = store_base + 14
    moved3_store = store_base + 16
    recno2_store = store_base + 18
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_delete",
            "rt_dbf_pack",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_readbyte",
        ]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()

    def store_a_as_word(store_addr: int) -> None:
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )

    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    store_a_as_word(handle_store)
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8, 0xA0, 0x02])
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    store_a_as_word(moved_store)
    for helper_name, store_addr in [
        ("rt_dbf_delete", delok_store),
        ("rt_dbf_pack", packed_store),
        ("rt_dbf_totalrecs", total_store),
        ("rt_dbf_currrecno", recno_store),
    ]:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
        code.extend(_jsr(module_addrs[helper_name]))
        store_a_as_word(store_addr)
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8, 0xA0, 0x02])
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    store_a_as_word(moved2_store)
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8, 0xA0, 0x01])
    code.extend(_jsr(module_addrs["rt_dbf_readbyte"]))
    store_a_as_word(value_store)
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8, 0xA0, 0x03])
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    store_a_as_word(moved3_store)
    code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_currrecno"]))
    store_a_as_word(recno2_store)
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Pack runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_header_record_len_runtime_tail() -> bytes:
    variable_count = 3
    root_len = 15 + 14 + 14 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    headerlen_store = store_base + 2
    recordlen_store = store_base + 4
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(["rt_dbf_open", "rt_dbf_headerlen", "rt_dbf_recordlen"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
        ]
    )
    for helper_name, store_addr in [
        ("rt_dbf_headerlen", headerlen_store),
        ("rt_dbf_recordlen", recordlen_store),
    ]:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Header/RecordLen runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_close_state_reset_runtime_tail() -> bytes:
    variable_count = 3
    root_len = 15 + 6 + 14 + 14 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    total_store = store_base + 2
    recno_store = store_base + 4
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        ["rt_dbf_open", "rt_dbf_close", "rt_dbf_totalrecs", "rt_dbf_currrecno"]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_close"]))
    for helper_name, store_addr in [
        ("rt_dbf_totalrecs", total_store),
        ("rt_dbf_currrecno", recno_store),
    ]:
        code.extend([0xAD, handle_store & 0xFF, handle_store >> 8])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 Close state reset runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_invalid_record_field_runtime_tail() -> bytes:
    variable_count = 4
    root_len = 15 + 16 + 14 + 16 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    recno_store = store_base + 4
    fieldlen_store = store_base + 6
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        ["rt_dbf_open", "rt_dbf_go", "rt_dbf_currrecno", "rt_dbf_fieldlen"]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x04,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_currrecno"]))
    code.extend(
        [
            0x8D,
            recno_store & 0xFF,
            recno_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (recno_store + 1) & 0xFF,
            (recno_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_fieldlen"]))
    code.extend(
        [
            0x8D,
            fieldlen_store & 0xFF,
            fieldlen_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (fieldlen_store + 1) & 0xFF,
            (fieldlen_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 invalid record/field runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_read_byte_joystick_offset_runtime_tail() -> bytes:
    variable_count = 3
    root_len = 15 + 13 + 17 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    offset_store = store_base + 2
    value_store = store_base + 4
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(["rt_dbf_open", "rt_joy", "rt_dbf_readbyte"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xA9,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_joy"]))
    code.extend(
        [
            0x8D,
            offset_store & 0xFF,
            offset_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (offset_store + 1) & 0xFF,
            (offset_store + 1) >> 8,
            0xAC,
            offset_store & 0xFF,
            offset_store >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_readbyte"]))
    code.extend(
        [
            0x8D,
            value_store & 0xFF,
            value_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (value_store + 1) & 0xFF,
            (value_store + 1) >> 8,
        ]
    )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 ReadByte/Joy offset runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_dbf1_read_byte_sprite_color_runtime_tail() -> bytes:
    variable_count = 3
    root_len = 15 + 16 + 16 + 8 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    handle_store = store_base
    moved_store = store_base + 2
    value_store = store_base + 4
    filename_addr = DBF_FIXTURE_NAME_ADDR
    modules = _runtime_module_closure(
        ["rt_dbf_open", "rt_dbf_go", "rt_dbf_readbyte", "rt_sprite_color"]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    code.extend([0xA2, filename_addr & 0xFF, 0xA0, filename_addr >> 8])
    code.extend(_jsr(module_addrs["rt_dbf_open"]))
    code.extend(
        [
            0x8D,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (handle_store + 1) & 0xFF,
            (handle_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_go"]))
    code.extend(
        [
            0x8D,
            moved_store & 0xFF,
            moved_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (moved_store + 1) & 0xFF,
            (moved_store + 1) >> 8,
            0xAD,
            handle_store & 0xFF,
            handle_store >> 8,
            0xA0,
            0x01,
        ]
    )
    code.extend(_jsr(module_addrs["rt_dbf_readbyte"]))
    code.extend(
        [
            0x8D,
            value_store & 0xFF,
            value_store >> 8,
            0xA9,
            0x00,
            0x8D,
            (value_store + 1) & 0xFF,
            (value_store + 1) >> 8,
            0xAD,
            value_store & 0xFF,
            value_store >> 8,
            0xA2,
            0x02,
        ]
    )
    code.extend(_jsr(module_addrs["rt_sprite_color"]))
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected DBF1 ReadByte/SpriteColor runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_mouse_two_button_mask_runtime_tail() -> bytes:
    # MouseBtn() imports rt_mb, which should bring in rt_ms and no joystick code.
    variable_count = 2
    root_len = 11 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    button_store = store_base + 2
    modules = _runtime_module_closure(["rt_mb"])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        _jsr(module_addrs["rt_mb"])
        + bytes(
            [
                0x8D,
                button_store & 0xFF,
                button_store >> 8,
                0xA9,
                0x00,
                0x8D,
                (button_store + 1) & 0xFF,
                (button_store + 1) >> 8,
            ]
        )
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2 * variable_count)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected INPUT mouse mask runtime root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_joystick_store_runtime_tail() -> bytes:
    helper_names = ["rt_joy", "rt_jp"]
    store_count = len(helper_names)
    root_len = (2 + 3 + 8) * store_count + len(_DIRECT_PRG_EXIT_MARKER) + (2 * store_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * store_count)
    modules = _runtime_module_closure(helper_names)
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for index, helper_name in enumerate(helper_names):
        store_addr = store_base + (2 * index)
        code.extend([0xA9, 0x02])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * store_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected input joystick store runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_mouse_store_runtime_tail() -> bytes:
    helper_names = ["rt_mp", "rt_mx", "rt_my", "rt_mb"]
    store_count = len(helper_names)
    root_len = 13 + (11 * (store_count - 1)) + len(_DIRECT_PRG_EXIT_MARKER) + (2 * store_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * store_count)
    modules = _runtime_module_closure(helper_names)
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for index, helper_name in enumerate(helper_names):
        store_addr = store_base + (2 * index)
        if helper_name == "rt_mp":
            code.extend([0xA9, 0x01])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * store_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected input mouse store runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_variable_port_store_runtime_tail() -> bytes:
    helper_calls = [
        (1, "rt_joy", 0x02),
        (3, "rt_mp", 0x01),
    ]
    variable_count = 4
    root_len = (13 * len(helper_calls)) + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    modules = _runtime_module_closure([helper_name for _var_index, helper_name, _arg in helper_calls])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for var_index, helper_name, arg in helper_calls:
        store_addr = store_base + (2 * var_index)
        code.extend([0xA9, arg])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected INPUT variable-port runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_dual_port_presence_runtime_tail() -> bytes:
    helper_calls = [
        (0, "rt_jp", 0x01),
        (1, "rt_jp", 0x02),
        (2, "rt_mp", 0x01),
        (3, "rt_mp", 0x02),
        (4, "rt_mseen", None),
    ]
    variable_count = 5
    call_bytes = sum(
        (2 if arg is not None else 0) + 3 + 8
        for _var_index, _helper_name, arg in helper_calls
    )
    root_len = call_bytes + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    modules = _runtime_module_closure([helper_name for _var_index, helper_name, _arg in helper_calls])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for var_index, helper_name, arg in helper_calls:
        store_addr = store_base + (2 * var_index)
        if arg is not None:
            code.extend([0xA9, arg & 0xFF])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected INPUT dual-port presence runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input1_export_sample_runtime_tail() -> bytes:
    # The two literal mask assignments reserve variable slots in the linked
    # layout even though they are constant-propagated out of the root code.
    helper_calls = [
        (2, "rt_joy", 0x02),
        (3, "rt_jp", 0x02),
        (4, "rt_jb1", 0x02),
        (5, "rt_jb2", 0x02),
        (6, "rt_mp", 0x01),
        (7, "rt_mseen", None),
        (8, "rt_mx", None),
        (9, "rt_my", None),
        (10, "rt_mb", None),
        (11, "rt_mb1", None),
        (12, "rt_mb2", None),
    ]
    variable_count = 13
    call_bytes = sum((2 if arg is not None else 0) + 3 + 8 for _var_index, _helper_name, arg in helper_calls)
    root_len = call_bytes + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    modules = _runtime_module_closure([helper_name for _var_index, helper_name, _arg in helper_calls])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for var_index, helper_name, arg in helper_calls:
        store_addr = store_base + (2 * var_index)
        if arg is not None:
            code.extend([0xA9, arg])
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected INPUT1 export sample runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_side_effect_mixed_runtime_tail(
    side_effect_helper: str, side_effect_arg: int, label: str
) -> bytes:
    helper_calls = [
        (0, "rt_joy", 0x02, True),
        (1, "rt_mp", 0x01, True),
        (None, side_effect_helper, side_effect_arg, False),
    ]
    variable_count = 2
    root_len = (13 * 2) + 5 + len(_DIRECT_PRG_EXIT_MARKER) + (2 * variable_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * variable_count)
    modules = _runtime_module_closure(
        [helper_name for _var_index, helper_name, _arg, _store in helper_calls]
    )
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for var_index, helper_name, arg, stores_result in helper_calls:
        code.extend([0xA9, arg])
        code.extend(_jsr(module_addrs[helper_name]))
        if stores_result:
            if var_index is None:
                raise RuntimeError("stored helper call missing variable index")
            store_addr = store_base + (2 * var_index)
            code.extend(
                [
                    0x8D,
                    store_addr & 0xFF,
                    store_addr >> 8,
                    0xA9,
                    0x00,
                    0x8D,
                    (store_addr + 1) & 0xFF,
                    (store_addr + 1) >> 8,
                ]
            )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * variable_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected input/{label} mixed runtime root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_arg_mixed_runtime_tail(
    input_module: str, input_arg: int | None, side_effect_helper: str, label: str
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    input_call_len = (2 if input_arg is not None else 0) + 3
    root_len = input_call_len + 11 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    if input_arg is not None:
        code.extend([0xA9, input_arg])
    code.extend(_jsr(module_addrs[input_module]))
    code.extend(
        [
            0x8D,
            store_addr & 0xFF,
            store_addr >> 8,
            0xA9,
            0x00,
            0x8D,
            (store_addr + 1) & 0xFF,
            (store_addr + 1) >> 8,
            0xAD,
            store_addr & 0xFF,
            store_addr >> 8,
        ]
    )
    code = (
        bytes(code)
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(f"unexpected input/{label} result-arg runtime root size: {len(code)}")
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_word_arg_runtime_tail(
    input_module: str, input_arg: int, side_effect_helper: str, label: str
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 1 + 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xAA,
                0xA0,
                0x00,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(f"unexpected input/{label} word result-arg runtime root size: {len(code)}")
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_first_arg_word_second_runtime_tail(
    input_module: str,
    input_arg: int,
    side_effect_helper: str,
    second_arg: int,
    label: str,
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 2 + 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA2,
                second_arg & 0xFF,
                0xA0,
                second_arg >> 8,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} first-result second-word runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_second_arg_word_first_runtime_tail(
    input_module: str,
    input_arg: int,
    side_effect_helper: str,
    first_arg: int,
    label: str,
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 1 + 2 + 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xAA,
                0xA9,
                first_arg,
                0xA0,
                0x00,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} second-result first-word runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_second_arg_xa_runtime_tail(
    input_module: str, input_arg: int | None, side_effect_helper: str, first_arg: int, label: str
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    input_call_len = (2 if input_arg is not None else 0) + 3
    root_len = input_call_len + 13 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    if input_arg is not None:
        code.extend([0xA9, input_arg])
    code.extend(_jsr(module_addrs[input_module]))
    code.extend(
        [
            0x8D,
            store_addr & 0xFF,
            store_addr >> 8,
            0xA9,
            0x00,
            0x8D,
            (store_addr + 1) & 0xFF,
            (store_addr + 1) >> 8,
            0xAD,
            store_addr & 0xFF,
            store_addr >> 8,
            0xA2,
            first_arg,
        ]
    )
    code = (
        bytes(code)
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(f"unexpected input/{label} XA result-arg runtime root size: {len(code)}")
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_second_arg_x1_a0_runtime_tail(
    input_module: str, input_arg: int, side_effect_helper: str, first_arg: int, label: str
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 1 + 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xAA,
                0xA9,
                first_arg,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} X1/A0 result-arg runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_first_arg_xa_runtime_tail(
    input_module: str, input_arg: int, side_effect_helper: str, second_arg: int, label: str
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 1 + 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xAA,
                0xA9,
                second_arg,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} XA first-result runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_first_arg_ay_runtime_tail(
    input_module: str, input_arg: int, side_effect_helper: str, second_arg: int, label: str
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA0,
                second_arg,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} AY first-result runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_second_arg_ay_runtime_tail(
    input_module: str, input_arg: int, side_effect_helper: str, first_arg: int, label: str
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 1 + 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA8,
                0xA9,
                first_arg,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(f"unexpected input/{label} AY result-arg runtime root size: {len(code)}")
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_first_arg_axy_runtime_tail(
    input_module: str,
    input_arg: int,
    side_effect_helper: str,
    second_arg: int,
    third_arg: int,
    label: str,
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 2 + 2 + 1 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA2,
                second_arg,
                0xA0,
                third_arg,
                0x18,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} AXY first-result runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_second_arg_axy_runtime_tail(
    input_module: str,
    input_arg: int,
    side_effect_helper: str,
    first_arg: int,
    third_arg: int,
    label: str,
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 1 + 2 + 2 + 1 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xAA,
                0xA9,
                first_arg,
                0xA0,
                third_arg,
                0x18,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} AXY second-result runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_third_arg_axy_runtime_tail(
    input_module: str,
    input_arg: int,
    side_effect_helper: str,
    first_arg: int,
    second_arg: int,
    label: str,
) -> bytes:
    modules = _runtime_module_closure([input_module, side_effect_helper])
    root_len = 13 + 3 + 1 + 2 + 2 + 1 + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
                0xAD,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA8,
                0xA9,
                first_arg,
                0xA2,
                second_arg,
                0x18,
            ]
        )
        + _jsr(module_addrs[side_effect_helper])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(f"unexpected input/{label} AXY result-arg runtime root size: {len(code)}")
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_sprite_pos_runtime_tail(
    input_module: str,
    input_arg: int | None,
    pending_arg: int,
    sprite_arg: int,
    x_arg: int,
    y_arg: int,
    label: str,
) -> bytes:
    if pending_arg not in {0, 1, 2}:
        raise RuntimeError(f"unsupported SpritePos pending arg: {pending_arg}")
    if not 0 <= x_arg <= 0x1FF:
        raise RuntimeError(f"SpritePos X argument out of VIC-II range: {x_arg}")
    modules = _runtime_module_closure([input_module, "rt_sprite_pos"])
    setup_len = {0: 8, 1: 9, 2: 9}[pending_arg]
    input_call_len = (2 if input_arg is not None else 0) + 3
    root_len = input_call_len + 8 + setup_len + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    carry = 0x38 if x_arg > 0xFF else 0x18
    load_result = [
        0xAD,
        store_addr & 0xFF,
        store_addr >> 8,
    ]
    if pending_arg == 0:
        setup = load_result + [0xA2, x_arg & 0xFF, 0xA0, y_arg & 0xFF, carry]
    elif pending_arg == 1:
        setup = load_result + [0xAA, 0xA9, sprite_arg & 0xFF, 0xA0, y_arg & 0xFF, 0x18]
    else:
        setup = load_result + [0xA8, 0xA9, sprite_arg & 0xFF, 0xA2, x_arg & 0xFF, carry]
    code = bytearray()
    if input_arg is not None:
        code.extend([0xA9, input_arg])
    code.extend(_jsr(module_addrs[input_module]))
    code.extend(
        [
            0x8D,
            store_addr & 0xFF,
            store_addr >> 8,
            0xA9,
            0x00,
            0x8D,
            (store_addr + 1) & 0xFF,
            (store_addr + 1) >> 8,
        ]
    )
    code = (
        bytes(code)
        + bytes(setup)
        + _jsr(module_addrs["rt_sprite_pos"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} SpritePos result-arg runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_result_sprite_data_runtime_tail(
    input_module: str,
    input_arg: int,
    pending_arg: int,
    sprite_arg: int,
    addr_arg: int,
    label: str,
) -> bytes:
    if pending_arg not in {0, 1}:
        raise RuntimeError(f"unsupported SpriteData pending arg: {pending_arg}")
    if not 0 <= addr_arg <= 0xFFFF:
        raise RuntimeError(f"SpriteData address argument out of range: {addr_arg}")
    modules = _runtime_module_closure([input_module, "rt_sprite_data"])
    setup_len = {0: 7, 1: 8}[pending_arg]
    root_len = 13 + setup_len + 3 + len(_DIRECT_PRG_EXIT_MARKER) + 2
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len - 2
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    load_result = [
        0xAD,
        store_addr & 0xFF,
        store_addr >> 8,
    ]
    if pending_arg == 0:
        setup = load_result + [0xA2, addr_arg & 0xFF, 0xA0, addr_arg >> 8]
    else:
        setup = load_result + [0xAA, 0xA9, sprite_arg & 0xFF, 0xA0, 0x00]
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
        + bytes(setup)
        + _jsr(module_addrs["rt_sprite_data"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len - 2:
        raise RuntimeError(
            f"unexpected input/{label} SpriteData result-arg runtime root size: {len(code)}"
        )
    return code + bytes(2) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_gfx_mixed_runtime_tail() -> bytes:
    return _actc_input_side_effect_mixed_runtime_tail("rt_gfx_bgcolor", 0x06, "graphics")


def _actc_input_sid_mixed_runtime_tail() -> bytes:
    return _actc_input_side_effect_mixed_runtime_tail("rt_sid_vol", 0x0A, "SID")


def _actc_input_sprite_mixed_runtime_tail() -> bytes:
    return _actc_input_side_effect_mixed_runtime_tail("rt_sprite_on", 0x02, "sprite")


def _actc_input_math_mixed_runtime_tail(
    input_module: str = "rt_joy", input_arg: int = 2
) -> bytes:
    modules = _runtime_module_closure([input_module, "rt_i_to_f", "rt_print_f"])
    root_len = 47
    real_var = DIRECT_PRG_LOAD_ADDR + root_len
    module_addrs = _runtime_module_addrs(modules, real_var + 4)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + _set_zp_word(0x02, real_var)
        + bytes([0xA9, 0x07, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_var)
        + _jsr(module_addrs["rt_print_f"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected input/math mixed runtime root size: {len(code)}")
    return code + bytes(4) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_input_stored_math_mixed_runtime_tail(
    input_module: str = "rt_mp", input_arg: int = 1
) -> bytes:
    modules = _runtime_module_closure([input_module, "rt_i_to_f", "rt_print_f"])
    root_len = 55
    store_addr = DIRECT_PRG_LOAD_ADDR + root_len
    real_var = store_addr + 2
    module_addrs = _runtime_module_addrs(modules, real_var + 4)
    code = (
        bytes([0xA9, input_arg])
        + _jsr(module_addrs[input_module])
        + bytes(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
        + _set_zp_word(0x02, real_var)
        + bytes([0xA9, 0x07, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_var)
        + _jsr(module_addrs["rt_print_f"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(
            f"unexpected stored input/math mixed runtime root size: {len(code)}"
        )
    return code + bytes(6) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_card_variable_sprite_data_runtime_tail() -> bytes:
    modules = ["rt_sprite_data"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02, 0xA2, 0x00, 0xA0, 0x20])
        + _jsr(module_addrs["rt_sprite_data"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected CARD variable SpriteData root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_card_variable_sprite_pos_runtime_tail() -> bytes:
    modules = ["rt_sprite_pos"]
    root_len = 30
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02, 0xA2, 0x34, 0xA0, 0x56, 0x38])
        + _jsr(module_addrs["rt_sprite_pos"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected CARD variable SpritePos root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_freq_runtime_tail() -> bytes:
    modules = ["rt_sid_freq"]
    root_len = 29
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01, 0xA2, 0x34, 0xA0, 0x12])
        + _jsr(module_addrs["rt_sid_freq"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidFreq root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_pulse_runtime_tail() -> bytes:
    modules = ["rt_sid_pulse"]
    root_len = 29
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01, 0xA2, 0x34, 0xA0, 0x12])
        + _jsr(module_addrs["rt_sid_pulse"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidPulse root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_wave_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_wave"])
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01, 0xA0, 0x40])
        + _jsr(module_addrs["rt_sid_wave"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidWave root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_ad_runtime_tail() -> bytes:
    modules = ["rt_sid_ad"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01, 0xA0, 0x97])
        + _jsr(module_addrs["rt_sid_ad"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidAD root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_sr_runtime_tail() -> bytes:
    modules = ["rt_sid_sr"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01, 0xA0, 0xF8])
        + _jsr(module_addrs["rt_sid_sr"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidSR root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_on_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_on"])
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01])
        + _jsr(module_addrs["rt_sid_on"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidOn root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_off_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_off"])
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01])
        + _jsr(module_addrs["rt_sid_off"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidOff root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_vol_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_vol"])
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x0A])
        + _jsr(module_addrs["rt_sid_vol"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidVol root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_reassigned_level_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_vol", "rt_sid_mode"])
    root_len = 30
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_sid_vol"])
        + bytes([0xA9, 0x30])
        + _jsr(module_addrs["rt_sid_mode"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected reassigned variable SID root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_mode_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_mode"])
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x30])
        + _jsr(module_addrs["rt_sid_mode"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidMode root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_route_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_route"])
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x07])
        + _jsr(module_addrs["rt_sid_route"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidRoute root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_res_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_res"])
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x0A])
        + _jsr(module_addrs["rt_sid_res"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidRes root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sid_cutoff_runtime_tail() -> bytes:
    modules = ["rt_sid_cutoff"]
    root_len = 25
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA2, 0x34, 0xA0, 0x12])
        + _jsr(module_addrs["rt_sid_cutoff"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SidCutoff root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_gfx_bgcolor_runtime_tail() -> bytes:
    modules = ["rt_gfx_bgcolor"]
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x06])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable BgColor root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_gfx_bordercolor_runtime_tail() -> bytes:
    modules = ["rt_gfx_bordercolor"]
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x1E])
        + _jsr(module_addrs["rt_gfx_bordercolor"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable BorderColor root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_gfx_reassigned_color_runtime_tail() -> bytes:
    modules = ["rt_gfx_bgcolor", "rt_gfx_bordercolor"]
    root_len = 30
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + bytes([0xA9, 0x1E])
        + _jsr(module_addrs["rt_gfx_bordercolor"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected reassigned variable GFX root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_gfx_vic_bank_runtime_tail() -> bytes:
    modules = ["rt_gfx_vic_bank"]
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x01])
        + _jsr(module_addrs["rt_gfx_vic_bank"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable VicBank root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_card_variable_gfx_screen_base_runtime_tail() -> bytes:
    modules = ["rt_gfx_screen_base"]
    root_len = 25
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA2, 0x00, 0xA0, 0x04])
        + _jsr(module_addrs["rt_gfx_screen_base"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected CARD variable ScreenBase root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_card_variable_gfx_bitmap_base_runtime_tail() -> bytes:
    modules = ["rt_gfx_bitmap_base"]
    root_len = 25
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA2, 0x00, 0xA0, 0x20])
        + _jsr(module_addrs["rt_gfx_bitmap_base"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected CARD variable BitmapBase root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_gfx_cell_runtime_tail(module_name: str, x: int, y: int, value: int) -> bytes:
    modules = [module_name]
    root_len = 32
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, x & 0xFF, 0xA2, y & 0xFF, 0xA0, value & 0xFF, 0x18])
        + _jsr(module_addrs[module_name])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(6)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable {module_name} root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_card_variable_gfx_copy_runtime_tail(module_name: str, source_addr: int) -> bytes:
    modules = [module_name]
    root_len = 25
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA2, source_addr & 0xFF, 0xA0, (source_addr >> 8) & 0xFF])
        + _jsr(module_addrs[module_name])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable {module_name} root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_gfx_byte_runtime_tail(module_name: str, value: int) -> bytes:
    modules = [module_name]
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, value & 0xFF])
        + _jsr(module_addrs[module_name])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable {module_name} root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_color_runtime_tail() -> bytes:
    modules = ["rt_sprite_color"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA2, 0x02, 0xA9, 0x06])
        + _jsr(module_addrs["rt_sprite_color"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SpriteColor root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_reassigned_color_runtime_tail() -> bytes:
    modules = ["rt_gfx_bgcolor", "rt_sprite_color"]
    root_len = 32
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_gfx_bgcolor"])
        + bytes([0xA2, 0x02, 0xA9, 0x06])
        + _jsr(module_addrs["rt_sprite_color"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected reassigned variable sprite root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_on_runtime_tail() -> bytes:
    modules = ["rt_sprite_on"]
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_sprite_on"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SpriteOn root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_off_runtime_tail() -> bytes:
    modules = ["rt_sprite_off"]
    root_len = 23
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02])
        + _jsr(module_addrs["rt_sprite_off"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(2)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SpriteOff root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_ptr_runtime_tail() -> bytes:
    modules = ["rt_sprite_ptr"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA2, 0x02, 0xA9, 0x80])
        + _jsr(module_addrs["rt_sprite_ptr"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SpritePtr root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_mc_runtime_tail(flag: int) -> bytes:
    modules = ["rt_sprite_mc"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02, 0xA0, flag & 0xFF])
        + _jsr(module_addrs["rt_sprite_mc"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SpriteMC root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_xexp_runtime_tail(flag: int) -> bytes:
    modules = ["rt_sprite_xexp"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02, 0xA0, flag & 0xFF])
        + _jsr(module_addrs["rt_sprite_xexp"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SpriteXExp root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_yexp_runtime_tail(flag: int) -> bytes:
    modules = ["rt_sprite_yexp"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02, 0xA0, flag & 0xFF])
        + _jsr(module_addrs["rt_sprite_yexp"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SpriteYExp root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_prio_runtime_tail(flag: int) -> bytes:
    modules = ["rt_sprite_prio"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x02, 0xA0, flag & 0xFF])
        + _jsr(module_addrs["rt_sprite_prio"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SpritePrio root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_sprite_set_mc_runtime_tail() -> bytes:
    modules = ["rt_sprite_set_mc"]
    root_len = 27
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA2, 0x0A, 0xA9, 0x05])
        + _jsr(module_addrs["rt_sprite_set_mc"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable SetSpriteMC root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_variable_mixed_gfx_sprite_runtime_tail() -> bytes:
    modules = ["rt_gfx_screen_cell", "rt_sprite_ptr", "rt_gfx_bitmap_fill"]
    root_len = 50
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x05, 0xA2, 0x02, 0xA0, 0x41, 0x18])
        + _jsr(module_addrs["rt_gfx_screen_cell"])
        + bytes([0xA2, 0x02, 0xA9, 0x80])
        + _jsr(module_addrs["rt_sprite_ptr"])
        + bytes([0xA9, 0x3C])
        + _jsr(module_addrs["rt_gfx_bitmap_fill"])
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(12)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected variable mixed graphics/sprite root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_mixed_hardware_runtime_tail() -> bytes:
    modules = ["rt_gfx_bordercolor", "rt_sid_pulse", "rt_sprite_color", "rt_gfx_screen_base"]
    root_len = 44
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, 0x1E])
        + _jsr(module_addrs["rt_gfx_bordercolor"])
        + bytes([0xA9, 0x01, 0xA2, 0x34, 0xA0, 0x12])
        + _jsr(module_addrs["rt_sid_pulse"])
        + bytes([0xA2, 0x02, 0xA9, 0x06])
        + _jsr(module_addrs["rt_sprite_color"])
        + bytes([0xA2, 0x00, 0xA0, 0x04])
        + _jsr(module_addrs["rt_gfx_screen_base"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected mixed hardware root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_no_arg_hardware_runtime_tail() -> bytes:
    modules = _runtime_module_closure(["rt_sid_rst", "rt_gfx_bitmap_on", "rt_gfx_mbitmap_on"])
    root_len = 25
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        _jsr(module_addrs["rt_sid_rst"])
        + _jsr(module_addrs["rt_gfx_bitmap_on"])
        + _jsr(module_addrs["rt_gfx_mbitmap_on"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected no-arg hardware root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_stateful_byte_hardware_runtime_tail() -> bytes:
    call_specs: list[tuple[str, str, int, int | None]] = [
        ("ay", "rt_sid_wave", 1, 64),
        ("ay", "rt_sid_ad", 1, 151),
        ("ay", "rt_sid_sr", 1, 248),
        ("a", "rt_sid_on", 1, None),
        ("a", "rt_sid_off", 1, None),
        ("a", "rt_sid_vol", 10, None),
        ("a", "rt_sid_mode", 48, None),
        ("a", "rt_sid_route", 7, None),
        ("a", "rt_sid_res", 10, None),
        ("a", "rt_sprite_on", 2, None),
        ("a", "rt_sprite_off", 2, None),
        ("a", "rt_gfx_vic_bank", 1, None),
        ("ay", "rt_sprite_mc", 2, 1),
        ("ay", "rt_sprite_xexp", 2, 1),
        ("ay", "rt_sprite_yexp", 2, 1),
        ("ay", "rt_sprite_prio", 2, 1),
    ]
    root_len = len(_DIRECT_PRG_EXIT_MARKER) + sum(7 if kind == "ay" else 5 for kind, _, _, _ in call_specs)
    modules = _runtime_module_closure([name for _, name, _, _ in call_specs])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for kind, name, arg0, arg1 in call_specs:
        if kind == "ay":
            if arg1 is None:
                raise RuntimeError(f"missing AY helper second argument for {name}")
            code.extend([0xA9, arg0 & 0xFF, 0xA0, arg1 & 0xFF])
        else:
            code.extend([0xA9, arg0 & 0xFF])
        code.extend(_jsr(module_addrs[name]))
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    if len(code) != root_len:
        raise RuntimeError(f"unexpected stateful byte hardware root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_word_copy_fill_runtime_tail() -> bytes:
    call_specs: list[tuple[str, str, int]] = [
        ("a", "rt_gfx_bitmap_fill", 0xAA),
        ("xy", "rt_gfx_screen_copy", 0x2000),
        ("xy", "rt_gfx_color_copy", 0x2000),
        ("xy", "rt_gfx_bitmap_copy", 0x2000),
        ("xy", "rt_sid_cutoff", 0x1234),
    ]
    root_len = len(_DIRECT_PRG_EXIT_MARKER) + sum(5 if kind == "a" else 7 for kind, _, _ in call_specs)
    modules = _runtime_module_closure([name for _, name, _ in call_specs])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for kind, name, arg0 in call_specs:
        if kind == "xy":
            code.extend([0xA2, arg0 & 0xFF, 0xA0, (arg0 >> 8) & 0xFF])
        else:
            code.extend([0xA9, arg0 & 0xFF])
        code.extend(_jsr(module_addrs[name]))
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    if len(code) != root_len:
        raise RuntimeError(f"unexpected word/copy/fill root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_remaining_hardware_runtime_tail() -> bytes:
    call_specs: list[tuple[str, str, int, int | None]] = [
        ("xy", "rt_gfx_bitmap_base", 0x2000, None),
        ("none", "rt_gfx_bitmap_off", 0, None),
        ("none", "rt_sid_osc3", 0, None),
        ("none", "rt_sid_env3", 0, None),
        ("none", "rt_sprite_hit", 0, None),
        ("none", "rt_sprite_hit_bg", 0, None),
        ("xa", "rt_sprite_ptr", 2, 0x80),
        ("xa", "rt_sprite_set_mc", 10, 5),
    ]
    root_len = len(_DIRECT_PRG_EXIT_MARKER) + sum(
        7 if kind in {"xy", "xa"} else 3 for kind, _, _, _ in call_specs
    )
    modules = _runtime_module_closure([name for _, name, _, _ in call_specs])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for kind, name, arg0, arg1 in call_specs:
        if kind == "xy":
            code.extend([0xA2, arg0 & 0xFF, 0xA0, (arg0 >> 8) & 0xFF])
        elif kind == "xa":
            if arg1 is None:
                raise RuntimeError(f"missing XA helper second argument for {name}")
            code.extend([0xA2, arg0 & 0xFF, 0xA9, arg1 & 0xFF])
        elif kind != "none":
            raise RuntimeError(f"unsupported helper call kind: {kind}")
        code.extend(_jsr(module_addrs[name]))
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    if len(code) != root_len:
        raise RuntimeError(f"unexpected remaining hardware helper root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_byte_readback_store_tail(helper_name: str) -> bytes:
    return _actc_byte_readback_multi_store_tail([helper_name])


def _actc_byte_readback_multi_store_tail(helper_names: list[str]) -> bytes:
    if not helper_names:
        raise RuntimeError("byte readback store helper list must not be empty")
    store_count = len(helper_names)
    root_len = (3 + 8) * store_count + len(_DIRECT_PRG_EXIT_MARKER) + (2 * store_count)
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - (2 * store_count)
    modules = _runtime_module_closure(helper_names)
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for index, helper_name in enumerate(helper_names):
        store_addr = store_base + (2 * index)
        code.extend(_jsr(module_addrs[helper_name]))
        code.extend(
            [
                0x8D,
                store_addr & 0xFF,
                store_addr >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_addr + 1) & 0xFF,
                (store_addr + 1) >> 8,
            ]
        )
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    code.extend(bytes(2 * store_count))
    if len(code) != root_len:
        raise RuntimeError(f"unexpected byte readback store root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_byte_readback_store_copy_tail(helper_name: str) -> bytes:
    root_len = 3 + 8 + 3 + 8 + len(_DIRECT_PRG_EXIT_MARKER) + 4
    store_base = DIRECT_PRG_LOAD_ADDR + root_len - 4
    modules = _runtime_module_closure([helper_name])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        _jsr(module_addrs[helper_name])
        + bytes(
            [
                0x8D,
                store_base & 0xFF,
                store_base >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_base + 1) & 0xFF,
                (store_base + 1) >> 8,
                0xAD,
                store_base & 0xFF,
                store_base >> 8,
                0x8D,
                (store_base + 2) & 0xFF,
                (store_base + 2) >> 8,
                0xA9,
                0x00,
                0x8D,
                (store_base + 3) & 0xFF,
                (store_base + 3) >> 8,
            ]
        )
        + _DIRECT_PRG_EXIT_MARKER
        + bytes(4)
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected byte readback store-copy root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_cell_runtime_tail() -> bytes:
    call_specs = [
        ("rt_gfx_screen_cell", 5, 2, 65),
        ("rt_gfx_color_cell", 6, 3, 10),
    ]
    root_len = len(_DIRECT_PRG_EXIT_MARKER) + (10 * len(call_specs))
    modules = _runtime_module_closure([name for name, _, _, _ in call_specs])
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytearray()
    for name, arg0, arg1, arg2 in call_specs:
        code.extend([0xA9, arg0 & 0xFF, 0xA2, arg1 & 0xFF, 0xA0, arg2 & 0xFF, 0x18])
        code.extend(_jsr(module_addrs[name]))
    code.extend(_DIRECT_PRG_EXIT_MARKER)
    if len(code) != root_len:
        raise RuntimeError(f"unexpected cell helper root size: {len(code)}")
    return bytes(code) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _actc_gfx_cell_single_runtime_tail(module_name: str, x: int, y: int, value: int) -> bytes:
    modules = [module_name]
    root_len = len(_DIRECT_PRG_EXIT_MARKER) + 10
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        bytes([0xA9, x & 0xFF, 0xA2, y & 0xFF, 0xA0, value & 0xFF, 0x18])
        + _jsr(module_addrs[module_name])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected single GFX cell root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _store_word_literal(addr: int, value: int) -> bytes:
    return bytes(
        [
            0xA9,
            value & 0xFF,
            0xA2,
            0x00,
            0x8D,
            addr & 0xFF,
            addr >> 8,
            0x8E,
            (addr + 1) & 0xFF,
            addr >> 8,
        ]
    )


def _real_printre_int_tail(value: int) -> bytes:
    modules = ["rt_i_to_f", "rt_print_f"]
    module_addrs = _runtime_module_addrs(modules, 0x102E)
    real_var = 0x102A
    code = (
        _set_zp_word(0x02, real_var)
        + bytes([0xA9, value & 0xFF, 0xA2, (value >> 8) & 0xFF])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_var)
        + _jsr(module_addrs["rt_print_f"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != 42:
        raise RuntimeError(f"unexpected REAL PrintRE integer root size: {len(code)}")
    return code + bytes(4) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _runtime_real_i_to_f_helper_tail(value: int) -> bytes:
    modules = ["rt_i_to_f"]
    root_len = 31
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = (
        _set_zp_word(0x02, 0x03D1)
        + bytes([0xA9, value & 0xFF, 0xA2, (value >> 8) & 0xFF])
        + _jsr(module_addrs["rt_i_to_f"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected rt_i_to_f helper root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_to_int_tail(value: int) -> bytes:
    modules = ["rt_i_to_f", "rt_f_to_i"]
    root_len = 48
    real_var = DIRECT_PRG_LOAD_ADDR + root_len
    int_var = real_var + 4
    module_addrs = _runtime_module_addrs(modules, int_var + 2)
    code = (
        _set_zp_word(0x02, real_var)
        + bytes([0xA9, value & 0xFF, 0xA2, (value >> 8) & 0xFF])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_var)
        + _jsr(module_addrs["rt_f_to_i"])
        + bytes([0x8D, int_var & 0xFF, int_var >> 8, 0x8E, (int_var + 1) & 0xFF, (int_var + 1) >> 8])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != root_len:
        raise RuntimeError(f"unexpected REAL INT root size: {len(code)}")
    return code + bytes(6) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_printre_binary_tail(left: int, right: int, op_module: str) -> bytes:
    modules = ["rt_i_to_f", op_module, "rt_print_f", "rt_s_to_f"]
    module_addrs = _runtime_module_addrs(modules, 0x1060)
    real_a = 0x1054
    real_b = 0x1058
    real_x = 0x105C
    code = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, left & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_b)
        + bytes([0xA9, right & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_b)
        + _set_zp_word(0x06, real_x)
        + _jsr(module_addrs[op_module])
        + _set_zp_word(0x02, real_x)
        + _jsr(module_addrs["rt_print_f"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != 84:
        raise RuntimeError(f"unexpected REAL PrintRE binary root size: {len(code)}")
    return code + bytes(12) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_printre_fabs_tail(value: int) -> bytes:
    modules = ["rt_s_to_f", "rt_f_abs", "rt_print_f"]
    module_addrs = _runtime_module_addrs(modules, 0x1045)
    real_a = 0x103D
    real_x = 0x1041
    code = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, value & 0xFF, 0xA2, (value >> 8) & 0xFF])
        + _jsr(module_addrs["rt_s_to_f"])
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x06, real_x)
        + _jsr(module_addrs["rt_f_abs"])
        + _set_zp_word(0x02, real_x)
        + _jsr(module_addrs["rt_print_f"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != 61:
        raise RuntimeError(f"unexpected REAL PrintRE FAbs root size: {len(code)}")
    return code + bytes(8) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_printre_fsqrt_tail(value: int) -> bytes:
    modules = ["rt_i_to_f", "rt_f_sqrt", "rt_print_f"]
    module_addrs = _runtime_module_addrs(modules, 0x1045)
    real_a = 0x103D
    real_x = 0x1041
    code = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, value & 0xFF, 0xA2, (value >> 8) & 0xFF])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x06, real_x)
        + _jsr(module_addrs["rt_f_sqrt"])
        + _set_zp_word(0x02, real_x)
        + _jsr(module_addrs["rt_print_f"])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != 61:
        raise RuntimeError(f"unexpected REAL PrintRE FSqrt root size: {len(code)}")
    return code + bytes(8) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_if_cmp_tail(
    left: int,
    right: int,
    store_value: int,
    cmp_value: int,
    skip_opcode: int = 0xD0,
    else_value: int | None = None,
) -> bytes:
    modules = ["rt_i_to_f", "rt_f_cmp"]
    has_else = else_value is not None
    module_base = 0x1074 if has_else else 0x1066
    module_addrs = _runtime_module_addrs(modules, module_base)
    real_a = 0x106A if has_else else 0x105C
    real_b = 0x106E if has_else else 0x1060
    word_y = 0x1072 if has_else else 0x1064
    condition_store = bytes(
        [
            0xC9,
            cmp_value & 0xFF,
            skip_opcode & 0xFF,
            0x0E if else_value is not None else 0x0A,
        ]
    ) + _store_word_literal(word_y, store_value)
    if else_value is not None:
        condition_store += bytes([0xA9, 0x01, 0xD0, 0x0A]) + _store_word_literal(
            word_y, else_value
        )
    code = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, left & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_b)
        + bytes([0xA9, right & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_b)
        + _jsr(module_addrs["rt_f_cmp"])
        + condition_store
        + bytes(
            [
                0xAD,
                word_y & 0xFF,
                word_y >> 8,
                0xAE,
                (word_y + 1) & 0xFF,
                word_y >> 8,
                0x8D,
                0xD1,
                0x03,
                0x8E,
                0xD2,
                0x03,
            ]
        )
        + bytes([0xEA])
        + _DIRECT_PRG_EXIT_MARKER
    )
    expected_len = 106 if else_value is not None else 92
    if len(code) != expected_len:
        raise RuntimeError(f"unexpected REAL IF comparison root size: {len(code)}")
    return code + bytes(10) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_nested_if_cmp_tail(
    left: int,
    right: int,
    store_value: int,
    cmp_value: int,
    skip_opcode: int = 0xD0,
) -> bytes:
    modules = ["rt_i_to_f", "rt_f_cmp"]
    module_addrs = _runtime_module_addrs(modules, 0x107E)
    real_a = 0x1074
    real_b = 0x1078
    word_y = 0x107C
    condition_store = bytes([0xC9, cmp_value & 0xFF, skip_opcode & 0xFF, 0x0A]) + _store_word_literal(
        word_y, store_value
    )
    inner_if = (
        _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_b)
        + _jsr(module_addrs["rt_f_cmp"])
        + condition_store
    )
    code = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, left & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_b)
        + bytes([0xA9, right & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_b)
        + _jsr(module_addrs["rt_f_cmp"])
        + bytes([0xC9, cmp_value & 0xFF, skip_opcode & 0xFF, len(inner_if)])
        + inner_if
        + bytes(
            [
                0xAD,
                word_y & 0xFF,
                word_y >> 8,
                0xAE,
                (word_y + 1) & 0xFF,
                word_y >> 8,
                0x8D,
                0xD1,
                0x03,
                0x8E,
                0xD2,
                0x03,
            ]
        )
        + bytes([0xEA, 0xEA])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(inner_if) != 33 or len(code) != 116:
        raise RuntimeError(f"unexpected nested REAL IF comparison sizes: {len(inner_if)}, {len(code)}")
    return code + bytes(10) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _store_real_literal(addr: int, value: int) -> bytes:
    return bytes(
        [
            0xA9,
            value & 0xFF,
            0x8D,
            addr & 0xFF,
            addr >> 8,
            0x8D,
            (addr + 1) & 0xFF,
            addr >> 8,
            0x8D,
            (addr + 2) & 0xFF,
            addr >> 8,
            0x8D,
            (addr + 3) & 0xFF,
            addr >> 8,
        ]
    )


def _store_real_zero(addr: int) -> bytes:
    return _store_real_literal(addr, 0)


def _real_do_until_cmp_tail(
    initial_right: int,
    loop_left: int,
    store_value: int,
    cmp_value: int,
    branch_opcode: int = 0xD0,
) -> bytes:
    modules = ["rt_i_to_f", "rt_f_cmp"]
    module_addrs = _runtime_module_addrs(modules, 0x1074)
    real_a = 0x106A
    real_b = 0x106E
    word_y = 0x1072
    prefix = (
        _store_real_zero(real_a)
        + _set_zp_word(0x02, real_b)
        + bytes([0xA9, initial_right & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
    )
    loop_start = len(prefix)
    loop_body = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, loop_left & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_b)
        + _jsr(module_addrs["rt_f_cmp"])
    )
    branch_after = loop_start + len(loop_body) + 4
    branch_back = (loop_start - branch_after) & 0xFF
    code = (
        prefix
        + loop_body
        + bytes([0xC9, cmp_value & 0xFF, branch_opcode & 0xFF, branch_back])
        + _store_word_literal(word_y, store_value)
        + bytes(
            [
                0xAD,
                word_y & 0xFF,
                word_y >> 8,
                0xAE,
                (word_y + 1) & 0xFF,
                word_y >> 8,
                0x8D,
                0xD1,
                0x03,
                0x8E,
                0xD2,
                0x03,
            ]
        )
        + bytes([0xEA])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != 106 or branch_back != 0xDA:
        raise RuntimeError(f"unexpected REAL DO/UNTIL sizes: {len(code)}, branch 0x{branch_back:02X}")
    return code + bytes(10) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_while_cmp_once_tail(
    initial_left: int,
    initial_right: int,
    store_value: int,
    cmp_value: int,
    branch_opcode: int = 0xD0,
    loop_update_value: int = 0,
    loop_update_target: str = "a",
    loop_update_uses_conversion: bool = False,
) -> bytes:
    modules = ["rt_i_to_f", "rt_f_cmp"]
    layout_shift = 1 if loop_update_uses_conversion else 0
    module_addrs = _runtime_module_addrs(modules, 0x1077 + layout_shift)
    real_a = 0x106D + layout_shift
    real_b = 0x1071 + layout_shift
    word_y = 0x1075 + layout_shift
    prefix = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, initial_left & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_b)
        + bytes([0xA9, initial_right & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
    )
    loop_start = len(prefix)
    if loop_update_target == "a":
        loop_update_addr = real_a
    elif loop_update_target == "b":
        loop_update_addr = real_b
    else:
        raise RuntimeError(f"unsupported REAL WHILE update target: {loop_update_target}")
    if loop_update_uses_conversion:
        loop_update = (
            _set_zp_word(0x02, loop_update_addr)
            + bytes([0xA9, loop_update_value & 0xFF, 0xA2, 0x00])
            + _jsr(module_addrs["rt_i_to_f"])
        )
    else:
        loop_update = _store_real_literal(loop_update_addr, loop_update_value)
    loop_body = _store_word_literal(word_y, store_value) + loop_update
    branch_after = loop_start + 8 + 8 + 3 + 4
    branch_skip = len(loop_body) + 3
    loop_addr = DIRECT_PRG_LOAD_ADDR + loop_start
    code = (
        prefix
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_b)
        + _jsr(module_addrs["rt_f_cmp"])
        + bytes([0xC9, cmp_value & 0xFF, branch_opcode & 0xFF, branch_skip])
        + loop_body
        + bytes([0x4C, loop_addr & 0xFF, loop_addr >> 8])
        + bytes(
            [
                0xAD,
                word_y & 0xFF,
                word_y >> 8,
                0xAE,
                (word_y + 1) & 0xFF,
                word_y >> 8,
                0x8D,
                0xD1,
                0x03,
                0x8E,
                0xD2,
                0x03,
            ]
        )
        + bytes([0xEA])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != 109 + layout_shift or loop_start != 30 or branch_after != 53 or branch_skip != 27 + layout_shift:
        raise RuntimeError(
            f"unexpected REAL WHILE sizes: {len(code)}, loop {loop_start}, "
            f"condition {branch_after}, skip {branch_skip}"
        )
    return code + bytes(10) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_while_real_binary_loop_tail(
    initial_left: int,
    initial_right: int,
    step_value: int,
    store_value: int,
    op_module: str,
    cmp_value: int,
    branch_opcode: int = 0xD0,
) -> bytes:
    modules = ["rt_i_to_f", "rt_f_cmp", op_module, "rt_s_to_f"]
    module_addrs = _runtime_module_addrs(modules, 0x1097)
    real_a = 0x1089
    real_b = 0x108D
    real_c = 0x1091
    word_y = 0x1095
    prefix = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, initial_left & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_b)
        + bytes([0xA9, initial_right & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_c)
        + bytes([0xA9, step_value & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
    )
    loop_start = len(prefix)
    loop_update = (
        _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_c)
        + _set_zp_word(0x06, real_a)
        + _jsr(module_addrs[op_module])
    )
    loop_body = _store_word_literal(word_y, store_value) + loop_update
    branch_skip = len(loop_body) + 3
    loop_addr = DIRECT_PRG_LOAD_ADDR + loop_start
    code = (
        prefix
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_b)
        + _jsr(module_addrs["rt_f_cmp"])
        + bytes([0xC9, cmp_value & 0xFF, branch_opcode & 0xFF, branch_skip])
        + loop_body
        + bytes([0x4C, loop_addr & 0xFF, loop_addr >> 8])
        + bytes(
            [
                0xAD,
                word_y & 0xFF,
                word_y >> 8,
                0xAE,
                (word_y + 1) & 0xFF,
                word_y >> 8,
                0x8D,
                0xD1,
                0x03,
                0x8E,
                0xD2,
                0x03,
            ]
        )
        + bytes([0xEA])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != 137 or loop_start != 45 or branch_skip != 40:
        raise RuntimeError(
            f"unexpected REAL WHILE sub-loop sizes: {len(code)}, loop {loop_start}, "
            f"skip {branch_skip}"
        )
    return code + bytes(14) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


def _real_do_until_real_binary_loop_tail(
    initial_left: int,
    initial_right: int,
    step_value: int,
    store_value: int,
    op_module: str,
    cmp_value: int,
    branch_opcode: int = 0xD0,
) -> bytes:
    modules = ["rt_i_to_f", op_module, "rt_f_cmp", "rt_s_to_f"]
    module_addrs = _runtime_module_addrs(modules, 0x1094)
    real_a = 0x1086
    real_b = 0x108A
    real_c = 0x108E
    word_y = 0x1092
    prefix = (
        _set_zp_word(0x02, real_a)
        + bytes([0xA9, initial_left & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_b)
        + bytes([0xA9, initial_right & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
        + _set_zp_word(0x02, real_c)
        + bytes([0xA9, step_value & 0xFF, 0xA2, 0x00])
        + _jsr(module_addrs["rt_i_to_f"])
    )
    loop_start = len(prefix)
    loop_update = (
        _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_c)
        + _set_zp_word(0x06, real_a)
        + _jsr(module_addrs[op_module])
    )
    loop_body = (
        loop_update
        + _set_zp_word(0x02, real_a)
        + _set_zp_word(0x04, real_b)
        + _jsr(module_addrs["rt_f_cmp"])
    )
    branch_after = loop_start + len(loop_body) + 4
    branch_back = (loop_start - branch_after) & 0xFF
    code = (
        prefix
        + loop_body
        + bytes([0xC9, cmp_value & 0xFF, branch_opcode & 0xFF, branch_back])
        + _store_word_literal(word_y, store_value)
        + bytes(
            [
                0xAD,
                word_y & 0xFF,
                word_y >> 8,
                0xAE,
                (word_y + 1) & 0xFF,
                word_y >> 8,
                0x8D,
                0xD1,
                0x03,
                0x8E,
                0xD2,
                0x03,
            ]
        )
        + bytes([0xEA])
        + _DIRECT_PRG_EXIT_MARKER
    )
    if len(code) != 134 or loop_start != 45 or branch_back != 0xCE:
        raise RuntimeError(
            f"unexpected REAL DO/UNTIL binary sizes: {len(code)}, loop {loop_start}, "
            f"branch 0x{branch_back:02X}"
        )
    return code + bytes(14) + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


DIRECT_PRG_CASES: dict[str, dict[str, object]] = {
    "single_call": {
        "source": "MODULE MAIN\rPROC A()\rRETURN\rPROC MAIN()\rA()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 20\n",
            "x a 19 1\n",
            "b M\n",
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
        ],
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
    },
    "fanout": {
        "source": "MODULE MAIN\rPROC A()\rRETURN\rPROC B()\rA()\rRETURN\rPROC MAIN()\rA()\rB()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 27\n",
            "x b 22 4\n",
            "x a 26 1\n",
            "b M\n",
            "m 20 1A 10 20 16 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 1A 10 60 60\n",
        ],
        "expected_tail": bytes.fromhex("201A10201610A9A58DD003A90085028503A2024C0FCF201A106060"),
    },
    "local_chain_mixed_call": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "RETURN\r"
            "PROC B()\r"
            "A()\r"
            "RETURN\r"
            "PROC C()\r"
            "B()\r"
            "A()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "C()\r"
            "B()\r"
            "A()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 37\n",
            "x c 25 7\n",
            "x b 32 4\n",
            "x a 36 1\n",
            "b M\n",
            "m 20 19 10 20 20 10 20 24 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 20 10 20 24 10 60 20 24 10 60 60\n",
        ],
        "expected_tail": bytes.fromhex(
            "201910202010202410A9A58DD003A90085028503A2024C0FCF202010202410602024106060"
        ),
    },
    "local_external_chain_mixed_call": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "RETURN\r"
            "PROC B()\r"
            "A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "B()\r"
            "A()\r"
            "Other()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 33\n",
            "x b 25 7\n",
            "x a 32 1\n",
            "b u1u0M\n",
            "b u0M\n",
            "b M\n",
            "u helper\n",
            "u other\n",
            "m 20 19 10 20 20 10 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 20 10 20 00 00 60 60\n",
            "r 7 u1\n",
            "r 29 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "OTHER.OBJ": "OBJ1\nx other 0 1\nb M\nm 60\nn other\n",
        },
        "expected_tail": bytes.fromhex(
            "201910202010202110A9A58DD003A90085028503A2024C0FCF20201020221060606060"
        ),
        "expected_alink_loads": ["LIB/HELPER.OBJ", "LIB/OTHER.OBJ"],
    },
    "local_external_helper_only_call": {
        "source": "MODULE MAIN\rPROC A()\rHelper()\rRETURN\rPROC MAIN()\rA()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 23\n",
            "x a 19 4\n",
            "b u0M\n",
            "u helper\n",
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n",
            "r 20 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "local_external_deep_helper_only_call": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC B()\r"
            "A()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "B()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 27\n",
            "x b 19 4\n",
            "x a 23 4\n",
            "b u0M\n",
            "u helper\n",
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 17 10 60 20 00 00 60\n",
            "r 24 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "local_external_helper_mixed_repeat_call": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Helper()\r"
            "Other()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "A()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 29\n",
            "x a 19 10\n",
            "b u0u1u0M\n",
            "u helper\n",
            "u other\n",
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 20 00 00 20 00 00 60\n",
            "r 20 u0\n",
            "r 23 u1\n",
            "r 26 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "OTHER.OBJ": "OBJ1\nx other 0 1\nb M\nm 60\nn other\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF201D10201E10201D10606060"
        ),
        "expected_alink_loads": ["LIB/HELPER.OBJ", "LIB/OTHER.OBJ"],
    },
    "local_external_project_library_helper_closure": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Proj()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "A()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 26\n",
            "x a 19 7\n",
            "b u0u1M\n",
            "u proj\n",
            "u helper\n",
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 20 00 00 60\n",
            "r 20 u0\n",
            "r 23 u1\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm 60\nn proj\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF201A10201B10606060"
        ),
        "expected_alink_loads": ["OBJ/PROJ.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ"],
    },
    "local_external_project_imports_actc_secondary_export": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 23\n",
            "x a 19 4\n",
            "b u1u0M\n",
            "b u0M\n",
            "u helper\n",
            "u wrap\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n",
            "r 1 u1\n",
            "r 20 u0\n",
        ],
        "extra_objects": {
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn wrap\n",
        },
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 1\nb M\nm EA\nn wrap\n",
        },
        "expected_tail": bytes.fromhex(
            "201710A9A58DD003A90085028503A2024C0FCF201B10602013106060"
        ),
        "expected_alink_loads": ["OBJ/WRAP.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": ["LIB/WRAP.OBJ"],
    },
    "local_external_project_imports_actc_secondary_export_local_chain": {
        "source": (
            "MODULE MAIN\r"
            "PROC B()\r"
            "RETURN\r"
            "PROC A()\r"
            "B()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 27\n",
            "x a 19 7\n",
            "x b 26 1\n",
            "u helper\n",
            "u wrap\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 1A 10 20 00 00 60 60\n",
            "r 1 u1\n",
            "r 23 u0\n",
        ],
        "extra_objects": {
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn wrap\n",
        },
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 1\nb M\nm EA\nn wrap\n",
        },
        "expected_tail": bytes.fromhex(
            "201B10A9A58DD003A90085028503A2024C0FCF201A10201F1060602013106060"
        ),
        "expected_alink_loads": ["OBJ/WRAP.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": ["LIB/WRAP.OBJ"],
    },
    "local_external_library_imports_actc_secondary_export": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 23\n",
            "x a 19 4\n",
            "b u1u0M\n",
            "b u0M\n",
            "u helper\n",
            "u wrap\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n",
            "r 1 u1\n",
            "r 20 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn wrap\n",
        },
        "expected_tail": bytes.fromhex(
            "201710A9A58DD003A90085028503A2024C0FCF201B10602013106060"
        ),
        "expected_alink_loads": ["LIB/WRAP.OBJ", "LIB/HELPER.OBJ"],
    },
    "local_external_library_imports_actc_secondary_export_local_chain": {
        "source": (
            "MODULE MAIN\r"
            "PROC B()\r"
            "RETURN\r"
            "PROC A()\r"
            "B()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 27\n",
            "x a 19 7\n",
            "x b 26 1\n",
            "u helper\n",
            "u wrap\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 1A 10 20 00 00 60 60\n",
            "r 1 u1\n",
            "r 23 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn wrap\n",
        },
        "expected_tail": bytes.fromhex(
            "201B10A9A58DD003A90085028503A2024C0FCF201A10201F1060602013106060"
        ),
        "expected_alink_loads": ["LIB/WRAP.OBJ", "LIB/HELPER.OBJ"],
    },
    "local_external_direct_and_library_imports_actc_tail": {
        "source": (
            "MODULE MAIN\r"
            "PROC B()\r"
            "RETURN\r"
            "PROC A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "A()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 27\n",
            "x a 22 4\n",
            "x b 26 1\n",
            "u helper\n",
            "u wrap\n",
            "m 20 16 10 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60 60\n",
            "r 4 u1\n",
            "r 23 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn wrap\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201B10A9A58DD003A90085028503A2024C0FCF"
            "201F106060201A106060"
        ),
        "expected_alink_loads": ["LIB/WRAP.OBJ", "LIB/HELPER.OBJ"],
    },
    "local_external_library_project_imports_actc_secondary_export": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 23\n",
            "x a 19 4\n",
            "b u1u0M\n",
            "b u0M\n",
            "u helper\n",
            "u wrap\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n",
            "r 1 u1\n",
            "r 20 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn proj\n",
        },
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu proj\nm 20 00 00 60\nr 1 u0\nn wrap\n",
        },
        "expected_tail": bytes.fromhex(
            "201710A9A58DD003A90085028503A2024C0FCF201B1060201C10606020131060"
        ),
        "expected_alink_loads": ["LIB/WRAP.OBJ", "OBJ/PROJ.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ"],
    },
    "local_external_library_project_imports_actc_secondary_export_local_chain": {
        "source": (
            "MODULE MAIN\r"
            "PROC B()\r"
            "RETURN\r"
            "PROC A()\r"
            "B()\r"
            "Helper()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 27\n",
            "x a 19 7\n",
            "x b 26 1\n",
            "u helper\n",
            "u wrap\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 1A 10 20 00 00 60 60\n",
            "r 1 u1\n",
            "r 23 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn proj\n",
        },
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu proj\nm 20 00 00 60\nr 1 u0\nn wrap\n",
        },
        "expected_tail": bytes.fromhex(
            "201B10A9A58DD003A90085028503A2024C0FCF"
            "201A10201F106060202010606020131060"
        ),
        "expected_alink_loads": ["LIB/WRAP.OBJ", "OBJ/PROJ.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ"],
    },
    "local_external_mixed_shared_library_dependency_dedup": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "A()\r"
            "Proj()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 29\n",
            "x a 25 4\n",
            "u shared\n",
            "u proj\n",
            "u wrap\n",
            "m 20 19 10 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n",
            "r 4 u1\n",
            "r 7 u2\n",
            "r 26 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu shared\nm 20 00 00 60\nr 1 u0\nn proj\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu shared\nm 20 00 00 60\nr 1 u0\nn wrap\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm 60\nn shared\n",
        },
        "expected_tail": bytes.fromhex(
            "201910201D10202110A9A58DD003A90085028503A2024C0FCF"
            "20251060202510602025106060"
        ),
        "expected_alink_loads": ["OBJ/PROJ.OBJ", "LIB/WRAP.OBJ", "LIB/SHARED.OBJ"],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ"],
    },
    "local_external_dual_secondary_exports_shared_library_dedup": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC B()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Proj()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 30\n",
            "x b 22 4\n",
            "x a 26 4\n",
            "u shared\n",
            "u proj\n",
            "u wrap\n",
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60 20 00 00 60\n",
            "r 1 u1\n",
            "r 4 u2\n",
            "r 23 u0\n",
            "r 27 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn proj\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn wrap\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm 60\nn shared\n",
        },
        "expected_tail": bytes.fromhex(
            "201E10202210A9A58DD003A90085028503A2024C0FCF"
            "2026106020261060201A10602016106060"
        ),
        "expected_alink_loads": ["OBJ/PROJ.OBJ", "LIB/WRAP.OBJ", "LIB/SHARED.OBJ"],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ"],
    },
    "local_external_dual_secondary_exports_shared_project_dedup": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC B()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Proj()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 30\n",
            "x b 22 4\n",
            "x a 26 4\n",
            "u shared\n",
            "u proj\n",
            "u wrap\n",
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60 20 00 00 60\n",
            "r 1 u1\n",
            "r 4 u2\n",
            "r 23 u0\n",
            "r 27 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn proj\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm 60\nn shared\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn wrap\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm EA\nn shared\n",
        },
        "expected_tail": bytes.fromhex(
            "201E10202210A9A58DD003A90085028503A2024C0FCF"
            "2026106020261060201A10602016106060"
        ),
        "expected_alink_loads": ["OBJ/PROJ.OBJ", "LIB/WRAP.OBJ", "OBJ/SHARED.OBJ"],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ", "LIB/SHARED.OBJ"],
    },
    "local_external_dual_secondary_exports_shared_actc_local_dedup": {
        "source": (
            "MODULE MAIN\r"
            "PROC C()\r"
            "RETURN\r"
            "PROC A()\r"
            "C()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC B()\r"
            "C()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Proj()\r"
            "Wrap()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 37\n",
            "x b 22 7\n",
            "x a 29 7\n",
            "x c 36 1\n",
            "u shared\n",
            "u proj\n",
            "u wrap\n",
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 24 10 20 00 00 60 20 24 10 20 00 00 60 60\n",
            "r 1 u1\n",
            "r 4 u2\n",
            "r 26 u0\n",
            "r 33 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn proj\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "WRAP.OBJ": "OBJ1\nx wrap 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn wrap\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm 60\nn shared\n",
        },
        "expected_tail": bytes.fromhex(
            "202510202910A9A58DD003A90085028503A2024C0FCF"
            "202410202D1060202410202D106060201D10602016106060"
        ),
        "expected_alink_loads": ["OBJ/PROJ.OBJ", "LIB/WRAP.OBJ", "LIB/SHARED.OBJ"],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ"],
    },
    "local_external_project_library_transitive_shared_tail": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Proj()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 23\n",
            "x a 19 4\n",
            "b u1u0M\n",
            "b u0M\n",
            "u shared\n",
            "u proj\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n",
            "r 1 u1\n",
            "r 20 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu bridge\nm 20 00 00 60\nr 1 u0\nn proj\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "BRIDGE.OBJ": (
                "OBJ1\n"
                "x bridge 0 7\n"
                "b u0u1M\n"
                "u a\n"
                "u tail\n"
                "m 20 00 00 20 00 00 60\n"
                "r 1 u0\n"
                "r 4 u1\n"
                "n bridge\n"
            ),
            "TAIL.OBJ": "OBJ1\nx tail 0 4\nb u0M\nu shared\nm 20 00 00 60\nr 1 u0\nn tail\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm 60\nn shared\n",
        },
        "expected_tail": bytes.fromhex(
            "201710A9A58DD003A90085028503A2024C0FCF"
            "201B1060201C10606020131020231060201B1060"
        ),
        "expected_alink_loads": [
            "OBJ/PROJ.OBJ",
            "LIB/BRIDGE.OBJ",
            "LIB/TAIL.OBJ",
            "LIB/SHARED.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ"],
    },
    "local_external_project_library_transitive_project_tail": {
        "source": (
            "MODULE MAIN\r"
            "PROC A()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Proj()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 23\n",
            "x a 19 4\n",
            "b u1u0M\n",
            "b u0M\n",
            "u shared\n",
            "u proj\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n",
            "r 1 u1\n",
            "r 20 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu bridge\nm 20 00 00 60\nr 1 u0\nn proj\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm 60\nn shared\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "BRIDGE.OBJ": (
                "OBJ1\n"
                "x bridge 0 7\n"
                "b u0u1M\n"
                "u a\n"
                "u tail\n"
                "m 20 00 00 20 00 00 60\n"
                "r 1 u0\n"
                "r 4 u1\n"
                "n bridge\n"
            ),
            "TAIL.OBJ": "OBJ1\nx tail 0 4\nb u0M\nu shared\nm 20 00 00 60\nr 1 u0\nn tail\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm EA\nn shared\n",
        },
        "expected_tail": bytes.fromhex(
            "201710A9A58DD003A90085028503A2024C0FCF"
            "201B1060201C10606020131020231060201B1060"
        ),
        "expected_alink_loads": [
            "OBJ/PROJ.OBJ",
            "LIB/BRIDGE.OBJ",
            "LIB/TAIL.OBJ",
            "OBJ/SHARED.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ", "LIB/SHARED.OBJ"],
    },
    "local_external_project_library_transitive_tail_imports_actc_local_chain": {
        "source": (
            "MODULE MAIN\r"
            "PROC B()\r"
            "RETURN\r"
            "PROC A()\r"
            "B()\r"
            "Shared()\r"
            "RETURN\r"
            "PROC MAIN()\r"
            "Proj()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 27\n",
            "x a 19 7\n",
            "x b 26 1\n",
            "u shared\n",
            "u proj\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 1A 10 20 00 00 60 60\n",
            "r 1 u1\n",
            "r 23 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu bridge\nm 20 00 00 60\nr 1 u0\nn proj\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "BRIDGE.OBJ": "OBJ1\nx bridge 0 4\nb u0M\nu tail\nm 20 00 00 60\nr 1 u0\nn bridge\n",
            "TAIL.OBJ": "OBJ1\nx tail 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn tail\n",
            "SHARED.OBJ": "OBJ1\nx shared 0 1\nb M\nm 60\nn shared\n",
        },
        "expected_tail": bytes.fromhex(
            "201B10A9A58DD003A90085028503A2024C0FCF"
            "201A10201F10606020201060602024106020131060"
        ),
        "expected_alink_loads": [
            "OBJ/PROJ.OBJ",
            "LIB/BRIDGE.OBJ",
            "LIB/TAIL.OBJ",
            "LIB/SHARED.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ"],
    },
    "external_project_library_project_library_chain": {
        "source": "MODULE MAIN\rPROC MAIN()\rProj()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 19\n",
            "b u0M\n",
            "u proj\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
        ],
        "extra_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 4\nb u0M\nu bridge\nm 20 00 00 60\nr 1 u0\nn proj\n",
            "TAIL.OBJ": "OBJ1\nx tail 0 4\nb u0M\nu leaf\nm 20 00 00 60\nr 1 u0\nn tail\n",
        },
        "extra_library_objects": {
            "PROJ.OBJ": "OBJ1\nx proj 0 1\nb M\nm EA\nn proj\n",
            "BRIDGE.OBJ": "OBJ1\nx bridge 0 4\nb u0M\nu tail\nm 20 00 00 60\nr 1 u0\nn bridge\n",
            "TAIL.OBJ": "OBJ1\nx tail 0 1\nb M\nm EA\nn tail\n",
            "LEAF.OBJ": "OBJ1\nx leaf 0 1\nb M\nm 60\nn leaf\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "20171060201B1060201F106060"
        ),
        "expected_alink_loads": [
            "OBJ/PROJ.OBJ",
            "LIB/BRIDGE.OBJ",
            "OBJ/TAIL.OBJ",
            "LIB/LEAF.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/PROJ.OBJ", "LIB/TAIL.OBJ"],
    },
    "external_call": {
        "source": "MODULE MAIN\rPROC MAIN()\rHelper()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 19\n",
            "b u0M\n",
            "u helper\n",
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "local_external_call": {
        "source": "MODULE MAIN\rPROC A()\rRETURN\rPROC MAIN()\rA()\rHelper()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 23\n",
            "x a 22 1\n",
            "b u0M\n",
            "u helper\n",
            "m 20 16 10 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
            "r 4 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "local_external_pair_call": {
        "source": "MODULE MAIN\rPROC A()\rRETURN\rPROC MAIN()\rA()\rHelper()\rOther()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 26\n",
            "x a 25 1\n",
            "b u0u1M\n",
            "u helper\n",
            "u other\n",
            "m 20 19 10 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
            "r 4 u0\n",
            "r 7 u1\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "OTHER.OBJ": "OBJ1\nx other 0 1\nb M\nm 60\nn other\n",
        },
        "expected_tail": bytes.fromhex("201910201A10201B10A9A58DD003A90085028503A2024C0FCF606060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ", "LIB/OTHER.OBJ"],
    },
    "local_external_call_twice": {
        "source": "MODULE MAIN\rPROC A()\rRETURN\rPROC MAIN()\rA()\rHelper()\rHelper()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 26\n",
            "x a 25 1\n",
            "b u0u0M\n",
            "u helper\n",
            "m 20 19 10 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
            "r 4 u0\n",
            "r 7 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201910201A10201A10A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "local_external_mixed_repeat_call": {
        "source": "MODULE MAIN\rPROC A()\rRETURN\rPROC MAIN()\rA()\rHelper()\rOther()\rHelper()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 29\n",
            "x a 28 1\n",
            "b u0u1u0M\n",
            "u helper\n",
            "u other\n",
            "m 20 1C 10 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
            "r 4 u0\n",
            "r 7 u1\n",
            "r 10 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "OTHER.OBJ": "OBJ1\nx other 0 1\nb M\nm 60\nn other\n",
        },
        "expected_tail": bytes.fromhex("201C10201D10201E10201D10A9A58DD003A90085028503A2024C0FCF606060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ", "LIB/OTHER.OBJ"],
    },
    "external_pair_call": {
        "source": "MODULE MAIN\rPROC MAIN()\rHelper()\rOther()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 22\n",
            "b u0u1M\n",
            "u helper\n",
            "u other\n",
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
            "r 4 u1\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "OTHER.OBJ": "OBJ1\nx other 0 1\nb M\nm 60\nn other\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ", "LIB/OTHER.OBJ"],
    },
    "external_triple_call": {
        "source": "MODULE MAIN\rPROC MAIN()\rHelper()\rOther()\rThird()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 25\n",
            "b u0u1u2M\n",
            "u helper\n",
            "u other\n",
            "u third\n",
            "m 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
            "r 4 u1\n",
            "r 7 u2\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "OTHER.OBJ": "OBJ1\nx other 0 1\nb M\nm 60\nn other\n",
            "THIRD.OBJ": "OBJ1\nx third 0 1\nb M\nm 60\nn third\n",
        },
        "expected_tail": bytes.fromhex("201910201A10201B10A9A58DD003A90085028503A2024C0FCF606060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ", "LIB/OTHER.OBJ", "LIB/THIRD.OBJ"],
    },
    "external_lettered_import_call": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "Alpha()\r"
            "Bravo()\r"
            "Charlie()\r"
            "Delta()\r"
            "Echo()\r"
            "Foxtrot()\r"
            "Golf()\r"
            "Hotel()\r"
            "India()\r"
            "Juliet()\r"
            "Kilo()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 49\n",
            "b u0u1u2u3u4u5u6u7u8u9uAM\n",
            "u alpha\n",
            "u bravo\n",
            "u charlie\n",
            "u delta\n",
            "u echo\n",
            "u foxtrot\n",
            "u golf\n",
            "u hotel\n",
            "u india\n",
            "u juliet\n",
            "u kilo\n",
            "m 20 00 00 20 00 00 20 00 00 20 00 00 20 00 00 20 00 00 20 00 00 20 00 00 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
            "r 4 u1\n",
            "r 7 u2\n",
            "r 10 u3\n",
            "r 13 u4\n",
            "r 16 u5\n",
            "r 19 u6\n",
            "r 22 u7\n",
            "r 25 u8\n",
            "r 28 u9\n",
            "r 31 uA\n",
        ],
        "extra_library_objects": {
            "ALPHA.OBJ": "OBJ1\nx alpha 0 1\nb M\nm 60\nn alpha\n",
            "BRAVO.OBJ": "OBJ1\nx bravo 0 1\nb M\nm 60\nn bravo\n",
            "CHARLIE.OBJ": "OBJ1\nx charlie 0 1\nb M\nm 60\nn charlie\n",
            "DELTA.OBJ": "OBJ1\nx delta 0 1\nb M\nm 60\nn delta\n",
            "ECHO.OBJ": "OBJ1\nx echo 0 1\nb M\nm 60\nn echo\n",
            "FOXTROT.OBJ": "OBJ1\nx foxtrot 0 1\nb M\nm 60\nn foxtrot\n",
            "GOLF.OBJ": "OBJ1\nx golf 0 1\nb M\nm 60\nn golf\n",
            "HOTEL.OBJ": "OBJ1\nx hotel 0 1\nb M\nm 60\nn hotel\n",
            "INDIA.OBJ": "OBJ1\nx india 0 1\nb M\nm 60\nn india\n",
            "JULIET.OBJ": "OBJ1\nx juliet 0 1\nb M\nm 60\nn juliet\n",
            "KILO.OBJ": "OBJ1\nx kilo 0 1\nb M\nm 60\nn kilo\n",
        },
        "expected_tail": bytes.fromhex(
            "203110203210203310203410203510203610203710203810203910203A10203B10"
            "A9A58DD003A90085028503A2024C0FCF6060606060606060606060"
        ),
        "expected_alink_loads": [
            "LIB/ALPHA.OBJ",
            "LIB/BRAVO.OBJ",
            "LIB/CHARLIE.OBJ",
            "LIB/DELTA.OBJ",
            "LIB/ECHO.OBJ",
            "LIB/FOXTROT.OBJ",
            "LIB/GOLF.OBJ",
            "LIB/HOTEL.OBJ",
            "LIB/INDIA.OBJ",
            "LIB/JULIET.OBJ",
            "LIB/KILO.OBJ",
        ],
    },
    "external_dependency_windowed_lettered_import_call": (
        _external_dependency_windowed_lettered_import_call_case()
    ),
    "local_external_project_dependency_windowed_lettered_import_call": (
        _local_external_project_dependency_windowed_lettered_import_call_case()
    ),
    "local_external_project_dependency_windowed_lettered_mixed_helper_call": (
        _local_external_project_dependency_windowed_lettered_mixed_helper_call_case()
    ),
    "external_mixed_repeat_call": {
        "source": "MODULE MAIN\rPROC MAIN()\rHelper()\rOther()\rHelper()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 25\n",
            "b u0u1M\n",
            "u helper\n",
            "u other\n",
            "m 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
            "r 4 u1\n",
            "r 7 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "OTHER.OBJ": "OBJ1\nx other 0 1\nb M\nm 60\nn other\n",
        },
        "expected_tail": bytes.fromhex("201910201A10201910A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ", "LIB/OTHER.OBJ"],
    },
    "external_call_twice": {
        "source": "MODULE MAIN\rPROC MAIN()\rHelper()\rHelper()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 22\n",
            "b u0M\n",
            "u helper\n",
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
            "r 1 u0\n",
            "r 4 u0\n",
        ],
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201610201610A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "word_store": {
        "seed_object": "OBJ1\nx main 0 7\nb p0S0r\ni 7\nv x 0\n",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A907A2008D22108E23108DD1038ED203A9A58DD003A90085028503A2024C0FCF00000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "word_load_store": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=7\rY=X\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A907A2008D2E108E2F10AD2E10AE2F108D30108E31108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "word_load_store_seeded": {
        "seed_object": "OBJ1\nx main 0 13\nb p0S0L0S1r\ni 7\nv x 0\nv y 0\nk 0\nn main\n",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A907A2008D2E108E2F10AD2E10AE2F108D30108E31108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "printmath": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            'PrintE("HELLO")\r'
            "W()\r"
            "PrintI(50 + 7 - 3)\r"
            "PrintIE(60 - 3 + 2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "W.OBJ": (
                "OBJ1\n"
                "x w 0 13\n"
                "b s0i0r\n"
                "s WIDG\n"
                "i 42\n"
                "n w\n"
            ),
        },
        "expected_tail": bytes.fromhex("2003cf2006cf60000000000000000048454c4c4f005749444700"),
        "screen_fragments": ["hello", "widg42", "5459"],
        "expected_alink_loads": ["LIB/W.OBJ"],
    },
    "transitive_library_load": {
        "seed_object": "OBJ1\nx main 0 1\nb r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb r\nu b\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb r\nn b\n",
        },
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "real_printre_int": {
        "source": (
            "MODULE MAIN\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "X=REAL(7)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_print_f"],
        "expected_tail": _real_printre_int_tail(7),
        "screen_fragments": ["7"],
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_PRINT_F.OBJ"],
    },
    "real_printre_byte": {
        "source": (
            "MODULE MAIN\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "X=REAL(42)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_print_f"],
        "expected_tail": _real_printre_int_tail(42),
        "screen_fragments": ["42"],
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_PRINT_F.OBJ"],
    },
    "real_printre_fraction": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(2)\r"
            "X=A/B\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_div", "rt_print_f", "rt_s_to_f"],
        "expected_tail": _real_printre_binary_tail(3, 2, "rt_f_div"),
        "screen_fragments": ["1.5"],
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_DIV.OBJ",
            "LIB/RT_PRINT_F.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_printre_add": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "X=A+B\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_add", "rt_print_f", "rt_s_to_f"],
        "expected_tail": _real_printre_binary_tail(1, 2, "rt_f_add"),
        "screen_fragments": ["3"],
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_PRINT_F.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "actc_runtime_helper_free_unused_helper_libraries_pruned": {
        "source": "MODULE MAIN\rPROC A()\rRETURN\rPROC MAIN()\rA()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_i_to_f",
            "rt_print_f",
            "rt_gfx_bgcolor",
            "rt_gfx_bitmap_on",
            "rt_sid_vol",
            "rt_sid_state",
            "rt_sprite_on",
            "rt_joy",
            "rt_mp",
            "rt_dbf_open",
        ],
        "expected_object_fragments": [
            "x main 0 20\n",
            "x a 19 1\n",
            "b M\n",
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n",
        ],
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "unexpected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_PRINT_F.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_GFX_BITMAP_ON.OBJ",
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SPRITE_ON.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_DBF_OPEN.OBJ",
        ],
    },
    "actc_runtime_math1_export_sample_linked": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(0-7)\r"
            "X=FAbs(A)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_s_to_f",
            "rt_f_abs",
            "rt_print_f",
            "rt_f_sub",
            "rt_f_sqrt",
        ],
        "expected_tail": _real_printre_fabs_tail(-7),
        "screen_fragments": ["7"],
        "expected_alink_loads": [
            "LIB/RT_S_TO_F.OBJ",
            "LIB/RT_F_ABS.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/RT_F_SUB.OBJ", "LIB/RT_F_SQRT.OBJ"],
    },
    "actc_runtime_math1_fabs_split_linked": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(0-9)\r"
            "X=FAbs(A)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_s_to_f",
            "rt_f_abs",
            "rt_print_f",
            "rt_f_sub",
            "rt_f_sqrt",
        ],
        "expected_tail": _real_printre_fabs_tail(-9),
        "screen_fragments": ["9"],
        "expected_alink_loads": [
            "LIB/RT_S_TO_F.OBJ",
            "LIB/RT_F_ABS.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_F_SQRT.OBJ",
        ],
    },
    "actc_runtime_math1_fsqrt_split_linked": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(256)\r"
            "X=FSqrt(A)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_i_to_f",
            "rt_f_sqrt",
            "rt_print_f",
            "rt_f_abs",
            "rt_f_sub",
        ],
        "expected_tail": _real_printre_fsqrt_tail(256),
        "screen_fragments": ["16"],
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_SQRT.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/RT_F_ABS.OBJ", "LIB/RT_F_SUB.OBJ"],
    },
    "actc_runtime_math1_printre_split_linked": {
        "source": (
            "MODULE MAIN\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "X=REAL(42)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_i_to_f",
            "rt_print_f",
            "rt_f_abs",
            "rt_f_sqrt",
            "rt_f_sub",
        ],
        "expected_tail": _real_printre_int_tail(42),
        "screen_fragments": ["42"],
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_F_ABS.OBJ",
            "LIB/RT_F_SQRT.OBJ",
            "LIB/RT_F_SUB.OBJ",
        ],
    },
    "actc_runtime_math1_printr_split_linked": {
        "source": (
            "MODULE MAIN\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "X=REAL(42)\r"
            "PrintR(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_i_to_f",
            "rt_print_f",
            "rt_f_abs",
            "rt_f_sqrt",
            "rt_f_sub",
        ],
        "expected_tail": _real_printre_int_tail(42),
        "screen_fragments": ["42"],
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_F_ABS.OBJ",
            "LIB/RT_F_SQRT.OBJ",
            "LIB/RT_F_SUB.OBJ",
        ],
    },
    "real_printre_fabs": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(0-7)\r"
            "X=FAbs(A)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_s_to_f", "rt_f_abs", "rt_print_f"],
        "expected_tail": _real_printre_fabs_tail(-7),
        "screen_fragments": ["7"],
        "expected_alink_loads": [
            "LIB/RT_S_TO_F.OBJ",
            "LIB/RT_F_ABS.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
    },
    "real_printre_fsqrt": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(256)\r"
            "X=FSqrt(A)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_sqrt", "rt_print_f"],
        "expected_tail": _real_printre_fsqrt_tail(256),
        "screen_fragments": ["16"],
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_SQRT.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
    },
    "real_printre_sub": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(5)\r"
            "B=REAL(2)\r"
            "X=A-B\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_sub", "rt_print_f", "rt_s_to_f"],
        "expected_tail": _real_printre_binary_tail(5, 2, "rt_f_sub"),
        "screen_fragments": ["3"],
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_PRINT_F.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_printre_mul": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(3)\r"
            "X=A*B\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_mul", "rt_print_f", "rt_s_to_f"],
        "expected_tail": _real_printre_binary_tail(2, 3, "rt_f_mul"),
        "screen_fragments": ["6"],
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_MUL.OBJ",
            "LIB/RT_PRINT_F.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_if_gt": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A>B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 1, 7, 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_gt_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A>B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_lt": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_lt_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A<B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 1, 7, 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_ge": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A>=B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 2, 7, 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_ge_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A>=B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_le": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<=B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_le_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A<=B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 1, 7, 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_eq": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A=B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 2, 7, 0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_eq_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A=B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_ne": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<>B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 0, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_ne_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A<>B THEN\r"
            "Y=7\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhp5S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 2, 7, 0, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_gt": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A>B THEN\r"
            "IF A>B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghL0U0L1U1u1p5ghp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(2, 1, 7, 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_gt_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A>B THEN\r"
            "IF A>B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghL0U0L1U1u1p5ghp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(1, 2, 7, 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_lt": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<B THEN\r"
            "IF A<B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhL0U0L1U1u1p5lhp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(1, 2, 7, 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_lt_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A<B THEN\r"
            "IF A<B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhL0U0L1U1u1p5lhp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(2, 1, 7, 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_ge": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A>=B THEN\r"
            "IF A>=B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghL0U0L1U1u1p5ghp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(2, 2, 7, 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_ge_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A>=B THEN\r"
            "IF A>=B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghL0U0L1U1u1p5ghp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(1, 2, 7, 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_le": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<=B THEN\r"
            "IF A<=B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhL0U0L1U1u1p5lhp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(1, 2, 7, 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_le_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A<=B THEN\r"
            "IF A<=B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhL0U0L1U1u1p5lhp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(2, 1, 7, 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_eq": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A=B THEN\r"
            "IF A=B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhL0U0L1U1u1p5qhp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(2, 2, 7, 0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_eq_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A=B THEN\r"
            "IF A=B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhL0U0L1U1u1p5qhp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(1, 2, 7, 0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_ne": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<>B THEN\r"
            "IF A<>B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhL0U0L1U1u1p5nhp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(1, 2, 7, 0, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_nested_if_ne_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A<>B THEN\r"
            "IF A<>B THEN\r"
            "Y=7\r"
            "FI\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhL0U0L1U1u1p5nhp6S2vvr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_nested_if_cmp_tail(2, 2, 7, 0, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_do_until_eq": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(1)\r"
            "DO\r"
            "A=REAL(1)\r"
            "UNTIL A=B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5qtop6S2r\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_cmp_tail(1, 1, 7, 0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_do_until_gt": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(1)\r"
            "DO\r"
            "A=REAL(2)\r"
            "UNTIL A>B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5gtop6S2r\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_cmp_tail(1, 2, 7, 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_do_until_lt": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(2)\r"
            "DO\r"
            "A=REAL(1)\r"
            "UNTIL A<B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5ltop6S2r\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_cmp_tail(2, 1, 7, 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_do_until_ge": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(2)\r"
            "DO\r"
            "A=REAL(2)\r"
            "UNTIL A>=B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5gtop6S2r\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_cmp_tail(2, 2, 7, 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_do_until_le": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(2)\r"
            "DO\r"
            "A=REAL(1)\r"
            "UNTIL A<=B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5ltop6S2r\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_cmp_tail(2, 1, 7, 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_do_until_ne": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(2)\r"
            "DO\r"
            "A=REAL(1)\r"
            "UNTIL A<>B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1dp4u0T0S0L0U0L1U1u1p5ntop6S2r\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_cmp_tail(2, 1, 7, 0, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_do_until_gt_real_add_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(3)\r"
            "C=REAL(1)\r"
            "DO\r"
            "A=A+C\r"
            "UNTIL A>B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_add", "rt_f_cmp", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5gtop6S3r\n",
            "u rt_i_to_f\n",
            "u rt_f_add\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_real_binary_loop_tail(0, 3, 1, 7, "rt_f_add", 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_do_until_ge_real_add_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(1)\r"
            "C=REAL(1)\r"
            "DO\r"
            "A=A+C\r"
            "UNTIL A>=B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_add", "rt_f_cmp", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5gtop6S3r\n",
            "u rt_i_to_f\n",
            "u rt_f_add\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_real_binary_loop_tail(0, 1, 1, 7, "rt_f_add", 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_do_until_lt_real_add_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(3)\r"
            "C=REAL(1)\r"
            "DO\r"
            "A=A+C\r"
            "UNTIL A<B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_add", "rt_f_cmp", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5ltop6S3r\n",
            "u rt_i_to_f\n",
            "u rt_f_add\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_real_binary_loop_tail(0, 3, 1, 7, "rt_f_add", 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_do_until_le_real_add_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(3)\r"
            "C=REAL(1)\r"
            "DO\r"
            "A=A+C\r"
            "UNTIL A<=B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_add", "rt_f_cmp", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5ltop6S3r\n",
            "u rt_i_to_f\n",
            "u rt_f_add\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_real_binary_loop_tail(0, 3, 1, 7, "rt_f_add", 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_do_until_gt_real_sub_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(0)\r"
            "C=REAL(1)\r"
            "DO\r"
            "A=A-C\r"
            "UNTIL A>B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_sub", "rt_f_cmp", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p5gtop6S3r\n",
            "u rt_i_to_f\n",
            "u rt_f_sub\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_real_binary_loop_tail(3, 0, 1, 7, "rt_f_sub", 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_do_until_ge_real_sub_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(1)\r"
            "C=REAL(1)\r"
            "DO\r"
            "A=A-C\r"
            "UNTIL A>=B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_sub", "rt_f_cmp", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p6gtop7S3r\n",
            "u rt_i_to_f\n",
            "u rt_f_sub\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_real_binary_loop_tail(3, 1, 1, 7, "rt_f_sub", 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_do_until_lt_real_sub_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(3)\r"
            "C=REAL(1)\r"
            "DO\r"
            "A=A-C\r"
            "UNTIL A<B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_sub", "rt_f_cmp", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p6ltop7S3r\n",
            "u rt_i_to_f\n",
            "u rt_f_sub\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_real_binary_loop_tail(3, 3, 1, 7, "rt_f_sub", 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_do_until_le_real_sub_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(1)\r"
            "C=REAL(1)\r"
            "DO\r"
            "A=A-C\r"
            "UNTIL A<=B\r"
            "OD\r"
            "Y=7\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_sub", "rt_f_cmp", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L2U2u1T0S0L0U0L1U1u2p6ltop7S3r\n",
            "u rt_i_to_f\n",
            "u rt_f_sub\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_do_until_real_binary_loop_tail(3, 1, 1, 7, "rt_f_sub", 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_while_gt_once": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "WHILE A>B DO\r"
            "Y=7\r"
            "A=REAL(0)\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1dL0U0L1U1u1p4gfp5S2p6p6T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_while_cmp_once_tail(2, 1, 7, 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_while_ge_once": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "WHILE A>=B DO\r"
            "Y=7\r"
            "A=REAL(0)\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1dL0U0L1U1u1p4gfp5S2p6p6T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_while_cmp_once_tail(2, 2, 7, 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_while_lt_once": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "WHILE A<B DO\r"
            "Y=7\r"
            "B=REAL(0)\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1dL0U0L1U1u1p4lfp5S2p6p6T1S1xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_while_cmp_once_tail(1, 2, 7, 0xFF, loop_update_target="b"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_while_le_once": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "WHILE A<=B DO\r"
            "Y=7\r"
            "B=REAL(0)\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1dL0U0L1U1u1p4lfp5S2p6p6T1S1xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_while_cmp_once_tail(2, 2, 7, 1, 0xF0, loop_update_target="b"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_while_gt_update_nonzero_once": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(2)\r"
            "WHILE A>B DO\r"
            "Y=7\r"
            "A=REAL(1)\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1dL0U0L1U1u1p4gfp5S2p7u0T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_while_cmp_once_tail(
            3,
            2,
            7,
            1,
            loop_update_value=1,
            loop_update_uses_conversion=True,
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_while_ge_update_nonzero_once": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(2)\r"
            "WHILE A>=B DO\r"
            "Y=7\r"
            "A=REAL(1)\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1dL0U0L1U1u1p4gfp5S2p7u0T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_while_cmp_once_tail(
            3,
            2,
            7,
            0xFF,
            0xF0,
            loop_update_value=1,
            loop_update_uses_conversion=True,
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_while_lt_update_nonzero_once": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "WHILE A<B DO\r"
            "Y=7\r"
            "B=REAL(1)\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1dL0U0L1U1u1p4lfp5S2p7u0T1S1xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_while_cmp_once_tail(
            1,
            2,
            7,
            0xFF,
            loop_update_value=1,
            loop_update_target="b",
            loop_update_uses_conversion=True,
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_while_le_update_nonzero_once": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(3)\r"
            "WHILE A<=B DO\r"
            "Y=7\r"
            "B=REAL(1)\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1dL0U0L1U1u1p4lfp5S2p7u0T1S1xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_while_cmp_once_tail(
            2,
            3,
            7,
            1,
            0xF0,
            loop_update_value=1,
            loop_update_target="b",
            loop_update_uses_conversion=True,
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },

    "real_while_gt_real_sub_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(0)\r"
            "C=REAL(1)\r"
            "WHILE A>B DO\r"
            "Y=7\r"
            "A=A-C\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp", "rt_f_sub", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L1U1u1p5gfp6S3L0U0L2U2u2T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
            "u rt_f_sub\n",
        ],
        "expected_tail": _real_while_real_binary_loop_tail(3, 0, 1, 7, "rt_f_sub", 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_while_ge_real_sub_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(3)\r"
            "B=REAL(1)\r"
            "C=REAL(1)\r"
            "WHILE A>=B DO\r"
            "Y=7\r"
            "A=A-C\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp", "rt_f_sub", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1p5u0T2S2dL0U0L1U1u1p6gfp7S3L0U0L2U2u2T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
            "u rt_f_sub\n",
        ],
        "expected_tail": _real_while_real_binary_loop_tail(3, 1, 1, 7, "rt_f_sub", 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_while_lt_real_add_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(3)\r"
            "C=REAL(1)\r"
            "WHILE A<B DO\r"
            "Y=7\r"
            "A=A+C\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp", "rt_f_add", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L1U1u1p5lfp6S3L0U0L2U2u2T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
            "u rt_f_add\n",
        ],
        "expected_tail": _real_while_real_binary_loop_tail(0, 3, 1, 7, "rt_f_add", 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_while_le_real_add_loop": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(3)\r"
            "C=REAL(1)\r"
            "WHILE A<=B DO\r"
            "Y=7\r"
            "A=A+C\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp", "rt_f_add", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L1U1u1p5lfp6S3L0U0L2U2u2T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
            "u rt_f_add\n",
        ],
        "expected_tail": _real_while_real_binary_loop_tail(0, 3, 1, 7, "rt_f_add", 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_while_gt_real_add_skip": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(1)\r"
            "C=REAL(1)\r"
            "WHILE A>B DO\r"
            "Y=7\r"
            "A=A+C\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp", "rt_f_add", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L1U1u1p5gfp6S3L0U0L2U2u2T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
            "u rt_f_add\n",
        ],
        "expected_tail": _real_while_real_binary_loop_tail(0, 1, 1, 7, "rt_f_add", 1),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_while_ge_real_add_skip": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(0)\r"
            "B=REAL(1)\r"
            "C=REAL(1)\r"
            "WHILE A>=B DO\r"
            "Y=7\r"
            "A=A+C\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp", "rt_f_add", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p0p0T0S0p2u0T1S1p4u0T2S2dL0U0L1U1u1p5gfp6S3L0U0L2U2u2T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
            "u rt_f_add\n",
        ],
        "expected_tail": _real_while_real_binary_loop_tail(0, 1, 1, 7, "rt_f_add", 0xFF, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_F_ADD.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_while_lt_real_sub_skip": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(0)\r"
            "C=REAL(1)\r"
            "WHILE A<B DO\r"
            "Y=7\r"
            "A=A-C\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp", "rt_f_sub", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L1U1u1p5lfp6S3L0U0L2U2u2T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
            "u rt_f_sub\n",
        ],
        "expected_tail": _real_while_real_binary_loop_tail(1, 0, 1, 7, "rt_f_sub", 0xFF),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_while_le_real_sub_skip": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "REAL C\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(0)\r"
            "C=REAL(1)\r"
            "WHILE A<=B DO\r"
            "Y=7\r"
            "A=A-C\r"
            "OD\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp", "rt_f_sub", "rt_s_to_f"],
        "expected_object_fragments": [
            "b p1u0T0S0p2p2T1S1p4u0T2S2dL0U0L1U1u1p5lfp6S3L0U0L2U2u2T0S0xr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
            "u rt_f_sub\n",
        ],
        "expected_tail": _real_while_real_binary_loop_tail(1, 0, 1, 7, "rt_f_sub", 1, 0xF0),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_F_CMP.OBJ",
            "LIB/RT_F_SUB.OBJ",
            "LIB/RT_S_TO_F.OBJ",
        ],
    },
    "real_if_else_true": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A>B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 1, 7, 1, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_else_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A>B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 1, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x09,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_lt_else_true": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 0xFF, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_lt_else_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A<B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 1, 7, 0xFF, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x09,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_ge_else_true": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A>=B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 2, 7, 0xFF, 0xF0, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_ge_else_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A>=B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4ghp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 0xFF, 0xF0, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x09,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_le_else_true": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<=B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 1, 0xF0, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_le_else_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(1)\r"
            "IF A<=B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4lhp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 1, 7, 1, 0xF0, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x09,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_eq_else_true": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A=B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 2, 7, 0, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_eq_else_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A=B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4qhp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 0, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x09,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_ne_else_true": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(1)\r"
            "B=REAL(2)\r"
            "IF A<>B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(1, 2, 7, 0, 0xF0, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "real_if_ne_else_false": {
        "source": (
            "MODULE MAIN\r"
            "REAL A\r"
            "REAL B\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "A=REAL(2)\r"
            "B=REAL(2)\r"
            "IF A<>B THEN\r"
            "Y=7\r"
            "ELSE\r"
            "Y=9\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f", "rt_f_cmp"],
        "expected_object_fragments": [
            "b p1u0T0S0p3u0T1S1L0U0L1U1u1p4nhp5S2wp6S2vr\n",
            "u rt_i_to_f\n",
            "u rt_f_cmp\n",
        ],
        "expected_tail": _real_if_cmp_tail(2, 2, 7, 0, 0xF0, else_value=9),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x09,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_CMP.OBJ"],
    },
    "runtime_real_i_to_f_byte_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 31\n"
            "b u0M\n"
            "u rt_i_to_f\n"
            "m A9 D1 85 02 A9 03 85 03 A9 07 A2 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 13 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f"],
        "expected_tail": _runtime_real_i_to_f_helper_tail(7),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0xE0},
            {"addr": 0x03D4, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ"],
    },
    "runtime_real_i_to_f_word_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 31\n"
            "b u0M\n"
            "u rt_i_to_f\n"
            "m A9 D1 85 02 A9 03 85 03 A9 00 A2 01 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 13 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_i_to_f"],
        "expected_tail": _runtime_real_i_to_f_helper_tail(256),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0x80},
            {"addr": 0x03D4, "value": 0x43},
        ],
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ"],
    },
    "runtime_real_s_to_f_word_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 61\n"
            "b u0M\n"
            "u rt_s_to_f\n"
            "m A9 D1 85 02 A9 03 85 03 A9 00 A2 FF 20 00 00 A9 D5 85 02 A9 03 85 03 A9 00 A2 01 20 00 00 A9 D9 85 02 A9 03 85 03 A9 00 A2 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 13 u0\n"
            "r 28 u0\n"
            "r 43 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9D18502A9038503A900A2FF203D10A9D58502A9038503A900A201203D10"
            "A9D98502A9038503A900A200203D10A9A58DD003A90085028503A2024C0FCF"
            "85048605A9008506A5052980F015A9808506A50449FF1869018504A50549FF"
            "69008505A5040505D010A000A9009102C89102C89102C8910260A9008507"
            "A505300806042605E607D0F4A98E38E5078508A000A9009102C8"
            "A5049102C8A505297F8509A5082901F006A5090980D002A5099102C8A508"
            "4A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0x80},
            {"addr": 0x03D4, "value": 0xC3},
            {"addr": 0x03D5, "value": 0x00},
            {"addr": 0x03D6, "value": 0x00},
            {"addr": 0x03D7, "value": 0x80},
            {"addr": 0x03D8, "value": 0x43},
            {"addr": 0x03D9, "value": 0x00},
            {"addr": 0x03DA, "value": 0x00},
            {"addr": 0x03DB, "value": 0x00},
            {"addr": 0x03DC, "value": 0x00},
        ],
        "expected_alink_loads": ["LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_to_i_byte_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 51\n"
            "b u0M\n"
            "u rt_f_to_i\n"
            "m A9 00 8D E0 03 8D E1 03 A9 E0 8D E2 03 A9 40 8D E3 03 A9 E0 85 02 A9 03 85 03 20 00 00 8D D1 03 8E D2 03 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 27 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_to_i"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9E08DE203A9408DE303A9E08502A9038503203310"
            "8DD1038ED203A9A58DD003A90085028503A2024C0FCF"
            "A003B1028504297F0A850588B10285092980F002E605A505C97F905CC98FB058"
            "A99638E5058506A000B1028507C8B1028508C8B102297F098085094609660866"
            "07C606D0F6A5083009A5043018A507A60860A5041022A508C980D01CA507D0"
            "18A900A28060A50749FF186901850AA50849FF6900AAA50A60A900AA60"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x07,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_F_TO_I.OBJ"],
    },
    "runtime_real_f_to_i_fraction_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 51\n"
            "b u0M\n"
            "u rt_f_to_i\n"
            "m A9 00 8D E0 03 8D E1 03 A9 C0 8D E2 03 A9 3F 8D E3 03 A9 E0 85 02 A9 03 85 03 20 00 00 8D D1 03 8E D2 03 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 27 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_to_i"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9C08DE203A93F8DE303A9E08502A9038503203310"
            "8DD1038ED203A9A58DD003A90085028503A2024C0FCF"
            "A003B1028504297F0A850588B10285092980F002E605A505C97F905CC98FB058"
            "A99638E5058506A000B1028507C8B1028508C8B102297F098085094609660866"
            "07C606D0F6A5083009A5043018A507A60860A5041022A508C980D01CA507D0"
            "18A900A28060A50749FF186901850AA50849FF6900AAA50A60A900AA60"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_F_TO_I.OBJ"],
    },
    "runtime_real_f_to_i_negative_fraction_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 51\n"
            "b u0M\n"
            "u rt_f_to_i\n"
            "m A9 00 8D E0 03 8D E1 03 A9 C0 8D E2 03 A9 BF 8D E3 03 A9 E0 85 02 A9 03 85 03 20 00 00 8D D1 03 8E D2 03 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 27 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_to_i"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9C08DE203A9BF8DE303A9E08502A9038503203310"
            "8DD1038ED203A9A58DD003A90085028503A2024C0FCF"
            "A003B1028504297F0A850588B10285092980F002E605A505C97F905CC98FB058"
            "A99638E5058506A000B1028507C8B1028508C8B102297F098085094609660866"
            "07C606D0F6A5083009A5043018A507A60860A5041022A508C980D01CA507D0"
            "18A900A28060A50749FF186901850AA50849FF6900AAA50A60A900AA60"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0xFF,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0xFF,
        "expected_alink_loads": ["LIB/RT_F_TO_I.OBJ"],
    },
    "runtime_real_print_f_byte_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 45\n"
            "b u0M\n"
            "u rt_print_f\n"
            "m A9 00 8D E0 03 8D E1 03 A9 28 8D E2 03 A9 42 8D E3 03 A9 E0 85 02 A9 03 85 03 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 27 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_print_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9288DE203A9428DE303A9E08502A9038503202D10"
            "A9A58DD003A90085028503A2024C0FCF"
            "A90085048505A003B1023049297F0A850988B102850D2980F002E609A509C9779033C986B02F"
            "A98E38E509850AA000B102850BC8B102850CC8B102297F0980850D460D660C660BC60AD0F6"
            "A50B8504A50C297F8505A5058506A9008507A506C964900938E9648506E607D0F1A9008508"
            "A506C90A900938E90A8506E608D0F1A507F01018693020D2FFA50818693020D2FFD00AA508"
            "F00618693020D2FFA50618693020D2FFA504D00160A92E20D2FFA504850EA900850F8510"
            "A50E0A26100A2610850FA9008512A50E0A26120A26120A26120A26120A2612851118A50F"
            "6511850FA51065128510A9008512A50E0A26120A26120A26120A26120A26120A26128511"
            "18A50F6511850FA51065128510A5108513A5138506A9008508A506C90A900938E90A8506"
            "E608D0F1A508D010A93020D2FFA506F01718693020D2FF6018693020D2FFA506F0061869"
            "3020D2FF60"
        ),
        "screen_fragments": ["42"],
        "expected_alink_loads": ["LIB/RT_PRINT_F.OBJ"],
    },
    "runtime_real_print_f_fraction_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 45\n"
            "b u0M\n"
            "u rt_print_f\n"
            "m A9 00 8D E0 03 8D E1 03 A9 C0 8D E2 03 A9 3F 8D E3 03 A9 E0 85 02 A9 03 85 03 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 27 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_print_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9C08DE203A93F8DE303A9E08502A9038503202D10"
            "A9A58DD003A90085028503A2024C0FCF"
            "A90085048505A003B1023049297F0A850988B102850D2980F002E609A509C9779033C986B02F"
            "A98E38E509850AA000B102850BC8B102850CC8B102297F0980850D460D660C660BC60AD0F6"
            "A50B8504A50C297F8505A5058506A9008507A506C964900938E9648506E607D0F1A9008508"
            "A506C90A900938E90A8506E608D0F1A507F01018693020D2FFA50818693020D2FFD00AA508"
            "F00618693020D2FFA50618693020D2FFA504D00160A92E20D2FFA504850EA900850F8510"
            "A50E0A26100A2610850FA9008512A50E0A26120A26120A26120A26120A2612851118A50F"
            "6511850FA51065128510A9008512A50E0A26120A26120A26120A26120A26120A26128511"
            "18A50F6511850FA51065128510A5108513A5138506A9008508A506C90A900938E90A8506"
            "E608D0F1A508D010A93020D2FFA506F01718693020D2FF6018693020D2FFA506F0061869"
            "3020D2FF60"
        ),
        "screen_fragments": ["1.5"],
        "expected_alink_loads": ["LIB/RT_PRINT_F.OBJ"],
    },
    "runtime_real_f_add_byte_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 77\n"
            "b u0M\n"
            "u rt_f_add\n"
            "m A9 00 8D E0 03 8D E1 03 A9 E0 8D E2 03 A9 40 8D E3 03 A9 00 8D E4 03 8D E5 03 8D E6 03 A9 40 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 59 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_add", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9E08DE203A9408DE303A9008DE4038DE5038DE603A9408DE703A9E08502A9038503A9E48504A903"
            "8505A9D18506A9038507204D10A9A58DD003A90085028503A2024C0FCFA5028508A5038509A504850AA505850BA50685"
            "0CA507850DA9008519A5088502A5098503A003B102304B297F0A851488B1022980F002E614A514F03DC9779039C986B0"
            "31A98E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A516850EA517850FA901"
            "D00AA9018519A900850E850FA50A8502A50B8503A003B102304B297F0A851488B1022980F002E614A514F03DC9779039"
            "C986B031A98E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A51785"
            "11A901D00AA9018519A90085108511A519D05C18A50E65108512A50F65118513304DA5120513F047A50C8502A50D8503"
            "A512A61320A711A003B102297F0A851488B1022980F002E614A51438E9088514A002B102297F8516A5142901F006A516"
            "0980D002A5169102C8A5144A910260A50C8502A50D8503A000A9009102C89102C89102C891026085048605A9008506A5"
            "052980F015A9808506A50449FF1869018504A50549FF69008505A5040505D010A000A9009102C89102C89102C8910260"
            "A9008507A505300806042605E607D0F4A98E38E5078508A000A9009102C8A5049102C8A505297F8509A5082901F006A5"
            "090980D002A5099102C8A5084A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0x10},
            {"addr": 0x03D4, "value": 0x41},
        ],
        "expected_alink_loads": ["LIB/RT_F_ADD.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_add_fraction_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 79\n"
            "b u0M\n"
            "u rt_f_add\n"
            "m A9 00 8D E0 03 8D E1 03 A9 C0 8D E2 03 A9 3F 8D E3 03 A9 00 8D E4 03 8D E5 03 A9 10 8D E6 03 A9 40 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 61 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_add", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9C08DE203A93F8DE303A9008DE4038DE503A9108DE603A9408DE703A9E08502A9038503A9E48504"
            "A9038505A9D18506A9038507204F10A9A58DD003A90085028503A2024C0FCFA5028508A5038509A504850AA505850BA5"
            "06850CA507850DA9008519A5088502A5098503A003B102304B297F0A851488B1022980F002E614A514F03DC9779039C9"
            "86B031A98E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A516850EA517850F"
            "A901D00AA9018519A900850E850FA50A8502A50B8503A003B102304B297F0A851488B1022980F002E614A514F03DC977"
            "9039C986B031A98E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A5"
            "178511A901D00AA9018519A90085108511A519D05C18A50E65108512A50F65118513304DA5120513F047A50C8502A50D"
            "8503A512A61320A911A003B102297F0A851488B1022980F002E614A51438E9088514A002B102297F8516A5142901F006"
            "A5160980D002A5169102C8A5144A910260A50C8502A50D8503A000A9009102C89102C89102C891026085048605A90085"
            "06A5052980F015A9808506A50449FF1869018504A50549FF69008505A5040505D010A000A9009102C89102C89102C891"
            "0260A9008507A505300806042605E607D0F4A98E38E5078508A000A9009102C8A5049102C8A505297F8509A5082901F0"
            "06A5090980D002A5099102C8A5084A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0x70},
            {"addr": 0x03D4, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_F_ADD.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_sub_byte_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 77\n"
            "b u0M\n"
            "u rt_f_sub\n"
            "m A9 00 8D E0 03 8D E1 03 A9 E0 8D E2 03 A9 40 8D E3 03 A9 00 8D E4 03 8D E5 03 8D E6 03 A9 40 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 59 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_sub", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9E08DE203A9408DE303A9008DE4038DE5038DE603A9408DE703"
            "A9E08502A9038503A9E48504A9038505A9D18506A9038507204D10A9A58DD003"
            "A90085028503A2024C0FCF"
            "A5028508A5038509A504850AA505850BA506850CA507850DA9008519A5088502A5098503"
            "A003B102304B297F0A851488B1022980F002E614A514F03DC9779039C986B031A98E38E514"
            "8515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A516850E"
            "A517850FA901D00AA9018519A900850E850FA50A8502A50B8503A003B102304B297F0A"
            "851488B1022980F002E614A514F03DC9779039C986B031A98E38E5148515A000B1028516"
            "C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A5178511A901D00A"
            "A9018519A90085108511A519D05E38A50EE5108512A50FE5118513904F304DA5120513F047"
            "A50C8502A50D8503A512A61320A911A003B102297F0A851488B1022980F002E614A51438"
            "E9088514A002B102297F8516A5142901F006A5160980D002A5169102C8A5144A910260"
            "A50C8502A50D8503A000A9009102C89102C89102C891026085048605A9008506A5052980"
            "F015A9808506A50449FF1869018504A50549FF69008505A5040505D010A000A9009102"
            "C89102C89102C8910260A9008507A505300806042605E607D0F4A98E38E5078508A000"
            "A9009102C8A5049102C8A505297F8509A5082901F006A5090980D002A5099102C8A508"
            "4A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0xA0},
            {"addr": 0x03D4, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_F_SUB.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_sub_fraction_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 79\n"
            "b u0M\n"
            "u rt_f_sub\n"
            "m A9 00 8D E0 03 8D E1 03 A9 70 8D E2 03 A9 40 8D E3 03 A9 00 8D E4 03 8D E5 03 A9 C0 8D E6 03 A9 3F 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 61 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_sub", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9708DE203A9408DE303A9008DE4038DE503A9C08DE603A93F8DE703"
            "A9E08502A9038503A9E48504A9038505A9D18506A9038507204F10A9A58DD003A9008502"
            "8503A2024C0FCFA5028508A5038509A504850AA505850BA506850CA507850DA9008519"
            "A5088502A5098503A003B102304B297F0A851488B1022980F002E614A514F03DC9779039"
            "C986B031A98E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616"
            "C615D0F6A516850EA517850FA901D00AA9018519A900850E850FA50A8502A50B8503A003"
            "B102304B297F0A851488B1022980F002E614A514F03DC9779039C986B031A98E38E5148515"
            "A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A517"
            "8511A901D00AA9018519A90085108511A519D05E38A50EE5108512A50FE5118513904F304D"
            "A5120513F047A50C8502A50D8503A512A61320AB11A003B102297F0A851488B1022980F0"
            "02E614A51438E9088514A002B102297F8516A5142901F006A5160980D002A5169102C8"
            "A5144A910260A50C8502A50D8503A000A9009102C89102C89102C891026085048605A900"
            "8506A5052980F015A9808506A50449FF1869018504A50549FF69008505A5040505D010"
            "A000A9009102C89102C89102C8910260A9008507A505300806042605E607D0F4A98E38"
            "E5078508A000A9009102C8A5049102C8A505297F8509A5082901F006A5090980D002A509"
            "9102C8A5084A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0x10},
            {"addr": 0x03D4, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_F_SUB.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_mul_byte_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 77\n"
            "b u0M\n"
            "u rt_f_mul\n"
            "m A9 00 8D E0 03 8D E1 03 A9 E0 8D E2 03 A9 40 8D E3 03 A9 00 8D E4 03 8D E5 03 8D E6 03 A9 40 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 59 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_mul", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9E08DE203A9408DE303A9008DE4038DE5038DE603A9408DE703A9E08502A9038503A9E48504A903"
            "8505A9D18506A9038507204D10A9A58DD003A90085028503A2024C0FCFA5028508A5038509A504850AA505850BA50685"
            "0CA507850DA5088502A5098503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033A98E38"
            "E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A516850EA517850FD00AA50ED006"
            "A900850E850FA50A8502A50B8503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033A98E"
            "38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A5178511D00AA510D0"
            "06A90085108511A9008512851385148515A50E8516A50F8517A90085188519A510851AA511851BA210461B661A901918"
            "A51265168512A51365178513A51465188514A515651985150616261726182619CAD0D6A515D057A5138512A514851330"
            "4DA5120513F047A50C8502A50D8503A512A61320E611A003B102297F0A851488B1022980F002E614A51438E9088514A0"
            "02B102297F8516A5142901F006A5160980D002A5169102C8A5144A910260A50C8502A50D8503A000A9009102C89102C8"
            "9102C891026085048605A9008506A5052980F015A9808506A50449FF1869018504A50549FF69008505A5040505D010A0"
            "00A9009102C89102C89102C8910260A9008507A505300806042605E607D0F4A98E38E5078508A000A9009102C8A50491"
            "02C8A505297F8509A5082901F006A5090980D002A5099102C8A5084A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0x60},
            {"addr": 0x03D4, "value": 0x41},
        ],
        "expected_alink_loads": ["LIB/RT_F_MUL.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_mul_fraction_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 79\n"
            "b u0M\n"
            "u rt_f_mul\n"
            "m A9 00 8D E0 03 8D E1 03 A9 C0 8D E2 03 A9 3F 8D E3 03 A9 00 8D E4 03 8D E5 03 A9 C0 8D E6 03 A9 3F 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 61 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_mul", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9C08DE203A93F8DE303A9008DE4038DE503A9C08DE603A93F8DE703A9E08502A9038503A9E48504"
            "A9038505A9D18506A9038507204F10A9A58DD003A90085028503A2024C0FCFA5028508A5038509A504850AA505850BA5"
            "06850CA507850DA5088502A5098503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033A9"
            "8E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A516850EA517850FD00AA50E"
            "D006A900850E850FA50A8502A50B8503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033"
            "A98E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A5178511D00AA5"
            "10D006A90085108511A9008512851385148515A50E8516A50F8517A90085188519A510851AA511851BA210461B661A90"
            "1918A51265168512A51365178513A51465188514A515651985150616261726182619CAD0D6A515D057A5138512A51485"
            "13304DA5120513F047A50C8502A50D8503A512A61320E811A003B102297F0A851488B1022980F002E614A51438E90885"
            "14A002B102297F8516A5142901F006A5160980D002A5169102C8A5144A910260A50C8502A50D8503A000A9009102C891"
            "02C89102C891026085048605A9008506A5052980F015A9808506A50449FF1869018504A50549FF69008505A5040505D0"
            "10A000A9009102C89102C89102C8910260A9008507A505300806042605E607D0F4A98E38E5078508A000A9009102C8A5"
            "049102C8A505297F8509A5082901F006A5090980D002A5099102C8A5084A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0x10},
            {"addr": 0x03D4, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_F_MUL.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_div_byte_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 77\n"
            "b u0M\n"
            "u rt_f_div\n"
            "m A9 00 8D E0 03 8D E1 03 A9 60 8D E2 03 A9 41 8D E3 03 A9 00 8D E4 03 8D E5 03 8D E6 03 A9 40 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 59 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_div", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9608DE203A9418DE303A9008DE4038DE5038DE603A9408DE703A9E08502A9038503A9E48504A903"
            "8505A9D18506A9038507204D10A9A58DD003A90085028503A2024C0FCFA5028508A5038509A504850AA505850BA50685"
            "0CA507850DA5088502A5098503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033A98E38"
            "E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A516850EA517850FD00AA50ED006"
            "A900850E850FA50A8502A50B8503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033A98E"
            "38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A5178511D00AA510D0"
            "06A90085108511A5100511D0034C8F01A50E050FD0034C8F01A9008512A50E8513A50F8514A900851585168517851885"
            "19A21806122613261426152616B00EA516C5119018D006A515C510901038A515E5108515A516E511851638B001182617"
            "26182619CAD0CCA519D051A518304DA5170518F047A50C8502A50D8503A517A61820F411A003B102297F0A851488B102"
            "2980F002E614A51438E9088514A002B102297F8516A5142901F006A5160980D002A5169102C8A5144A910260A50C8502"
            "A50D8503A000A9009102C89102C89102C891026085048605A9008506A5052980F015A9808506A50449FF1869018504A5"
            "0549FF69008505A5040505D010A000A9009102C89102C89102C8910260A9008507A505300806042605E607D0F4A98E38"
            "E5078508A000A9009102C8A5049102C8A505297F8509A5082901F006A5090980D002A5099102C8A5084A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0xE0},
            {"addr": 0x03D4, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_F_DIV.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_div_half_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 77\n"
            "b u0M\n"
            "u rt_f_div\n"
            "m A9 00 8D E0 03 8D E1 03 A9 40 8D E2 03 A9 40 8D E3 03 A9 00 8D E4 03 8D E5 03 8D E6 03 A9 40 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 59 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_div", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9408DE203A9408DE303A9008DE4038DE5038DE603A9408DE703A9E08502A9038503A9E48504A903"
            "8505A9D18506A9038507204D10A9A58DD003A90085028503A2024C0FCFA5028508A5038509A504850AA505850BA50685"
            "0CA507850DA5088502A5098503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033A98E38"
            "E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A516850EA517850FD00AA50ED006"
            "A900850E850FA50A8502A50B8503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033A98E"
            "38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A5178511D00AA510D0"
            "06A90085108511A5100511D0034C8F01A50E050FD0034C8F01A9008512A50E8513A50F8514A900851585168517851885"
            "19A21806122613261426152616B00EA516C5119018D006A515C510901038A515E5108515A516E511851638B001182617"
            "26182619CAD0CCA519D051A518304DA5170518F047A50C8502A50D8503A517A61820F411A003B102297F0A851488B102"
            "2980F002E614A51438E9088514A002B102297F8516A5142901F006A5160980D002A5169102C8A5144A910260A50C8502"
            "A50D8503A000A9009102C89102C89102C891026085048605A9008506A5052980F015A9808506A50449FF1869018504A5"
            "0549FF69008505A5040505D010A000A9009102C89102C89102C8910260A9008507A505300806042605E607D0F4A98E38"
            "E5078508A000A9009102C8A5049102C8A505297F8509A5082901F006A5090980D002A5099102C8A5084A0506910260"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0xC0},
            {"addr": 0x03D4, "value": 0x3F},
        ],
        "expected_alink_loads": ["LIB/RT_F_DIV.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_div_fraction_input_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 79\n"
            "b u0M\n"
            "u rt_f_div\n"
            "m A9 00 8D E0 03 8D E1 03 A9 C0 8D E2 03 A9 3F 8D E3 03 A9 00 8D E4 03 8D E5 03 A9 40 8D E6 03 A9 3F 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 A9 D1 85 06 A9 03 85 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 61 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_div", "rt_s_to_f"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9C08DE203A93F8DE303A9008DE4038DE503A9408DE603A93F8DE703A9E08502A9038503A9E48504"
            "A9038505A9D18506A9038507204F10A9A58DD003A90085028503A2024C0FCFA5028508A5038509A504850AA505850BA5"
            "06850CA507850DA5088502A5098503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033A9"
            "8E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A516850EA517850FD00AA50E"
            "D006A900850E850FA50A8502A50B8503A003B102304D297F0A851488B1022980F002E614A514F03BC9779037C986B033"
            "A98E38E5148515A000B1028516C8B1028517C8B102297F09808518461866176616C615D0F6A5168510A5178511D00AA5"
            "10D006A90085108511A5100511D0034C8F01A50E050FD0034C8F01A9008512A50E8513A50F8514A90085158516851785"
            "188519A21806122613261426152616B00EA516C5119018D006A515C510901038A515E5108515A516E511851638B00118"
            "261726182619CAD0CCA519D051A518304DA5170518F047A50C8502A50D8503A517A61820F611A003B102297F0A851488"
            "B1022980F002E614A51438E9088514A002B102297F8516A5142901F006A5160980D002A5169102C8A5144A910260A50C"
            "8502A50D8503A000A9009102C89102C89102C891026085048605A9008506A5052980F015A9808506A50449FF18690185"
            "04A50549FF69008505A5040505D010A000A9009102C89102C89102C8910260A9008507A505300806042605E607D0F4A9"
            "8E38E5078508A000A9009102C8A5049102C8A505297F8509A5082901F006A5090980D002A5099102C8A5084A05069102"
            "60"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0x00},
            {"addr": 0x03D4, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_F_DIV.OBJ", "LIB/RT_S_TO_F.OBJ"],
    },
    "runtime_real_f_cmp_byte_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 125\n"
            "b u0M\n"
            "u rt_f_cmp\n"
            "m A9 00 8D E0 03 8D E1 03 A9 E0 8D E2 03 A9 40 8D E3 03 A9 00 8D E4 03 8D E5 03 8D E6 03 A9 40 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 20 00 00 8D D1 03 8E D2 03 A9 E4 85 02 A9 03 85 03 A9 E0 85 04 A9 03 85 05 20 00 00 8D D3 03 8E D4 03 A9 E0 85 02 A9 03 85 03 A9 E0 85 04 A9 03 85 05 20 00 00 8D D5 03 8E D6 03 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 51 u0\n"
            "r 76 u0\n"
            "r 101 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_cmp"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9E08DE203A9408DE303A9008DE4038DE5038DE603A9408DE703"
            "A9E08502A9038503A9E48504A9038505207D108DD1038ED203A9E48502A9038503"
            "A9E08504A9038505207D108DD3038ED403A9E08502A9038503A9E08504A9038505"
            "207D108DD5038ED603A9A58DD003A90085028503A2024C0FCFA5028508A5038509"
            "A504850AA505850BA5088502A5098503A003B102304D297F0A851088B1022980F0"
            "02E610A510F03BC9779037C986B033A98E38E5108511A000B1028512C8B1028513"
            "C8B102297F09808514461466136612C611D0F6A512850CA513850DD00AA50CD006"
            "A900850C850DA50A8502A50B8503A003B102304D297F0A851088B1022980F002E6"
            "10A510F03BC9779037C986B033A98E38E5108511A000B1028512C8B1028513C8B1"
            "02297F09808514461466136612C611D0F6A512850EA513850FD00AA50ED006A900"
            "850E850FA50DC50F900ED010A50CC50E9006D008A900AA60A9FFAA60A901A20060"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0xFF},
            {"addr": 0x03D4, "value": 0xFF},
            {"addr": 0x03D5, "value": 0x00},
            {"addr": 0x03D6, "value": 0x00},
        ],
        "expected_alink_loads": ["LIB/RT_F_CMP.OBJ"],
    },
    "runtime_real_f_cmp_fraction_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 127\n"
            "b u0M\n"
            "u rt_f_cmp\n"
            "m A9 00 8D E0 03 8D E1 03 A9 C0 8D E2 03 A9 3F 8D E3 03 A9 00 8D E4 03 8D E5 03 A9 A0 8D E6 03 A9 3F 8D E7 03 A9 E0 85 02 A9 03 85 03 A9 E4 85 04 A9 03 85 05 20 00 00 8D D1 03 8E D2 03 A9 E4 85 02 A9 03 85 03 A9 E0 85 04 A9 03 85 05 20 00 00 8D D3 03 8E D4 03 A9 E0 85 02 A9 03 85 03 A9 E0 85 04 A9 03 85 05 20 00 00 8D D5 03 8E D6 03 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 53 u0\n"
            "r 78 u0\n"
            "r 103 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_f_cmp"],
        "expected_tail": bytes.fromhex(
            "A9008DE0038DE103A9C08DE203A93F8DE303A9008DE4038DE503A9A08DE603A93F8DE703"
            "A9E08502A9038503A9E48504A9038505207F108DD1038ED203A9E48502A9038503"
            "A9E08504A9038505207F108DD3038ED403A9E08502A9038503A9E08504A9038505"
            "207F108DD5038ED603A9A58DD003A90085028503A2024C0FCFA5028508A5038509"
            "A504850AA505850BA5088502A5098503A003B102304D297F0A851088B1022980F0"
            "02E610A510F03BC9779037C986B033A98E38E5108511A000B1028512C8B1028513"
            "C8B102297F09808514461466136612C611D0F6A512850CA513850DD00AA50CD006"
            "A900850C850DA50A8502A50B8503A003B102304D297F0A851088B1022980F002E6"
            "10A510F03BC9779037C986B033A98E38E5108511A000B1028512C8B1028513C8B1"
            "02297F09808514461466136612C611D0F6A512850EA513850FD00AA50ED006A900"
            "850E850FA50DC50F900ED010A50CC50E9006D008A900AA60A9FFAA60A901A20060"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x03D3, "value": 0xFF},
            {"addr": 0x03D4, "value": 0xFF},
            {"addr": 0x03D5, "value": 0x00},
            {"addr": 0x03D6, "value": 0x00},
        ],
        "expected_alink_loads": ["LIB/RT_F_CMP.OBJ"],
    },
    "runtime_sprite_on_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 21\n"
            "b u0M\n"
            "u rt_sprite_on\n"
            "m A9 02 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 3 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_on"],
        "expected_tail": bytes.fromhex(
            "A902201510A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FC0D15D08D15D060"
        ),
        "store_check_addr": 0xD015,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_ON.OBJ"],
    },
    "actc_runtime_sprite_on_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteOn(2)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_on"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_sprite_on\n",
            "i 2\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902201510A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FC0D15D08D15D060"
        ),
        "store_check_addr": 0xD015,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_ON.OBJ"],
    },
    "actc_runtime_variable_sprite_on_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "SpriteOn(SPRITE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_on",
            "rt_sprite_off",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sprite_on\n",
            "i 2\n",
            "v sprite 0\n",
        ],
        "expected_tail": _actc_variable_sprite_on_runtime_tail(),
        "store_check_addr": 0xD015,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_ON.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_OFF.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "runtime_gfx_bgcolor_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 21\n"
            "b u0M\n"
            "u rt_gfx_bgcolor\n"
            "m A9 06 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 3 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bgcolor"],
        "expected_tail": bytes.fromhex(
            "A906201510A9A58DD003A90085028503A2024C0FCF290F8D21D060"
        ),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_BGCOLOR.OBJ"],
    },
    "actc_runtime_gfx_bgcolor_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBgColor(6)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bgcolor"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bgcolor\n",
            "i 6\n",
        ],
        "expected_tail": bytes.fromhex(
            "A906201510A9A58DD003A90085028503A2024C0FCF290F8D21D060"
        ),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_BGCOLOR.OBJ"],
    },
    "actc_runtime_variable_gfx_bgcolor_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE COLOR\r"
            "PROC MAIN()\r"
            "COLOR=6\r"
            "BgColor(COLOR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_bgcolor\n",
            "i 6\n",
            "v color 0\n",
        ],
        "expected_tail": _actc_variable_gfx_bgcolor_runtime_tail(),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_BGCOLOR.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_repeated_bgcolor_helper_dedup": {
        "source": "MODULE MAIN\rPROC MAIN()\rBgColor(2)\rBgColor(6)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_gfx_bgcolor\n",
            "i 2\n",
            "i 6\n",
        ],
        "expected_tail": _actc_repeated_bgcolor_runtime_tail(),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_BGCOLOR.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_input_joystick_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "Joy(2)\r"
            "JoySeen(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_jp",
            "rt_js",
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_jp\n",
            "i 2\n",
        ],
        "expected_tail": _actc_input_joystick_runtime_tail(),
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
    },
    "actc_runtime_input_joystick_condition_gfx_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "IF Joy(2)=0 THEN\r"
            "BgColor(6)\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_gfx_bgcolor",
            "rt_jp",
            "rt_mp",
            "rt_gfx_bordercolor",
        ],
        "expected_object_fragments": [
            "b p0u0p1qhp2u1vr\n",
            "u rt_joy\n",
            "u rt_gfx_bgcolor\n",
            "i 2\n",
            "i 0\n",
            "i 6\n",
        ],
        "expected_tail": _actc_input_joystick_condition_gfx_runtime_tail(),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
    },
    "actc_runtime_input_joystick_not_equal_condition_gfx_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "IF Joy(2)<>1 THEN\r"
            "BgColor(6)\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_gfx_bgcolor",
            "rt_jp",
            "rt_mp",
            "rt_gfx_bordercolor",
        ],
        "expected_object_fragments": [
            "b p0u0p1nhp2u1vr\n",
            "u rt_joy\n",
            "u rt_gfx_bgcolor\n",
            "i 2\n",
            "i 1\n",
            "i 6\n",
        ],
        "expected_tail": _actc_input_joystick_condition_gfx_runtime_tail(1, 0xF0),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
    },
    "actc_runtime_input_joystick_state_store_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "BYTE P\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "P=JoySeen(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_jp",
            "rt_js",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_jp\n",
            "i 2\n",
            "v j 0\n",
            "v p 0\n",
        ],
        "expected_tail": _actc_input_joystick_store_runtime_tail(),
        "store_check_hi_addr": 0x102B,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x102D, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
    },
    "actc_runtime_input_joystick_two_button_mask_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE MASK\r"
            "BYTE STATE\r"
            "PROC MAIN()\r"
            "MASK=JOY_BUTTON1+JOY_BUTTON2\r"
            "STATE=Joy(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_jp",
            "rt_js",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "i 48\n",
            "i 2\n",
            "v mask 0\n",
            "v state 0\n",
        ],
        "expected_tail": _actc_input_joystick_two_button_mask_runtime_tail(),
        "store_check_hi_addr": 0x1020,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
    },
    "actc_runtime_input_joystick_button_state_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE B1\r"
            "BYTE B2\r"
            "PROC MAIN()\r"
            "B1=JoyBtn1(2)\r"
            "B2=JoyBtn2(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_jb1",
            "rt_jb2",
            "rt_joy",
            "rt_jp",
            "rt_js",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1u1S1r\n",
            "u rt_jb1\n",
            "u rt_jb2\n",
            "i 2\n",
            "v b1 0\n",
            "v b2 0\n",
        ],
        "expected_tail": _actc_input_dual_store_runtime_tail(("rt_jb1", "rt_jb2"), (2, 2)),
        "spin_after_marker_for_live": True,
        "store_check_hi_addr": 0x102B,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x102D, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JB1.OBJ",
            "LIB/RT_JB2.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
    },
    "actc_runtime_input_mouse_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "MousePoll(1)\r"
            "MouseSeen()\r"
            "MouseX()\r"
            "MouseY()\r"
            "MouseBtn()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_mp\n",
            "u rt_mseen\n",
            "u rt_mx\n",
            "u rt_my\n",
            "u rt_mb\n",
            "i 1\n",
        ],
        "expected_tail": _actc_input_mouse_runtime_tail(),
        "expected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_input_mouse_state_store_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE X\r"
            "BYTE Y\r"
            "BYTE B\r"
            "BYTE P\r"
            "PROC MAIN()\r"
            "P=MousePoll(1)\r"
            "X=MouseX()\r"
            "Y=MouseY()\r"
            "B=MouseBtn()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_mp\n",
            "u rt_mx\n",
            "u rt_my\n",
            "u rt_mb\n",
            "i 1\n",
            "v x 0\n",
            "v y 0\n",
            "v b 0\n",
            "v p 0\n",
        ],
        "expected_tail": _actc_input_mouse_store_runtime_tail(),
        "store_check_hi_addr": 0x103F,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1041, "value": 0x00},
            {"addr": 0x1043, "value": 0x00},
            {"addr": 0x1045, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MSEEN.OBJ",
        ],
    },
    "actc_runtime_input_mouse_two_button_mask_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE MASK\r"
            "BYTE BUTTONS\r"
            "PROC MAIN()\r"
            "MASK=MOUSE_BUTTON1+MOUSE_BUTTON2\r"
            "BUTTONS=MouseBtn()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mb",
            "rt_ms",
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_mb\n",
            "i 3\n",
            "v mask 0\n",
            "v buttons 0\n",
        ],
        "expected_tail": _actc_input_mouse_two_button_mask_runtime_tail(),
        "store_check_hi_addr": 0x101E,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_input_mouse_button_state_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE B1\r"
            "BYTE B2\r"
            "PROC MAIN()\r"
            "B1=MouseBtn1()\r"
            "B2=MouseBtn2()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mb1",
            "rt_mb2",
            "rt_mb",
            "rt_ms",
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "b u0S0u1S1r\n",
            "u rt_mb1\n",
            "u rt_mb2\n",
            "v b1 0\n",
            "v b2 0\n",
        ],
        "expected_tail": _actc_input_dual_store_runtime_tail(("rt_mb1", "rt_mb2"), (None, None)),
        "spin_after_marker_for_live": True,
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1029, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_MB1.OBJ",
            "LIB/RT_MB2.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_input_mouse_button_condition_gfx_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "IF MouseBtn()=0 THEN\r"
            "BgColor(6)\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mb",
            "rt_ms",
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_mp",
            "rt_mseen",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "b u0p0qhp1u1vr\n",
            "u rt_mb\n",
            "u rt_gfx_bgcolor\n",
            "i 0\n",
            "i 6\n",
        ],
        "expected_tail": _actc_input_mouse_condition_gfx_runtime_tail(),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
    },
    "actc_runtime_input_mouse_button_not_equal_condition_gfx_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "IF MouseBtn()<>1 THEN\r"
            "BgColor(6)\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mb",
            "rt_ms",
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_mp",
            "rt_mseen",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "b u0p0nhp1u1vr\n",
            "u rt_mb\n",
            "u rt_gfx_bgcolor\n",
            "i 1\n",
            "i 6\n",
        ],
        "expected_tail": _actc_input_mouse_condition_gfx_runtime_tail(1, 0xF0),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
    },
    "actc_runtime_input_joystick_button_condition_gfx_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "IF JoyBtn1(2)=0 THEN\r"
            "BgColor(3)\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_jb1",
            "rt_joy",
            "rt_gfx_bgcolor",
            "rt_jb2",
            "rt_jp",
            "rt_js",
            "rt_gfx_bordercolor",
        ],
        "expected_object_fragments": [
            "b p0u0p1qhp2u1vr\n",
            "u rt_jb1\n",
            "u rt_gfx_bgcolor\n",
            "i 2\n",
            "i 0\n",
            "i 3\n",
        ],
        "expected_tail": _actc_input_joystick_condition_gfx_runtime_tail(
            0, 0xD0, "rt_jb1", 2, 3
        ),
        "spin_after_marker_for_live": True,
        "store_check_addr": 0xD021,
        "store_check_value": 0x03,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_JB1.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JB2.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
    },
    "actc_runtime_input_mouse_button2_condition_gfx_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "IF MouseBtn2()=0 THEN\r"
            "BgColor(7)\r"
            "FI\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mb2",
            "rt_mb",
            "rt_ms",
            "rt_gfx_bgcolor",
            "rt_mb1",
            "rt_mp",
            "rt_mseen",
            "rt_joy",
            "rt_gfx_bordercolor",
        ],
        "expected_object_fragments": [
            "b u0p0qhp1u1vr\n",
            "u rt_mb2\n",
            "u rt_gfx_bgcolor\n",
            "i 0\n",
            "i 7\n",
        ],
        "expected_tail": _actc_input_mouse_condition_gfx_runtime_tail(0, 0xD0, "rt_mb2", 7),
        "spin_after_marker_for_live": True,
        "store_check_addr": 0xD021,
        "store_check_value": 0x07,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_MB2.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MB1.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
    },
    "actc_runtime_input_variable_port_store_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE PORT\r"
            "BYTE J\r"
            "BYTE M\r"
            "PROC MAIN()\r"
            "PORT=2\r"
            "J=Joy(PORT)\r"
            "PORT=1\r"
            "M=MousePoll(PORT)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_jp",
            "rt_js",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_mp\n",
            "i 2\n",
            "i 1\n",
            "v port 0\n",
            "v j 0\n",
            "v m 0\n",
        ],
        "expected_tail": _actc_input_variable_port_store_runtime_tail(),
        "store_check_addr": 0x102C,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x102D,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x102E, "value": 0x00},
            {"addr": 0x102F, "value": 0x00},
            {"addr": 0x1030, "value": 0x00},
            {"addr": 0x1031, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
        ],
    },
    "actc_runtime_input_dual_port_presence_store_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE JSA\r"
            "BYTE JSB\r"
            "BYTE MPA\r"
            "BYTE MPB\r"
            "BYTE MSN\r"
            "PROC MAIN()\r"
            "JSA=JoySeen(1)\r"
            "JSB=JoySeen(2)\r"
            "MPA=MousePoll(1)\r"
            "MPB=MousePoll(2)\r"
            "MSN=MouseSeen()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_jp",
            "rt_joy",
            "rt_js",
            "rt_mp",
            "rt_ms",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_mb1",
            "rt_mb2",
            "rt_jb1",
            "rt_jb2",
        ],
        "expected_object_fragments": [
            "u rt_jp\n",
            "u rt_mp\n",
            "u rt_mseen\n",
            "i 1\n",
            "i 2\n",
            "v jsa 0\n",
            "v jsb 0\n",
            "v mpa 0\n",
            "v mpb 0\n",
            "v msn 0\n",
        ],
        "expected_tail": _actc_input_dual_port_presence_runtime_tail(),
        "store_check_addr": 0x104F,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1050,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1051, "value": 0x00},
            {"addr": 0x1052, "value": 0x00},
            {"addr": 0x1053, "value": 0x00},
            {"addr": 0x1054, "value": 0x00},
            {"addr": 0x1055, "value": 0x00},
            {"addr": 0x1056, "value": 0x00},
            {"addr": 0x1057, "value": 0x00},
            {"addr": 0x1058, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_MSEEN.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MB1.OBJ",
            "LIB/RT_MB2.OBJ",
            "LIB/RT_JB1.OBJ",
            "LIB/RT_JB2.OBJ",
        ],
    },
    "actc_runtime_input_gfx_mixed_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "BYTE M\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "M=MousePoll(1)\r"
            "BgColor(6)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_mp",
            "rt_ms",
            "rt_jp",
            "rt_js",
            "rt_mb",
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_mp\n",
            "u rt_gfx_bgcolor\n",
            "i 2\n",
            "i 1\n",
            "i 6\n",
            "v j 0\n",
            "v m 0\n",
        ],
        "expected_tail": _actc_input_gfx_mixed_runtime_tail(),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x1030, "value": 0x00},
            {"addr": 0x1032, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_input_mouse_result_gfx_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE M\r"
            "PROC MAIN()\r"
            "M=MousePoll(1)\r"
            "BgColor(M)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mp",
            "rt_ms",
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_joy",
            "rt_mx",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0u1r\n",
            "u rt_mp\n",
            "u rt_gfx_bgcolor\n",
            "i 1\n",
            "v m 0\n",
        ],
        "expected_tail": _actc_input_result_arg_mixed_runtime_tail(
            "rt_mp", 1, "rt_gfx_bgcolor", "graphics"
        ),
        "store_check_addr": 0xD021,
        "store_check_value": 0x00,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x1023, "value": 0x00},
            {"addr": 0x1024, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
    },
    "actc_runtime_input_mouse_result_sid_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE M\r"
            "PROC MAIN()\r"
            "M=MousePoll(1)\r"
            "SidVol(M)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mp",
            "rt_ms",
            "rt_sid_vol",
            "rt_sid_volume_state",
            "rt_joy",
            "rt_sid_mode",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0u1r\n",
            "u rt_mp\n",
            "u rt_sid_vol\n",
            "i 1\n",
            "v m 0\n",
        ],
        "expected_tail": _actc_input_result_arg_mixed_runtime_tail(
            "rt_mp", 1, "rt_sid_vol", "SID"
        ),
        "store_check_addr": 0xD418,
        "store_check_value": 0x00,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_MODE.OBJ",
        ],
    },
    "actc_runtime_input_mouse_result_sprite_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE M\r"
            "PROC MAIN()\r"
            "M=MousePoll(1)\r"
            "SpriteColor(1,M)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mp",
            "rt_ms",
            "rt_sprite_color",
            "rt_sprite_on",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_mp\n",
            "u rt_sprite_color\n",
            "i 1\n",
            "v m 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_xa_runtime_tail(
            "rt_mp", 1, "rt_sprite_color", 1, "sprite"
        ),
        "store_check_addr": 0xD028,
        "store_check_value": 0x00,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_ON.OBJ",
        ],
    },
    "actc_runtime_input_mouse_x_result_sprite_pos_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE X\r"
            "PROC MAIN()\r"
            "X=MouseX()\r"
            "SpritePos(1,X,4)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mx",
            "rt_ms",
            "rt_sprite_pos",
            "rt_sprite_data",
            "rt_mp",
            "rt_my",
            "rt_mb",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_mx\n",
            "u rt_sprite_pos\n",
            "i 1\n",
            "i 4\n",
            "v x 0\n",
        ],
        "expected_tail": _actc_input_result_sprite_pos_runtime_tail(
            "rt_mx", None, 1, 1, 0, 4, "sprite"
        ),
        "store_check_addr": 0x1027,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1028,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MX.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_SPRITE_POS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
    },
    "actc_runtime_input_mouse_y_result_sprite_pos_third_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE Y\r"
            "PROC MAIN()\r"
            "Y=MouseY()\r"
            "SpritePos(1,52,Y)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_my",
            "rt_ms",
            "rt_sprite_pos",
            "rt_sprite_data",
            "rt_mp",
            "rt_mx",
            "rt_mb",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_my\n",
            "u rt_sprite_pos\n",
            "i 1\n",
            "i 52\n",
            "v y 0\n",
        ],
        "expected_tail": _actc_input_result_sprite_pos_runtime_tail(
            "rt_my", None, 2, 1, 52, 0, "sprite"
        ),
        "store_check_addr": 0x1027,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1028,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MY.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_SPRITE_POS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
    },
    "actc_runtime_input_mouse_button_result_sid_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE B\r"
            "PROC MAIN()\r"
            "B=MouseBtn()\r"
            "SidVol(B)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mb",
            "rt_ms",
            "rt_sid_vol",
            "rt_sid_volume_state",
            "rt_sid_mode",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_mb\n",
            "u rt_sid_vol\n",
            "v b 0\n",
        ],
        "expected_tail": _actc_input_result_arg_mixed_runtime_tail(
            "rt_mb", None, "rt_sid_vol", "SID"
        ),
        "store_check_addr": 0xD418,
        "store_check_value": 0x00,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_MODE.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidVol(J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_vol",
            "rt_sid_volume_state",
            "rt_sid_mode",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0u1r\n",
            "u rt_joy\n",
            "u rt_sid_vol\n",
            "i 2\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_arg_mixed_runtime_tail(
            "rt_joy", 2, "rt_sid_vol", "SID"
        ),
        "store_check_addr": 0xD418,
        "store_check_value": 0x00,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x1023, "value": 0x00},
            {"addr": 0x1024, "value": 0x00},
            {"addr": 0x1065, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_MODE.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_word_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidCutoff(J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_cutoff",
            "rt_sid_freq",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0u1r\n",
            "u rt_joy\n",
            "u rt_sid_cutoff\n",
            "i 2\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_word_arg_runtime_tail(
            "rt_joy", 2, "rt_sid_cutoff", "SID"
        ),
        "store_check_addr": 0xD415,
        "store_check_value": 0x00,
        "store_check_mask": 0x07,
        "store_check_hi_addr": 0xD416,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1026, "value": 0x00},
            {"addr": 0x1027, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_CUTOFF.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidFreq(J,4660)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_freq",
            "rt_sid_pulse",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sid_freq\n",
            "i 2\n",
            "i 4660\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_word_second_runtime_tail(
            "rt_joy", 2, "rt_sid_freq", 4660, "SID"
        ),
        "store_check_addr": 0x1027,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1028,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_PULSE.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_freq_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidFreq(1,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_freq",
            "rt_sid_pulse",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sid_freq\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_word_first_runtime_tail(
            "rt_joy", 2, "rt_sid_freq", 1, "SID"
        ),
        "store_check_addr": 0x1028,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1029,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_PULSE.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_pulse_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidPulse(1,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_pulse",
            "rt_sid_freq",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sid_pulse\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_word_first_runtime_tail(
            "rt_joy", 2, "rt_sid_pulse", 1, "SID"
        ),
        "store_check_addr": 0x1028,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1029,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_PULSE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteColor(1,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_color",
            "rt_sprite_on",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_color\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_xa_runtime_tail(
            "rt_joy", 2, "rt_sprite_color", 1, "sprite"
        ),
        "store_check_addr": 0xD028,
        "store_check_value": 0x00,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x1025, "value": 0x00},
            {"addr": 0x1026, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_ON.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteColor(J,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_color",
            "rt_sprite_on",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sprite_color\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_xa_runtime_tail(
            "rt_joy", 2, "rt_sprite_color", 1, "sprite"
        ),
        "store_check_addr": 0xD027,
        "store_check_value": 0x01,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x1026, "value": 0x00},
            {"addr": 0x1027, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_ON.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_data_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteData(J,8192)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_data",
            "rt_sprite_ptr",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sprite_data\n",
            "i 2\n",
            "i 8192\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_sprite_data_runtime_tail(
            "rt_joy", 2, 0, 0, 8192, "sprite"
        ),
        "store_check_addr": 0x07F8,
        "store_check_value": 0x80,
        "extra_store_checks": [
            {"addr": 0x1027, "value": 0x00},
            {"addr": 0x1028, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_data_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteData(3,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_data",
            "rt_sprite_ptr",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_data\n",
            "i 2\n",
            "i 3\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_sprite_data_runtime_tail(
            "rt_joy", 2, 1, 3, 0, "sprite"
        ),
        "pre_run_memory": [
            {"addr": 0x07FB, "value": 0xFF},
        ],
        "store_check_addr": 0x07FB,
        "store_check_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1028, "value": 0x00},
            {"addr": 0x1029, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_ptr_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpritePtr(J,128)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_ptr",
            "rt_sprite_data",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sprite_ptr\n",
            "i 2\n",
            "i 128\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_xa_runtime_tail(
            "rt_joy", 2, "rt_sprite_ptr", 128, "sprite"
        ),
        "store_check_addr": 0x07F8,
        "store_check_value": 0x80,
        "extra_store_checks": [
            {"addr": 0x1026, "value": 0x00},
            {"addr": 0x1027, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_ptr_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpritePtr(3,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_ptr",
            "rt_sprite_data",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_ptr\n",
            "i 2\n",
            "i 3\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_xa_runtime_tail(
            "rt_joy", 2, "rt_sprite_ptr", 3, "sprite"
        ),
        "pre_run_memory": [
            {"addr": 0x07FB, "value": 0xFF},
        ],
        "store_check_addr": 0x07FB,
        "store_check_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1025, "value": 0x00},
            {"addr": 0x1026, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_mc_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteMC(J,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
            "rt_sprite_prio",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sprite_mc\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sprite_mc", 1, "sprite"
        ),
        "store_check_addr": 0x1025,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1026,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_mc_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteMC(3,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
            "rt_sprite_prio",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_mc\n",
            "i 2\n",
            "i 3\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sprite_mc", 3, "sprite"
        ),
        "store_check_addr": 0x1026,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_xexp_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteXExp(J,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_xexp",
            "rt_sprite_mc",
            "rt_sprite_yexp",
            "rt_sprite_prio",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sprite_xexp\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sprite_xexp", 1, "sprite"
        ),
        "store_check_addr": 0x1025,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1026,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_xexp_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteXExp(3,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_xexp",
            "rt_sprite_mc",
            "rt_sprite_yexp",
            "rt_sprite_prio",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_xexp\n",
            "i 2\n",
            "i 3\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sprite_xexp", 3, "sprite"
        ),
        "store_check_addr": 0x1026,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_yexp_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteYExp(J,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_yexp",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_prio",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sprite_yexp\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sprite_yexp", 1, "sprite"
        ),
        "store_check_addr": 0x1025,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1026,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_yexp_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpriteYExp(3,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_yexp",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_prio",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_yexp\n",
            "i 2\n",
            "i 3\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sprite_yexp", 3, "sprite"
        ),
        "store_check_addr": 0x1026,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_prio_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpritePrio(J,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_prio",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sprite_prio\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sprite_prio", 1, "sprite"
        ),
        "store_check_addr": 0x1025,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1026,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_prio_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpritePrio(3,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_prio",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_prio\n",
            "i 2\n",
            "i 3\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sprite_prio", 3, "sprite"
        ),
        "store_check_addr": 0x1026,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_set_mc_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SetSpriteMC(J,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_set_mc",
            "rt_sprite_color",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sprite_set_mc\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_xa_runtime_tail(
            "rt_joy", 2, "rt_sprite_set_mc", 1, "sprite"
        ),
        "store_check_addr": 0x1025,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1026,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_SET_MC.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_set_mc_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SetSpriteMC(1,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_set_mc",
            "rt_sprite_color",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_set_mc\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_x1_a0_runtime_tail(
            "rt_joy", 2, "rt_sprite_set_mc", 1, "sprite"
        ),
        "store_check_addr": 0x1026,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_SET_MC.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_pos_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpritePos(J,52,86)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_pos",
            "rt_sprite_data",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1p2u1r\n",
            "u rt_joy\n",
            "u rt_sprite_pos\n",
            "i 2\n",
            "i 52\n",
            "i 86\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_sprite_pos_runtime_tail(
            "rt_joy", 2, 0, 0, 52, 86, "sprite"
        ),
        "store_check_addr": 0x1028,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1029,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_POS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_pos_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpritePos(3,J,4)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_pos",
            "rt_sprite_data",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0p2u1r\n",
            "u rt_joy\n",
            "u rt_sprite_pos\n",
            "i 2\n",
            "i 3\n",
            "i 4\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_sprite_pos_runtime_tail(
            "rt_joy", 2, 1, 3, 0, 4, "sprite"
        ),
        "store_check_addr": 0x1029,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x102A,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_POS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sprite_pos_third_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SpritePos(3,52,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sprite_pos",
            "rt_sprite_data",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1p2L0u1r\n",
            "u rt_joy\n",
            "u rt_sprite_pos\n",
            "i 2\n",
            "i 3\n",
            "i 52\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_sprite_pos_runtime_tail(
            "rt_joy", 2, 2, 3, 52, 0, "sprite"
        ),
        "store_check_addr": 0x1029,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x102A,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_POS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidWave(1,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_wave",
            "rt_sid_state",
            "rt_sid_vol",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sid_wave\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sid_wave", 1, "SID"
        ),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x00,
        "store_check_mask": 0xFF,
        "extra_store_checks": [
            {"addr": 0x1026, "value": 0x00},
            {"addr": 0x1027, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_VOL.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_wave_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidWave(J,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_wave",
            "rt_sid_state",
            "rt_sid_vol",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sid_wave\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sid_wave", 1, "SID"
        ),
        "store_check_addr": 0x106D,
        "store_check_value": 0x01,
        "store_check_mask": 0xFF,
        "extra_store_checks": [
            {"addr": 0x1025, "value": 0x00},
            {"addr": 0x1026, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_VOL.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_ad_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidAD(J,151)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_ad",
            "rt_sid_sr",
            "rt_sid_wave",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sid_ad\n",
            "i 2\n",
            "i 151\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sid_ad", 151, "SID"
        ),
        "store_check_addr": 0x1025,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1026,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_AD.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_SR.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_ad_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidAD(1,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_ad",
            "rt_sid_sr",
            "rt_sid_wave",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sid_ad\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sid_ad", 1, "SID"
        ),
        "store_check_addr": 0x1026,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_AD.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_SR.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_sr_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidSR(J,248)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_sr",
            "rt_sid_ad",
            "rt_sid_wave",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1r\n",
            "u rt_joy\n",
            "u rt_sid_sr\n",
            "i 2\n",
            "i 248\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sid_sr", 248, "SID"
        ),
        "store_check_addr": 0x1025,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1026,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_SR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_AD.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_sid_sr_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "SidSR(1,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_sid_sr",
            "rt_sid_ad",
            "rt_sid_wave",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0u1r\n",
            "u rt_joy\n",
            "u rt_sid_sr\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_ay_runtime_tail(
            "rt_joy", 2, "rt_sid_sr", 1, "SID"
        ),
        "store_check_addr": 0x1026,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_SR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_SID_AD.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_gfx_first_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "ColorCell(J,1,2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_gfx_color_cell",
            "rt_gfx_screen_cell",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1p2u1r\n",
            "u rt_joy\n",
            "u rt_gfx_color_cell\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_first_arg_axy_runtime_tail(
            "rt_joy", 2, "rt_gfx_color_cell", 1, 2, "graphics"
        ),
        "store_check_addr": 0x1028,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1029,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_gfx_second_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "ColorCell(1,J,2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_gfx_color_cell",
            "rt_gfx_screen_cell",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1L0p2u1r\n",
            "u rt_joy\n",
            "u rt_gfx_color_cell\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_second_arg_axy_runtime_tail(
            "rt_joy", 2, "rt_gfx_color_cell", 1, 2, "graphics"
        ),
        "store_check_addr": 0x1029,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x102A,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
        ],
    },
    "actc_runtime_input_joystick_result_gfx_third_arg_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "ColorCell(1,2,J)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_gfx_color_cell",
            "rt_gfx_screen_cell",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "b p0u0S0p1p2L0u1r\n",
            "u rt_joy\n",
            "u rt_gfx_color_cell\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
        ],
        "expected_tail": _actc_input_result_third_arg_axy_runtime_tail(
            "rt_joy", 2, "rt_gfx_color_cell", 1, 2, "graphics"
        ),
        "store_check_addr": 0x1029,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x102A,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
        ],
    },
    "actc_runtime_input_sid_mixed_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "BYTE M\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "M=MousePoll(1)\r"
            "SidVol(10)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_mp",
            "rt_ms",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_jp",
            "rt_js",
            "rt_sid_vol",
            "rt_sid_volume_state",
            "rt_sid_mode",
            "rt_sid_freq",
            "rt_gfx_bgcolor",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_mp\n",
            "u rt_sid_vol\n",
            "i 2\n",
            "i 1\n",
            "i 10\n",
            "v j 0\n",
            "v m 0\n",
        ],
        "expected_tail": _actc_input_sid_mixed_runtime_tail(),
        "store_check_addr": 0xD418,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x1030, "value": 0x00},
            {"addr": 0x1032, "value": 0x00},
            {"addr": 0x1138, "value": 0x0A},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
    },
    "actc_runtime_input_sprite_mixed_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE J\r"
            "BYTE M\r"
            "PROC MAIN()\r"
            "J=Joy(2)\r"
            "M=MousePoll(1)\r"
            "SpriteOn(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_mp",
            "rt_ms",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_jp",
            "rt_js",
            "rt_sprite_on",
            "rt_sprite_off",
            "rt_sprite_color",
            "rt_sprite_ptr",
            "rt_gfx_bgcolor",
            "rt_sid_vol",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_mp\n",
            "u rt_sprite_on\n",
            "i 2\n",
            "i 1\n",
            "v j 0\n",
            "v m 0\n",
        ],
        "expected_tail": _actc_input_sprite_mixed_runtime_tail(),
        "store_check_addr": 0xD015,
        "store_check_value": 0x04,
        "store_check_mask": 0x04,
        "extra_store_checks": [
            {"addr": 0x1030, "value": 0x00},
            {"addr": 0x1032, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_SPRITE_ON.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_SPRITE_OFF.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_SID_VOL.OBJ",
        ],
    },
    "actc_runtime_input_math_mixed_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "Joy(2)\r"
            "X=REAL(7)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_i_to_f",
            "rt_print_f",
            "rt_mp",
            "rt_f_abs",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_i_to_f\n",
            "u rt_print_f\n",
            "i 2\n",
            "i 7\n",
        ],
        "expected_tail": _actc_input_math_mixed_runtime_tail(),
        "screen_fragments": ["7"],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_F_ABS.OBJ",
        ],
    },
    "actc_runtime_input_mouse_math_mixed_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "MousePoll(1)\r"
            "X=REAL(7)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mp",
            "rt_ms",
            "rt_i_to_f",
            "rt_print_f",
            "rt_joy",
            "rt_mx",
            "rt_f_abs",
        ],
        "expected_object_fragments": [
            "u rt_mp\n",
            "u rt_i_to_f\n",
            "u rt_print_f\n",
            "i 1\n",
            "i 7\n",
        ],
        "expected_tail": _actc_input_math_mixed_runtime_tail("rt_mp", 1),
        "screen_fragments": ["7"],
        "expected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_PRINT_F.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_F_ABS.OBJ",
        ],
    },
    "actc_runtime_input_joystick_math_store_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE P\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "P=Joy(2)\r"
            "X=REAL(7)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_i_to_f",
            "rt_print_f",
            "rt_mp",
            "rt_ms",
            "rt_f_abs",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_i_to_f\n",
            "u rt_print_f\n",
            "i 2\n",
            "i 7\n",
            "v p 0\n",
            "v x 0 4\n",
        ],
        "expected_tail": _actc_input_stored_math_mixed_runtime_tail("rt_joy", 2),
        "screen_fragments": ["7"],
        "store_check_hi_addr": 0x1038,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_PRINT_F.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MS.OBJ",
            "LIB/RT_F_ABS.OBJ",
        ],
    },
    "actc_runtime_input_mouse_math_store_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE P\r"
            "REAL X\r"
            "PROC MAIN()\r"
            "P=MousePoll(1)\r"
            "X=REAL(7)\r"
            "PrintRE(X)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mp",
            "rt_ms",
            "rt_i_to_f",
            "rt_print_f",
            "rt_joy",
            "rt_mx",
            "rt_f_abs",
        ],
        "expected_object_fragments": [
            "u rt_mp\n",
            "u rt_i_to_f\n",
            "u rt_print_f\n",
            "i 1\n",
            "i 7\n",
            "v p 0\n",
            "v x 0 4\n",
        ],
        "expected_tail": _actc_input_stored_math_mixed_runtime_tail("rt_mp", 1),
        "screen_fragments": ["7"],
        "store_check_addr": 0x1037,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1038,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_I_TO_F.OBJ",
            "LIB/RT_PRINT_F.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_F_ABS.OBJ",
        ],
    },
    "actc_runtime_input1_export_sample_linked": {
        "source": (
            "MODULE main\r"
            "BYTE jstate\r"
            "BYTE seen\r"
            "BYTE mseen\r"
            "BYTE mx\r"
            "BYTE my\r"
            "BYTE mb\r"
            "BYTE jb1\r"
            "BYTE jb2\r"
            "BYTE mb1\r"
            "BYTE mb2\r"
            "BYTE mpresent\r"
            "BYTE jmask\r"
            "BYTE mmask\r"
            "PROC main()\r"
            "jmask=JOY_UP+JOY_BUTTON1+JOY_BUTTON2\r"
            "mmask=MOUSE_BUTTON1+MOUSE_BUTTON2\r"
            "jstate=Joy(2)\r"
            "seen=JoySeen(2)\r"
            "jb1=JoyBtn1(2)\r"
            "jb2=JoyBtn2(2)\r"
            "mseen=MousePoll(1)\r"
            "mpresent=MouseSeen()\r"
            "mx=MouseX()\r"
            "my=MouseY()\r"
            "mb=MouseBtn()\r"
            "mb1=MouseBtn1()\r"
            "mb2=MouseBtn2()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_jp",
            "rt_jb1",
            "rt_jb2",
            "rt_js",
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_mb1",
            "rt_mb2",
            "rt_ms",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "u rt_jp\n",
            "u rt_jb1\n",
            "u rt_jb2\n",
            "u rt_mp\n",
            "u rt_mseen\n",
            "u rt_mx\n",
            "u rt_my\n",
            "u rt_mb\n",
            "u rt_mb1\n",
            "u rt_mb2\n",
            "i 49\n",
            "i 3\n",
            "i 2\n",
            "i 1\n",
            "v jstate 0\n",
            "v seen 0\n",
            "v mseen 0\n",
            "v mpresent 0\n",
            "v mx 0\n",
            "v my 0\n",
            "v mb 0\n",
            "v jb1 0\n",
            "v jb2 0\n",
            "v mb1 0\n",
            "v mb2 0\n",
            "v jmask 0\n",
            "v mmask 0\n",
        ],
        "expected_tail": _actc_input1_export_sample_runtime_tail(),
        "spin_after_marker_for_live": True,
        "store_check_hi_addr": 0x1094,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1096, "value": 0x00},
            {"addr": 0x1098, "value": 0x00},
            {"addr": 0x109A, "value": 0x00},
            {"addr": 0x109C, "value": 0x00},
            {"addr": 0x109E, "value": 0x00},
            {"addr": 0x10A0, "value": 0x00},
            {"addr": 0x10A2, "value": 0x00},
            {"addr": 0x10A4, "value": 0x00},
            {"addr": 0x10A6, "value": 0x00},
            {"addr": 0x10A8, "value": 0x00},
            {"addr": 0x10AA, "value": 0x00},
            {"addr": 0x10AC, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JB1.OBJ",
            "LIB/RT_JB2.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MB1.OBJ",
            "LIB/RT_MB2.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/RT_SID_FREQ.OBJ"],
    },
    "actc_runtime_input1_joy_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE jstate\r"
            "PROC main()\r"
            "jstate=Joy(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_joy",
            "rt_jp",
            "rt_js",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
        ],
        "expected_object_fragments": [
            "u rt_joy\n",
            "i 2\n",
            "v jstate 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_joy", 2),
        "store_check_hi_addr": 0x101D,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JOY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
    },
    "actc_runtime_input1_joy_seen_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE seen\r"
            "PROC main()\r"
            "seen=JoySeen(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_jp",
            "rt_js",
            "rt_joy",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
        ],
        "expected_object_fragments": [
            "u rt_jp\n",
            "i 2\n",
            "v seen 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_jp", 2),
        "store_check_hi_addr": 0x101D,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
    },
    "actc_runtime_input1_joy_button_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE button\r"
            "PROC main()\r"
            "button=JoyBtn1(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_jb1",
            "rt_joy",
            "rt_jb2",
            "rt_jp",
            "rt_js",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_ms",
        ],
        "expected_object_fragments": [
            "u rt_jb1\n",
            "i 2\n",
            "v button 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_jb1", 2),
        "spin_after_marker_for_live": True,
        "store_check_hi_addr": 0x101E,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_JB1.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JB2.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
    },
    "actc_runtime_input1_mouse_poll_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE mseen\r"
            "PROC main()\r"
            "mseen=MousePoll(1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mp",
            "rt_ms",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_mp\n",
            "i 1\n",
            "v mseen 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_mp", 1),
        "store_check_hi_addr": 0x101D,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_input1_mouse_seen_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE present\r"
            "PROC main()\r"
            "present=MouseSeen()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mseen",
            "rt_ms",
            "rt_mp",
            "rt_mx",
            "rt_my",
            "rt_mb",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_mseen\n",
            "v present 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_mseen", None),
        "store_check_hi_addr": 0x101B,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_input1_mouse_x_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE xpos\r"
            "PROC main()\r"
            "xpos=MouseX()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mx",
            "rt_ms",
            "rt_mp",
            "rt_mseen",
            "rt_my",
            "rt_mb",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_mx\n",
            "v xpos 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_mx", None),
        "store_check_hi_addr": 0x101B,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MX.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_input1_mouse_y_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE ypos\r"
            "PROC main()\r"
            "ypos=MouseY()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_my",
            "rt_ms",
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_mb",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_my\n",
            "v ypos 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_my", None),
        "store_check_hi_addr": 0x101B,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MY.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_input1_mouse_button_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE buttons\r"
            "PROC main()\r"
            "buttons=MouseBtn()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mb",
            "rt_ms",
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_mb\n",
            "v buttons 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_mb", None),
        "store_check_hi_addr": 0x101B,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_input1_mouse_button_state_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE button\r"
            "PROC main()\r"
            "button=MouseBtn2()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_mb2",
            "rt_mb",
            "rt_ms",
            "rt_mb1",
            "rt_mp",
            "rt_mseen",
            "rt_mx",
            "rt_my",
            "rt_joy",
            "rt_jp",
            "rt_js",
        ],
        "expected_object_fragments": [
            "u rt_mb2\n",
            "v button 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_mb2", None),
        "spin_after_marker_for_live": True,
        "store_check_hi_addr": 0x101C,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_MB2.OBJ",
            "LIB/RT_MB.OBJ",
            "LIB/RT_MS.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_MB1.OBJ",
            "LIB/RT_MP.OBJ",
            "LIB/RT_MX.OBJ",
            "LIB/RT_MY.OBJ",
            "LIB/RT_MSEEN.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_JS.OBJ",
        ],
    },
    "actc_runtime_dbf1_export_sample_linked": {
        "source": (
            "MODULE main\r"
            "CARD filename\r"
            "BYTE handle\r"
            "BYTE fields\r"
            "BYTE fieldlen\r"
            "BYTE moved\r"
            "BYTE deleted\r"
            "BYTE headerlen\r"
            "BYTE recordlen\r"
            "BYTE total\r"
            "BYTE recno\r"
            "PROC main()\r"
            "filename=12288\r"
            "handle=DbfOpen(filename)\r"
            "fields=DbfFieldCount(handle)\r"
            "fieldlen=DbfFieldLen(handle,1)\r"
            "moved=DbfGo(handle,2)\r"
            "deleted=DbfDeleted(handle)\r"
            "headerlen=DbfHeaderLen(handle)\r"
            "recordlen=DbfRecordLen(handle)\r"
            "total=DbfTotalRecs(handle)\r"
            "recno=DbfCurrRecNo(handle)\r"
            "DbfClose(handle)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_close",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_deleted",
            "rt_dbf_readbyte",
            "rt_dbf_headerlen",
            "rt_dbf_recordlen",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_close\n",
            "u rt_dbf_go\n",
            "u rt_dbf_fieldcount\n",
            "u rt_dbf_fieldlen\n",
            "u rt_dbf_deleted\n",
            "u rt_dbf_headerlen\n",
            "u rt_dbf_recordlen\n",
            "u rt_dbf_totalrecs\n",
            "u rt_dbf_currrecno\n",
            "i 12288\n",
            "i 1\n",
            "i 2\n",
            "v filename 0\n",
            "v handle 0\n",
            "v fields 0\n",
            "v fieldlen 0\n",
            "v moved 0\n",
            "v deleted 0\n",
            "v headerlen 0\n",
            "v recordlen 0\n",
            "v total 0\n",
            "v recno 0\n",
        ],
        "expected_tail": _actc_dbf1_export_sample_runtime_tail(),
        "store_check_addr": 0x109B,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x109C,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1099, "value": 0x00},
            {"addr": 0x109A, "value": 0x00},
            {"addr": 0x109D, "value": 0x01},
            {"addr": 0x109E, "value": 0x00},
            {"addr": 0x109F, "value": 0x01},
            {"addr": 0x10A0, "value": 0x00},
            {"addr": 0x10A1, "value": 0x01},
            {"addr": 0x10A2, "value": 0x00},
            {"addr": 0x10A3, "value": 0x00},
            {"addr": 0x10A4, "value": 0x00},
            {"addr": 0x10A5, "value": 0x41},
            {"addr": 0x10A6, "value": 0x00},
            {"addr": 0x10A7, "value": 0x02},
            {"addr": 0x10A8, "value": 0x00},
            {"addr": 0x10A9, "value": 0x03},
            {"addr": 0x10AA, "value": 0x00},
            {"addr": 0x10AB, "value": 0x02},
            {"addr": 0x10AC, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_DELETED.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_HEADERLEN.OBJ",
            "LIB/RT_DBF_RECORDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_create_split_linked": {
        "source": (
            'MODULE main\r'
            'BYTE handle\r'
            'BYTE appended\r'
            'BYTE saved\r'
            'BYTE reopened\r'
            'BYTE total\r'
            'BYTE value\r'
            'PROC main()\r'
            'handle=DbfCreate(12288)\r'
            'appended=DbfAppend(handle)\r'
            'saved=DbfSave(handle)\r'
            'DbfClose(handle)\r'
            'reopened=DbfOpen(12288)\r'
            'total=DbfTotalRecs(reopened)\r'
            'value=DbfReadByte(reopened,0)\r'
            'RETURN\r'
        ),
        "has_stub": False,
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_CREATE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            'rt_dbf_create',
            'rt_dbf_append',
            'rt_dbf_save',
            'rt_dbf_close',
            'rt_dbf_open',
            'rt_dbf_totalrecs',
            'rt_dbf_readbyte',
            'rt_dbf_state',
            'rt_dbf_go',
            'rt_dbf_fieldcount',
            'rt_dbf_fieldlen',
            'rt_dbf_writebyte',
            'rt_dbf_delete',
            'rt_dbf_undelete',
            'rt_dbf_deleted',
            'rt_joy',
        ],
        "expected_object_fragments": [
            'u rt_dbf_create\n',
            'u rt_dbf_append\n',
            'u rt_dbf_save\n',
            'u rt_dbf_close\n',
            'u rt_dbf_open\n',
            'u rt_dbf_totalrecs\n',
            'u rt_dbf_readbyte\n',
            'i 12288\n',
            'i 0\n',
            'v handle 0\n',
            'v appended 0\n',
            'v saved 0\n',
            'v reopened 0\n',
            'v total 0\n',
            'v value 0\n',
        ],
        "expected_tail": _actc_dbf1_create_runtime_tail(),
        "store_check_addr": 0x1078,
        "store_check_value": 0x20,
        "store_check_hi_addr": 0x1079,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x106E, "value": 0x01},
            {"addr": 0x106F, "value": 0x00},
            {"addr": 0x1070, "value": 0x01},
            {"addr": 0x1071, "value": 0x00},
            {"addr": 0x1072, "value": 0x01},
            {"addr": 0x1073, "value": 0x00},
            {"addr": 0x1074, "value": 0x01},
            {"addr": 0x1075, "value": 0x00},
            {"addr": 0x1076, "value": 0x01},
            {"addr": 0x1077, "value": 0x00},
        ],
        "expected_alink_loads": [
            'LIB/RT_DBF_CREATE.OBJ',
            'LIB/RT_DBF_APPEND.OBJ',
            'LIB/RT_DBF_SAVE.OBJ',
            'LIB/RT_DBF_CLOSE.OBJ',
            'LIB/RT_DBF_OPEN.OBJ',
            'LIB/RT_DBF_TOTALRECS.OBJ',
            'LIB/RT_DBF_READBYTE.OBJ',
            'LIB/RT_DBF_STATE.OBJ',
        ],
        "unexpected_alink_loads": [
            'LIB/RT_DBF_GO.OBJ',
            'LIB/RT_DBF_FIELDCOUNT.OBJ',
            'LIB/RT_DBF_FIELDLEN.OBJ',
            'LIB/RT_DBF_WRITEBYTE.OBJ',
            'LIB/RT_DBF_DELETE.OBJ',
            'LIB/RT_DBF_UNDELETE.OBJ',
            'LIB/RT_DBF_DELETED.OBJ',
            'LIB/RT_JOY.OBJ',
        ],
    },
    "actc_runtime_dbf1_open_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_close",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "i 12288\n",
            "v handle 0\n",
        ],
        "expected_tail": _actc_xy_word_readback_store_runtime_tail(
            "rt_dbf_open", DBF_FIXTURE_NAME_ADDR
        ),
        "store_check_addr": 0x101F,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x1020,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_open_missing_file_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_MISSING_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_close",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "i 12288\n",
            "v handle 0\n",
        ],
        "expected_tail": _actc_xy_word_readback_store_runtime_tail(
            "rt_dbf_open", DBF_FIXTURE_NAME_ADDR
        ),
        "store_check_addr": 0x101F,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1020,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_close_split_linked": {
        "source": "MODULE main\rPROC main()\rDbfClose(1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_close",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_close\n",
            "i 1\n",
        ],
        "expected_tail": _actc_a_byte_side_effect_runtime_tail("rt_dbf_close", 1),
        "expected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_close_state_reset_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE total\r"
            "BYTE recno\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "DbfClose(handle)\r"
            "total=DbfTotalRecs(handle)\r"
            "recno=DbfCurrRecNo(handle)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_state",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_deleted",
            "rt_dbf_headerlen",
            "rt_dbf_recordlen",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_close\n",
            "u rt_dbf_totalrecs\n",
            "u rt_dbf_currrecno\n",
            "i 12288\n",
            "v handle 0\n",
            "v total 0\n",
            "v recno 0\n",
        ],
        "expected_tail": _actc_dbf1_close_state_reset_runtime_tail(),
        "store_check_addr": 0x1043,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1044,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1041, "value": 0x01},
            {"addr": 0x1042, "value": 0x00},
            {"addr": 0x1045, "value": 0x00},
            {"addr": 0x1046, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_DELETED.OBJ",
            "LIB/RT_DBF_HEADERLEN.OBJ",
            "LIB/RT_DBF_RECORDLEN.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_go_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE recno\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "recno=DbfCurrRecNo(handle)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_currrecno\n",
            "i 12288\n",
            "i 2\n",
            "v handle 0\n",
            "v moved 0\n",
            "v recno 0\n",
        ],
        "expected_tail": _actc_dbf1_go_runtime_tail(),
        "store_check_addr": 0x103F,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x1040,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103D, "value": 0x01},
            {"addr": 0x103E, "value": 0x00},
            {"addr": 0x1041, "value": 0x02},
            {"addr": 0x1042, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_invalid_record_field_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE recno\r"
            "BYTE fieldlen\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,4)\r"
            "recno=DbfCurrRecNo(handle)\r"
            "fieldlen=DbfFieldLen(handle,2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_currrecno",
            "rt_dbf_fieldlen",
            "rt_dbf_state",
            "rt_dbf_close",
            "rt_dbf_fieldcount",
            "rt_dbf_readbyte",
            "rt_dbf_deleted",
            "rt_dbf_headerlen",
            "rt_dbf_recordlen",
            "rt_dbf_totalrecs",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_currrecno\n",
            "u rt_dbf_fieldlen\n",
            "i 12288\n",
            "i 4\n",
            "i 2\n",
            "v handle 0\n",
            "v moved 0\n",
            "v recno 0\n",
            "v fieldlen 0\n",
        ],
        "expected_tail": _actc_dbf1_invalid_record_field_runtime_tail(),
        "store_check_addr": 0x104F,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1050,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x104D, "value": 0x01},
            {"addr": 0x104E, "value": 0x00},
            {"addr": 0x1051, "value": 0x01},
            {"addr": 0x1052, "value": 0x00},
            {"addr": 0x1053, "value": 0x00},
            {"addr": 0x1054, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_DELETED.OBJ",
            "LIB/RT_DBF_HEADERLEN.OBJ",
            "LIB/RT_DBF_RECORDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_field_count_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE fields\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "fields=DbfFieldCount(handle)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_go",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_fieldcount\n",
            "i 12288\n",
            "v handle 0\n",
            "v fields 0\n",
        ],
        "expected_tail": _actc_dbf1_field_count_runtime_tail(),
        "store_check_addr": 0x102F,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x1030,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x102D, "value": 0x01},
            {"addr": 0x102E, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_field_len_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE fieldlen\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "fieldlen=DbfFieldLen(handle,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_fieldlen",
            "rt_dbf_fieldcount",
            "rt_dbf_go",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_fieldlen\n",
            "i 12288\n",
            "i 1\n",
            "v handle 0\n",
            "v fieldlen 0\n",
        ],
        "expected_tail": _actc_dbf1_field_len_runtime_tail(),
        "store_check_addr": 0x1031,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x1032,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x102F, "value": 0x01},
            {"addr": 0x1030, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_read_byte_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "value=DbfReadByte(handle,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 2\n",
            "i 1\n",
            "v handle 0\n",
            "v moved 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_read_byte_runtime_tail(),
        "store_check_addr": 0x1043,
        "store_check_value": 0x42,
        "store_check_hi_addr": 0x1044,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103F, "value": 0x01},
            {"addr": 0x1040, "value": 0x00},
            {"addr": 0x1041, "value": 0x01},
            {"addr": 0x1042, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_large_file_read_byte_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,130)\r"
            "value=DbfReadByte(handle,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(record_count=130),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 130\n",
            "i 1\n",
            "v handle 0\n",
            "v moved 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_read_byte_runtime_tail(go_record=130),
        "store_check_addr": 0x1043,
        "store_check_value": 0xC2,
        "store_check_hi_addr": 0x1044,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103F, "value": 0x01},
            {"addr": 0x1040, "value": 0x00},
            {"addr": 0x1041, "value": 0x01},
            {"addr": 0x1042, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_read_field_byte_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "value=DbfReadFieldByte(handle,1,0)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_readfieldbyte",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_fieldcount",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_dbf_writebyte",
            "rt_joy",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_readfieldbyte\n",
            "i 12288\n",
            "i 2\n",
            "i 1\n",
            "i 0\n",
            "v handle 0\n",
            "v moved 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_read_field_byte_runtime_tail(),
        "store_check_addr": 0x1046,
        "store_check_value": 0x42,
        "store_check_hi_addr": 0x1047,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1042, "value": 0x01},
            {"addr": 0x1043, "value": 0x00},
            {"addr": 0x1044, "value": 0x01},
            {"addr": 0x1045, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_READFIELDBYTE.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_dbf1_write_field_byte_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE wrote\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "wrote=DbfWriteFieldByte(handle,1,0,90)\r"
            "value=DbfReadFieldByte(handle,1,0)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_writefieldbyte",
            "rt_dbf_readfieldbyte",
            "rt_dbf_fieldlen",
            "rt_dbf_writebyte",
            "rt_dbf_readbyte",
            "rt_dbf_fieldcount",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_writefieldbyte\n",
            "u rt_dbf_readfieldbyte\n",
            "i 12288\n",
            "i 2\n",
            "i 1\n",
            "i 0\n",
            "i 90\n",
            "v handle 0\n",
            "v moved 0\n",
            "v wrote 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_write_field_byte_runtime_tail(),
        "store_check_addr": 0x105F,
        "store_check_value": 0x5A,
        "store_check_hi_addr": 0x1060,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1059, "value": 0x01},
            {"addr": 0x105A, "value": 0x00},
            {"addr": 0x105B, "value": 0x01},
            {"addr": 0x105C, "value": 0x00},
            {"addr": 0x105D, "value": 0x01},
            {"addr": 0x105E, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_WRITEFIELDBYTE.OBJ",
            "LIB/RT_DBF_READFIELDBYTE.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_dbf1_write_byte_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE wrote\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "wrote=DbfWriteByte(handle,1,90)\r"
            "value=DbfReadByte(handle,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_writebyte",
            "rt_dbf_readbyte",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_writebyte\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 2\n",
            "i 1\n",
            "i 90\n",
            "v handle 0\n",
            "v moved 0\n",
            "v wrote 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_write_byte_runtime_tail(),
        "store_check_addr": 0x1058,
        "store_check_value": 0x5A,
        "store_check_hi_addr": 0x1059,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1052, "value": 0x01},
            {"addr": 0x1053, "value": 0x00},
            {"addr": 0x1054, "value": 0x01},
            {"addr": 0x1055, "value": 0x00},
            {"addr": 0x1056, "value": 0x01},
            {"addr": 0x1057, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_dbf1_save_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE wrote\r"
            "BYTE saved\r"
            "BYTE handle2\r"
            "BYTE moved2\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "wrote=DbfWriteByte(handle,1,90)\r"
            "saved=DbfSave(handle)\r"
            "DbfClose(handle)\r"
            "handle2=DbfOpen(12288)\r"
            "moved2=DbfGo(handle2,2)\r"
            "value=DbfReadByte(handle2,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_writebyte",
            "rt_dbf_save",
            "rt_dbf_close",
            "rt_dbf_readbyte",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_currrecno",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_writebyte\n",
            "u rt_dbf_save\n",
            "u rt_dbf_close\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 2\n",
            "i 1\n",
            "i 90\n",
            "v handle 0\n",
            "v moved 0\n",
            "v wrote 0\n",
            "v saved 0\n",
            "v handle2 0\n",
            "v moved2 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_save_runtime_tail(),
        "store_check_addr": 0x1091,
        "store_check_value": 0x5A,
        "store_check_hi_addr": 0x1092,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1085, "value": 0x01},
            {"addr": 0x1086, "value": 0x00},
            {"addr": 0x1087, "value": 0x01},
            {"addr": 0x1088, "value": 0x00},
            {"addr": 0x1089, "value": 0x01},
            {"addr": 0x108A, "value": 0x00},
            {"addr": 0x108B, "value": 0x01},
            {"addr": 0x108C, "value": 0x00},
            {"addr": 0x108D, "value": 0x01},
            {"addr": 0x108E, "value": 0x00},
            {"addr": 0x108F, "value": 0x01},
            {"addr": 0x1090, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_DBF_SAVE.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_dbf1_large_file_save_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE wrote\r"
            "BYTE saved\r"
            "BYTE handle2\r"
            "BYTE moved2\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,130)\r"
            "wrote=DbfWriteByte(handle,1,90)\r"
            "saved=DbfSave(handle)\r"
            "DbfClose(handle)\r"
            "handle2=DbfOpen(12288)\r"
            "moved2=DbfGo(handle2,130)\r"
            "value=DbfReadByte(handle2,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(record_count=130),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_writebyte",
            "rt_dbf_save",
            "rt_dbf_close",
            "rt_dbf_readbyte",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_currrecno",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_writebyte\n",
            "u rt_dbf_save\n",
            "u rt_dbf_close\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 130\n",
            "i 1\n",
            "i 90\n",
            "v handle 0\n",
            "v moved 0\n",
            "v wrote 0\n",
            "v saved 0\n",
            "v handle2 0\n",
            "v moved2 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_save_runtime_tail(go_record=130),
        "store_check_addr": 0x1091,
        "store_check_value": 0x5A,
        "store_check_hi_addr": 0x1092,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1085, "value": 0x01},
            {"addr": 0x1086, "value": 0x00},
            {"addr": 0x1087, "value": 0x01},
            {"addr": 0x1088, "value": 0x00},
            {"addr": 0x1089, "value": 0x01},
            {"addr": 0x108A, "value": 0x00},
            {"addr": 0x108B, "value": 0x01},
            {"addr": 0x108C, "value": 0x00},
            {"addr": 0x108D, "value": 0x01},
            {"addr": 0x108E, "value": 0x00},
            {"addr": 0x108F, "value": 0x01},
            {"addr": 0x1090, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_DBF_SAVE.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_dbf1_save_invalid_handle_linked": {
        "source": (
            "MODULE main\r"
            "BYTE saved\r"
            "PROC main()\r"
            "saved=DbfSave(2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_dbf_save",
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_writebyte",
            "rt_dbf_readbyte",
            "rt_dbf_close",
            "rt_dbf_state",
            "rt_joy",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "u rt_dbf_save\n",
            "i 2\n",
            "v saved 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_dbf_save", 2),
        "store_check_addr": 0x101D,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x101E,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_DBF_SAVE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_dbf1_read_byte_invalid_offset_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,1)\r"
            "value=DbfReadByte(handle,2)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 1\n",
            "i 2\n",
            "v handle 0\n",
            "v moved 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_read_byte_runtime_tail(go_record=1, read_offset=2),
        "store_check_addr": 0x1043,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1044,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103F, "value": 0x01},
            {"addr": 0x1040, "value": 0x00},
            {"addr": 0x1041, "value": 0x01},
            {"addr": 0x1042, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_read_byte_invalid_handle_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "value=DbfReadByte(2,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 2\n",
            "i 1\n",
            "v handle 0\n",
            "v moved 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_read_byte_runtime_tail(read_handle=2),
        "store_check_addr": 0x1042,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1043,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103E, "value": 0x01},
            {"addr": 0x103F, "value": 0x00},
            {"addr": 0x1040, "value": 0x01},
            {"addr": 0x1041, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_delete_undelete_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE delok\r"
            "BYTE deleted\r"
            "BYTE undelok\r"
            "BYTE deleted2\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "delok=DbfDelete(handle)\r"
            "deleted=DbfDeleted(handle)\r"
            "undelok=DbfUndelete(handle)\r"
            "deleted2=DbfDeleted(handle)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_delete",
            "rt_dbf_deleted",
            "rt_dbf_undelete",
            "rt_dbf_writebyte",
            "rt_dbf_readbyte",
            "rt_dbf_state",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_save",
            "rt_joy",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_delete\n",
            "u rt_dbf_deleted\n",
            "u rt_dbf_undelete\n",
            "i 12288\n",
            "i 2\n",
            "v handle 0\n",
            "v moved 0\n",
            "v delok 0\n",
            "v deleted 0\n",
            "v undelok 0\n",
            "v deleted2 0\n",
        ],
        "expected_tail": _actc_dbf1_delete_undelete_runtime_tail(),
        "store_check_addr": 0x1071,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x1072,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1067, "value": 0x01},
            {"addr": 0x1068, "value": 0x00},
            {"addr": 0x1069, "value": 0x01},
            {"addr": 0x106A, "value": 0x00},
            {"addr": 0x106B, "value": 0x01},
            {"addr": 0x106C, "value": 0x00},
            {"addr": 0x106D, "value": 0x01},
            {"addr": 0x106E, "value": 0x00},
            {"addr": 0x106F, "value": 0x01},
            {"addr": 0x1070, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_DELETE.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_DBF_DELETED.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_UNDELETE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_SAVE.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "actc_runtime_dbf1_append_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE appended\r"
            "BYTE total\r"
            "BYTE recno\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "appended=DbfAppend(handle)\r"
            "total=DbfTotalRecs(handle)\r"
            "recno=DbfCurrRecNo(handle)\r"
            "value=DbfReadByte(handle,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_append",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_readbyte",
            "rt_dbf_state",
            "rt_dbf_go",
            "rt_dbf_writebyte",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_close",
            "rt_dbf_save",
            "rt_dbf_delete",
            "rt_dbf_undelete",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_append\n",
            "u rt_dbf_totalrecs\n",
            "u rt_dbf_currrecno\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 1\n",
            "v handle 0\n",
            "v appended 0\n",
            "v total 0\n",
            "v recno 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_append_runtime_tail(),
        "store_check_addr": 0x1061,
        "store_check_value": 0x20,
        "store_check_hi_addr": 0x1062,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1059, "value": 0x01},
            {"addr": 0x105A, "value": 0x00},
            {"addr": 0x105B, "value": 0x01},
            {"addr": 0x105C, "value": 0x00},
            {"addr": 0x105D, "value": 0x04},
            {"addr": 0x105E, "value": 0x00},
            {"addr": 0x105F, "value": 0x04},
            {"addr": 0x1060, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_APPEND.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_DBF_SAVE.OBJ",
            "LIB/RT_DBF_DELETE.OBJ",
            "LIB/RT_DBF_UNDELETE.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_pack_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE delok\r"
            "BYTE packed\r"
            "BYTE total\r"
            "BYTE recno\r"
            "BYTE moved2\r"
            "BYTE value\r"
            "BYTE moved3\r"
            "BYTE recno2\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "delok=DbfDelete(handle)\r"
            "packed=DbfPack(handle)\r"
            "total=DbfTotalRecs(handle)\r"
            "recno=DbfCurrRecNo(handle)\r"
            "moved2=DbfGo(handle,2)\r"
            "value=DbfReadByte(handle,1)\r"
            "moved3=DbfGo(handle,3)\r"
            "recno2=DbfCurrRecNo(handle)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_delete",
            "rt_dbf_pack",
            "rt_dbf_pack_step",
            "rt_dbf_pack_read",
            "rt_dbf_pack_write",
            "rt_dbf_pack_copy",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_dbf_readbyte",
            "rt_dbf_writebyte",
            "rt_dbf_state",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_close",
            "rt_dbf_save",
            "rt_dbf_append",
            "rt_dbf_undelete",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_delete\n",
            "u rt_dbf_pack\n",
            "u rt_dbf_totalrecs\n",
            "u rt_dbf_currrecno\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 1\n",
            "i 2\n",
            "i 3\n",
            "v handle 0\n",
            "v moved 0\n",
            "v delok 0\n",
            "v packed 0\n",
            "v total 0\n",
            "v recno 0\n",
            "v moved2 0\n",
            "v value 0\n",
            "v moved3 0\n",
            "v recno2 0\n",
        ],
        "expected_tail": _actc_dbf1_pack_runtime_tail(),
        "store_check_addr": 0x10B3,
        "store_check_value": 0x43,
        "store_check_hi_addr": 0x10B4,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x10A5, "value": 0x01},
            {"addr": 0x10A6, "value": 0x00},
            {"addr": 0x10A7, "value": 0x01},
            {"addr": 0x10A8, "value": 0x00},
            {"addr": 0x10A9, "value": 0x01},
            {"addr": 0x10AA, "value": 0x00},
            {"addr": 0x10AB, "value": 0x01},
            {"addr": 0x10AC, "value": 0x00},
            {"addr": 0x10AD, "value": 0x02},
            {"addr": 0x10AE, "value": 0x00},
            {"addr": 0x10AF, "value": 0x01},
            {"addr": 0x10B0, "value": 0x00},
            {"addr": 0x10B1, "value": 0x01},
            {"addr": 0x10B2, "value": 0x00},
            {"addr": 0x10B5, "value": 0x00},
            {"addr": 0x10B6, "value": 0x00},
            {"addr": 0x10B7, "value": 0x02},
            {"addr": 0x10B8, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_DELETE.OBJ",
            "LIB/RT_DBF_WRITEBYTE.OBJ",
            "LIB/RT_DBF_PACK.OBJ",
            "LIB/RT_DBF_PACK_STEP.OBJ",
            "LIB/RT_DBF_PACK_READ.OBJ",
            "LIB/RT_DBF_PACK_WRITE.OBJ",
            "LIB/RT_DBF_PACK_COPY.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_SAVE.OBJ",
            "LIB/RT_DBF_APPEND.OBJ",
            "LIB/RT_DBF_UNDELETE.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_deleted_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE deleted\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "deleted=DbfDeleted(handle)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(deleted_records={2}),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_deleted",
            "rt_dbf_readbyte",
            "rt_dbf_state",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_deleted\n",
            "i 12288\n",
            "i 2\n",
            "v handle 0\n",
            "v moved 0\n",
            "v deleted 0\n",
        ],
        "expected_tail": _actc_dbf1_deleted_runtime_tail(),
        "store_check_addr": 0x1041,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x1042,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103D, "value": 0x01},
            {"addr": 0x103E, "value": 0x00},
            {"addr": 0x103F, "value": 0x01},
            {"addr": 0x1040, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_DELETED.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_header_record_len_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE headerlen\r"
            "BYTE recordlen\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "headerlen=DbfHeaderLen(handle)\r"
            "recordlen=DbfRecordLen(handle)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_headerlen",
            "rt_dbf_recordlen",
            "rt_dbf_state",
            "rt_dbf_go",
            "rt_dbf_readbyte",
            "rt_dbf_deleted",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_dbf_headerlen\n",
            "u rt_dbf_recordlen\n",
            "i 12288\n",
            "v handle 0\n",
            "v headerlen 0\n",
            "v recordlen 0\n",
        ],
        "expected_tail": _actc_dbf1_header_record_len_runtime_tail(),
        "store_check_addr": 0x103D,
        "store_check_value": 0x41,
        "store_check_hi_addr": 0x103E,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103B, "value": 0x01},
            {"addr": 0x103C, "value": 0x00},
            {"addr": 0x103F, "value": 0x02},
            {"addr": 0x1040, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_HEADERLEN.OBJ",
            "LIB/RT_DBF_RECORDLEN.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_DELETED.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_read_byte_result_sprite_arg_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE moved\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "moved=DbfGo(handle,2)\r"
            "value=DbfReadByte(handle,1)\r"
            "SpriteColor(2,value)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_go",
            "rt_dbf_readbyte",
            "rt_dbf_state",
            "rt_sprite_color",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_close",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_joy",
            "rt_sprite_on",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0p1u1S1L0p2u2S2p3L2u3r\n",
            "u rt_dbf_open\n",
            "u rt_dbf_go\n",
            "u rt_dbf_readbyte\n",
            "u rt_sprite_color\n",
            "i 12288\n",
            "i 2\n",
            "i 1\n",
            "v handle 0\n",
            "v moved 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_read_byte_sprite_color_runtime_tail(),
        "store_check_addr": 0xD029,
        "store_check_value": 0x02,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x1047, "value": 0x01},
            {"addr": 0x1048, "value": 0x00},
            {"addr": 0x1049, "value": 0x01},
            {"addr": 0x104A, "value": 0x00},
            {"addr": 0x104B, "value": 0x42},
            {"addr": 0x104C, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SPRITE_ON.OBJ",
        ],
    },
    "actc_runtime_dbf1_read_byte_joystick_offset_linked": {
        "source": (
            "MODULE main\r"
            "BYTE handle\r"
            "BYTE offset\r"
            "BYTE value\r"
            "PROC main()\r"
            "handle=DbfOpen(12288)\r"
            "offset=Joy(2)\r"
            "value=DbfReadByte(handle,offset)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "extra_files": {
            DBF_FIXTURE_STAGE_PATH: _dbf_fixture_bytes(),
        },
        "pre_run_memory": _pre_run_memory_bytes(
            DBF_FIXTURE_NAME_ADDR,
            DBF_FIXTURE_NAME.encode("ascii") + b"\x00",
        ),
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_readbyte",
            "rt_dbf_state",
            "rt_joy",
            "rt_dbf_go",
            "rt_dbf_close",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_totalrecs",
            "rt_dbf_currrecno",
            "rt_jp",
            "rt_mp",
        ],
        "expected_object_fragments": [
            "u rt_dbf_open\n",
            "u rt_joy\n",
            "u rt_dbf_readbyte\n",
            "i 12288\n",
            "i 2\n",
            "v handle 0\n",
            "v offset 0\n",
            "v value 0\n",
        ],
        "expected_tail": _actc_dbf1_read_byte_joystick_offset_runtime_tail(),
        "store_check_addr": 0x1041,
        "store_check_value": 0x20,
        "store_check_hi_addr": 0x1042,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103D, "value": 0x01},
            {"addr": 0x103E, "value": 0x00},
            {"addr": 0x103F, "value": 0x00},
            {"addr": 0x1040, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JP.OBJ",
            "LIB/RT_MP.OBJ",
        ],
    },
    "actc_runtime_dbf1_total_recs_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE total\r"
            "PROC main()\r"
            "total=DbfTotalRecs(1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_totalrecs",
            "rt_dbf_close",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_totalrecs\n",
            "i 1\n",
            "v total 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_dbf_totalrecs", 1),
        "store_check_addr": 0x101D,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x101E,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_curr_rec_no_split_linked": {
        "source": (
            "MODULE main\r"
            "BYTE recno\r"
            "PROC main()\r"
            "recno=DbfCurrRecNo(1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_dbf_open",
            "rt_dbf_currrecno",
            "rt_dbf_close",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_joy",
        ],
        "expected_object_fragments": [
            "u rt_dbf_currrecno\n",
            "i 1\n",
            "v recno 0\n",
        ],
        "expected_tail": _actc_input_single_store_runtime_tail("rt_dbf_currrecno", 1),
        "store_check_addr": 0x101D,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0x101E,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": [
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_JOY.OBJ",
        ],
    },
    "actc_runtime_dbf1_total_recs_result_sid_arg_linked": {
        "source": (
            "MODULE main\r"
            "BYTE total\r"
            "PROC main()\r"
            "total=DbfTotalRecs(1)\r"
            "SidVol(total)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_dbf_totalrecs",
            "rt_dbf_state",
            "rt_sid_vol",
            "rt_sid_volume_state",
            "rt_dbf_open",
            "rt_dbf_close",
            "rt_dbf_go",
            "rt_dbf_fieldcount",
            "rt_dbf_fieldlen",
            "rt_dbf_readbyte",
            "rt_dbf_currrecno",
            "rt_joy",
            "rt_sid_mode",
        ],
        "expected_object_fragments": [
            "b p0u0S0L0u1r\n",
            "u rt_dbf_totalrecs\n",
            "u rt_sid_vol\n",
            "i 1\n",
            "v total 0\n",
        ],
        "expected_tail": _actc_input_result_arg_mixed_runtime_tail(
            "rt_dbf_totalrecs", 1, "rt_sid_vol", "DBF/SID"
        ),
        "store_check_addr": 0xD418,
        "store_check_value": 0x00,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x1023, "value": 0x00},
            {"addr": 0x1024, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_DBF_TOTALRECS.OBJ",
            "LIB/RT_DBF_STATE.OBJ",
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_DBF_OPEN.OBJ",
            "LIB/RT_DBF_CLOSE.OBJ",
            "LIB/RT_DBF_GO.OBJ",
            "LIB/RT_DBF_FIELDCOUNT.OBJ",
            "LIB/RT_DBF_FIELDLEN.OBJ",
            "LIB/RT_DBF_READBYTE.OBJ",
            "LIB/RT_DBF_CURRRECNO.OBJ",
            "LIB/RT_JOY.OBJ",
            "LIB/RT_SID_MODE.OBJ",
        ],
    },
    "actc_runtime_sidspr1_export_sample_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidWave(1,SID_TRI+SID_SAW+SID_PULSE+SID_NOISE)\r"
            "SidMode(SID_LOW+SID_BAND+SID_HIGH)\r"
            "SpritePrio(2,SPR_BACK)\r"
            "SpritePrio(3,SPR_FRONT)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": _runtime_module_closure(
            ["rt_sid_wave", "rt_sid_mode", "rt_sprite_prio"]
        )
        + [
            "rt_sid_freq",
            "rt_gfx_bgcolor",
        ],
        "expected_object_fragments": [
            "u rt_sid_wave\n",
            "u rt_sid_mode\n",
            "u rt_sprite_prio\n",
            "i 240\n",
            "i 112\n",
            "i 1\n",
            "i 0\n",
        ],
        "expected_tail": _actc_named_hardware_constants_runtime_tail(),
        "store_check_addr": 0xD418,
        "store_check_value": 0x70,
        "store_check_mask": 0x70,
        "extra_store_checks": [
            {"addr": 0xD01B, "value": 0x04, "mask": 0x0C},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_FREQ.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
    },
    "actc_runtime_sidspr1_sid_wave_mask_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidWave(1,SID_TRI+SID_SAW+SID_PULSE+SID_NOISE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_wave",
            "rt_sid_state",
            "rt_sid_mode",
            "rt_sprite_prio",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_sid_wave\n",
            "i 1\n",
            "i 240\n",
        ],
        "expected_tail": _actc_sidspr1_sid_wave_mask_runtime_tail(),
        "store_check_addr": 0xD40B,
        "store_check_value": 0xF0,
        "extra_store_checks": [
            {"addr": 0x1034, "value": 0xF0},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_sidspr1_sid_mode_mask_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidMode(SID_LOW+SID_BAND+SID_HIGH)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_mode",
            "rt_sid_volume_state",
            "rt_sid_wave",
            "rt_sid_state",
            "rt_sprite_prio",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_sid_mode\n",
            "i 112\n",
        ],
        "expected_tail": _actc_sidspr1_sid_mode_mask_runtime_tail(),
        "store_check_addr": 0xD418,
        "store_check_value": 0x70,
        "store_check_mask": 0x70,
        "extra_store_checks": [
            {"addr": 0x102B, "value": 0x70},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_sidspr1_sprite_prio_back_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SpritePrio(2,SPR_BACK)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_prio",
            "rt_sid_wave",
            "rt_sid_state",
            "rt_sid_mode",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_sprite_prio\n",
            "i 2\n",
            "i 1\n",
        ],
        "expected_tail": _actc_sidspr1_sprite_prio_back_runtime_tail(),
        "store_check_addr": 0xD01B,
        "store_check_value": 0x04,
        "expected_alink_loads": [
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_named_hardware_constants_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidWave(1,SID_TRI+SID_SAW+SID_PULSE+SID_NOISE)\r"
            "SidMode(SID_LOW+SID_BAND+SID_HIGH)\r"
            "SpritePrio(2,SPR_BACK)\r"
            "SpritePrio(3,SPR_FRONT)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": _runtime_module_closure(
            ["rt_sid_wave", "rt_sid_mode", "rt_sprite_prio"]
        )
        + [
            "rt_sid_freq",
            "rt_gfx_bgcolor",
        ],
        "expected_object_fragments": [
            "u rt_sid_wave\n",
            "u rt_sid_mode\n",
            "u rt_sprite_prio\n",
            "i 240\n",
            "i 112\n",
            "i 1\n",
            "i 0\n",
        ],
        "expected_tail": _actc_named_hardware_constants_runtime_tail(),
        "store_check_addr": 0xD418,
        "store_check_value": 0x70,
        "store_check_mask": 0x70,
        "extra_store_checks": [
            {"addr": 0xD01B, "value": 0x04, "mask": 0x0C},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_FREQ.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
    },
    "actc_runtime_named_constant_mixed_runtime_expr_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD MASK\r"
            "PROC MAIN()\r"
            "MASK=SID_BAND+SID_HIGH\r"
            "SidMode(SID_LOW+MASK)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": _runtime_module_closure(["rt_sid_mode"])
        + [
            "rt_sid_wave",
            "rt_sprite_prio",
        ],
        "expected_object_fragments": [
            "b p0S0p1L0au0r\n",
            "u rt_sid_mode\n",
            "i 96\n",
            "i 16\n",
            "v mask 0\n",
        ],
        "expected_tail": _actc_named_constant_mixed_runtime_expr_tail(),
        "store_check_addr": 0xD418,
        "store_check_value": 0x70,
        "store_check_mask": 0x70,
        "expected_alink_loads": [
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "runtime_gfx_vic_bank_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 21\n"
            "b u0M\n"
            "u rt_gfx_vic_bank\n"
            "m A9 01 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 3 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_vic_bank"],
        "expected_tail": bytes.fromhex(
            "A901201510A9A58DD003A90085028503A2024C0FCF"
            "290349038502AD02DD09038D02DDAD00DD29FC05028D00DD60"
        ),
        "store_check_addr": 0xDD00,
        "store_check_value": 0x02,
        "store_check_mask": 0x03,
        "extra_store_checks": [
            {"addr": 0xDD02, "value": 0x03, "mask": 0x03},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_VIC_BANK.OBJ"],
    },
    "actc_runtime_gfx_vic_bank_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rVicBank(1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_vic_bank"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_vic_bank\n",
            "i 1\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901201510A9A58DD003A90085028503A2024C0FCF"
            "290349038502AD02DD09038D02DDAD00DD29FC05028D00DD60"
        ),
        "store_check_addr": 0xDD00,
        "store_check_value": 0x02,
        "store_check_mask": 0x03,
        "extra_store_checks": [
            {"addr": 0xDD02, "value": 0x03, "mask": 0x03},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_VIC_BANK.OBJ"],
    },
    "actc_runtime_variable_gfx_vic_bank_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE BANK\r"
            "PROC MAIN()\r"
            "BANK=1\r"
            "VicBank(BANK)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_vic_bank",
            "rt_gfx_screen_base",
            "rt_gfx_bitmap_base",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_vic_bank\n",
            "i 1\n",
            "v bank 0\n",
        ],
        "expected_tail": _actc_variable_gfx_vic_bank_runtime_tail(),
        "store_check_addr": 0xDD00,
        "store_check_value": 0x02,
        "store_check_mask": 0x03,
        "extra_store_checks": [
            {"addr": 0xDD02, "value": 0x03, "mask": 0x03},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_VIC_BANK.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_BASE.OBJ",
            "LIB/RT_GFX_BITMAP_BASE.OBJ",
        ],
    },
    "runtime_gfx_screen_base_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "b u0M\n"
            "u rt_gfx_screen_base\n"
            "m A2 00 A0 04 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_screen_base"],
        "expected_tail": bytes.fromhex(
            "A200A004201710A9A58DD003A90085028503A2024C0FCF"
            "98293C0A0A8502AD18D0290F05028D18D060"
        ),
        "store_check_addr": 0xD018,
        "store_check_value": 0x10,
        "store_check_mask": 0xF0,
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_BASE.OBJ"],
    },
    "actc_runtime_gfx_screen_base_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rScreenBase(1024)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_screen_base"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_screen_base\n",
            "i 1024\n",
        ],
        "expected_tail": bytes.fromhex(
            "A200A004201710A9A58DD003A90085028503A2024C0FCF"
            "98293C0A0A8502AD18D0290F05028D18D060"
        ),
        "store_check_addr": 0xD018,
        "store_check_value": 0x10,
        "store_check_mask": 0xF0,
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_BASE.OBJ"],
    },
    "actc_runtime_card_variable_gfx_screen_base_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD BASE\r"
            "PROC MAIN()\r"
            "BASE=1024\r"
            "ScreenBase(BASE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_base",
            "rt_gfx_bitmap_base",
            "rt_gfx_vic_bank",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_screen_base\n",
            "i 1024\n",
            "v base 0\n",
        ],
        "expected_tail": _actc_card_variable_gfx_screen_base_runtime_tail(),
        "store_check_addr": 0xD018,
        "store_check_value": 0x10,
        "store_check_mask": 0xF0,
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_BASE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_BASE.OBJ",
            "LIB/RT_GFX_VIC_BANK.OBJ",
        ],
    },
    "runtime_gfx_bitmap_base_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "b u0M\n"
            "u rt_gfx_bitmap_base\n"
            "m A2 00 A0 20 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_base"],
        "expected_tail": bytes.fromhex(
            "A200A020201710A9A58DD003A90085028503A2024C0FCF"
            "9829204A4A8502AD18D029F705028D18D060"
        ),
        "store_check_addr": 0xD018,
        "store_check_value": 0x08,
        "store_check_mask": 0x08,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_BASE.OBJ"],
    },
    "actc_runtime_gfx_bitmap_base_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapBase(8192)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_base"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bitmap_base\n",
            "i 8192\n",
        ],
        "expected_tail": bytes.fromhex(
            "A200A020201710A9A58DD003A90085028503A2024C0FCF"
            "9829204A4A8502AD18D029F705028D18D060"
        ),
        "store_check_addr": 0xD018,
        "store_check_value": 0x08,
        "store_check_mask": 0x08,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_BASE.OBJ"],
    },
    "actc_runtime_card_variable_gfx_bitmap_base_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD BASE\r"
            "PROC MAIN()\r"
            "BASE=8192\r"
            "BitmapBase(BASE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_base",
            "rt_gfx_screen_base",
            "rt_gfx_vic_bank",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_bitmap_base\n",
            "i 8192\n",
            "v base 0\n",
        ],
        "expected_tail": _actc_card_variable_gfx_bitmap_base_runtime_tail(),
        "store_check_addr": 0xD018,
        "store_check_value": 0x08,
        "store_check_mask": 0x08,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_BASE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_BASE.OBJ",
            "LIB/RT_GFX_VIC_BANK.OBJ",
        ],
    },
    "runtime_gfx_screen_cell_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 26\n"
            "b u0M\n"
            "u rt_gfx_screen_cell\n"
            "m A9 05 A2 02 A0 41 18 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 8 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_screen_cell"],
        "expected_tail": bytes.fromhex(
            "A905A202A04118201A10A9A58DD003A90085028503A2024C0FCF"
            "85048405A9008502A9048503E000F01018A50269288502A50369008503CAD0F0"
            "18A50265048502A50369008503A000A505910260"
        ),
        "store_check_addr": 0x0455,
        "store_check_value": 0x41,
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_CELL.OBJ"],
    },
    "actc_runtime_gfx_screen_cell_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rScreenCell(5,2,65)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_screen_cell"],
        "expected_object_fragments": [
            "b p0p1p2u0r\n",
            "u rt_gfx_screen_cell\n",
            "i 5\n",
            "i 2\n",
            "i 65\n",
        ],
        "expected_tail": bytes.fromhex(
            "A905A202A04118201A10A9A58DD003A90085028503A2024C0FCF"
            "85048405A9008502A9048503E000F01018A50269288502A50369008503CAD0F0"
            "18A50265048502A50369008503A000A505910260"
        ),
        "store_check_addr": 0x0455,
        "store_check_value": 0x41,
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_CELL.OBJ"],
    },
    "actc_runtime_variable_gfx_screen_cell_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE X\r"
            "BYTE Y\r"
            "BYTE CH\r"
            "PROC MAIN()\r"
            "X=5\r"
            "Y=2\r"
            "CH=65\r"
            "ScreenCell(X,Y,CH)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_screen_copy",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1p2S2L0L1L2u0r\n",
            "u rt_gfx_screen_cell\n",
            "i 5\n",
            "i 2\n",
            "i 65\n",
            "v x 0\n",
            "v y 0\n",
            "v ch 0\n",
        ],
        "expected_tail": _actc_variable_gfx_cell_runtime_tail(
            "rt_gfx_screen_cell", 5, 2, 65
        ),
        "store_check_addr": 0x0455,
        "store_check_value": 0x41,
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_CELL.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_COLOR_CELL.OBJ",
            "LIB/RT_GFX_SCREEN_COPY.OBJ",
        ],
    },
    "runtime_gfx_color_cell_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 26\n"
            "b u0M\n"
            "u rt_gfx_color_cell\n"
            "m A9 05 A2 02 A0 0A 18 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 8 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_color_cell"],
        "expected_tail": bytes.fromhex(
            "A905A202A00A18201A10A9A58DD003A90085028503A2024C0FCF"
            "850498290F8505A9008502A9D88503E000F01018A50269288502A50369008503CAD0F0"
            "18A50265048502A50369008503A000A505910260"
        ),
        "store_check_addr": 0xD855,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_COLOR_CELL.OBJ"],
    },
    "actc_runtime_gfx_color_cell_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rColorCell(5,2,10)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_color_cell"],
        "expected_object_fragments": [
            "b p0p1p2u0r\n",
            "u rt_gfx_color_cell\n",
            "i 5\n",
            "i 2\n",
            "i 10\n",
        ],
        "expected_tail": bytes.fromhex(
            "A905A202A00A18201A10A9A58DD003A90085028503A2024C0FCF"
            "850498290F8505A9008502A9D88503E000F01018A50269288502A50369008503CAD0F0"
            "18A50265048502A50369008503A000A505910260"
        ),
        "store_check_addr": 0xD855,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_COLOR_CELL.OBJ"],
    },
    "actc_runtime_variable_gfx_color_cell_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE X\r"
            "BYTE Y\r"
            "BYTE COLOR\r"
            "PROC MAIN()\r"
            "X=5\r"
            "Y=2\r"
            "COLOR=10\r"
            "ColorCell(X,Y,COLOR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_color_cell",
            "rt_gfx_screen_cell",
            "rt_gfx_color_copy",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1p2S2L0L1L2u0r\n",
            "u rt_gfx_color_cell\n",
            "i 5\n",
            "i 2\n",
            "i 10\n",
            "v x 0\n",
            "v y 0\n",
            "v color 0\n",
        ],
        "expected_tail": _actc_variable_gfx_cell_runtime_tail(
            "rt_gfx_color_cell", 5, 2, 10
        ),
        "store_check_addr": 0xD855,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_COLOR_CELL.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_COLOR_COPY.OBJ",
        ],
    },
    "actc_runtime_cell_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "ScreenCell(5,2,65)\r"
            "ColorCell(6,3,10)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0p1p2u0p3p4p5u1r\n",
            "u rt_gfx_screen_cell\n",
            "u rt_gfx_color_cell\n",
            "i 5\n",
            "i 2\n",
            "i 65\n",
            "i 6\n",
            "i 3\n",
            "i 10\n",
        ],
        "expected_tail": _actc_cell_runtime_tail(),
        "store_check_addr": 0x0455,
        "store_check_value": 0x41,
        "extra_store_checks": [
            {"addr": 0xD87E, "value": 0x0A, "mask": 0x0F},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/RT_GFX_BITMAP_FILL.OBJ"],
    },
    "actc_runtime_gfx1_export_sample_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "ScreenCell(5,2,65)\r"
            "ColorCell(6,3,10)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0p1p2u0p3p4p5u1r\n",
            "u rt_gfx_screen_cell\n",
            "u rt_gfx_color_cell\n",
            "i 5\n",
            "i 2\n",
            "i 65\n",
            "i 6\n",
            "i 3\n",
            "i 10\n",
        ],
        "expected_tail": _actc_cell_runtime_tail(),
        "store_check_addr": 0x0455,
        "store_check_value": 0x41,
        "extra_store_checks": [
            {"addr": 0xD87E, "value": 0x0A, "mask": 0x0F},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
        ],
        "unexpected_alink_loads": ["LIB/RT_GFX_BITMAP_FILL.OBJ"],
    },
    "actc_runtime_gfx1_bgcolor_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBgColor(6)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bgcolor\n",
            "i 6\n",
        ],
        "expected_tail": bytes.fromhex(
            "A906201510A9A58DD003A90085028503A2024C0FCF290F8D21D060"
        ),
        "store_check_addr": 0xD021,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_bordercolor_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBorderColor(30)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bordercolor",
            "rt_gfx_bgcolor",
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bordercolor\n",
            "i 30\n",
        ],
        "expected_tail": bytes.fromhex(
            "A91E201510A9A58DD003A90085028503A2024C0FCF290F8D20D060"
        ),
        "store_check_addr": 0xD020,
        "store_check_value": 0x0E,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_vic_bank_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rVicBank(1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_vic_bank",
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_vic_bank\n",
            "i 1\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901201510A9A58DD003A90085028503A2024C0FCF"
            "290349038502AD02DD09038D02DDAD00DD29FC05028D00DD60"
        ),
        "store_check_addr": 0xDD00,
        "store_check_value": 0x02,
        "store_check_mask": 0x03,
        "extra_store_checks": [
            {"addr": 0xDD02, "value": 0x03, "mask": 0x03},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_VIC_BANK.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_screen_base_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rScreenBase(1024)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_base",
            "rt_gfx_bitmap_base",
            "rt_gfx_vic_bank",
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_screen_base\n",
            "i 1024\n",
        ],
        "expected_tail": bytes.fromhex(
            "A200A004201710A9A58DD003A90085028503A2024C0FCF"
            "98293C0A0A8502AD18D0290F05028D18D060"
        ),
        "store_check_addr": 0xD018,
        "store_check_value": 0x10,
        "store_check_mask": 0xF0,
        "expected_alink_loads": [
            "LIB/RT_GFX_SCREEN_BASE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_BASE.OBJ",
            "LIB/RT_GFX_VIC_BANK.OBJ",
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_bitmap_base_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapBase(8192)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_base",
            "rt_gfx_screen_base",
            "rt_gfx_vic_bank",
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bitmap_base\n",
            "i 8192\n",
        ],
        "expected_tail": bytes.fromhex(
            "A200A020201710A9A58DD003A90085028503A2024C0FCF"
            "9829204A4A8502AD18D029F705028D18D060"
        ),
        "store_check_addr": 0xD018,
        "store_check_value": 0x08,
        "store_check_mask": 0x08,
        "expected_alink_loads": [
            "LIB/RT_GFX_BITMAP_BASE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_BASE.OBJ",
            "LIB/RT_GFX_VIC_BANK.OBJ",
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_COLOR_CELL.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_screen_cell_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rScreenCell(5,2,65)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_cell",
            "rt_gfx_color_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0p1p2u0r\n",
            "u rt_gfx_screen_cell\n",
            "i 5\n",
            "i 2\n",
            "i 65\n",
        ],
        "expected_tail": _actc_gfx_cell_single_runtime_tail(
            "rt_gfx_screen_cell", 5, 2, 65
        ),
        "store_check_addr": 0x0455,
        "store_check_value": 0x41,
        "expected_alink_loads": [
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_COLOR_CELL.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_color_cell_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rColorCell(6,3,10)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_color_cell",
            "rt_gfx_screen_cell",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0p1p2u0r\n",
            "u rt_gfx_color_cell\n",
            "i 6\n",
            "i 3\n",
            "i 10\n",
        ],
        "expected_tail": _actc_gfx_cell_single_runtime_tail(
            "rt_gfx_color_cell", 6, 3, 10
        ),
        "store_check_addr": 0xD87E,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "expected_alink_loads": [
            "LIB/RT_GFX_COLOR_CELL.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_screen_copy_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rScreenCopy(12288)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_copy",
            "rt_gfx_color_copy",
            "rt_gfx_bitmap_copy",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_screen_copy\n",
            "i 12288\n",
        ],
        "expected_tail": bytes.fromhex(
            "A200A030201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9048505A203A000B1029104C8D0F9E603E605CAD0F2"
            "A000B1029104C8C0E8D0F760"
        ),
        "pre_run_memory": [
            {"addr": 0x3000, "value": 0x51},
            {"addr": 0x3001, "value": 0x52},
        ],
        "store_check_addr": 0x0400,
        "store_check_value": 0x51,
        "extra_store_checks": [
            {"addr": 0x0401, "value": 0x52},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_SCREEN_COPY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_COLOR_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_color_copy_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rColorCopy(12304)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_color_copy",
            "rt_gfx_screen_copy",
            "rt_gfx_bitmap_copy",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_color_copy\n",
            "i 12304\n",
        ],
        "expected_tail": bytes.fromhex(
            "A210A030201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9D88505A203A000B102290F9104C8D0F7E603E605CAD0F0"
            "A000B102290F9104C8C0E8D0F560"
        ),
        "pre_run_memory": [
            {"addr": 0x3010, "value": 0x8A},
            {"addr": 0x3011, "value": 0x0B},
        ],
        "store_check_addr": 0xD800,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0xD801, "value": 0x0B, "mask": 0x0F},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_COLOR_COPY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_bitmap_fill_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapFill(60)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_fill",
            "rt_gfx_screen_copy",
            "rt_gfx_color_copy",
            "rt_gfx_bitmap_copy",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bitmap_fill\n",
            "i 60\n",
        ],
        "expected_tail": bytes.fromhex(
            "A93C201510A9A58DD003A90085028503A2024C0FCF"
            "8502A9008504A9208505A21FA000A5029104C8D0F9E605CAD0F4"
            "A000A5029104C8C040D0F760"
        ),
        "store_check_addr": 0x2000,
        "store_check_value": 0x3C,
        "extra_store_checks": [
            {"addr": 0x3F3F, "value": 0x3C},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": [
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_COPY.OBJ",
            "LIB/RT_GFX_COLOR_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
        ],
    },
    "actc_runtime_gfx1_bitmap_copy_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapCopy(20480)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_copy",
            "rt_gfx_screen_copy",
            "rt_gfx_color_copy",
            "rt_gfx_bitmap_fill",
        ],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bitmap_copy\n",
            "i 20480\n",
        ],
        "expected_tail": bytes.fromhex(
            "A200A050201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9208505A21FA000B1029104C8D0F9E603E605CAD0F2"
            "A000B1029104C8C040D0F760"
        ),
        "pre_run_memory": [
            {"addr": 0x5000, "value": 0x71},
            {"addr": 0x5001, "value": 0x72},
        ],
        "store_check_addr": 0x2000,
        "store_check_value": 0x71,
        "extra_store_checks": [
            {"addr": 0x2001, "value": 0x72},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": [
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_COPY.OBJ",
            "LIB/RT_GFX_COLOR_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
    },
    "actc_runtime_gfx1_bitmap_on_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapOn()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_on",
            "rt_gfx_bitmap_off",
            "rt_gfx_mbitmap_on",
            "rt_gfx_mbitmap_off",
        ],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_gfx_bitmap_on\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D009208D11D060"
        ),
        "store_check_addr": 0xD011,
        "store_check_value": 0x20,
        "store_check_mask": 0x20,
        "expected_alink_loads": [
            "LIB/RT_GFX_BITMAP_ON.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_OFF.OBJ",
            "LIB/RT_GFX_MBITMAP_ON.OBJ",
            "LIB/RT_GFX_MBITMAP_OFF.OBJ",
        ],
    },
    "actc_runtime_gfx1_bitmap_off_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapOff()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_off",
            "rt_gfx_bitmap_on",
            "rt_gfx_mbitmap_on",
            "rt_gfx_mbitmap_off",
        ],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_gfx_bitmap_off\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D029DF8D11D060"
        ),
        "pre_run_memory": [
            {"addr": 0xD011, "value": 0x20},
        ],
        "store_check_addr": 0xD011,
        "store_check_value": 0x00,
        "store_check_mask": 0x20,
        "expected_alink_loads": [
            "LIB/RT_GFX_BITMAP_OFF.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_ON.OBJ",
            "LIB/RT_GFX_MBITMAP_ON.OBJ",
            "LIB/RT_GFX_MBITMAP_OFF.OBJ",
        ],
    },
    "actc_runtime_gfx1_mbitmap_on_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rMBitmapOn()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_mbitmap_on",
            "rt_gfx_bitmap_on",
            "rt_gfx_bitmap_off",
            "rt_gfx_mbitmap_off",
        ],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_gfx_mbitmap_on\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D009208D11D0AD16D009108D16D060"
        ),
        "store_check_addr": 0xD011,
        "store_check_value": 0x20,
        "store_check_mask": 0x20,
        "extra_store_checks": [
            {"addr": 0xD016, "value": 0x10, "mask": 0x10},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_MBITMAP_ON.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_ON.OBJ",
            "LIB/RT_GFX_BITMAP_OFF.OBJ",
            "LIB/RT_GFX_MBITMAP_OFF.OBJ",
        ],
    },
    "actc_runtime_gfx1_mbitmap_off_split_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rMBitmapOff()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_mbitmap_off",
            "rt_gfx_mbitmap_on",
            "rt_gfx_bitmap_on",
            "rt_gfx_bitmap_off",
        ],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_gfx_mbitmap_off\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D029DF8D11D0AD16D029EF8D16D060"
        ),
        "pre_run_memory": [
            {"addr": 0xD011, "value": 0x20},
            {"addr": 0xD016, "value": 0x10},
        ],
        "store_check_addr": 0xD011,
        "store_check_value": 0x00,
        "store_check_mask": 0x20,
        "extra_store_checks": [
            {"addr": 0xD016, "value": 0x00, "mask": 0x10},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_MBITMAP_OFF.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_MBITMAP_ON.OBJ",
            "LIB/RT_GFX_BITMAP_ON.OBJ",
            "LIB/RT_GFX_BITMAP_OFF.OBJ",
        ],
    },
    "runtime_gfx_screen_copy_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 7\n"
            "b p0u0r\n"
            "u rt_gfx_screen_copy\n"
            "i 12288\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_screen_copy"],
        "expected_tail": bytes.fromhex(
            "A200A030201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9048505A203A000B1029104C8D0F9E603E605CAD0F2"
            "A000B1029104C8C0E8D0F760"
        ),
        "pre_run_memory": [
            {"addr": 0x3000, "value": 0x51},
            {"addr": 0x3001, "value": 0x52},
        ],
        "store_check_addr": 0x0400,
        "store_check_value": 0x51,
        "extra_store_checks": [
            {"addr": 0x0401, "value": 0x52},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_COPY.OBJ"],
    },
    "actc_runtime_gfx_screen_copy_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rScreenCopy(12288)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_screen_copy"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_screen_copy\n",
            "i 12288\n",
        ],
        "expected_tail": bytes.fromhex(
            "A200A030201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9048505A203A000B1029104C8D0F9E603E605CAD0F2"
            "A000B1029104C8C0E8D0F760"
        ),
        "pre_run_memory": [
            {"addr": 0x3000, "value": 0x51},
            {"addr": 0x3001, "value": 0x52},
        ],
        "store_check_addr": 0x0400,
        "store_check_value": 0x51,
        "extra_store_checks": [
            {"addr": 0x0401, "value": 0x52},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_COPY.OBJ"],
    },
    "actc_runtime_card_variable_gfx_screen_copy_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD ADDR\r"
            "PROC MAIN()\r"
            "ADDR=12288\r"
            "ScreenCopy(ADDR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_copy",
            "rt_gfx_color_copy",
            "rt_gfx_bitmap_copy",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_screen_copy\n",
            "i 12288\n",
            "v addr 0\n",
        ],
        "expected_tail": _actc_card_variable_gfx_copy_runtime_tail(
            "rt_gfx_screen_copy", 12288
        ),
        "pre_run_memory": [
            {"addr": 0x3000, "value": 0x51},
            {"addr": 0x3001, "value": 0x52},
        ],
        "store_check_addr": 0x0400,
        "store_check_value": 0x51,
        "extra_store_checks": [
            {"addr": 0x0401, "value": 0x52},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_SCREEN_COPY.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_COLOR_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
        ],
    },
    "runtime_gfx_color_copy_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 7\n"
            "b p0u0r\n"
            "u rt_gfx_color_copy\n"
            "i 12304\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_color_copy"],
        "expected_tail": bytes.fromhex(
            "A210A030201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9D88505A203A000B102290F9104C8D0F7E603E605CAD0F0"
            "A000B102290F9104C8C0E8D0F560"
        ),
        "pre_run_memory": [
            {"addr": 0x3010, "value": 0x8A},
            {"addr": 0x3011, "value": 0x0B},
        ],
        "store_check_addr": 0xD800,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0xD801, "value": 0x0B, "mask": 0x0F},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_COLOR_COPY.OBJ"],
    },
    "actc_runtime_gfx_color_copy_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rColorCopy(12304)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_color_copy"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_color_copy\n",
            "i 12304\n",
        ],
        "expected_tail": bytes.fromhex(
            "A210A030201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9D88505A203A000B102290F9104C8D0F7E603E605CAD0F0"
            "A000B102290F9104C8C0E8D0F560"
        ),
        "pre_run_memory": [
            {"addr": 0x3010, "value": 0x8A},
            {"addr": 0x3011, "value": 0x0B},
        ],
        "store_check_addr": 0xD800,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0xD801, "value": 0x0B, "mask": 0x0F},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_COLOR_COPY.OBJ"],
    },
    "actc_runtime_card_variable_gfx_color_copy_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD ADDR\r"
            "PROC MAIN()\r"
            "ADDR=12304\r"
            "ColorCopy(ADDR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_color_copy",
            "rt_gfx_screen_copy",
            "rt_gfx_bitmap_copy",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_color_copy\n",
            "i 12304\n",
            "v addr 0\n",
        ],
        "expected_tail": _actc_card_variable_gfx_copy_runtime_tail(
            "rt_gfx_color_copy", 12304
        ),
        "pre_run_memory": [
            {"addr": 0x3010, "value": 0x8A},
            {"addr": 0x3011, "value": 0x0B},
        ],
        "store_check_addr": 0xD800,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0xD801, "value": 0x0B, "mask": 0x0F},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_COLOR_COPY.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_SCREEN_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
        ],
    },
    "runtime_gfx_bitmap_fill_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 7\n"
            "b p0u0r\n"
            "u rt_gfx_bitmap_fill\n"
            "i 60\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_fill"],
        "expected_tail": bytes.fromhex(
            "A93C201510A9A58DD003A90085028503A2024C0FCF"
            "8502A9008504A9208505A21FA000A5029104C8D0F9E605CAD0F4"
            "A000A5029104C8C040D0F760"
        ),
        "store_check_addr": 0x2000,
        "store_check_value": 0x3C,
        "extra_store_checks": [
            {"addr": 0x3F3F, "value": 0x3C},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_FILL.OBJ"],
    },
    "actc_runtime_gfx_bitmap_fill_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapFill(60)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_fill"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bitmap_fill\n",
            "i 60\n",
        ],
        "expected_tail": bytes.fromhex(
            "A93C201510A9A58DD003A90085028503A2024C0FCF"
            "8502A9008504A9208505A21FA000A5029104C8D0F9E605CAD0F4"
            "A000A5029104C8C040D0F760"
        ),
        "store_check_addr": 0x2000,
        "store_check_value": 0x3C,
        "extra_store_checks": [
            {"addr": 0x3F3F, "value": 0x3C},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_FILL.OBJ"],
    },
    "actc_runtime_variable_gfx_bitmap_fill_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE COLOR\r"
            "PROC MAIN()\r"
            "COLOR=60\r"
            "BitmapFill(COLOR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_fill",
            "rt_gfx_bitmap_copy",
            "rt_gfx_screen_copy",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_bitmap_fill\n",
            "i 60\n",
            "v color 0\n",
        ],
        "expected_tail": _actc_variable_gfx_byte_runtime_tail(
            "rt_gfx_bitmap_fill", 60
        ),
        "store_check_addr": 0x2000,
        "store_check_value": 0x3C,
        "extra_store_checks": [
            {"addr": 0x3F3F, "value": 0x3C},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_FILL.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
            "LIB/RT_GFX_SCREEN_COPY.OBJ",
        ],
    },
    "runtime_gfx_bitmap_copy_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 7\n"
            "b p0u0r\n"
            "u rt_gfx_bitmap_copy\n"
            "i 20480\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_copy"],
        "expected_tail": bytes.fromhex(
            "A200A050201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9208505A21FA000B1029104C8D0F9E603E605CAD0F2"
            "A000B1029104C8C040D0F760"
        ),
        "pre_run_memory": [
            {"addr": 0x5000, "value": 0x71},
            {"addr": 0x5001, "value": 0x72},
        ],
        "store_check_addr": 0x2000,
        "store_check_value": 0x71,
        "extra_store_checks": [
            {"addr": 0x2001, "value": 0x72},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_COPY.OBJ"],
    },
    "actc_runtime_gfx_bitmap_copy_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapCopy(20480)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_copy"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bitmap_copy\n",
            "i 20480\n",
        ],
        "expected_tail": bytes.fromhex(
            "A200A050201710A9A58DD003A90085028503A2024C0FCF"
            "86028403A9008504A9208505A21FA000B1029104C8D0F9E603E605CAD0F2"
            "A000B1029104C8C040D0F760"
        ),
        "pre_run_memory": [
            {"addr": 0x5000, "value": 0x71},
            {"addr": 0x5001, "value": 0x72},
        ],
        "store_check_addr": 0x2000,
        "store_check_value": 0x71,
        "extra_store_checks": [
            {"addr": 0x2001, "value": 0x72},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_COPY.OBJ"],
    },
    "actc_runtime_card_variable_gfx_bitmap_copy_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD ADDR\r"
            "PROC MAIN()\r"
            "ADDR=20480\r"
            "BitmapCopy(ADDR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_copy",
            "rt_gfx_bitmap_fill",
            "rt_gfx_color_copy",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_bitmap_copy\n",
            "i 20480\n",
            "v addr 0\n",
        ],
        "expected_tail": _actc_card_variable_gfx_copy_runtime_tail(
            "rt_gfx_bitmap_copy", 20480
        ),
        "pre_run_memory": [
            {"addr": 0x5000, "value": 0x71},
            {"addr": 0x5001, "value": 0x72},
        ],
        "store_check_addr": 0x2000,
        "store_check_value": 0x71,
        "extra_store_checks": [
            {"addr": 0x2001, "value": 0x72},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_COPY.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
            "LIB/RT_GFX_COLOR_COPY.OBJ",
        ],
    },
    "runtime_gfx_bitmap_on_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u rt_gfx_bitmap_on\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_on"],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D009208D11D060"
        ),
        "store_check_addr": 0xD011,
        "store_check_value": 0x20,
        "store_check_mask": 0x20,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_ON.OBJ"],
    },
    "actc_runtime_gfx_bitmap_on_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapOn()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_on"],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_gfx_bitmap_on\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D009208D11D060"
        ),
        "store_check_addr": 0xD011,
        "store_check_value": 0x20,
        "store_check_mask": 0x20,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_ON.OBJ"],
    },
    "runtime_gfx_bitmap_off_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u rt_gfx_bitmap_off\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_off"],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D029DF8D11D060"
        ),
        "pre_run_memory": [
            {"addr": 0xD011, "value": 0x20},
        ],
        "store_check_addr": 0xD011,
        "store_check_value": 0x00,
        "store_check_mask": 0x20,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_OFF.OBJ"],
    },
    "actc_runtime_gfx_bitmap_off_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBitmapOff()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bitmap_off"],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_gfx_bitmap_off\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D029DF8D11D060"
        ),
        "pre_run_memory": [
            {"addr": 0xD011, "value": 0x20},
        ],
        "store_check_addr": 0xD011,
        "store_check_value": 0x00,
        "store_check_mask": 0x20,
        "expected_alink_loads": ["LIB/RT_GFX_BITMAP_OFF.OBJ"],
    },
    "runtime_gfx_mbitmap_on_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u rt_gfx_mbitmap_on\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_mbitmap_on"],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D009208D11D0AD16D009108D16D060"
        ),
        "store_check_addr": 0xD011,
        "store_check_value": 0x20,
        "store_check_mask": 0x20,
        "extra_store_checks": [
            {"addr": 0xD016, "value": 0x10, "mask": 0x10},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_MBITMAP_ON.OBJ"],
    },
    "actc_runtime_gfx_mbitmap_on_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rMBitmapOn()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_mbitmap_on"],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_gfx_mbitmap_on\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D009208D11D0AD16D009108D16D060"
        ),
        "store_check_addr": 0xD011,
        "store_check_value": 0x20,
        "store_check_mask": 0x20,
        "extra_store_checks": [
            {"addr": 0xD016, "value": 0x10, "mask": 0x10},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_MBITMAP_ON.OBJ"],
    },
    "runtime_gfx_mbitmap_off_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u rt_gfx_mbitmap_off\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_mbitmap_off"],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D029DF8D11D0AD16D029EF8D16D060"
        ),
        "pre_run_memory": [
            {"addr": 0xD011, "value": 0x20},
            {"addr": 0xD016, "value": 0x10},
        ],
        "store_check_addr": 0xD011,
        "store_check_value": 0x00,
        "store_check_mask": 0x20,
        "extra_store_checks": [
            {"addr": 0xD016, "value": 0x00, "mask": 0x10},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_MBITMAP_OFF.OBJ"],
    },
    "actc_runtime_gfx_mbitmap_off_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rMBitmapOff()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_mbitmap_off"],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_gfx_mbitmap_off\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD11D029DF8D11D0AD16D029EF8D16D060"
        ),
        "pre_run_memory": [
            {"addr": 0xD011, "value": 0x20},
            {"addr": 0xD016, "value": 0x10},
        ],
        "store_check_addr": 0xD011,
        "store_check_value": 0x00,
        "store_check_mask": 0x20,
        "extra_store_checks": [
            {"addr": 0xD016, "value": 0x00, "mask": 0x10},
        ],
        "expected_alink_loads": ["LIB/RT_GFX_MBITMAP_OFF.OBJ"],
    },
    "runtime_gfx_bordercolor_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 21\n"
            "b u0M\n"
            "u rt_gfx_bordercolor\n"
            "m A9 1E 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 3 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bordercolor"],
        "expected_tail": bytes.fromhex(
            "A91E201510A9A58DD003A90085028503A2024C0FCF290F8D20D060"
        ),
        "store_check_addr": 0xD020,
        "store_check_value": 0x0E,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_BORDERCOLOR.OBJ"],
    },
    "actc_runtime_gfx_bordercolor_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rBorderColor(30)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_gfx_bordercolor"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_gfx_bordercolor\n",
            "i 30\n",
        ],
        "expected_tail": bytes.fromhex(
            "A91E201510A9A58DD003A90085028503A2024C0FCF290F8D20D060"
        ),
        "store_check_addr": 0xD020,
        "store_check_value": 0x0E,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_BORDERCOLOR.OBJ"],
    },
    "actc_runtime_variable_gfx_bordercolor_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE COLOR\r"
            "PROC MAIN()\r"
            "COLOR=30\r"
            "BorderColor(COLOR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bordercolor",
            "rt_gfx_bgcolor",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_gfx_bordercolor\n",
            "i 30\n",
            "v color 0\n",
        ],
        "expected_tail": _actc_variable_gfx_bordercolor_runtime_tail(),
        "store_check_addr": 0xD020,
        "store_check_value": 0x0E,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_GFX_BORDERCOLOR.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_variable_gfx_reassigned_color_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE COLOR\r"
            "PROC MAIN()\r"
            "COLOR=2\r"
            "BgColor(COLOR)\r"
            "COLOR=30\r"
            "BorderColor(COLOR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bgcolor",
            "rt_gfx_bordercolor",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_gfx_bgcolor\n",
            "u rt_gfx_bordercolor\n",
            "i 2\n",
            "i 30\n",
            "v color 0\n",
        ],
        "expected_tail": _actc_variable_gfx_reassigned_color_runtime_tail(),
        "store_check_addr": 0xD021,
        "store_check_value": 0x02,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0xD020, "value": 0x0E, "mask": 0x0F},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "runtime_sid_vol_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 21\n"
            "b u0M\n"
            "u rt_sid_vol\n"
            "m A9 0A 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 3 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_vol", "rt_sid_volume_state"],
        "expected_tail": bytes.fromhex(
            "A90A201510A9A58DD003A90085028503A2024C0FCF"
            "8502AD2B1029F08503A502290F05038D2B108D18D460"
            "00"
        ),
        "store_check_addr": 0xD418,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x102B, "value": 0x0A},
        ],
        "expected_alink_loads": ["LIB/RT_SID_VOL.OBJ", "LIB/RT_SID_VOLUME_STATE.OBJ"],
    },
    "actc_runtime_sid_vol_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidVol(10)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_vol", "rt_sid_volume_state"],
        "expected_object_fragments": [
            "x main 0 7\n",
            "b p0u0r\n",
            "u rt_sid_vol\n",
            "i 10\n",
        ],
        "expected_tail": bytes.fromhex(
            "A90A201510A9A58DD003A90085028503A2024C0FCF"
            "8502AD2B1029F08503A502290F05038D2B108D18D460"
            "00"
        ),
        "store_check_addr": 0xD418,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x102B, "value": 0x0A},
        ],
        "expected_alink_loads": ["LIB/RT_SID_VOL.OBJ", "LIB/RT_SID_VOLUME_STATE.OBJ"],
    },
    "actc_runtime_variable_sid_vol_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE VOLUME\r"
            "PROC MAIN()\r"
            "VOLUME=10\r"
            "SidVol(VOLUME)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_vol",
            "rt_sid_volume_state",
            "rt_sid_mode",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sid_vol\n",
            "i 10\n",
            "v volume 0\n",
        ],
        "expected_tail": _actc_variable_sid_vol_runtime_tail(),
        "store_check_addr": 0xD418,
        "store_check_value": 0x0A,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x102D, "value": 0x0A},
        ],
        "expected_alink_loads": ["LIB/RT_SID_VOL.OBJ", "LIB/RT_SID_VOLUME_STATE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_variable_sid_reassigned_level_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE LEVEL\r"
            "PROC MAIN()\r"
            "LEVEL=2\r"
            "SidVol(LEVEL)\r"
            "LEVEL=48\r"
            "SidMode(LEVEL)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_vol",
            "rt_sid_mode",
            "rt_sid_volume_state",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_sid_vol\n",
            "u rt_sid_mode\n",
            "i 2\n",
            "i 48\n",
            "v level 0\n",
        ],
        "expected_tail": _actc_variable_sid_reassigned_level_runtime_tail(),
        "store_check_addr": 0xD418,
        "store_check_value": 0x32,
        "extra_store_checks": [
            {"addr": 0x104A, "value": 0x32},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "runtime_sid_mode_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 26\n"
            "b u0u1M\n"
            "u rt_sid_vol\n"
            "u rt_sid_mode\n"
            "m A9 0A 20 00 00 A9 30 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 3 u0\n"
            "r 8 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_vol", "rt_sid_mode", "rt_sid_volume_state"],
        "expected_tail": bytes.fromhex(
            "A90A201A10A930203010A9A58DD003A90085028503A2024C0FCF"
            "8502AD461029F08503A502290F05038D46108D18D460"
            "8502AD4610290F8503A50229F005038D46108D18D460"
            "00"
        ),
        "store_check_addr": 0xD418,
        "store_check_value": 0x3A,
        "extra_store_checks": [
            {"addr": 0x1046, "value": 0x3A},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
    },
    "actc_runtime_sid_mode_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidMode(48)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_mode", "rt_sid_volume_state"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_sid_mode\n",
            "i 48\n",
        ],
        "expected_tail": bytes.fromhex(
            "A930201510A9A58DD003A90085028503A2024C0FCF"
            "8502AD2B10290F8503A50229F005038D2B108D18D460"
            "00"
        ),
        "store_check_addr": 0xD418,
        "store_check_value": 0x30,
        "extra_store_checks": [
            {"addr": 0x102B, "value": 0x30},
        ],
        "expected_alink_loads": ["LIB/RT_SID_MODE.OBJ", "LIB/RT_SID_VOLUME_STATE.OBJ"],
    },
    "actc_runtime_variable_sid_mode_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE MODE\r"
            "PROC MAIN()\r"
            "MODE=48\r"
            "SidMode(MODE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_mode",
            "rt_sid_volume_state",
            "rt_sid_vol",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sid_mode\n",
            "i 48\n",
            "v mode 0\n",
        ],
        "expected_tail": _actc_variable_sid_mode_runtime_tail(),
        "store_check_addr": 0xD418,
        "store_check_value": 0x30,
        "store_check_mask": 0xF0,
        "extra_store_checks": [
            {"addr": 0x102D, "value": 0x30},
        ],
        "expected_alink_loads": ["LIB/RT_SID_MODE.OBJ", "LIB/RT_SID_VOLUME_STATE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "runtime_sid_freq_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 25\n"
            "b u0M\n"
            "u rt_sid_freq\n"
            "m A9 01 A2 34 A0 12 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 7 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_freq"],
        "expected_tail": bytes.fromhex(
            "A901A234A012201910A9A58DD003A90085028503A2024C0FCF"
            "850286038404A5020A0A0A38E502AAA5039D00D4A5049D01D460"
        ),
        "store_check_addr": 0xD407,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD408,
        "store_check_hi_value": 0x12,
        "expected_alink_loads": ["LIB/RT_SID_FREQ.OBJ"],
    },
    "actc_runtime_sid_freq_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidFreq(1,4660)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_freq"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sid_freq\n",
            "i 1\n",
            "i 4660\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901A234A012201910A9A58DD003A90085028503A2024C0FCF"
            "850286038404A5020A0A0A38E502AAA5039D00D4A5049D01D460"
        ),
        "store_check_addr": 0xD407,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD408,
        "store_check_hi_value": 0x12,
        "expected_alink_loads": ["LIB/RT_SID_FREQ.OBJ"],
    },
    "actc_runtime_variable_sid_freq_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE VOICE\r"
            "CARD FREQ\r"
            "PROC MAIN()\r"
            "VOICE=1\r"
            "FREQ=4660\r"
            "SidFreq(VOICE,FREQ)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_freq",
            "rt_sid_pulse",
            "rt_sprite_pos",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sid_freq\n",
            "i 1\n",
            "i 4660\n",
            "v voice 0\n",
            "v freq 0\n",
        ],
        "expected_tail": _actc_variable_sid_freq_runtime_tail(),
        "store_check_addr": 0xD407,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD408,
        "store_check_hi_value": 0x12,
        "expected_alink_loads": ["LIB/RT_SID_FREQ.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_PULSE.OBJ",
            "LIB/RT_SPRITE_POS.OBJ",
        ],
    },
    "runtime_sid_pulse_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 25\n"
            "b u0M\n"
            "u rt_sid_pulse\n"
            "m A9 01 A2 34 A0 12 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 7 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_pulse"],
        "expected_tail": bytes.fromhex(
            "A901A234A012201910A9A58DD003A90085028503A2024C0FCF"
            "850286038404A5020A0A0A38E502AAA5039D02D4A504290F9D03D460"
        ),
        "store_check_addr": 0xD409,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD40A,
        "store_check_hi_value": 0x02,
        "expected_alink_loads": ["LIB/RT_SID_PULSE.OBJ"],
    },
    "actc_runtime_sid_pulse_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidPulse(1,4660)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_pulse"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sid_pulse\n",
            "i 1\n",
            "i 4660\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901A234A012201910A9A58DD003A90085028503A2024C0FCF"
            "850286038404A5020A0A0A38E502AAA5039D02D4A504290F9D03D460"
        ),
        "store_check_addr": 0xD409,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD40A,
        "store_check_hi_value": 0x02,
        "expected_alink_loads": ["LIB/RT_SID_PULSE.OBJ"],
    },
    "actc_runtime_variable_sid_pulse_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE VOICE\r"
            "CARD WIDTH\r"
            "PROC MAIN()\r"
            "VOICE=1\r"
            "WIDTH=4660\r"
            "SidPulse(VOICE,WIDTH)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_pulse",
            "rt_sid_freq",
            "rt_sprite_pos",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sid_pulse\n",
            "i 1\n",
            "i 4660\n",
            "v voice 0\n",
            "v width 0\n",
        ],
        "expected_tail": _actc_variable_sid_pulse_runtime_tail(),
        "store_check_addr": 0xD409,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD40A,
        "store_check_hi_value": 0x02,
        "expected_alink_loads": ["LIB/RT_SID_PULSE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_FREQ.OBJ",
            "LIB/RT_SPRITE_POS.OBJ",
        ],
    },
    "runtime_sid_wave_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 28\n"
            "b u0M\n"
            "u rt_sid_wave\n"
            "m A9 01 8D 0B D4 A9 01 A0 40 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 10 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_wave", "rt_sid_state"],
        "expected_tail": bytes.fromhex(
            "A9018D0BD4A901A040201C10A9A58DD003A90085028503A2024C0FCF"
            "85028403AAA5039D3810A5020A0A0A38E502186904AAA5039D00D460"
            "000000"
        ),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x40,
        "extra_store_checks": [
            {"addr": 0x1039, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_SID_WAVE.OBJ", "LIB/RT_SID_STATE.OBJ"],
    },
    "actc_runtime_sid_wave_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidWave(1,64)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_wave", "rt_sid_state"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sid_wave\n",
            "i 1\n",
            "i 64\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901A040201710A9A58DD003A90085028503A2024C0FCF"
            "85028403AAA5039D3310A5020A0A0A38E502186904AAA5039D00D460"
            "000000"
        ),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x40,
        "extra_store_checks": [
            {"addr": 0x1034, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_SID_WAVE.OBJ", "LIB/RT_SID_STATE.OBJ"],
    },
    "actc_runtime_variable_sid_wave_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE VOICE\r"
            "BYTE WAVE\r"
            "PROC MAIN()\r"
            "VOICE=1\r"
            "WAVE=64\r"
            "SidWave(VOICE,WAVE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_wave",
            "rt_sid_state",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sid_wave\n",
            "i 1\n",
            "i 64\n",
            "v voice 0\n",
            "v wave 0\n",
        ],
        "expected_tail": _actc_variable_sid_wave_runtime_tail(),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x40,
        "extra_store_checks": [
            {"addr": 0x1038, "value": 0x40},
        ],
        "expected_alink_loads": ["LIB/RT_SID_WAVE.OBJ", "LIB/RT_SID_STATE.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SID_FREQ.OBJ"],
    },
    "runtime_sid_ad_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "b u0M\n"
            "u rt_sid_ad\n"
            "m A9 01 A0 97 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_ad"],
        "expected_tail": bytes.fromhex(
            "A901A097201710A9A58DD003A90085028503A2024C0FCF"
            "85028403A5020A0A0A38E502186905AAA5039D00D460"
        ),
        "store_check_addr": 0xD40C,
        "store_check_value": 0x97,
        "expected_alink_loads": ["LIB/RT_SID_AD.OBJ"],
    },
    "actc_runtime_sid_ad_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidAD(1,151)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_ad"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sid_ad\n",
            "i 1\n",
            "i 151\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901A097201710A9A58DD003A90085028503A2024C0FCF"
            "85028403A5020A0A0A38E502186905AAA5039D00D460"
        ),
        "store_check_addr": 0xD40C,
        "store_check_value": 0x97,
        "expected_alink_loads": ["LIB/RT_SID_AD.OBJ"],
    },
    "actc_runtime_variable_sid_ad_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE VOICE\r"
            "BYTE AD\r"
            "PROC MAIN()\r"
            "VOICE=1\r"
            "AD=151\r"
            "SidAD(VOICE,AD)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_ad",
            "rt_sid_sr",
            "rt_sid_wave",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sid_ad\n",
            "i 1\n",
            "i 151\n",
            "v voice 0\n",
            "v ad 0\n",
        ],
        "expected_tail": _actc_variable_sid_ad_runtime_tail(),
        "store_check_addr": 0xD40C,
        "store_check_value": 0x97,
        "expected_alink_loads": ["LIB/RT_SID_AD.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_SR.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
        ],
    },
    "runtime_sid_sr_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "b u0M\n"
            "u rt_sid_sr\n"
            "m A9 01 A0 F8 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_sr"],
        "expected_tail": bytes.fromhex(
            "A901A0F8201710A9A58DD003A90085028503A2024C0FCF"
            "85028403A5020A0A0A38E502186906AAA5039D00D460"
        ),
        "store_check_addr": 0xD40D,
        "store_check_value": 0xF8,
        "expected_alink_loads": ["LIB/RT_SID_SR.OBJ"],
    },
    "actc_runtime_sid_sr_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidSR(1,248)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_sr"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sid_sr\n",
            "i 1\n",
            "i 248\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901A0F8201710A9A58DD003A90085028503A2024C0FCF"
            "85028403A5020A0A0A38E502186906AAA5039D00D460"
        ),
        "store_check_addr": 0xD40D,
        "store_check_value": 0xF8,
        "expected_alink_loads": ["LIB/RT_SID_SR.OBJ"],
    },
    "actc_runtime_variable_sid_sr_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE VOICE\r"
            "BYTE SR\r"
            "PROC MAIN()\r"
            "VOICE=1\r"
            "SR=248\r"
            "SidSR(VOICE,SR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_sr",
            "rt_sid_ad",
            "rt_sid_wave",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sid_sr\n",
            "i 1\n",
            "i 248\n",
            "v voice 0\n",
            "v sr 0\n",
        ],
        "expected_tail": _actc_variable_sid_sr_runtime_tail(),
        "store_check_addr": 0xD40D,
        "store_check_value": 0xF8,
        "expected_alink_loads": ["LIB/RT_SID_SR.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_AD.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
        ],
    },
    "runtime_sid_on_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 28\n"
            "b u0u1M\n"
            "u rt_sid_wave\n"
            "u rt_sid_on\n"
            "m A9 01 A0 40 20 00 00 A9 01 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "r 10 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_wave", "rt_sid_on", "rt_sid_state"],
        "expected_tail": bytes.fromhex(
            "A901A040201C10A901203810A9A58DD003A90085028503A2024C0FCF"
            "85028403AAA5039D5710A5020A0A0A38E502186904AAA5039D00D460"
            "8502AABD571009019D57108503A5020A0A0A38E502186904AAA5039D00D460"
            "000000"
        ),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x41,
        "extra_store_checks": [
            {"addr": 0x1058, "value": 0x41},
        ],
        "expected_alink_loads": ["LIB/RT_SID_WAVE.OBJ", "LIB/RT_SID_ON.OBJ", "LIB/RT_SID_STATE.OBJ"],
    },
    "actc_runtime_sid_on_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidWave(1,64)\rSidOn(1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_wave", "rt_sid_on", "rt_sid_state"],
        "expected_object_fragments": [
            "b p0p1u0p2u1r\n",
            "u rt_sid_wave\n",
            "u rt_sid_on\n",
            "i 1\n",
            "i 64\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901A040201C10A901203810A9A58DD003A90085028503A2024C0FCF"
            "85028403AAA5039D5710A5020A0A0A38E502186904AAA5039D00D460"
            "8502AABD571009019D57108503A5020A0A0A38E502186904AAA5039D00D460"
            "000000"
        ),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x41,
        "extra_store_checks": [
            {"addr": 0x1058, "value": 0x41},
        ],
        "expected_alink_loads": ["LIB/RT_SID_WAVE.OBJ", "LIB/RT_SID_ON.OBJ", "LIB/RT_SID_STATE.OBJ"],
    },
    "actc_runtime_variable_sid_on_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE VOICE\r"
            "PROC MAIN()\r"
            "VOICE=1\r"
            "SidOn(VOICE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_on",
            "rt_sid_state",
            "rt_sid_off",
            "rt_sid_wave",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sid_on\n",
            "i 1\n",
            "v voice 0\n",
        ],
        "expected_tail": _actc_variable_sid_on_runtime_tail(),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x01,
        "extra_store_checks": [
            {"addr": 0x1037, "value": 0x01},
        ],
        "expected_alink_loads": ["LIB/RT_SID_ON.OBJ", "LIB/RT_SID_STATE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_OFF.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
        ],
    },
    "runtime_sid_off_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 33\n"
            "b u0u1u2M\n"
            "u rt_sid_wave\n"
            "u rt_sid_on\n"
            "u rt_sid_off\n"
            "m A9 01 A0 40 20 00 00 A9 01 20 00 00 A9 01 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "r 10 u1\n"
            "r 15 u2\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_wave", "rt_sid_on", "rt_sid_off", "rt_sid_state"],
        "expected_tail": bytes.fromhex(
            "A901A040202110A901203D10A901205C10A9A58DD003A90085028503A2024C0FCF"
            "85028403AAA5039D7B10A5020A0A0A38E502186904AAA5039D00D460"
            "8502AABD7B1009019D7B108503A5020A0A0A38E502186904AAA5039D00D460"
            "8502AABD7B1029FE9D7B108503A5020A0A0A38E502186904AAA5039D00D460"
            "000000"
        ),
        "store_check_addr": 0x107C,
        "store_check_value": 0x40,
        "expected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_ON.OBJ",
            "LIB/RT_SID_OFF.OBJ",
            "LIB/RT_SID_STATE.OBJ",
        ],
    },
    "actc_runtime_sid_off_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidWave(1,64)\rSidOn(1)\rSidOff(1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_wave", "rt_sid_on", "rt_sid_off", "rt_sid_state"],
        "expected_object_fragments": [
            "b p0p1u0p2u1p3u2r\n",
            "u rt_sid_wave\n",
            "u rt_sid_on\n",
            "u rt_sid_off\n",
            "i 1\n",
            "i 64\n",
        ],
        "expected_tail": bytes.fromhex(
            "A901A040202110A901203D10A901205C10A9A58DD003A90085028503A2024C0FCF"
            "85028403AAA5039D7B10A5020A0A0A38E502186904AAA5039D00D460"
            "8502AABD7B1009019D7B108503A5020A0A0A38E502186904AAA5039D00D460"
            "8502AABD7B1029FE9D7B108503A5020A0A0A38E502186904AAA5039D00D460"
            "000000"
        ),
        "store_check_addr": 0x107C,
        "store_check_value": 0x40,
        "expected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_ON.OBJ",
            "LIB/RT_SID_OFF.OBJ",
            "LIB/RT_SID_STATE.OBJ",
        ],
    },
    "actc_runtime_variable_sid_off_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE VOICE\r"
            "PROC MAIN()\r"
            "VOICE=1\r"
            "SidOff(VOICE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_off",
            "rt_sid_state",
            "rt_sid_on",
            "rt_sid_wave",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sid_off\n",
            "i 1\n",
            "v voice 0\n",
        ],
        "expected_tail": _actc_variable_sid_off_runtime_tail(),
        "store_check_addr": 0x1037,
        "store_check_value": 0x00,
        "expected_alink_loads": ["LIB/RT_SID_OFF.OBJ", "LIB/RT_SID_STATE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_ON.OBJ",
            "LIB/RT_SID_WAVE.OBJ",
        ],
    },
    "runtime_sid_rst_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 36\n"
            "b u0u1M\n"
            "u rt_sid_rst\n"
            "u rt_sid_state\n"
            "m A9 FF 8D 0B D4 A9 0A 8D 18 D4 A2 01 A9 55 9D 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 15 u1\n"
            "r 18 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_rst",
            "rt_sid_state",
            "rt_sid_filter_state",
            "rt_sid_volume_state",
        ],
        "expected_tail": bytes.fromhex(
            "A9FF8D0BD4A90A8D18D4A201A9559D3D10202410A9A58DD003A90085028503A2024C0FCF"
            "A900A2189D00D4CA10FAA2029D3D10CA10FA8D40108D411060"
            "0000000000"
        ),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0xD418,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x103E, "value": 0x00},
            {"addr": 0x1040, "value": 0x00},
            {"addr": 0x1041, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_RST.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SID_FILTER_STATE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
    },
    "actc_runtime_sid_rst_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidRst()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_rst",
            "rt_sid_state",
            "rt_sid_filter_state",
            "rt_sid_volume_state",
        ],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_sid_rst\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "A900A2189D00D4CA10FAA2029D2C10CA10FA8D2F108D301060"
            "0000000000"
        ),
        "store_check_addr": 0xD40B,
        "store_check_value": 0x00,
        "store_check_hi_addr": 0xD418,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x102D, "value": 0x00},
            {"addr": 0x102F, "value": 0x00},
            {"addr": 0x1030, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_RST.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SID_FILTER_STATE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
    },
    "runtime_sid_route_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 21\n"
            "b u0M\n"
            "u rt_sid_route\n"
            "m A9 07 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 3 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_route", "rt_sid_filter_state"],
        "expected_tail": bytes.fromhex(
            "A907201510A9A58DD003A90085028503A2024C0FCF"
            "8502AD2B1029F08503A502290F05038D2B108D17D460"
            "00"
        ),
        "store_check_addr": 0xD417,
        "store_check_value": 0x07,
        "extra_store_checks": [
            {"addr": 0x102B, "value": 0x07},
        ],
        "expected_alink_loads": ["LIB/RT_SID_ROUTE.OBJ", "LIB/RT_SID_FILTER_STATE.OBJ"],
    },
    "actc_runtime_sid_route_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidRoute(7)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_route", "rt_sid_filter_state"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_sid_route\n",
            "i 7\n",
        ],
        "expected_tail": bytes.fromhex(
            "A907201510A9A58DD003A90085028503A2024C0FCF"
            "8502AD2B1029F08503A502290F05038D2B108D17D460"
            "00"
        ),
        "store_check_addr": 0xD417,
        "store_check_value": 0x07,
        "extra_store_checks": [
            {"addr": 0x102B, "value": 0x07},
        ],
        "expected_alink_loads": ["LIB/RT_SID_ROUTE.OBJ", "LIB/RT_SID_FILTER_STATE.OBJ"],
    },
    "actc_runtime_variable_sid_route_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE ROUTE\r"
            "PROC MAIN()\r"
            "ROUTE=7\r"
            "SidRoute(ROUTE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_route",
            "rt_sid_filter_state",
            "rt_sid_res",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sid_route\n",
            "i 7\n",
            "v route 0\n",
        ],
        "expected_tail": _actc_variable_sid_route_runtime_tail(),
        "store_check_addr": 0xD417,
        "store_check_value": 0x07,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0x102D, "value": 0x07},
        ],
        "expected_alink_loads": ["LIB/RT_SID_ROUTE.OBJ", "LIB/RT_SID_FILTER_STATE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_RES.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "runtime_sid_res_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 26\n"
            "b u0u1M\n"
            "u rt_sid_route\n"
            "u rt_sid_res\n"
            "m A9 07 20 00 00 A9 0A 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 3 u0\n"
            "r 8 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_route", "rt_sid_res", "rt_sid_filter_state"],
        "expected_tail": bytes.fromhex(
            "A907201A10A90A203010A9A58DD003A90085028503A2024C0FCF"
            "8502AD481029F08503A502290F05038D48108D17D460"
            "8502AD4810290F8503A5020A0A0A0A05038D48108D17D460"
            "00"
        ),
        "store_check_addr": 0xD417,
        "store_check_value": 0xA7,
        "extra_store_checks": [
            {"addr": 0x1048, "value": 0xA7},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_ROUTE.OBJ",
            "LIB/RT_SID_RES.OBJ",
            "LIB/RT_SID_FILTER_STATE.OBJ",
        ],
    },
    "actc_runtime_sid_res_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidRes(10)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_res", "rt_sid_filter_state"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_sid_res\n",
            "i 10\n",
        ],
        "expected_tail": bytes.fromhex(
            "A90A201510A9A58DD003A90085028503A2024C0FCF"
            "8502AD2D10290F8503A5020A0A0A0A05038D2D108D17D460"
            "00"
        ),
        "store_check_addr": 0xD417,
        "store_check_value": 0xA0,
        "extra_store_checks": [
            {"addr": 0x102D, "value": 0xA0},
        ],
        "expected_alink_loads": ["LIB/RT_SID_RES.OBJ", "LIB/RT_SID_FILTER_STATE.OBJ"],
    },
    "actc_runtime_variable_sid_res_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE AMT\r"
            "PROC MAIN()\r"
            "AMT=10\r"
            "SidRes(AMT)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_res",
            "rt_sid_filter_state",
            "rt_sid_route",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sid_res\n",
            "i 10\n",
            "v amt 0\n",
        ],
        "expected_tail": _actc_variable_sid_res_runtime_tail(),
        "store_check_addr": 0xD417,
        "store_check_value": 0xA0,
        "store_check_mask": 0xF0,
        "extra_store_checks": [
            {"addr": 0x102F, "value": 0xA0},
        ],
        "expected_alink_loads": ["LIB/RT_SID_RES.OBJ", "LIB/RT_SID_FILTER_STATE.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_ROUTE.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "runtime_sid_cutoff_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "b u0M\n"
            "u rt_sid_cutoff\n"
            "m A2 34 A0 12 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_cutoff"],
        "expected_tail": bytes.fromhex(
            "A234A012201710A9A58DD003A90085028503A2024C0FCF"
            "8A29078D15D48A4A4A4A85029829070A0A0A0A0A05028D16D460"
        ),
        "store_check_addr": 0xD415,
        "store_check_value": 0x04,
        "store_check_mask": 0x07,
        "store_check_hi_addr": 0xD416,
        "store_check_hi_value": 0x46,
        "expected_alink_loads": ["LIB/RT_SID_CUTOFF.OBJ"],
    },
    "actc_runtime_sid_cutoff_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidCutoff(4660)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_cutoff"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_sid_cutoff\n",
            "i 4660\n",
        ],
        "expected_tail": bytes.fromhex(
            "A234A012201710A9A58DD003A90085028503A2024C0FCF"
            "8A29078D15D48A4A4A4A85029829070A0A0A0A0A05028D16D460"
        ),
        "store_check_addr": 0xD415,
        "store_check_value": 0x04,
        "store_check_mask": 0x07,
        "store_check_hi_addr": 0xD416,
        "store_check_hi_value": 0x46,
        "expected_alink_loads": ["LIB/RT_SID_CUTOFF.OBJ"],
    },
    "actc_runtime_variable_sid_cutoff_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD CUTOFF\r"
            "PROC MAIN()\r"
            "CUTOFF=4660\r"
            "SidCutoff(CUTOFF)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_cutoff",
            "rt_sid_res",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sid_cutoff\n",
            "i 4660\n",
            "v cutoff 0\n",
        ],
        "expected_tail": _actc_variable_sid_cutoff_runtime_tail(),
        "store_check_addr": 0xD415,
        "store_check_value": 0x04,
        "store_check_mask": 0x07,
        "store_check_hi_addr": 0xD416,
        "store_check_hi_value": 0x46,
        "expected_alink_loads": ["LIB/RT_SID_CUTOFF.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SID_RES.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "runtime_sid_readback_helpers_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u rt_sid_osc3\n"
            "u rt_sid_env3\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_osc3", "rt_sid_env3"],
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF"
            "AD1BD460AD1CD460"
        ),
        "expected_alink_loads": ["LIB/RT_SID_OSC3.OBJ", "LIB/RT_SID_ENV3.OBJ"],
    },
    "actc_runtime_sid_osc3_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidOsc3()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_osc3"],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_sid_osc3\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD1BD460"
        ),
        "expected_alink_loads": ["LIB/RT_SID_OSC3.OBJ"],
    },
    "actc_runtime_sid_osc3_readback_store_linked": {
        "source": "MODULE MAIN\rCARD X\rPROC MAIN()\rX=SidOsc3()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_osc3", "rt_sid_env3"],
        "expected_object_fragments": [
            "b u0S0r\n",
            "u rt_sid_osc3\n",
            "v x 0\n",
        ],
        "expected_tail": _actc_byte_readback_store_tail("rt_sid_osc3"),
        "store_check_hi_addr": 0x101C,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_SID_OSC3.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SID_ENV3.OBJ"],
    },
    "actc_runtime_sid_osc3_byte_readback_store_linked": {
        "source": "MODULE MAIN\rBYTE B\rPROC MAIN()\rB=SidOsc3()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_osc3", "rt_sid_env3"],
        "expected_object_fragments": [
            "b u0S0r\n",
            "u rt_sid_osc3\n",
            "v b 0\n",
        ],
        "expected_tail": _actc_byte_readback_store_tail("rt_sid_osc3"),
        "store_check_hi_addr": 0x101C,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_SID_OSC3.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SID_ENV3.OBJ"],
    },
    "actc_runtime_sid_env3_readback_store_linked": {
        "source": "MODULE MAIN\rCARD X\rPROC MAIN()\rX=SidEnv3()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_env3", "rt_sid_osc3"],
        "expected_object_fragments": [
            "b u0S0r\n",
            "u rt_sid_env3\n",
            "v x 0\n",
        ],
        "expected_tail": _actc_byte_readback_store_tail("rt_sid_env3"),
        "store_check_hi_addr": 0x101C,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_SID_ENV3.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SID_OSC3.OBJ"],
    },
    "actc_runtime_multi_readback_store_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=SidOsc3()\r"
            "Y=SidEnv3()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_osc3", "rt_sid_env3", "rt_sprite_hit"],
        "expected_object_fragments": [
            "b u0S0u1S1r\n",
            "u rt_sid_osc3\n",
            "u rt_sid_env3\n",
            "v x 0\n",
            "v y 0\n",
        ],
        "expected_tail": _actc_byte_readback_multi_store_tail(["rt_sid_osc3", "rt_sid_env3"]),
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1029, "value": 0x00},
        ],
        "expected_alink_loads": ["LIB/RT_SID_OSC3.OBJ", "LIB/RT_SID_ENV3.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SPRITE_HIT.OBJ"],
    },
    "actc_runtime_readback_store_copy_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD X\r"
            "CARD Y\r"
            "PROC MAIN()\r"
            "X=SidOsc3()\r"
            "Y=X\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_osc3", "rt_sid_env3"],
        "expected_object_fragments": [
            "b u0S0L0S1r\n",
            "u rt_sid_osc3\n",
            "v x 0\n",
            "v y 0\n",
        ],
        "expected_tail": _actc_byte_readback_store_copy_tail("rt_sid_osc3"),
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1029, "value": 0x00},
        ],
        "expected_alink_loads": ["LIB/RT_SID_OSC3.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SID_ENV3.OBJ"],
    },
    "actc_runtime_byte_readback_store_copy_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE B\r"
            "BYTE C\r"
            "PROC MAIN()\r"
            "B=SidOsc3()\r"
            "C=B\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_osc3", "rt_sid_env3"],
        "expected_object_fragments": [
            "b u0S0L0S1r\n",
            "u rt_sid_osc3\n",
            "v b 0\n",
            "v c 0\n",
        ],
        "expected_tail": _actc_byte_readback_store_copy_tail("rt_sid_osc3"),
        "store_check_hi_addr": 0x1027,
        "store_check_hi_value": 0x00,
        "extra_store_checks": [
            {"addr": 0x1029, "value": 0x00},
        ],
        "expected_alink_loads": ["LIB/RT_SID_OSC3.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SID_ENV3.OBJ"],
    },
    "actc_runtime_sid_env3_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSidEnv3()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sid_env3"],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_sid_env3\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD1CD460"
        ),
        "expected_alink_loads": ["LIB/RT_SID_ENV3.OBJ"],
    },
    "runtime_sprite_collision_helpers_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u rt_sprite_hit\n"
            "u rt_sprite_hit_bg\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_hit", "rt_sprite_hit_bg"],
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF"
            "AD1ED060AD1FD060"
        ),
        "expected_alink_loads": [
            "LIB/RT_SPRITE_HIT.OBJ",
            "LIB/RT_SPRITE_HIT_BG.OBJ",
        ],
    },
    "actc_runtime_sprite_hit_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteHit()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_hit"],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_sprite_hit\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD1ED060"
        ),
        "expected_alink_loads": ["LIB/RT_SPRITE_HIT.OBJ"],
    },
    "actc_runtime_sprite_hit_readback_store_linked": {
        "source": "MODULE MAIN\rCARD X\rPROC MAIN()\rX=SpriteHit()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_hit", "rt_sprite_hit_bg"],
        "expected_object_fragments": [
            "b u0S0r\n",
            "u rt_sprite_hit\n",
            "v x 0\n",
        ],
        "expected_tail": _actc_byte_readback_store_tail("rt_sprite_hit"),
        "store_check_hi_addr": 0x101C,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_SPRITE_HIT.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SPRITE_HIT_BG.OBJ"],
    },
    "actc_runtime_sprite_hit_bg_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteHitBg()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_hit_bg"],
        "expected_object_fragments": [
            "b u0M\n",
            "u rt_sprite_hit_bg\n",
        ],
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF"
            "AD1FD060"
        ),
        "expected_alink_loads": ["LIB/RT_SPRITE_HIT_BG.OBJ"],
    },
    "actc_runtime_sprite_hit_bg_readback_store_linked": {
        "source": "MODULE MAIN\rCARD X\rPROC MAIN()\rX=SpriteHitBg()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_hit_bg", "rt_sprite_hit"],
        "expected_object_fragments": [
            "b u0S0r\n",
            "u rt_sprite_hit_bg\n",
            "v x 0\n",
        ],
        "expected_tail": _actc_byte_readback_store_tail("rt_sprite_hit_bg"),
        "store_check_hi_addr": 0x101C,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/RT_SPRITE_HIT_BG.OBJ"],
        "unexpected_alink_loads": ["LIB/RT_SPRITE_HIT.OBJ"],
    },
    "runtime_sprite_off_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 26\n"
            "b u0M\n"
            "u rt_sprite_off\n"
            "m A9 FF 8D 15 D0 A9 02 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 8 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_off"],
        "expected_tail": bytes.fromhex(
            "A9FF8D15D0A902201A10A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FC49FF2D15D08D15D060"
        ),
        "store_check_addr": 0xD015,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_OFF.OBJ"],
    },
    "actc_runtime_sprite_off_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteOff(2)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_off"],
        "expected_object_fragments": [
            "b p0u0r\n",
            "u rt_sprite_off\n",
            "i 2\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902201510A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FC49FF2D15D08D15D060"
        ),
        "store_check_addr": 0xD015,
        "store_check_value": 0x00,
        "expected_alink_loads": ["LIB/RT_SPRITE_OFF.OBJ"],
    },
    "actc_runtime_variable_sprite_off_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "SpriteOff(SPRITE)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_off",
            "rt_sprite_on",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "b p0S0L0u0r\n",
            "u rt_sprite_off\n",
            "i 2\n",
            "v sprite 0\n",
        ],
        "expected_tail": _actc_variable_sprite_off_runtime_tail(),
        "pre_run_memory": [{"addr": 0xD015, "value": 0xFF}],
        "store_check_addr": 0xD015,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_OFF.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_ON.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "runtime_sprite_color_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "b u0M\n"
            "u rt_sprite_color\n"
            "m A2 02 A9 06 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_color"],
        "expected_tail": bytes.fromhex(
            "A202A906201710A9A58DD003A90085028503A2024C0FCF9D27D060"
        ),
        "store_check_addr": 0xD029,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_SPRITE_COLOR.OBJ"],
    },
    "actc_runtime_sprite_color_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteColor(2,6)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_color"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_color\n",
            "i 2\n",
            "i 6\n",
        ],
        "expected_tail": bytes.fromhex(
            "A202A906201710A9A58DD003A90085028503A2024C0FCF9D27D060"
        ),
        "store_check_addr": 0xD029,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_SPRITE_COLOR.OBJ"],
    },
    "actc_runtime_variable_sprite_color_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE COLOR\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "COLOR=6\r"
            "SpriteColor(SPRITE,COLOR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_color",
            "rt_sprite_pos",
            "rt_gfx_bgcolor",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_color\n",
            "i 2\n",
            "i 6\n",
            "v sprite 0\n",
            "v color 0\n",
        ],
        "expected_tail": _actc_variable_sprite_color_runtime_tail(),
        "store_check_addr": 0xD029,
        "store_check_value": 0x06,
        "store_check_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_SPRITE_COLOR.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_POS.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
    },
    "actc_runtime_variable_sprite_reassigned_color_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE COLOR\r"
            "PROC MAIN()\r"
            "COLOR=2\r"
            "BgColor(COLOR)\r"
            "COLOR=6\r"
            "SpriteColor(2,COLOR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_color",
            "rt_gfx_bgcolor",
            "rt_sprite_pos",
        ],
        "expected_object_fragments": [
            "u rt_gfx_bgcolor\n",
            "u rt_sprite_color\n",
            "i 2\n",
            "i 6\n",
            "v color 0\n",
        ],
        "expected_tail": _actc_variable_sprite_reassigned_color_runtime_tail(),
        "store_check_addr": 0xD021,
        "store_check_value": 0x02,
        "store_check_mask": 0x0F,
        "extra_store_checks": [
            {"addr": 0xD029, "value": 0x06, "mask": 0x0F},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_POS.OBJ",
        ],
    },
    "runtime_sprite_pos_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 31\n"
            "b u0M\n"
            "u rt_sprite_pos\n"
            "m A9 00 8D 10 D0 A9 02 A2 34 A0 56 38 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 13 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_pos"],
        "expected_tail": bytes.fromhex(
            "A9008D10D0A902A234A05638201F10A9A58DD003A90085028503A2024C0FCF"
            "850286039013A901A602F0040ACAD0FC0D10D08D10D0189012"
            "A901A602F0040ACAD0FC49FF2D10D08D10D0A5020AAAA5039D00D0989D01D060"
        ),
        "store_check_addr": 0xD004,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD005,
        "store_check_hi_value": 0x56,
        "extra_store_checks": [
            {"addr": 0xD010, "value": 0x04, "mask": 0x04},
        ],
        "expected_alink_loads": ["LIB/RT_SPRITE_POS.OBJ"],
    },
    "actc_runtime_sprite_pos_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpritePos(2,308,86)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_pos"],
        "expected_object_fragments": [
            "b p0p1p2u0r\n",
            "u rt_sprite_pos\n",
            "i 2\n",
            "i 308\n",
            "i 86\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A234A05638201A10A9A58DD003A90085028503A2024C0FCF"
            "850286039013A901A602F0040ACAD0FC0D10D08D10D0189012"
            "A901A602F0040ACAD0FC49FF2D10D08D10D0A5020AAAA5039D00D0989D01D060"
        ),
        "store_check_addr": 0xD004,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD005,
        "store_check_hi_value": 0x56,
        "extra_store_checks": [
            {"addr": 0xD010, "value": 0x04, "mask": 0x04},
        ],
        "expected_alink_loads": ["LIB/RT_SPRITE_POS.OBJ"],
    },
    "actc_runtime_sprite_pos_low_x_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpritePos(2,52,86)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_pos"],
        "expected_object_fragments": [
            "b p0p1p2u0r\n",
            "u rt_sprite_pos\n",
            "i 2\n",
            "i 52\n",
            "i 86\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A234A05618201A10A9A58DD003A90085028503A2024C0FCF"
            "850286039013A901A602F0040ACAD0FC0D10D08D10D0189012"
            "A901A602F0040ACAD0FC49FF2D10D08D10D0A5020AAAA5039D00D0989D01D060"
        ),
        "pre_run_memory": [
            {"addr": 0xD010, "value": 0xFF},
        ],
        "store_check_addr": 0xD004,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD005,
        "store_check_hi_value": 0x56,
        "extra_store_checks": [
            {"addr": 0xD010, "value": 0xFB},
        ],
        "expected_alink_loads": ["LIB/RT_SPRITE_POS.OBJ"],
    },
    "actc_runtime_card_variable_sprite_pos_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD X\r"
            "BYTE Y\r"
            "PROC MAIN()\r"
            "X=308\r"
            "Y=86\r"
            "SpritePos(2,X,Y)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_pos",
            "rt_sprite_data",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1p2L0L1u0r\n",
            "u rt_sprite_pos\n",
            "i 308\n",
            "i 86\n",
            "i 2\n",
            "v x 0\n",
            "v y 0\n",
        ],
        "expected_tail": _actc_card_variable_sprite_pos_runtime_tail(),
        "store_check_addr": 0xD004,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD005,
        "store_check_hi_value": 0x56,
        "extra_store_checks": [
            {"addr": 0xD010, "value": 0x04, "mask": 0x04},
        ],
        "expected_alink_loads": ["LIB/RT_SPRITE_POS.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_DATA.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "runtime_sprite_data_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 25\n"
            "b u0M\n"
            "u rt_sprite_data\n"
            "m A9 02 A2 00 A0 20 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 7 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_data"],
        "expected_tail": bytes.fromhex(
            "A902A200A020201910A9A58DD003A90085028503A2024C0FCF"
            "48980A0A85028A4A4A4A4A4A4A0502AA68A88A99F80760"
        ),
        "store_check_addr": 0x07FA,
        "store_check_value": 0x80,
        "expected_alink_loads": ["LIB/RT_SPRITE_DATA.OBJ"],
    },
    "actc_runtime_sprite_data_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteData(2,8192)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_data"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_data\n",
            "i 2\n",
            "i 8192\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A200A020201910A9A58DD003A90085028503A2024C0FCF"
            "48980A0A85028A4A4A4A4A4A4A0502AA68A88A99F80760"
        ),
        "store_check_addr": 0x07FA,
        "store_check_value": 0x80,
        "expected_alink_loads": ["LIB/RT_SPRITE_DATA.OBJ"],
    },
    "actc_runtime_card_variable_sprite_data_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "CARD ADDR\r"
            "PROC MAIN()\r"
            "ADDR=8192\r"
            "SpriteData(2,ADDR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_data",
            "rt_sprite_ptr",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "b p0S0p1L0u0r\n",
            "u rt_sprite_data\n",
            "i 8192\n",
            "i 2\n",
            "v addr 0\n",
        ],
        "expected_tail": _actc_card_variable_sprite_data_runtime_tail(),
        "store_check_addr": 0x07FA,
        "store_check_value": 0x80,
        "expected_alink_loads": ["LIB/RT_SPRITE_DATA.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_PTR.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "runtime_sprite_ptr_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "b u0M\n"
            "u rt_sprite_ptr\n"
            "m A2 02 A9 80 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_ptr"],
        "expected_tail": bytes.fromhex(
            "A202A980201710A9A58DD003A90085028503A2024C0FCF"
            "9DF80760"
        ),
        "store_check_addr": 0x07FA,
        "store_check_value": 0x80,
        "expected_alink_loads": ["LIB/RT_SPRITE_PTR.OBJ"],
    },
    "actc_runtime_sprite_ptr_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpritePtr(2,128)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_ptr"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_ptr\n",
            "i 2\n",
            "i 128\n",
        ],
        "expected_tail": bytes.fromhex(
            "A202A980201710A9A58DD003A90085028503A2024C0FCF9DF80760"
        ),
        "store_check_addr": 0x07FA,
        "store_check_value": 0x80,
        "expected_alink_loads": ["LIB/RT_SPRITE_PTR.OBJ"],
    },
    "actc_runtime_variable_sprite_ptr_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE POINTER\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "POINTER=128\r"
            "SpritePtr(SPRITE,POINTER)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_ptr",
            "rt_sprite_data",
            "rt_sprite_color",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_ptr\n",
            "i 2\n",
            "i 128\n",
            "v sprite 0\n",
            "v pointer 0\n",
        ],
        "expected_tail": _actc_variable_sprite_ptr_runtime_tail(),
        "store_check_addr": 0x07FA,
        "store_check_value": 0x80,
        "expected_alink_loads": ["LIB/RT_SPRITE_PTR.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_DATA.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
        ],
    },
    "runtime_sprite_mc_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 28\n"
            "b u0M\n"
            "u rt_sprite_mc\n"
            "m A9 00 8D 1C D0 A0 01 A9 02 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 10 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_mc"],
        "expected_tail": bytes.fromhex(
            "A9008D1CD0A001A902201C10A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1CD08D1CD06049FF2D1CD08D1CD060"
        ),
        "store_check_addr": 0xD01C,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_MC.OBJ"],
    },
    "actc_runtime_sprite_mc_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteMC(2,1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_mc"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_mc\n",
            "i 2\n",
            "i 1\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A001201710A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1CD08D1CD06049FF2D1CD08D1CD060"
        ),
        "store_check_addr": 0xD01C,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_MC.OBJ"],
    },
    "actc_runtime_variable_sprite_mc_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE FLAG\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "FLAG=1\r"
            "SpriteMC(SPRITE,FLAG)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
            "rt_sprite_prio",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_mc\n",
            "i 2\n",
            "i 1\n",
            "v sprite 0\n",
            "v flag 0\n",
        ],
        "expected_tail": _actc_variable_sprite_mc_runtime_tail(1),
        "store_check_addr": 0xD01C,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_MC.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_sprite_mc_clear_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteMC(2,0)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_mc"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_mc\n",
            "i 2\n",
            "i 0\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A000201710A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1CD08D1CD06049FF2D1CD08D1CD060"
        ),
        "pre_run_memory": [
            {"addr": 0xD01C, "value": 0xFF},
        ],
        "store_check_addr": 0xD01C,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_MC.OBJ"],
    },
    "actc_runtime_variable_sprite_mc_clear_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE FLAG\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "FLAG=0\r"
            "SpriteMC(SPRITE,FLAG)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
            "rt_sprite_prio",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_mc\n",
            "i 2\n",
            "i 0\n",
            "v sprite 0\n",
            "v flag 0\n",
        ],
        "expected_tail": _actc_variable_sprite_mc_runtime_tail(0),
        "pre_run_memory": [
            {"addr": 0xD01C, "value": 0xFF},
        ],
        "store_check_addr": 0xD01C,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_MC.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "runtime_sprite_xexp_clear_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 28\n"
            "b u0M\n"
            "u rt_sprite_xexp\n"
            "m A9 FF 8D 1D D0 A0 00 A9 02 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 10 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_xexp"],
        "expected_tail": bytes.fromhex(
            "A9FF8D1DD0A000A902201C10A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1DD08D1DD06049FF2D1DD08D1DD060"
        ),
        "store_check_addr": 0xD01D,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_XEXP.OBJ"],
    },
    "actc_runtime_sprite_xexp_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteXExp(2,1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_xexp"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_xexp\n",
            "i 2\n",
            "i 1\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A001201710A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1DD08D1DD06049FF2D1DD08D1DD060"
        ),
        "store_check_addr": 0xD01D,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_XEXP.OBJ"],
    },
    "actc_runtime_variable_sprite_xexp_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE FLAG\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "FLAG=1\r"
            "SpriteXExp(SPRITE,FLAG)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_xexp",
            "rt_sprite_mc",
            "rt_sprite_yexp",
            "rt_sprite_prio",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_xexp\n",
            "i 2\n",
            "i 1\n",
            "v sprite 0\n",
            "v flag 0\n",
        ],
        "expected_tail": _actc_variable_sprite_xexp_runtime_tail(1),
        "store_check_addr": 0xD01D,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_XEXP.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_sprite_xexp_clear_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteXExp(2,0)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_xexp"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_xexp\n",
            "i 2\n",
            "i 0\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A000201710A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1DD08D1DD06049FF2D1DD08D1DD060"
        ),
        "pre_run_memory": [
            {"addr": 0xD01D, "value": 0xFF},
        ],
        "store_check_addr": 0xD01D,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_XEXP.OBJ"],
    },
    "actc_runtime_variable_sprite_xexp_clear_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE FLAG\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "FLAG=0\r"
            "SpriteXExp(SPRITE,FLAG)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_xexp",
            "rt_sprite_mc",
            "rt_sprite_yexp",
            "rt_sprite_prio",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_xexp\n",
            "i 2\n",
            "i 0\n",
            "v sprite 0\n",
            "v flag 0\n",
        ],
        "expected_tail": _actc_variable_sprite_xexp_runtime_tail(0),
        "pre_run_memory": [
            {"addr": 0xD01D, "value": 0xFF},
        ],
        "store_check_addr": 0xD01D,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_XEXP.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "runtime_sprite_yexp_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 28\n"
            "b u0M\n"
            "u rt_sprite_yexp\n"
            "m A9 00 8D 17 D0 A0 01 A9 02 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 10 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_yexp"],
        "expected_tail": bytes.fromhex(
            "A9008D17D0A001A902201C10A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D17D08D17D06049FF2D17D08D17D060"
        ),
        "store_check_addr": 0xD017,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_YEXP.OBJ"],
    },
    "actc_runtime_sprite_yexp_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteYExp(2,1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_yexp"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_yexp\n",
            "i 2\n",
            "i 1\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A001201710A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D17D08D17D06049FF2D17D08D17D060"
        ),
        "store_check_addr": 0xD017,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_YEXP.OBJ"],
    },
    "actc_runtime_variable_sprite_yexp_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE FLAG\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "FLAG=1\r"
            "SpriteYExp(SPRITE,FLAG)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_yexp",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_prio",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_yexp\n",
            "i 2\n",
            "i 1\n",
            "v sprite 0\n",
            "v flag 0\n",
        ],
        "expected_tail": _actc_variable_sprite_yexp_runtime_tail(1),
        "store_check_addr": 0xD017,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_YEXP.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "actc_runtime_sprite_yexp_clear_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpriteYExp(2,0)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_yexp"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_yexp\n",
            "i 2\n",
            "i 0\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A000201710A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D17D08D17D06049FF2D17D08D17D060"
        ),
        "pre_run_memory": [
            {"addr": 0xD017, "value": 0xFF},
        ],
        "store_check_addr": 0xD017,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_YEXP.OBJ"],
    },
    "actc_runtime_variable_sprite_yexp_clear_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE FLAG\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "FLAG=0\r"
            "SpriteYExp(SPRITE,FLAG)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_yexp",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_prio",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_yexp\n",
            "i 2\n",
            "i 0\n",
            "v sprite 0\n",
            "v flag 0\n",
        ],
        "expected_tail": _actc_variable_sprite_yexp_runtime_tail(0),
        "pre_run_memory": [
            {"addr": 0xD017, "value": 0xFF},
        ],
        "store_check_addr": 0xD017,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_YEXP.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
        ],
    },
    "runtime_sprite_prio_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 28\n"
            "b u0M\n"
            "u rt_sprite_prio\n"
            "m A9 00 8D 1B D0 A0 01 A9 02 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 10 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_prio"],
        "expected_tail": bytes.fromhex(
            "A9008D1BD0A001A902201C10A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1BD08D1BD06049FF2D1BD08D1BD060"
        ),
        "store_check_addr": 0xD01B,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_PRIO.OBJ"],
    },
    "actc_runtime_sprite_prio_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpritePrio(2,1)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_prio"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_prio\n",
            "i 2\n",
            "i 1\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A001201710A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1BD08D1BD06049FF2D1BD08D1BD060"
        ),
        "store_check_addr": 0xD01B,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_PRIO.OBJ"],
    },
    "actc_runtime_variable_sprite_prio_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE FLAG\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "FLAG=1\r"
            "SpritePrio(SPRITE,FLAG)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_prio",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_prio\n",
            "i 2\n",
            "i 1\n",
            "v sprite 0\n",
            "v flag 0\n",
        ],
        "expected_tail": _actc_variable_sprite_prio_runtime_tail(1),
        "store_check_addr": 0xD01B,
        "store_check_value": 0x04,
        "expected_alink_loads": ["LIB/RT_SPRITE_PRIO.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
        ],
    },
    "actc_runtime_sprite_prio_clear_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSpritePrio(2,0)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_prio"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_prio\n",
            "i 2\n",
            "i 0\n",
        ],
        "expected_tail": bytes.fromhex(
            "A902A000201710A9A58DD003A90085028503A2024C0FCF"
            "AAA901E000F0040ACAD0FCC000F0070D1BD08D1BD06049FF2D1BD08D1BD060"
        ),
        "pre_run_memory": [
            {"addr": 0xD01B, "value": 0xFF},
        ],
        "store_check_addr": 0xD01B,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_PRIO.OBJ"],
    },
    "actc_runtime_variable_sprite_prio_clear_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE SPRITE\r"
            "BYTE FLAG\r"
            "PROC MAIN()\r"
            "SPRITE=2\r"
            "FLAG=0\r"
            "SpritePrio(SPRITE,FLAG)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_prio",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_prio\n",
            "i 2\n",
            "i 0\n",
            "v sprite 0\n",
            "v flag 0\n",
        ],
        "expected_tail": _actc_variable_sprite_prio_runtime_tail(0),
        "pre_run_memory": [
            {"addr": 0xD01B, "value": 0xFF},
        ],
        "store_check_addr": 0xD01B,
        "store_check_value": 0xFB,
        "expected_alink_loads": ["LIB/RT_SPRITE_PRIO.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
        ],
    },
    "runtime_sprite_set_mc_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "b u0M\n"
            "u rt_sprite_set_mc\n"
            "m A2 0A A9 05 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_set_mc"],
        "expected_tail": bytes.fromhex(
            "A20AA905201710A9A58DD003A90085028503A2024C0FCF8D25D08E26D060"
        ),
        "store_check_addr": 0xD025,
        "store_check_value": 0x05,
        "store_check_mask": 0x0F,
        "store_check_hi_addr": 0xD026,
        "store_check_hi_value": 0x0A,
        "store_check_hi_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_SPRITE_SET_MC.OBJ"],
    },
    "actc_runtime_sprite_set_mc_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSetSpriteMC(5,10)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_set_mc"],
        "expected_object_fragments": [
            "b p0p1u0r\n",
            "u rt_sprite_set_mc\n",
            "i 5\n",
            "i 10\n",
        ],
        "expected_tail": bytes.fromhex(
            "A20AA905201710A9A58DD003A90085028503A2024C0FCF8D25D08E26D060"
        ),
        "store_check_addr": 0xD025,
        "store_check_value": 0x05,
        "store_check_mask": 0x0F,
        "store_check_hi_addr": 0xD026,
        "store_check_hi_value": 0x0A,
        "store_check_hi_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_SPRITE_SET_MC.OBJ"],
    },
    "actc_runtime_variable_sprite_set_mc_helper_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE COLOR0\r"
            "BYTE COLOR1\r"
            "PROC MAIN()\r"
            "COLOR0=5\r"
            "COLOR1=10\r"
            "SetSpriteMC(COLOR0,COLOR1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_set_mc",
            "rt_sprite_color",
            "rt_gfx_bgcolor",
        ],
        "expected_object_fragments": [
            "b p0S0p1S1L0L1u0r\n",
            "u rt_sprite_set_mc\n",
            "i 5\n",
            "i 10\n",
            "v color0 0\n",
            "v color1 0\n",
        ],
        "expected_tail": _actc_variable_sprite_set_mc_runtime_tail(),
        "store_check_addr": 0xD025,
        "store_check_value": 0x05,
        "store_check_mask": 0x0F,
        "store_check_hi_addr": 0xD026,
        "store_check_hi_value": 0x0A,
        "store_check_hi_mask": 0x0F,
        "expected_alink_loads": ["LIB/RT_SPRITE_SET_MC.OBJ"],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_COLOR.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
    },
    "actc_runtime_selective_hardware_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SpriteData(2,8192)\r"
            "SpritePos(2,308,86)\r"
            "BgColor(6)\r"
            "SidFreq(1,4660)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sprite_data",
            "rt_sprite_pos",
            "rt_gfx_bgcolor",
            "rt_sid_freq",
            "rt_sprite_on",
            "rt_sprite_ptr",
            "rt_gfx_bordercolor",
            "rt_sid_pulse",
            "rt_sid_state",
        ],
        "expected_object_fragments": [
            "b p0p1u0p2p3p4u1p5u2p6p7u3r\n",
            "u rt_sprite_data\n",
            "u rt_sprite_pos\n",
            "u rt_gfx_bgcolor\n",
            "u rt_sid_freq\n",
            "i 2\n",
            "i 8192\n",
            "i 308\n",
            "i 86\n",
            "i 6\n",
            "i 1\n",
            "i 4660\n",
        ],
        "expected_tail": _actc_selective_hardware_runtime_tail(),
        "store_check_addr": 0xD407,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD408,
        "store_check_hi_value": 0x12,
        "extra_store_checks": [
            {"addr": 0x07FA, "value": 0x80},
            {"addr": 0xD004, "value": 0x34},
            {"addr": 0xD005, "value": 0x56},
            {"addr": 0xD010, "value": 0x04, "mask": 0x04},
            {"addr": 0xD021, "value": 0x06, "mask": 0x0F},
        ],
        "expected_alink_loads": [
            "LIB/RT_SPRITE_DATA.OBJ",
            "LIB/RT_SPRITE_POS.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_ON.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
            "LIB/RT_SID_PULSE.OBJ",
            "LIB/RT_SID_STATE.OBJ",
        ],
    },
    "actc_runtime_reordered_hardware_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "BgColor(3)\r"
            "SidFreq(1,4660)\r"
            "SpriteData(2,8192)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bgcolor",
            "rt_sid_freq",
            "rt_sprite_data",
            "rt_sprite_pos",
            "rt_sprite_ptr",
            "rt_sid_pulse",
            "rt_sid_state",
        ],
        "expected_object_fragments": [
            "b p0u0p1p2u1p3p4u2r\n",
            "u rt_gfx_bgcolor\n",
            "u rt_sid_freq\n",
            "u rt_sprite_data\n",
            "i 3\n",
            "i 1\n",
            "i 4660\n",
            "i 2\n",
            "i 8192\n",
        ],
        "expected_tail": _actc_reordered_hardware_runtime_tail(),
        "store_check_addr": 0xD407,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD408,
        "store_check_hi_value": 0x12,
        "extra_store_checks": [
            {"addr": 0xD021, "value": 0x03, "mask": 0x0F},
            {"addr": 0x07FA, "value": 0x80},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_POS.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
            "LIB/RT_SID_PULSE.OBJ",
            "LIB/RT_SID_STATE.OBJ",
        ],
    },
    "actc_runtime_mixed_hardware_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "BorderColor(30)\r"
            "SidPulse(1,4660)\r"
            "SpriteColor(2,6)\r"
            "ScreenBase(1024)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bordercolor",
            "rt_sid_pulse",
            "rt_sprite_color",
            "rt_gfx_screen_base",
            "rt_gfx_bgcolor",
            "rt_sid_freq",
            "rt_sprite_ptr",
            "rt_gfx_bitmap_base",
        ],
        "expected_object_fragments": [
            "b p0u0p1p2u1p3p4u2p5u3r\n",
            "u rt_gfx_bordercolor\n",
            "u rt_sid_pulse\n",
            "u rt_sprite_color\n",
            "u rt_gfx_screen_base\n",
            "i 30\n",
            "i 1\n",
            "i 4660\n",
            "i 2\n",
            "i 6\n",
            "i 1024\n",
        ],
        "expected_tail": _actc_mixed_hardware_runtime_tail(),
        "store_check_addr": 0xD409,
        "store_check_value": 0x34,
        "store_check_hi_addr": 0xD40A,
        "store_check_hi_value": 0x02,
        "extra_store_checks": [
            {"addr": 0xD020, "value": 0x0E, "mask": 0x0F},
            {"addr": 0xD029, "value": 0x06, "mask": 0x0F},
            {"addr": 0xD018, "value": 0x10, "mask": 0xF0},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_BORDERCOLOR.OBJ",
            "LIB/RT_SID_PULSE.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
            "LIB/RT_GFX_SCREEN_BASE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BGCOLOR.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
            "LIB/RT_GFX_BITMAP_BASE.OBJ",
        ],
    },
    "actc_runtime_variable_mixed_gfx_sprite_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "BYTE X\r"
            "BYTE Y\r"
            "BYTE CH\r"
            "BYTE SPRITE\r"
            "BYTE POINTER\r"
            "BYTE COLOR\r"
            "PROC MAIN()\r"
            "X=5\r"
            "Y=2\r"
            "CH=65\r"
            "SPRITE=2\r"
            "POINTER=128\r"
            "COLOR=60\r"
            "ScreenCell(X,Y,CH)\r"
            "SpritePtr(SPRITE,POINTER)\r"
            "BitmapFill(COLOR)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_screen_cell",
            "rt_sprite_ptr",
            "rt_gfx_bitmap_fill",
            "rt_gfx_color_cell",
            "rt_sprite_data",
            "rt_gfx_bitmap_copy",
        ],
        "expected_object_fragments": [
            "u rt_gfx_screen_cell\n",
            "u rt_sprite_ptr\n",
            "u rt_gfx_bitmap_fill\n",
            "i 5\n",
            "i 2\n",
            "i 65\n",
            "i 128\n",
            "i 60\n",
            "v x 0\n",
            "v y 0\n",
            "v ch 0\n",
            "v sprite 0\n",
            "v pointer 0\n",
            "v color 0\n",
        ],
        "expected_tail": _actc_variable_mixed_gfx_sprite_runtime_tail(),
        "store_check_addr": 0x0455,
        "store_check_value": 0x41,
        "extra_store_checks": [
            {"addr": 0x07FA, "value": 0x80},
            {"addr": 0x2000, "value": 0x3C},
            {"addr": 0x3F3F, "value": 0x3C},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": [
            "LIB/RT_GFX_SCREEN_CELL.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_COLOR_CELL.OBJ",
            "LIB/RT_SPRITE_DATA.OBJ",
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
        ],
    },
    "actc_runtime_no_arg_hardware_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidRst()\r"
            "BitmapOn()\r"
            "MBitmapOn()\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_rst",
            "rt_gfx_bitmap_on",
            "rt_gfx_mbitmap_on",
            "rt_sid_state",
            "rt_sid_filter_state",
            "rt_sid_volume_state",
            "rt_gfx_bitmap_off",
            "rt_sid_osc3",
        ],
        "expected_object_fragments": [
            "b u0u1u2M\n",
            "u rt_sid_rst\n",
            "u rt_gfx_bitmap_on\n",
            "u rt_gfx_mbitmap_on\n",
        ],
        "expected_tail": _actc_no_arg_hardware_runtime_tail(),
        "store_check_addr": 0xD011,
        "store_check_value": 0x20,
        "store_check_mask": 0x20,
        "store_check_hi_addr": 0xD016,
        "store_check_hi_value": 0x10,
        "store_check_hi_mask": 0x10,
        "extra_store_checks": [
            {"addr": 0xD418, "value": 0x00},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_RST.OBJ",
            "LIB/RT_GFX_BITMAP_ON.OBJ",
            "LIB/RT_GFX_MBITMAP_ON.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SID_FILTER_STATE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_OFF.OBJ",
            "LIB/RT_SID_OSC3.OBJ",
        ],
    },
    "actc_runtime_stateful_byte_hardware_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "SidWave(1,64)\r"
            "SidAD(1,151)\r"
            "SidSR(1,248)\r"
            "SidOn(1)\r"
            "SidOff(1)\r"
            "SidVol(10)\r"
            "SidMode(48)\r"
            "SidRoute(7)\r"
            "SidRes(10)\r"
            "SpriteOn(2)\r"
            "SpriteOff(2)\r"
            "VicBank(1)\r"
            "SpriteMC(2,1)\r"
            "SpriteXExp(2,1)\r"
            "SpriteYExp(2,1)\r"
            "SpritePrio(2,1)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_sid_wave",
            "rt_sid_ad",
            "rt_sid_sr",
            "rt_sid_on",
            "rt_sid_off",
            "rt_sid_vol",
            "rt_sid_mode",
            "rt_sid_route",
            "rt_sid_res",
            "rt_sprite_on",
            "rt_sprite_off",
            "rt_gfx_vic_bank",
            "rt_sprite_mc",
            "rt_sprite_xexp",
            "rt_sprite_yexp",
            "rt_sprite_prio",
            "rt_sid_state",
            "rt_sid_volume_state",
            "rt_sid_filter_state",
            "rt_sid_pulse",
            "rt_sprite_color",
            "rt_gfx_bgcolor",
        ],
        "expected_object_fragments": [
            "u rt_sid_wave\n",
            "u rt_sid_ad\n",
            "u rt_sid_sr\n",
            "u rt_sid_on\n",
            "u rt_sid_off\n",
            "u rt_sid_vol\n",
            "u rt_sid_mode\n",
            "u rt_sid_route\n",
            "u rt_sid_res\n",
            "u rt_sprite_on\n",
            "u rt_sprite_off\n",
            "u rt_gfx_vic_bank\n",
            "u rt_sprite_mc\n",
            "u rt_sprite_xexp\n",
            "u rt_sprite_yexp\n",
            "u rt_sprite_prio\n",
            "i 151\n",
            "i 248\n",
        ],
        "expected_tail": _actc_stateful_byte_hardware_runtime_tail(),
        "pre_run_memory": [
            {"addr": 0xD015, "value": 0xFF},
        ],
        "store_check_addr": 0xD417,
        "store_check_value": 0xA7,
        "extra_store_checks": [
            {"addr": 0xD418, "value": 0x3A},
            {"addr": 0xD015, "value": 0xFB},
            {"addr": 0xD01C, "value": 0x04, "mask": 0x04},
            {"addr": 0xD01D, "value": 0x04, "mask": 0x04},
            {"addr": 0xD017, "value": 0x04, "mask": 0x04},
            {"addr": 0xD01B, "value": 0x04, "mask": 0x04},
            {"addr": 0xDD00, "value": 0x02, "mask": 0x03},
            {"addr": 0xDD02, "value": 0x03, "mask": 0x03},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_AD.OBJ",
            "LIB/RT_SID_SR.OBJ",
            "LIB/RT_SID_ON.OBJ",
            "LIB/RT_SID_OFF.OBJ",
            "LIB/RT_SID_VOL.OBJ",
            "LIB/RT_SID_MODE.OBJ",
            "LIB/RT_SID_ROUTE.OBJ",
            "LIB/RT_SID_RES.OBJ",
            "LIB/RT_SPRITE_ON.OBJ",
            "LIB/RT_SPRITE_OFF.OBJ",
            "LIB/RT_GFX_VIC_BANK.OBJ",
            "LIB/RT_SPRITE_MC.OBJ",
            "LIB/RT_SPRITE_XEXP.OBJ",
            "LIB/RT_SPRITE_YEXP.OBJ",
            "LIB/RT_SPRITE_PRIO.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
            "LIB/RT_SID_FILTER_STATE.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_SID_PULSE.OBJ",
            "LIB/RT_SPRITE_COLOR.OBJ",
            "LIB/RT_GFX_BGCOLOR.OBJ",
        ],
    },
    "actc_runtime_word_copy_fill_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "BitmapFill(170)\r"
            "ScreenCopy(8192)\r"
            "ColorCopy(8192)\r"
            "BitmapCopy(8192)\r"
            "SidCutoff(4660)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_fill",
            "rt_gfx_screen_copy",
            "rt_gfx_color_copy",
            "rt_gfx_bitmap_copy",
            "rt_sid_cutoff",
            "rt_gfx_bitmap_on",
            "rt_sid_freq",
        ],
        "expected_object_fragments": [
            "u rt_gfx_bitmap_fill\n",
            "u rt_gfx_screen_copy\n",
            "u rt_gfx_color_copy\n",
            "u rt_gfx_bitmap_copy\n",
            "u rt_sid_cutoff\n",
            "i 170\n",
            "i 8192\n",
            "i 4660\n",
        ],
        "expected_tail": _actc_word_copy_fill_runtime_tail(),
        "store_check_addr": 0x2000,
        "store_check_value": 0xAA,
        "extra_store_checks": [
            {"addr": 0x3F3F, "value": 0xAA},
            {"addr": 0x0400, "value": 0xAA},
            {"addr": 0xD800, "value": 0x0A, "mask": 0x0F},
            {"addr": 0xD415, "value": 0x04},
            {"addr": 0xD416, "value": 0x46},
        ],
        "spin_after_marker_for_live": True,
        "expected_alink_loads": [
            "LIB/RT_GFX_BITMAP_FILL.OBJ",
            "LIB/RT_GFX_SCREEN_COPY.OBJ",
            "LIB/RT_GFX_COLOR_COPY.OBJ",
            "LIB/RT_GFX_BITMAP_COPY.OBJ",
            "LIB/RT_SID_CUTOFF.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_ON.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
        ],
    },
    "actc_runtime_remaining_hardware_helpers_linked": {
        "source": (
            "MODULE MAIN\r"
            "PROC MAIN()\r"
            "BitmapBase(8192)\r"
            "BitmapOff()\r"
            "SidOsc3()\r"
            "SidEnv3()\r"
            "SpriteHit()\r"
            "SpriteHitBg()\r"
            "SpritePtr(2,128)\r"
            "SetSpriteMC(5,10)\r"
            "RETURN\r"
        ),
        "has_stub": False,
        "runtime_library_objects": [
            "rt_gfx_bitmap_base",
            "rt_gfx_bitmap_off",
            "rt_sid_osc3",
            "rt_sid_env3",
            "rt_sprite_hit",
            "rt_sprite_hit_bg",
            "rt_sprite_ptr",
            "rt_sprite_set_mc",
            "rt_gfx_bitmap_on",
            "rt_sid_state",
            "rt_sprite_on",
        ],
        "expected_object_fragments": [
            "u rt_gfx_bitmap_base\n",
            "u rt_gfx_bitmap_off\n",
            "u rt_sid_osc3\n",
            "u rt_sid_env3\n",
            "u rt_sprite_hit\n",
            "u rt_sprite_hit_bg\n",
            "u rt_sprite_ptr\n",
            "u rt_sprite_set_mc\n",
            "i 8192\n",
            "i 2\n",
            "i 128\n",
            "i 5\n",
            "i 10\n",
        ],
        "expected_tail": _actc_remaining_hardware_runtime_tail(),
        "pre_run_memory": [
            {"addr": 0xD011, "value": 0x20},
        ],
        "store_check_addr": 0xD018,
        "store_check_value": 0x08,
        "store_check_mask": 0x08,
        "extra_store_checks": [
            {"addr": 0xD011, "value": 0x00, "mask": 0x20},
            {"addr": 0x07FA, "value": 0x80},
            {"addr": 0xD025, "value": 0x05, "mask": 0x0F},
            {"addr": 0xD026, "value": 0x0A, "mask": 0x0F},
        ],
        "expected_alink_loads": [
            "LIB/RT_GFX_BITMAP_BASE.OBJ",
            "LIB/RT_GFX_BITMAP_OFF.OBJ",
            "LIB/RT_SID_OSC3.OBJ",
            "LIB/RT_SID_ENV3.OBJ",
            "LIB/RT_SPRITE_HIT.OBJ",
            "LIB/RT_SPRITE_HIT_BG.OBJ",
            "LIB/RT_SPRITE_PTR.OBJ",
            "LIB/RT_SPRITE_SET_MC.OBJ",
        ],
        "unexpected_alink_loads": [
            "LIB/RT_GFX_BITMAP_ON.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SPRITE_ON.OBJ",
        ],
    },
    "empty_return": {
        "seed_object": "OBJ1\nx main 0 1\nb r\nn main\n",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
    },
    "actc_object_code_empty_return": {
        "source": "MODULE MAIN\rPROC MAIN()\rRETURN\r",
        "has_stub": False,
        "expected_object_fragments": [
            "x main 0 16\n",
            "b M\n",
            "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
        ],
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
    },
    "actc_empty_ignores_available_runtime_libs": {
        "source": "MODULE MAIN\rPROC MAIN()\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sprite_on", "rt_sid_freq", "rt_sid_state"],
        "expected_object_fragments": [
            "x main 0 16\n",
            "b M\n",
            "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n",
        ],
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
        "unexpected_alink_loads": [
            "LIB/RT_SPRITE_ON.OBJ",
            "LIB/RT_SID_FREQ.OBJ",
            "LIB/RT_SID_STATE.OBJ",
        ],
    },
    "object_code_return": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 16\n"
            "b M\n"
            "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "n main\n"
        ),
        "has_stub": False,
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
    },
    "object_code_split_machine_records": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 16\n"
            "b M\n"
            "m A9 A5 8D D0 03 A9 00 85\n"
            "m 02 85 03 A2 02 4C 0F CF\n"
            "n main\n"
        ),
        "has_stub": False,
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
    },
    "object_code_split_dependency_machine_records": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b u0M\n"
                "u b\n"
                "m 20 00\n"
                "m 00 60\n"
                "r 1 u0\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_named_symbol_relocations": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 23\n"
            "x local 22 1\n"
            "b u0M\n"
            "b M\n"
            "u helper\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 1 x local\n"
            "r 4 x helper\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "object_code_named_symbol_relocation_import_closure": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b M\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 x helper\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "object_code_named_symbol_dependency_import_closure": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb M\nm 20 00 00 60\nr 1 x b\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_named_symbol_dependency_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 5\n"
                "x b 4 1\n"
                "b M\n"
                "b M\n"
                "m 20 00 00 60 60\n"
                "r 1 x b\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ"],
        "unexpected_alink_loads": ["LIB/B.OBJ"],
    },
    "object_code_local_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 20\n"
            "x a 19 1\n"
            "b M\n"
            "b M\n"
            "m 20 13 10 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "n main\n"
        ),
        "has_stub": False,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
    },
    "object_code_external_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u helper\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "object_code_offset_external_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 3 19\n"
            "b u0M\n"
            "u helper\n"
            "m EA EA EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 4 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "object_code_root_unused_import_ignored": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 16\n"
            "b M\n"
            "u missing\n"
            "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "n main\n"
        ),
        "has_stub": False,
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_root_unused_export_import_ignored": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 16\n"
            "x unused 16 4\n"
            "b M\n"
            "b u0M\n"
            "u missing\n"
            "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 20 00 00 60\n"
            "r 17 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_root_second_export_selected": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 16\n"
            "b u0M\n"
            "b M\n"
            "u missing\n"
            "m 20 00 00 60 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "expected_tail": bytes.fromhex("A9A58DD003A90085028503A2024C0FCF"),
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_root_second_export_import": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 19\n"
            "b M\n"
            "b u0M\n"
            "u helper\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "object_code_root_second_export_named_symbol_import": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 19\n"
            "b u0M\n"
            "b M\n"
            "u missing\n"
            "m 20 00 00 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 5 x helper\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_root_second_export_transitive_library_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_root_second_export_transitive_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_root_second_export_project_second_export_library_tail": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 19\n"
            "b u0M\n"
            "b u1M\n"
            "u missing\n"
            "u a\n"
            "m 20 00 00 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused_a 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/B.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_root_second_export_library_second_export_project_second_export_tail": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 19\n"
            "b u0M\n"
            "b u1M\n"
            "u missing\n"
            "u a\n"
            "m 20 00 00 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 1\n"
                "b u0M\n"
                "b M\n"
                "u missing\n"
                "m 20 00 00 60 60\n"
                "r 1 u0\n"
                "n b\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused_a 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": [
            "LIB/B.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_root_second_export_mixed_project_library_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_root_second_export_mixed_library_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 19\n"
            "b M\n"
            "b u0M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/B.OBJ"],
    },
    "object_code_root_second_export_dual_import_project_library_dependencies": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 22\n"
            "b M\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m EA 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_root_second_export_dual_import_library_project_dependencies": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 22\n"
            "b M\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m EA 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/B.OBJ"],
    },
    "object_code_root_second_export_dual_import_shared_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 22\n"
            "b M\n"
            "b u0u1M\n"
            "u a\n"
            "u c\n"
            "m EA 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex("201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/C.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/C.OBJ"],
    },
    "object_code_root_second_export_dual_import_shared_project_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 22\n"
            "b M\n"
            "b u0u1M\n"
            "u a\n"
            "u c\n"
            "m EA 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "expected_tail": bytes.fromhex("201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/C.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/B.OBJ"],
    },
    "object_code_root_second_export_root_project_share_project_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 22\n"
            "b M\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m EA 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6020161060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_root_second_export_root_library_share_project_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 22\n"
            "b M\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m EA 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6020161060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_root_second_export_root_project_share_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 22\n"
            "b M\n"
            "b u0u1M\n"
            "u a\n"
            "u c\n"
            "m EA 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201610201A10A9A58DD003A90085028503A2024C0FCF201A106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_root_second_export_root_library_share_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 22\n"
            "b M\n"
            "b u0u1M\n"
            "u b\n"
            "u c\n"
            "m EA 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201610201A10A9A58DD003A90085028503A2024C0FCF201A106060"),
        "expected_alink_loads": ["LIB/B.OBJ", "LIB/C.OBJ"],
    },
    "object_code_root_second_export_root_project_library_share_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 25\n"
            "b M\n"
            "b u0u1u2M\n"
            "u a\n"
            "u b\n"
            "u c\n"
            "m EA 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "r 8 u2\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201910201D10202110A9A58DD003A90085028503A2024C0FCF202110602021106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_root_second_export_root_project_library_share_project_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 25\n"
            "b M\n"
            "b u0u1u2M\n"
            "u a\n"
            "u b\n"
            "u c\n"
            "m EA 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 2 u0\n"
            "r 5 u1\n"
            "r 8 u2\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201910201D10202110A9A58DD003A90085028503A2024C0FCF202110602021106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/C.OBJ"],
    },
    "object_code_root_second_export_dependency_dual_lettered_import_mixed_helpers": (
        _object_code_root_second_export_dependency_dual_lettered_import_mixed_helpers_case()
    ),
    "object_code_root_second_export_dependency_lowercase_z_import_project_helper": (
        _object_code_root_second_export_dependency_lowercase_z_import_project_helper_case()
    ),
    "object_code_root_second_export_dependency_lowercase_z_import_library_helper": (
        _object_code_root_second_export_dependency_lowercase_z_import_library_helper_case()
    ),
    "object_code_root_second_export_library_dependency_lowercase_z_import_project_helper": (
        _object_code_root_second_export_library_dependency_lowercase_z_import_project_helper_case()
    ),
    "object_code_root_second_export_library_dependency_lowercase_z_import_library_helper": (
        _object_code_root_second_export_library_dependency_lowercase_z_import_library_helper_case()
    ),
    "object_code_root_second_export_dependency_imports_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 20\n"
            "x a 20 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF6020131060"),
        "expected_alink_loads": ["LIB/B.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_root_second_export_dependency_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF6020131060"),
        "expected_alink_loads": ["LIB/B.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_root_second_export_imports_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 1\n"
            "x main 1 20\n"
            "x a 20 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u a\n"
            "m EA 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 2 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_root_second_export_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u a\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_root_second_export_offset_local_and_library_project_tail": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 23\n"
            "x a 26 1\n"
            "b M\n"
            "b u0u1M\n"
            "b M\n"
            "u a\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "r 8 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF60201B106060"),
        "expected_alink_loads": ["LIB/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ", "LIB/C.OBJ"],
    },
    "object_code_external_offset_transitive_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 2 4\nb u0M\nu b\nm EA EA 20 00 00 60\nr 3 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_large_root_page_crossing": _object_code_large_root_page_crossing_case(),
    "object_code_large_root_multi_reloc_page_crossing": (
        _object_code_large_root_multi_reloc_page_crossing_case()
    ),
    "object_code_reloc_scan_windowed_imports": _object_code_reloc_scan_windowed_imports_case(),
    "object_code_dependency_reloc_scan_windowed_imports": (
        _object_code_dependency_reloc_scan_windowed_imports_case()
    ),
    "object_code_large_dependency_page_crossing": _object_code_large_dependency_page_crossing_case(),
    "object_code_project_large_dependency_page_crossing": (
        _object_code_project_large_dependency_page_crossing_case()
    ),
    "object_code_project_large_dependency_library_tail_page_crossing": (
        _object_code_project_large_dependency_library_tail_page_crossing_case()
    ),
    "object_code_external_unused_import_ignored": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 1\n"
                "x unused 1 4\n"
                "b M\n"
                "b u0M\n"
                "u missing\n"
                "m 60 20 00 00 60\n"
                "r 2 u0\n"
                "n a\n"
            ),
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/A.OBJ"],
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_external_second_export": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 1\n"
                "b u0M\n"
                "b M\n"
                "u missing\n"
                "m 20 00 00 60 60\n"
                "r 1 u0\n"
                "n a\n"
            ),
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/A.OBJ"],
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_external_second_export_import": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 1\n"
                "x a 1 4\n"
                "b M\n"
                "b u0M\n"
                "u b\n"
                "m 60 20 00 00 60\n"
                "r 2 u0\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_external_lettered_import_pruned": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uAM\n"
                "u d0\n"
                "u d1\n"
                "u d2\n"
                "u d3\n"
                "u d4\n"
                "u d5\n"
                "u d6\n"
                "u d7\n"
                "u d8\n"
                "u d9\n"
                "u helper\n"
                "m 20 00 00 60\n"
                "r 1 uA\n"
                "n a\n"
            ),
            "D0.OBJ": "OBJ1\nx d0 0 1\nb M\nm 60\nn d0\n",
            "D1.OBJ": "OBJ1\nx d1 0 1\nb M\nm 60\nn d1\n",
            "D2.OBJ": "OBJ1\nx d2 0 1\nb M\nm 60\nn d2\n",
            "D3.OBJ": "OBJ1\nx d3 0 1\nb M\nm 60\nn d3\n",
            "D4.OBJ": "OBJ1\nx d4 0 1\nb M\nm 60\nn d4\n",
            "D5.OBJ": "OBJ1\nx d5 0 1\nb M\nm 60\nn d5\n",
            "D6.OBJ": "OBJ1\nx d6 0 1\nb M\nm 60\nn d6\n",
            "D7.OBJ": "OBJ1\nx d7 0 1\nb M\nm 60\nn d7\n",
            "D8.OBJ": "OBJ1\nx d8 0 1\nb M\nm 60\nn d8\n",
            "D9.OBJ": "OBJ1\nx d9 0 1\nb M\nm 60\nn d9\n",
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/D0.OBJ",
            "LIB/D1.OBJ",
            "LIB/D2.OBJ",
            "LIB/D3.OBJ",
            "LIB/D4.OBJ",
            "LIB/D5.OBJ",
            "LIB/D6.OBJ",
            "LIB/D7.OBJ",
            "LIB/D8.OBJ",
            "LIB/D9.OBJ",
        ],
    },
    "object_code_project_lettered_import_pruned": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 4\n"
                "b uAM\n"
                "u d0\n"
                "u d1\n"
                "u d2\n"
                "u d3\n"
                "u d4\n"
                "u d5\n"
                "u d6\n"
                "u d7\n"
                "u d8\n"
                "u d9\n"
                "u helper\n"
                "m 20 00 00 60\n"
                "r 1 uA\n"
                "n a\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "D0.OBJ": "OBJ1\nx d0 0 1\nb M\nm 60\nn d0\n",
            "D1.OBJ": "OBJ1\nx d1 0 1\nb M\nm 60\nn d1\n",
            "D2.OBJ": "OBJ1\nx d2 0 1\nb M\nm 60\nn d2\n",
            "D3.OBJ": "OBJ1\nx d3 0 1\nb M\nm 60\nn d3\n",
            "D4.OBJ": "OBJ1\nx d4 0 1\nb M\nm 60\nn d4\n",
            "D5.OBJ": "OBJ1\nx d5 0 1\nb M\nm 60\nn d5\n",
            "D6.OBJ": "OBJ1\nx d6 0 1\nb M\nm 60\nn d6\n",
            "D7.OBJ": "OBJ1\nx d7 0 1\nb M\nm 60\nn d7\n",
            "D8.OBJ": "OBJ1\nx d8 0 1\nb M\nm 60\nn d8\n",
            "D9.OBJ": "OBJ1\nx d9 0 1\nb M\nm 60\nn d9\n",
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/D0.OBJ",
            "LIB/D1.OBJ",
            "LIB/D2.OBJ",
            "LIB/D3.OBJ",
            "LIB/D4.OBJ",
            "LIB/D5.OBJ",
            "LIB/D6.OBJ",
            "LIB/D7.OBJ",
            "LIB/D8.OBJ",
            "LIB/D9.OBJ",
        ],
    },
    "object_code_external_call_twice": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0M\n"
            "u helper\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201610201610A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
    },
    "object_code_lettered_import_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b uAM\n"
            "u d0\n"
            "u d1\n"
            "u d2\n"
            "u d3\n"
            "u d4\n"
            "u d5\n"
            "u d6\n"
            "u d7\n"
            "u d8\n"
            "u d9\n"
            "u helper\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 uA\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "D0.OBJ": "OBJ1\nx d0 0 1\nb M\nm 60\nn d0\n",
            "D1.OBJ": "OBJ1\nx d1 0 1\nb M\nm 60\nn d1\n",
            "D2.OBJ": "OBJ1\nx d2 0 1\nb M\nm 60\nn d2\n",
            "D3.OBJ": "OBJ1\nx d3 0 1\nb M\nm 60\nn d3\n",
            "D4.OBJ": "OBJ1\nx d4 0 1\nb M\nm 60\nn d4\n",
            "D5.OBJ": "OBJ1\nx d5 0 1\nb M\nm 60\nn d5\n",
            "D6.OBJ": "OBJ1\nx d6 0 1\nb M\nm 60\nn d6\n",
            "D7.OBJ": "OBJ1\nx d7 0 1\nb M\nm 60\nn d7\n",
            "D8.OBJ": "OBJ1\nx d8 0 1\nb M\nm 60\nn d8\n",
            "D9.OBJ": "OBJ1\nx d9 0 1\nb M\nm 60\nn d9\n",
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/D0.OBJ",
            "LIB/D1.OBJ",
            "LIB/D2.OBJ",
            "LIB/D3.OBJ",
            "LIB/D4.OBJ",
            "LIB/D5.OBJ",
            "LIB/D6.OBJ",
            "LIB/D7.OBJ",
            "LIB/D8.OBJ",
            "LIB/D9.OBJ",
        ],
    },
    "object_code_project_lettered_import_call": (
        _object_code_project_lettered_import_call_case()
    ),
    "object_code_project_dependency_lettered_import_project_helper": (
        _object_code_project_dependency_lettered_import_project_helper_case()
    ),
    "object_code_project_dependency_lettered_import_library_helper": (
        _object_code_project_dependency_lettered_import_library_helper_case()
    ),
    "object_code_library_dependency_lettered_import_project_helper": (
        _object_code_library_dependency_lettered_import_project_helper_case()
    ),
    "object_code_library_dependency_lettered_import_library_helper": (
        _object_code_library_dependency_lettered_import_library_helper_case()
    ),
    "object_code_library_dependency_lowercase_z_import_project_helper": (
        _object_code_library_dependency_lowercase_z_import_project_helper_case()
    ),
    "object_code_lowercase_z_import_call": _object_code_lowercase_z_import_call_case(),
    "object_code_project_lowercase_z_import_call": (
        _object_code_project_lowercase_z_import_call_case()
    ),
    "object_code_dependency_lowercase_z_import_pruned": (
        _object_code_dependency_lowercase_z_import_pruned_case()
    ),
    "object_code_project_dependency_lowercase_z_import_pruned": (
        _object_code_project_dependency_lowercase_z_import_pruned_case()
    ),
    "object_code_project_dependency_lowercase_z_import_project_helper": (
        _object_code_project_dependency_lowercase_z_import_project_helper_case()
    ),
    "object_code_external_pair": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_external_triple_root_imports": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 25\n"
            "b u0u1u2M\n"
            "u a\n"
            "u b\n"
            "u c\n"
            "m 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "r 7 u2\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201910201A10201B10A9A58DD003A90085028503A2024C0FCF606060"
        ),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
    },
    "object_code_transitive_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_project_transitive_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
    },
    "object_code_project_offset_library_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 2 4\nb u0M\nu b\nm EA EA 20 00 00 60\nr 3 u0\nn a\n",
        },
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_project_precedes_library": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_second_export_import": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 1\n"
                "x a 1 4\n"
                "b M\n"
                "b u0M\n"
                "u b\n"
                "m EA 20 00 00 60\n"
                "r 2 u0\n"
                "n a\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_second_export_named_symbol_import": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 19\n"
                "b u0M\n"
                "b M\n"
                "u missing\n"
                "m 20 00 00 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "r 1 u0\n"
                "r 5 x helper\n"
                "n a\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF202610A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_project_second_export_named_symbol_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "x b 8 1\n"
                "b u0M\n"
                "b M\n"
                "b M\n"
                "u missing\n"
                "m 20 00 00 60 20 00 00 60 60\n"
                "r 1 u0\n"
                "r 5 x b\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "OBJ/B.OBJ",
            "LIB/B.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_project_second_export_imports_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "OBJ/MISSING.OBJ", "LIB/MISSING.OBJ", "LIB/B.OBJ"],
    },
    "object_code_project_second_export_lettered_import_project_helper": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b uAM\n"
                "u missing\n"
                "u d1\n"
                "u d2\n"
                "u d3\n"
                "u d4\n"
                "u d5\n"
                "u d6\n"
                "u d7\n"
                "u d8\n"
                "u d9\n"
                "u helper\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 uA\n"
                "n a\n"
            ),
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n",
            "D1.OBJ": "OBJ1\nx d1 0 1\nb M\nm EA\nn d1\n",
            "D2.OBJ": "OBJ1\nx d2 0 1\nb M\nm EA\nn d2\n",
            "D3.OBJ": "OBJ1\nx d3 0 1\nb M\nm EA\nn d3\n",
            "D4.OBJ": "OBJ1\nx d4 0 1\nb M\nm EA\nn d4\n",
            "D5.OBJ": "OBJ1\nx d5 0 1\nb M\nm EA\nn d5\n",
            "D6.OBJ": "OBJ1\nx d6 0 1\nb M\nm EA\nn d6\n",
            "D7.OBJ": "OBJ1\nx d7 0 1\nb M\nm EA\nn d7\n",
            "D8.OBJ": "OBJ1\nx d8 0 1\nb M\nm EA\nn d8\n",
            "D9.OBJ": "OBJ1\nx d9 0 1\nb M\nm EA\nn d9\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
            "LIB/HELPER.OBJ",
            "LIB/D1.OBJ",
            "LIB/D2.OBJ",
            "LIB/D3.OBJ",
            "LIB/D4.OBJ",
            "LIB/D5.OBJ",
            "LIB/D6.OBJ",
            "LIB/D7.OBJ",
            "LIB/D8.OBJ",
            "LIB/D9.OBJ",
        ],
    },
    "object_code_project_second_export_lettered_import_library_helper": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b uAM\n"
                "u missing\n"
                "u d1\n"
                "u d2\n"
                "u d3\n"
                "u d4\n"
                "u d5\n"
                "u d6\n"
                "u d7\n"
                "u d8\n"
                "u d9\n"
                "u helper\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 uA\n"
                "n a\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "D1.OBJ": "OBJ1\nx d1 0 1\nb M\nm EA\nn d1\n",
            "D2.OBJ": "OBJ1\nx d2 0 1\nb M\nm EA\nn d2\n",
            "D3.OBJ": "OBJ1\nx d3 0 1\nb M\nm EA\nn d3\n",
            "D4.OBJ": "OBJ1\nx d4 0 1\nb M\nm EA\nn d4\n",
            "D5.OBJ": "OBJ1\nx d5 0 1\nb M\nm EA\nn d5\n",
            "D6.OBJ": "OBJ1\nx d6 0 1\nb M\nm EA\nn d6\n",
            "D7.OBJ": "OBJ1\nx d7 0 1\nb M\nm EA\nn d7\n",
            "D8.OBJ": "OBJ1\nx d8 0 1\nb M\nm EA\nn d8\n",
            "D9.OBJ": "OBJ1\nx d9 0 1\nb M\nm EA\nn d9\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
            "LIB/D1.OBJ",
            "LIB/D2.OBJ",
            "LIB/D3.OBJ",
            "LIB/D4.OBJ",
            "LIB/D5.OBJ",
            "LIB/D6.OBJ",
            "LIB/D7.OBJ",
            "LIB/D8.OBJ",
            "LIB/D9.OBJ",
        ],
    },
    "object_code_project_second_export_lowercase_z_import_library_helper": (
        _object_code_project_second_export_lowercase_z_import_library_helper_case()
    ),
    "object_code_project_second_export_lowercase_z_import_project_helper": (
        _object_code_project_second_export_lowercase_z_import_project_helper_case()
    ),
    "object_code_project_second_export_dependency_dual_lettered_import_mixed_helpers": (
        _object_code_project_second_export_dependency_dual_lettered_import_mixed_helpers_case()
    ),
    "object_code_project_second_export_transitive_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/B.OBJ",
            "LIB/C.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_project_second_export_project_dependency_imports_library_tail": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/B.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_project_second_export_transitive_library_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_mixed_second_export_transitive_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/C.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_mixed_project_library_closure": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF201B10606060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_mixed_dual_transitive_project_library_closure": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
            "D.OBJ": "OBJ1\nx d 0 1\nb M\nm 60\nn d\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu d\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
            "D.OBJ": "OBJ1\nx d 0 1\nb M\nm EA\nn d\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201F10606060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ", "OBJ/D.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/D.OBJ"],
    },
    "object_code_library_imports_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u b\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/B.OBJ", "OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_library_second_export_imports_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ", "LIB/B.OBJ"],
    },
    "object_code_library_second_export_named_symbol_import": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 19\n"
                "b u0M\n"
                "b M\n"
                "u missing\n"
                "m 20 00 00 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
                "r 1 u0\n"
                "r 5 x helper\n"
                "n a\n"
            ),
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF202610A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ", "LIB/HELPER.OBJ"],
    },
    "object_code_library_second_export_dependency_dual_lettered_import_mixed_helpers": (
        _object_code_library_second_export_dependency_dual_lettered_import_mixed_helpers_case()
    ),
    "object_code_library_second_export_lettered_import_project_helper": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b uAM\n"
                "u missing\n"
                "u d1\n"
                "u d2\n"
                "u d3\n"
                "u d4\n"
                "u d5\n"
                "u d6\n"
                "u d7\n"
                "u d8\n"
                "u d9\n"
                "u helper\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 uA\n"
                "n a\n"
            ),
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm EA\nn helper\n",
            "D1.OBJ": "OBJ1\nx d1 0 1\nb M\nm EA\nn d1\n",
            "D2.OBJ": "OBJ1\nx d2 0 1\nb M\nm EA\nn d2\n",
            "D3.OBJ": "OBJ1\nx d3 0 1\nb M\nm EA\nn d3\n",
            "D4.OBJ": "OBJ1\nx d4 0 1\nb M\nm EA\nn d4\n",
            "D5.OBJ": "OBJ1\nx d5 0 1\nb M\nm EA\nn d5\n",
            "D6.OBJ": "OBJ1\nx d6 0 1\nb M\nm EA\nn d6\n",
            "D7.OBJ": "OBJ1\nx d7 0 1\nb M\nm EA\nn d7\n",
            "D8.OBJ": "OBJ1\nx d8 0 1\nb M\nm EA\nn d8\n",
            "D9.OBJ": "OBJ1\nx d9 0 1\nb M\nm EA\nn d9\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
            "LIB/HELPER.OBJ",
            "LIB/D1.OBJ",
            "LIB/D2.OBJ",
            "LIB/D3.OBJ",
            "LIB/D4.OBJ",
            "LIB/D5.OBJ",
            "LIB/D6.OBJ",
            "LIB/D7.OBJ",
            "LIB/D8.OBJ",
            "LIB/D9.OBJ",
        ],
    },
    "object_code_library_second_export_lettered_import_library_helper": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b uAM\n"
                "u missing\n"
                "u d1\n"
                "u d2\n"
                "u d3\n"
                "u d4\n"
                "u d5\n"
                "u d6\n"
                "u d7\n"
                "u d8\n"
                "u d9\n"
                "u helper\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 uA\n"
                "n a\n"
            ),
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
            "D1.OBJ": "OBJ1\nx d1 0 1\nb M\nm EA\nn d1\n",
            "D2.OBJ": "OBJ1\nx d2 0 1\nb M\nm EA\nn d2\n",
            "D3.OBJ": "OBJ1\nx d3 0 1\nb M\nm EA\nn d3\n",
            "D4.OBJ": "OBJ1\nx d4 0 1\nb M\nm EA\nn d4\n",
            "D5.OBJ": "OBJ1\nx d5 0 1\nb M\nm EA\nn d5\n",
            "D6.OBJ": "OBJ1\nx d6 0 1\nb M\nm EA\nn d6\n",
            "D7.OBJ": "OBJ1\nx d7 0 1\nb M\nm EA\nn d7\n",
            "D8.OBJ": "OBJ1\nx d8 0 1\nb M\nm EA\nn d8\n",
            "D9.OBJ": "OBJ1\nx d9 0 1\nb M\nm EA\nn d9\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/HELPER.OBJ"],
        "unexpected_alink_loads": [
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
            "LIB/D1.OBJ",
            "LIB/D2.OBJ",
            "LIB/D3.OBJ",
            "LIB/D4.OBJ",
            "LIB/D5.OBJ",
            "LIB/D6.OBJ",
            "LIB/D7.OBJ",
            "LIB/D8.OBJ",
            "LIB/D9.OBJ",
        ],
    },
    "object_code_library_second_export_lowercase_z_import_project_helper": (
        _object_code_library_second_export_lowercase_z_import_project_helper_case()
    ),
    "object_code_library_second_export_lowercase_z_import_library_helper": (
        _object_code_library_second_export_lowercase_z_import_library_helper_case()
    ),
    "object_code_library_second_export_imports_library_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_library_second_export_transitive_library_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_library_second_export_transitive_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": [
            "LIB/B.OBJ",
            "LIB/C.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_library_second_export_project_dependency_imports_library_tail": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": (
                "OBJ1\n"
                "x unused_b 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u b\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF20171060201B106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": [
            "LIB/B.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_mixed_second_export_shared_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_mixed_second_export_shared_project_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x a 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n a\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": [
            "LIB/A.OBJ",
            "LIB/C.OBJ",
            "OBJ/MISSING.OBJ",
            "LIB/MISSING.OBJ",
        ],
    },
    "object_code_library_offset_project_dependency": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u b\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 2 4\nb u0M\nu a\nm EA EA 20 00 00 60\nr 3 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/B.OBJ", "OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_library_imports_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 20\n"
            "x a 19 1\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF6020131060"),
        "expected_alink_loads": ["LIB/B.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_library_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF6020131060"),
        "expected_alink_loads": ["LIB/B.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_library_second_export_imports_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 20\n"
            "x a 19 1\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u a\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF6020131060"),
        "expected_alink_loads": ["LIB/B.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ", "OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_library_second_export_dependency_imports_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 20\n"
            "x a 19 1\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF602018106020131060"),
        "expected_alink_loads": ["LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ", "OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_library_second_export_dependency_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": (
                "OBJ1\n"
                "x unused 0 4\n"
                "x b 4 4\n"
                "b u0M\n"
                "b u1M\n"
                "u missing\n"
                "u c\n"
                "m 20 00 00 60 20 00 00 60\n"
                "r 1 u0\n"
                "r 5 u1\n"
                "n b\n"
            ),
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF602018106020131060"),
        "expected_alink_loads": ["LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ", "OBJ/MISSING.OBJ", "LIB/MISSING.OBJ"],
    },
    "object_code_project_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF6020131060"),
        "expected_alink_loads": ["OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/B.OBJ", "OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_transitive_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF602018106020131060"),
        "expected_alink_loads": ["LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_mixed_transitive_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF602018106020131060"),
        "expected_alink_loads": ["OBJ/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/B.OBJ", "OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_library_project_transitive_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF602018106020131060"),
        "expected_alink_loads": ["LIB/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": ["LIB/C.OBJ", "OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_project_transitive_imports_offset_root_local_export": {
        "seed_object": (
            "OBJ1\n"
            "x unused 0 4\n"
            "x main 4 20\n"
            "x a 23 1\n"
            "b M\n"
            "b u0M\n"
            "b M\n"
            "u b\n"
            "m EA EA EA 60 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF 60\n"
            "r 5 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex("201410A9A58DD003A90085028503A2024C0FCF602018106020131060"),
        "expected_alink_loads": ["OBJ/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": ["LIB/B.OBJ", "LIB/C.OBJ", "OBJ/A.OBJ", "LIB/A.OBJ"],
    },
    "object_code_library_dual_import_project_library_dependencies": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 7\n"
                "b u0u1M\n"
                "u b\n"
                "u c\n"
                "m 20 00 00 20 00 00 60\n"
                "r 1 u0\n"
                "r 4 u1\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF201A10201B10606060"
        ),
        "expected_alink_loads": ["LIB/A.OBJ", "OBJ/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/B.OBJ"],
    },
    "object_code_project_dual_import_project_library_dependencies": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 7\n"
                "b u0u1M\n"
                "u b\n"
                "u c\n"
                "m 20 00 00 20 00 00 60\n"
                "r 1 u0\n"
                "r 4 u1\n"
                "n a\n"
            ),
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF201A10201B10606060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_root_library_share_project_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6020161060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_root_library_share_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u b\n"
            "u c\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201610201A10A9A58DD003A90085028503A2024C0FCF201A106060"),
        "expected_alink_loads": ["LIB/B.OBJ", "LIB/C.OBJ"],
    },
    "object_code_root_project_share_project_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu a\nm 20 00 00 60\nr 1 u0\nn b\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm EA\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6020161060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "OBJ/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_root_project_share_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u c\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex("201610201A10A9A58DD003A90085028503A2024C0FCF201A106060"),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_library_project_library_chain": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "C.OBJ": "OBJ1\nx c 0 4\nb u0M\nu d\nm 20 00 00 60\nr 1 u0\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
            "D.OBJ": "OBJ1\nx d 0 1\nb M\nm 60\nn d\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF20171060201B1060201F106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "OBJ/C.OBJ", "LIB/D.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/C.OBJ"],
    },
    "object_code_mixed_shared_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/C.OBJ"],
    },
    "object_code_root_project_library_share_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 25\n"
            "b u0u1u2M\n"
            "u a\n"
            "u b\n"
            "u c\n"
            "m 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "r 7 u2\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201910201D10202110A9A58DD003A90085028503A2024C0FCF202110602021106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_root_project_library_share_project_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 25\n"
            "b u0u1u2M\n"
            "u a\n"
            "u b\n"
            "u c\n"
            "m 20 00 00 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "r 7 u2\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm EA\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201910201D10202110A9A58DD003A90085028503A2024C0FCF202110602021106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "OBJ/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/C.OBJ"],
    },
    "object_code_mixed_shared_library_dependency_dedup": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_unresolved_import_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u missing\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "expect_alink_failure": True,
        "expected_alink_error": "NO OBJECT",
    },
    "object_code_duplicate_export_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 16\n"
            "x main 0 16\n"
            "b M\n"
            "m A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "n main\n"
        ),
        "has_stub": False,
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
    },
    "object_code_missing_machine_record_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 16\n"
            "b M\n"
            "n main\n"
        ),
        "has_stub": False,
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
    },
    "object_code_zero_size_export_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 0\n"
            "b M\n"
            "m 60\n"
            "n main\n"
        ),
        "has_stub": False,
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
    },
    "object_code_export_offset_past_machine_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 2 1\n"
            "b M\n"
            "m 60\n"
            "n main\n"
        ),
        "has_stub": False,
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
    },
    "object_code_export_size_overruns_machine_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 2\n"
            "b M\n"
            "m 60\n"
            "n main\n"
        ),
        "has_stub": False,
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
    },
    "object_code_reloc_unknown_import_index_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u helper\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
    },
    "object_code_dependency_unknown_lowercase_import_index_rejects": (
        _object_code_dependency_unknown_lowercase_import_index_rejects_case()
    ),
    "object_code_project_unknown_lowercase_import_index_blocks_library_fallback": (
        _object_code_project_unknown_lowercase_import_index_blocks_library_fallback_case()
    ),
    "object_code_reloc_malformed_offset_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u helper\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r x u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "HELPER.OBJ": "OBJ1\nx helper 0 1\nb M\nm 60\nn helper\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
    },
    "object_code_library_missing_machine_record_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_library_duplicate_export_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_library_zero_size_export_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 0\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_library_export_offset_past_machine_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 2 1\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_library_export_size_overruns_machine_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 2\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_library_reloc_malformed_offset_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr x u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_library_wrong_export_rejects": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx z 0 1\nb M\nm 60\nn z\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_bad_dependency_blocks_library_fallback": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_zero_size_export_blocks_library_fallback": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 0\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_export_offset_past_machine_blocks_library_fallback": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 2 1\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_export_size_overruns_machine_blocks_library_fallback": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 2\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_duplicate_export_blocks_library_fallback": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_project_reloc_malformed_offset_blocks_library_fallback": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr x u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_project_wrong_export_blocks_library_fallback": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx z 0 1\nb M\nm 60\nn z\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm 60\nn a\n",
        },
        "expect_alink_failure": True,
        "expected_alink_error": "BAD OBJECT",
        "expected_alink_loads": ["OBJ/A.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_external_cycle": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nu a\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_external_back_edge_cycle": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 5\nb u0M\nu a\nm 60 20 00 00 60\nr 2 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF201710606020131060"
        ),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_mixed_project_library_back_edge_cycle": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 5\nb u0M\nu a\nm 60 20 00 00 60\nr 2 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF201710606020131060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_mixed_project_offset_back_edge_cycle": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_objects": {
            "A.OBJ": "OBJ1\nx a 2 5\nb u0M\nu b\nm EA EA EA 20 00 00 60\nr 4 u0\nn a\n",
        },
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb M\nm EA\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 5\nb u0M\nu a\nm 60 20 00 00 60\nr 2 u0\nn b\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCFEA201810606020131060"
        ),
        "expected_alink_loads": ["OBJ/A.OBJ", "LIB/B.OBJ"],
        "unexpected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_external_triangle": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb M\nm 60\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201A10A9A58DD003A90085028503A2024C0FCF201A106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_external_diamond": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201E106060"
        ),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ"],
    },
    "object_code_external_square": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 22\n"
            "b u0u1M\n"
            "u a\n"
            "u b\n"
            "m 20 00 00 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "r 4 u1\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu c\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 4\nb u0M\nu d\nm 20 00 00 60\nr 1 u0\nn b\n",
            "C.OBJ": "OBJ1\nx c 0 1\nb M\nm 60\nn c\n",
            "D.OBJ": "OBJ1\nx d 0 1\nb M\nm 60\nn d\n",
        },
        "expected_tail": bytes.fromhex(
            "201610201A10A9A58DD003A90085028503A2024C0FCF201E1060201F10606060"
        ),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ", "LIB/C.OBJ", "LIB/D.OBJ"],
    },
    "object_code_external_print_line": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u w\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "W.OBJ": (
                "OBJ1\n"
                "x w 0 24\n"
                "b M\n"
                "m A9 24 85 02 A9 10 85 03 A2 02 20 03 CF 20 06 CF 60 "
                "4C 49 4E 4B 45 44 00\n"
                "n w\n"
            ),
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCFA9248502A9108503"
            "A2022003CF2006CF604C494E4B454400"
        ),
        "screen_fragments": ["linked"],
        "expected_alink_loads": ["LIB/W.OBJ"],
    },
    "object_code_external_store_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 11\nb M\nm A9 2A A2 00 8D D1 03 8E D2 03 60\nn a\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCFA92AA2008DD1038ED20360"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x2A,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_external_load_store_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 29\n"
                "b M\n"
                "m A9 2A A2 00 8D 38 10 8E 39 10 AD 38 10 AE 39 10 "
                "8D 3A 10 8E 3B 10 8D D1 03 8E D2 03 60\n"
                "n a\n"
            ),
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCFA92A"
            "A2008D38108E3910AD3810AE39108D3A108E3B108DD1038ED20360"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x2A,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_external_string_int_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": (
                "OBJ1\n"
                "x a 0 135\n"
                "b M\n"
                f"m {_EXTERNAL_STRING_INT_HELPER_CODE}\n"
                "n a\n"
            ),
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCFA9958502A9108503A2022003CFA92A"
            "8D9110A9008D9210A200AD9110C964900938E9648D9110E8D0F0E000F00C8A186930"
            "207B10A9018D9210A200AD9110C90A900938E90A8D9110E8D0F0E000D005AD9210"
            "F0078A186930207B10AD9110186930207B102006CF608D9310A9008D9410A993"
            "8502A9108503A2022003CF6000000000544F4F4C00"
        ),
        "screen_fragments": ["tool42"],
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "object_code_transitive_external_print_line": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": (
                "OBJ1\n"
                "x b 0 22\n"
                "b M\n"
                "m A9 28 85 02 A9 10 85 03 A2 02 20 03 CF 20 06 CF 60 "
                "44 45 45 50 00\n"
                "n b\n"
            ),
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF20171060"
            "A9288502A9108503A2022003CF2006CF604445455000"
        ),
        "screen_fragments": ["deep"],
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_transitive_external_store_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 11\nb M\nm A9 2A A2 00 8D D1 03 8E D2 03 60\nn b\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF20171060"
            "A92AA2008DD1038ED20360"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x2A,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_transitive_external_load_store_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": (
                "OBJ1\n"
                "x b 0 29\n"
                "b M\n"
                "m A9 2A A2 00 8D 38 10 8E 39 10 AD 38 10 AE 39 10 "
                "8D 3A 10 8E 3B 10 8D D1 03 8E D2 03 60\n"
                "n b\n"
            ),
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF20171060"
            "A92AA2008D38108E3910AD3810AE39108D3A108E3B108DD1038ED20360"
        ),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x2A,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "object_code_transitive_external_string_int_call": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 19\n"
            "b u0M\n"
            "u a\n"
            "m 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 1 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 4\nb u0M\nu b\nm 20 00 00 60\nr 1 u0\nn a\n",
            "B.OBJ": (
                "OBJ1\n"
                "x b 0 135\n"
                "b M\n"
                f"m {_TRANSITIVE_EXTERNAL_STRING_INT_HELPER_CODE}\n"
                "n b\n"
            ),
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF20171060A9998502A9108503A202"
            "2003CFA92A8D9510A9008D9610A200AD9510C964900938E9648D9510E8D0F0E0"
            "00F00C8A186930207F10A9018D9610A200AD9510C90A900938E90A8D9510E8D0"
            "F0E000D005AD9610F0078A186930207F10AD9510186930207F102006CF608D"
            "9710A9008D9810A9978502A9108503A2022003CF6000000000544F4F4C00"
        ),
        "screen_fragments": ["tool42"],
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "unsupported_body": {
        "seed_object": "OBJ1\nx main 0 2\nb zr\nn main\n",
        "has_stub": False,
        "expect_alink_failure": True,
        "expected_alink_error": "UNSUPPORTED BODY",
    },
    "if_eq": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=7\rIF X=7 THEN\rY=1\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A907A2008D49108E4A10AD4910AE4A108D47108E4810A907A200EC4810D005CD4710F0034C3110A901A2008D4B108E4C108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_lt": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=1\rY=2\rIF X<Y THEN\rY=3\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D65108E6610A902A2008D67108E6810AD6510AE66108D63108E6410AD6710AE6810EC6410900DD007CD63109006F004A901D002A900A200C900D0034C4D10A903A2008D67108E68108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x03,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_gt": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=2\rY=1\rIF X>Y THEN\rY=3\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A902A2008D65108E6610A901A2008D67108E6810AD6510AE66108D63108E6410AD6710AE6810EC64109007D00DCD63109002F004A901D002A900A200C900D0034C4D10A903A2008D67108E68108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x03,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_ge": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=2\rY=1\rIF X>=Y THEN\rY=3\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A902A2008D75108E7610A901A2008D77108E7810AD7510AE76108D73108E7410AD7710AE7810EC7410900DD007CD73109006F004A901D002A900A2008D73108E7410A900A200EC7410D005CD7310F0034C5D10A903A2008D77108E78108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x03,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_ne": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=2\rY=1\rIF X<>Y THEN\rY=3\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A902A2008D61108E6210A901A2008D63108E6410AD6110AE62108D5F108E6010AD6310AE6410EC6010D005CD5F10F004A901D002A900A200C900D0034C4910A903A2008D63108E64108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x03,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_le": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=1\rY=1\rIF X<=Y THEN\rY=3\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D75108E7610A901A2008D77108E7810AD7510AE76108D73108E7410AD7710AE7810EC74109007D00DCD73109002F004A901D002A900A2008D73108E7410A900A200EC7410D005CD7310F0034C5D10A903A2008D77108E78108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x03,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_else": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=7\rIF X=8 THEN\rY=1\rELSE\rY=2\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A907A2008D56108E5710AD5610AE57108D54108E5510A908A200EC5510D005CD5410F0034C3410A901A2008D58108E59104C3E10A902A2008D58108E59108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x02,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_if": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rCARD Z\rPROC MAIN()\rX=1\rY=2\rIF X<Y THEN\rIF Y>1 THEN\rZ=3\rFI\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D92108E9310A902A2008D94108E9510AD9210AE93108D90108E9110AD9410AE9510EC9110900DD007CD90109006F004A901D002A900A200C900D0034C7A10AD9410AE95108D90108E9110A901A200EC91109007D00DCD90109002F004A901D002A900A200C900D0034C7A10A903A2008D96108E97108DD1038ED203A9A58DD003A90085028503A2024C0FCF0000000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x03,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_else": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rCARD Z\rPROC MAIN()\rX=1\rY=2\rIF X<Y THEN\rIF Y>2 THEN\rZ=3\rELSE\rZ=4\rFI\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D9F108EA010A902A2008DA1108EA210AD9F10AEA0108D9D108E9E10ADA110AEA210EC9E10900DD007CD9D109006F004A901D002A900A200C900D0034C8710ADA110AEA2108D9D108E9E10A902A200EC9E109007D00DCD9D109002F004A901D002A900A200C900D0034C7D10A903A2008DA3108EA4104C8710A904A2008DA3108EA4108DD1038ED203A9A58DD003A90085028503A2024C0FCF0000000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x04,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_do_until_eq": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=0\rY=0\rDO\rX=1\rDO\rY=2\rUNTIL Y=2\rOD\rUNTIL X=1\rOD\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A900A2008D7A108E7B10A900A2008D7C108E7D10A901A2008D7A108E7B10A902A2008D7C108E7D10AD7C10AE7D108D78108E7910A902A200EC7910D005CD7810F0034C1E10AD7A10AE7B108D78108E7910A901A200EC7910D005CD7810F0034C14108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "do_if_until_eq": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=0\rY=0\rDO\rX=1\rIF X=1 THEN\rY=2\rFI\rUNTIL Y=2\rOD\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A900A2008D7A108E7B10A900A2008D7C108E7D10A901A2008D7A108E7B10AD7A10AE7B108D78108E7910A901A200EC7910D005CD7810F0034C4510A902A2008D7C108E7D10AD7C10AE7D108D78108E7910A902A200EC7910D005CD7810F0034C14108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x02,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "do_if_else_until_eq": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=0\rY=0\rDO\rX=1\rIF X=2 THEN\rY=3\rELSE\rY=4\rFI\rUNTIL Y=4\rOD\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A900A2008D87108E8810A900A2008D89108E8A10A901A2008D87108E8810AD8710AE88108D85108E8610A902A200EC8610D005CD8510F0034C4810A903A2008D89108E8A104C5210A904A2008D89108E8A10AD8910AE8A108D85108E8610A904A200EC8610D005CD8510F0034C14108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x04,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_do_until_eq": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=1\rY=0\rIF X=1 THEN\rDO\rY=2\rUNTIL Y=2\rOD\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D70108E7110A900A2008D72108E7310AD7010AE71108D6E008E6F00A901A200EC6F00D005CD6E00F0034C5810A902A2008D72108E7310AD7210AE73108D6E008E6F00A902A200EC6F00D005CD6E00F0034C31108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x02,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_else_do_until_eq": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=1\rY=0\rIF X=2 THEN\rDO\rY=3\rUNTIL Y=3\rOD\rELSE\rDO\rY=4\rUNTIL Y=4\rOD\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D9A108E9B10A900A2008D9C108E9D10AD9A10AE9B108D98108E9910A902A200EC9910D005CD9810F0034C5B10A903A2008D9C108E9D10AD9C10AE9D108D98108E9910A903A200EC9910D005CD9810F0034C31104C8210A904A2008D9C108E9D10AD9C10AE9D108D98108E9910A904A200EC9910D005CD9810F0034C5B108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x04,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_local_call_do_until_eq": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rDO\rY=2\rUNTIL Y=2\rOD\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=1 THEN\rA()\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D74108E7510A900A2008D76108E7710AD7410AE75108D72008E7300A901A200EC7300D005CD7200F0034C3410204A108DD1038ED203A9A58DD003A90085028503A2024C0FCFA902A2008D76108E7710AD7610AE77108D4A008E4B00A902A200EC4B00D005CD4A00F0034C001060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x02,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_else_local_call_do_until_eq": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rDO\rY=4\rUNTIL Y=4\rOD\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=2 THEN\rY=3\rELSE\rA()\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D81108E8210A900A2008D83108E8410AD8110AE82108D7F008E8000A902A200EC8000D005CD7F00F0034C3E10A903A2008D83108E84104C41102057108DD1038ED203A9A58DD003A90085028503A2024C0FCFA904A2008D83108E8410AD8310AE84108D57008E5800A904A200EC5800D005CD5700F0034C001060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x04,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_if_local_call": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rY=5\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=1 THEN\rIF Y=0 THEN\rA()\rFI\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D74108E7510A900A2008D76108E7710AD7410AE75108D72008E7300A901A200EC7300D005CD7200F0034C5110AD7610AE77108D72008E7300A900A200EC7300D005CD7200F0034C51102067108DD1038ED203A9A58DD003A90085028503A2024C0FCFA905A2008D76108E771060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x05,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_else_local_call": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rY=6\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=1 THEN\rIF Y=1 THEN\rY=3\rELSE\rA()\rFI\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D81108E8210A900A2008D83108E8410AD8110AE82108D7F008E8000A901A200EC8000D005CD7F00F0034C5E10AD8310AE84108D7F008E8000A901A200EC8000D005CD7F00F0034C5B10A903A2008D83108E84104C5E102074108DD1038ED203A9A58DD003A90085028503A2024C0FCFA906A2008D83108E841060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x06,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_do_local_call": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rY=7\rRETURN\rPROC MAIN()\rX=0\rY=0\rDO\rX=1\rDO\rA()\rUNTIL Y=7\rOD\rUNTIL X=1\rOD\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A900A2008D7E108E7F10A900A2008D80108E8110A901A2008D7E108E7F10207110AD8010AE81108D71008E7200A907A200EC7200D005CD7100F0034C1E10AD7E10AE7F108D71008E7200A901A200EC7200D005CD7100F0034C14108DD1038ED203A9A58DD003A90085028503A2024C0FCFA907A2008D80108E811060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_do_if_else_local_call": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rY=8\rRETURN\rPROC MAIN()\rX=0\rY=0\rDO\rX=1\rDO\rIF X=2 THEN\rY=3\rELSE\rA()\rFI\rUNTIL Y=8\rOD\rUNTIL X=1\rOD\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A900A2008DA8108EA910A900A2008DAA108EAB10A901A2008DA8108EA910ADA810AEA9108DA6008EA700A902A200ECA700D005CDA600F0034C4810A903A2008DAA108EAB104C4B10209B10ADAA10AEAB108D9B008E9C00A908A200EC9C00D005CD9B00F0034C1E10ADA810AEA9108D9B008E9C00A901A200EC9C00D005CD9B00F0034C14108DD1038ED203A9A58DD003A90085028503A2024C0FCFA908A2008DAA108EAB1060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_local_call_nested_do_if_else": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rDO\rIF Y=1 THEN\rY=3\rELSE\rY=9\rFI\rUNTIL Y=9\rOD\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=1 THEN\rA()\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D9E108E9F10A900A2008DA0108EA110AD9E10AE9F108D9C008E9D00A901A200EC9D00D005CD9C00F0034C3410204A108DD1038ED203A9A58DD003A90085028503A2024C0FCFADA010AEA1108D4A008E4B00A901A200EC4B00D005CD4A00F0034C7410A903A2008DA0108EA1104C7E10A909A2008DA0108EA110ADA010AEA1108D4A008E4B00A909A200EC4B00D005CD4A00F0034C4A1060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x09,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_else_local_call_nested_do_if_else": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rDO\rIF Y=1 THEN\rY=3\rELSE\rY=10\rFI\rUNTIL Y=10\rOD\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=2 THEN\rY=4\rELSE\rA()\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008DAB108EAC10A900A2008DAD108EAE10ADAB10AEAC108DA9008EAA00A902A200ECAA00D005CDA900F0034C3E10A904A2008DAD108EAE104C41102057108DD1038ED203A9A58DD003A90085028503A2024C0FCFADAD10AEAE108D57008E5800A901A200EC5800D005CD5700F0034C8110A903A2008DAD108EAE104C8B10A90AA2008DAD108EAE10ADAD10AEAE108D57008E5800A90AA200EC5800D005CD5700F0034C571060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x0A,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_else_local_call_nested_do_if_else": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC A()\rDO\rIF Y=1 THEN\rY=3\rELSE\rY=11\rFI\rUNTIL Y=11\rOD\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=1 THEN\rIF Y=1 THEN\rY=4\rELSE\rA()\rFI\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008DC8108EC910A900A2008DCA108ECB10ADC810AEC9108DC6008EC700A901A200ECC700D005CDC600F0034C5E10ADCA10AECB108D00008E0100A901A200EC0100D005CD0000F0034C5B10A904A2008DCA108ECB104C5E102074108DD1038ED203A9A58DD003A90085028503A2024C0FCFADCA10AECB108D74008E7500A901A200EC7500D005CD7400F0034C9E10A903A2008DCA108ECB104CA810A90BA2008DCA108ECB10ADCA10AECB108D74008E7500A90BA200EC7500D005CD7400F0034C741060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x0B,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "if_else_local_call_chain_nested_do_if_else": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC B()\rDO\rIF Y=1 THEN\rY=3\rELSE\rY=12\rFI\rUNTIL Y=12\rOD\rRETURN\rPROC A()\rB()\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=2 THEN\rY=4\rELSE\rA()\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008DAF108EB010A900A2008DB1108EB210ADAF10AEB0108DAD008EAE00A902A200ECAE00D005CDAD00F0034C3E10A904A2008DB1108EB2104C411020A9108DD1038ED203A9A58DD003A90085028503A2024C0FCFADB110AEB2108DA9008EAA00A901A200ECAA00D005CDA900F0034C8110A903A2008DB1108EB2104C8B10A90CA2008DB1108EB210ADB110AEB2108D57008E5800A90CA200EC5800D005CD5700F0034C57106020571060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x0C,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "nested_else_local_call_chain_nested_do_if_else": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC B()\rDO\rIF Y=1 THEN\rY=3\rELSE\rY=13\rFI\rUNTIL Y=13\rOD\rRETURN\rPROC A()\rB()\rRETURN\rPROC MAIN()\rX=1\rY=0\rIF X=1 THEN\rIF Y=1 THEN\rY=4\rELSE\rA()\rFI\rFI\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008DCC108ECD10A900A2008DCE108ECF10ADCC10AECD108DCA008ECB00A901A200ECCB00D005CDCA00F0034C5E10ADCE10AECF108D00008E0100A901A200EC0100D005CD0000F0034C5B10A904A2008DCE108ECF104C5E1020C6108DD1038ED203A9A58DD003A90085028503A2024C0FCFADCE10AECF108DC6008EC700A901A200ECC700D005CDC600F0034C9E10A903A2008DCE108ECF104CA810A90DA2008DCE108ECF10ADCE10AECF108D74008E7500A90DA200EC7500D005CD7400F0034C74106020741060000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x0D,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "do_until_eq": {
        "source": "MODULE MAIN\rCARD X\rPROC MAIN()\rX=0\rDO\rX=1\rUNTIL X=1\rOD\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A900A2008D49108E4A10A901A2008D49108E4A10AD4910AE4A108D47108E4810A901A200EC4810D005CD4710F0034C0A108DD1038ED203A9A58DD003A90085028503A2024C0FCF00000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
    "do_until_lt": {
        "source": "MODULE MAIN\rCARD X\rCARD Y\rPROC MAIN()\rX=1\rY=2\rDO\rX=1\rUNTIL X<Y\rOD\rRETURN\r",
        "has_stub": False,
        "expected_tail": bytes.fromhex("A901A2008D65108E6610A902A2008D67108E6810A901A2008D65108E6610AD6510AE66108D63108E6410AD6710AE6810EC6410900DD007CD63109006F004A901D002A900A200C900D0034C14108DD1038ED203A9A58DD003A90085028503A2024C0FCF000000000000"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x01,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
    },
}


def _add_derived_math1_core_split_case(
    name: str,
    source_case: str,
    runtime_library_objects: list[str],
    unexpected_alink_loads: list[str],
) -> None:
    case = dict(DIRECT_PRG_CASES[source_case])
    case["runtime_library_objects"] = runtime_library_objects
    case["unexpected_alink_loads"] = unexpected_alink_loads
    DIRECT_PRG_CASES[name] = case


_MATH1_ALL_CORE_RUNTIME_OBJECTS = [
    "rt_i_to_f",
    "rt_s_to_f",
    "rt_f_to_i",
    "rt_f_add",
    "rt_f_sub",
    "rt_f_mul",
    "rt_f_div",
    "rt_f_cmp",
    "rt_f_abs",
    "rt_f_sqrt",
    "rt_print_f",
]

DIRECT_PRG_CASES["actc_runtime_math1_real_to_int_split_linked"] = {
    "source": (
        "MODULE MAIN\r"
        "REAL A\r"
        "INT X\r"
        "PROC MAIN()\r"
        "A=REAL(7)\r"
        "X=INT(A)\r"
        "RETURN\r"
    ),
    "has_stub": False,
    "runtime_library_objects": _MATH1_ALL_CORE_RUNTIME_OBJECTS,
    "expected_object_fragments": [
        "u rt_i_to_f\n",
        "u rt_f_to_i\n",
        "i 7\n",
        "v x 0\n",
    ],
    "expected_tail": _real_to_int_tail(7),
    "store_check_addr": 0x1034,
    "store_check_value": 0x07,
    "store_check_hi_addr": 0x1035,
    "store_check_hi_value": 0x00,
    "expected_alink_loads": [
        "LIB/RT_I_TO_F.OBJ",
        "LIB/RT_F_TO_I.OBJ",
    ],
    "unexpected_alink_loads": [
        "LIB/RT_S_TO_F.OBJ",
        "LIB/RT_F_ADD.OBJ",
        "LIB/RT_F_SUB.OBJ",
        "LIB/RT_F_MUL.OBJ",
        "LIB/RT_F_DIV.OBJ",
        "LIB/RT_F_CMP.OBJ",
        "LIB/RT_F_ABS.OBJ",
        "LIB/RT_F_SQRT.OBJ",
        "LIB/RT_PRINT_F.OBJ",
    ],
}

_add_derived_math1_core_split_case(
    "actc_runtime_math1_real_int_split_linked",
    "real_printre_int",
    _MATH1_ALL_CORE_RUNTIME_OBJECTS,
    [
        "LIB/RT_S_TO_F.OBJ",
        "LIB/RT_F_TO_I.OBJ",
        "LIB/RT_F_ADD.OBJ",
        "LIB/RT_F_SUB.OBJ",
        "LIB/RT_F_MUL.OBJ",
        "LIB/RT_F_DIV.OBJ",
        "LIB/RT_F_CMP.OBJ",
        "LIB/RT_F_ABS.OBJ",
        "LIB/RT_F_SQRT.OBJ",
    ],
)
_add_derived_math1_core_split_case(
    "actc_runtime_math1_real_add_split_linked",
    "real_printre_add",
    _MATH1_ALL_CORE_RUNTIME_OBJECTS,
    [
        "LIB/RT_F_TO_I.OBJ",
        "LIB/RT_F_SUB.OBJ",
        "LIB/RT_F_MUL.OBJ",
        "LIB/RT_F_DIV.OBJ",
        "LIB/RT_F_CMP.OBJ",
        "LIB/RT_F_ABS.OBJ",
        "LIB/RT_F_SQRT.OBJ",
    ],
)
_add_derived_math1_core_split_case(
    "actc_runtime_math1_real_sub_split_linked",
    "real_printre_sub",
    _MATH1_ALL_CORE_RUNTIME_OBJECTS,
    [
        "LIB/RT_F_TO_I.OBJ",
        "LIB/RT_F_ADD.OBJ",
        "LIB/RT_F_MUL.OBJ",
        "LIB/RT_F_DIV.OBJ",
        "LIB/RT_F_CMP.OBJ",
        "LIB/RT_F_ABS.OBJ",
        "LIB/RT_F_SQRT.OBJ",
    ],
)
_add_derived_math1_core_split_case(
    "actc_runtime_math1_real_mul_split_linked",
    "real_printre_mul",
    _MATH1_ALL_CORE_RUNTIME_OBJECTS,
    [
        "LIB/RT_F_TO_I.OBJ",
        "LIB/RT_F_ADD.OBJ",
        "LIB/RT_F_SUB.OBJ",
        "LIB/RT_F_DIV.OBJ",
        "LIB/RT_F_CMP.OBJ",
        "LIB/RT_F_ABS.OBJ",
        "LIB/RT_F_SQRT.OBJ",
    ],
)
_add_derived_math1_core_split_case(
    "actc_runtime_math1_real_div_split_linked",
    "real_printre_fraction",
    _MATH1_ALL_CORE_RUNTIME_OBJECTS,
    [
        "LIB/RT_F_TO_I.OBJ",
        "LIB/RT_F_ADD.OBJ",
        "LIB/RT_F_SUB.OBJ",
        "LIB/RT_F_MUL.OBJ",
        "LIB/RT_F_CMP.OBJ",
        "LIB/RT_F_ABS.OBJ",
        "LIB/RT_F_SQRT.OBJ",
    ],
)
_add_derived_math1_core_split_case(
    "actc_runtime_math1_real_cmp_split_linked",
    "real_if_gt",
    _MATH1_ALL_CORE_RUNTIME_OBJECTS,
    [
        "LIB/RT_S_TO_F.OBJ",
        "LIB/RT_F_TO_I.OBJ",
        "LIB/RT_F_ADD.OBJ",
        "LIB/RT_F_SUB.OBJ",
        "LIB/RT_F_MUL.OBJ",
        "LIB/RT_F_DIV.OBJ",
        "LIB/RT_F_ABS.OBJ",
        "LIB/RT_F_SQRT.OBJ",
        "LIB/RT_PRINT_F.OBJ",
    ],
)


def _add_derived_sidspr1_sid_split_case(
    name: str,
    source_case: str,
    runtime_library_objects: list[str],
    unexpected_alink_loads: list[str],
) -> None:
    case = dict(DIRECT_PRG_CASES[source_case])
    case["runtime_library_objects"] = runtime_library_objects
    case["unexpected_alink_loads"] = unexpected_alink_loads
    DIRECT_PRG_CASES[name] = case


def _sidspr1_sid_gate_constant_tail(helper_name: str) -> bytes:
    modules = _runtime_module_closure([helper_name])
    root_len = 2 + 3 + len(_DIRECT_PRG_EXIT_MARKER)
    module_addrs = _runtime_module_addrs(modules, DIRECT_PRG_LOAD_ADDR + root_len)
    code = bytes([0xA9, 0x01]) + _jsr(module_addrs[helper_name]) + _DIRECT_PRG_EXIT_MARKER
    if len(code) != root_len:
        raise RuntimeError(f"unexpected SID gate root size: {len(code)}")
    return code + b"".join(
        _linked_runtime_module_bytes(module, module_addrs) for module in modules
    )


_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_vol_split_linked",
    "actc_runtime_sid_vol_helper_linked",
    [
        "rt_sid_vol",
        "rt_sid_volume_state",
        "rt_sid_mode",
        "rt_sid_freq",
        "rt_sid_pulse",
        "rt_sid_filter_state",
    ],
    [
        "LIB/RT_SID_MODE.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
        "LIB/RT_SID_PULSE.OBJ",
        "LIB/RT_SID_FILTER_STATE.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_freq_split_linked",
    "actc_runtime_sid_freq_helper_linked",
    [
        "rt_sid_freq",
        "rt_sid_pulse",
        "rt_sid_ad",
        "rt_sid_sr",
    ],
    [
        "LIB/RT_SID_PULSE.OBJ",
        "LIB/RT_SID_AD.OBJ",
        "LIB/RT_SID_SR.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_pulse_split_linked",
    "actc_runtime_sid_pulse_helper_linked",
    [
        "rt_sid_pulse",
        "rt_sid_freq",
        "rt_sid_ad",
        "rt_sid_sr",
    ],
    [
        "LIB/RT_SID_FREQ.OBJ",
        "LIB/RT_SID_AD.OBJ",
        "LIB/RT_SID_SR.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_ad_split_linked",
    "actc_runtime_sid_ad_helper_linked",
    [
        "rt_sid_ad",
        "rt_sid_sr",
        "rt_sid_wave",
        "rt_sid_freq",
    ],
    [
        "LIB/RT_SID_SR.OBJ",
        "LIB/RT_SID_WAVE.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_sr_split_linked",
    "actc_runtime_sid_sr_helper_linked",
    [
        "rt_sid_sr",
        "rt_sid_ad",
        "rt_sid_wave",
        "rt_sid_freq",
    ],
    [
        "LIB/RT_SID_AD.OBJ",
        "LIB/RT_SID_WAVE.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_route_split_linked",
    "actc_runtime_sid_route_helper_linked",
    [
        "rt_sid_route",
        "rt_sid_filter_state",
        "rt_sid_res",
        "rt_sid_freq",
        "rt_sid_vol",
    ],
    [
        "LIB/RT_SID_RES.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
        "LIB/RT_SID_VOL.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_res_split_linked",
    "actc_runtime_sid_res_helper_linked",
    [
        "rt_sid_res",
        "rt_sid_filter_state",
        "rt_sid_route",
        "rt_sid_freq",
        "rt_sid_vol",
    ],
    [
        "LIB/RT_SID_ROUTE.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
        "LIB/RT_SID_VOL.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_cutoff_split_linked",
    "actc_runtime_sid_cutoff_helper_linked",
    [
        "rt_sid_cutoff",
        "rt_sid_res",
        "rt_sid_freq",
        "rt_sid_route",
    ],
    [
        "LIB/RT_SID_RES.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
        "LIB/RT_SID_ROUTE.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_mode_split_linked",
    "actc_runtime_sid_mode_helper_linked",
    [
        "rt_sid_mode",
        "rt_sid_volume_state",
        "rt_sid_vol",
        "rt_sid_freq",
        "rt_sid_wave",
    ],
    [
        "LIB/RT_SID_VOL.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
        "LIB/RT_SID_WAVE.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_wave_split_linked",
    "actc_runtime_sid_wave_helper_linked",
    [
        "rt_sid_wave",
        "rt_sid_state",
        "rt_sid_on",
        "rt_sid_off",
        "rt_sid_freq",
    ],
    [
        "LIB/RT_SID_ON.OBJ",
        "LIB/RT_SID_OFF.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
    ],
)
DIRECT_PRG_CASES["actc_runtime_sidspr1_sid_on_split_linked"] = {
    "source": "MODULE MAIN\rPROC MAIN()\rSidOn(1)\rRETURN\r",
    "has_stub": False,
    "runtime_library_objects": [
        "rt_sid_on",
        "rt_sid_state",
        "rt_sid_off",
        "rt_sid_wave",
    ],
    "expected_object_fragments": [
        "b p0u0r\n",
        "u rt_sid_on\n",
        "i 1\n",
    ],
    "expected_tail": _sidspr1_sid_gate_constant_tail("rt_sid_on"),
    "store_check_addr": 0xD40B,
    "store_check_value": 0x01,
    "expected_alink_loads": ["LIB/RT_SID_ON.OBJ", "LIB/RT_SID_STATE.OBJ"],
    "unexpected_alink_loads": [
        "LIB/RT_SID_OFF.OBJ",
        "LIB/RT_SID_WAVE.OBJ",
    ],
}
DIRECT_PRG_CASES["actc_runtime_sidspr1_sid_off_split_linked"] = {
    "source": "MODULE MAIN\rPROC MAIN()\rSidOff(1)\rRETURN\r",
    "has_stub": False,
    "runtime_library_objects": [
        "rt_sid_off",
        "rt_sid_state",
        "rt_sid_on",
        "rt_sid_wave",
    ],
    "expected_object_fragments": [
        "b p0u0r\n",
        "u rt_sid_off\n",
        "i 1\n",
    ],
    "expected_tail": _sidspr1_sid_gate_constant_tail("rt_sid_off"),
    "pre_run_memory": [
        {"addr": 0xD40B, "value": 0x01},
    ],
    "store_check_addr": 0xD40B,
    "store_check_value": 0x00,
    "expected_alink_loads": ["LIB/RT_SID_OFF.OBJ", "LIB/RT_SID_STATE.OBJ"],
    "unexpected_alink_loads": [
        "LIB/RT_SID_ON.OBJ",
        "LIB/RT_SID_WAVE.OBJ",
    ],
}
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_rst_split_linked",
    "actc_runtime_sid_rst_helper_linked",
    [
        "rt_sid_rst",
        "rt_sid_state",
        "rt_sid_filter_state",
        "rt_sid_volume_state",
        "rt_sid_on",
        "rt_sid_vol",
        "rt_sid_route",
    ],
    [
        "LIB/RT_SID_ON.OBJ",
        "LIB/RT_SID_VOL.OBJ",
        "LIB/RT_SID_ROUTE.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_osc3_split_linked",
    "actc_runtime_sid_osc3_helper_linked",
    [
        "rt_sid_osc3",
        "rt_sid_env3",
        "rt_sid_freq",
    ],
    [
        "LIB/RT_SID_ENV3.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
    ],
)
_add_derived_sidspr1_sid_split_case(
    "actc_runtime_sidspr1_sid_env3_split_linked",
    "actc_runtime_sid_env3_helper_linked",
    [
        "rt_sid_env3",
        "rt_sid_osc3",
        "rt_sid_freq",
    ],
    [
        "LIB/RT_SID_OSC3.OBJ",
        "LIB/RT_SID_FREQ.OBJ",
    ],
)


def _add_derived_sidspr1_sprite_split_case(
    name: str,
    source_case: str,
    runtime_library_objects: list[str],
    unexpected_alink_loads: list[str],
) -> None:
    case = dict(DIRECT_PRG_CASES[source_case])
    case["runtime_library_objects"] = runtime_library_objects
    case["unexpected_alink_loads"] = unexpected_alink_loads
    DIRECT_PRG_CASES[name] = case


_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_color_split_linked",
    "actc_runtime_sprite_color_helper_linked",
    ["rt_sprite_color", "rt_sprite_pos", "rt_sprite_ptr", "rt_sprite_on"],
    ["LIB/RT_SPRITE_POS.OBJ", "LIB/RT_SPRITE_PTR.OBJ", "LIB/RT_SPRITE_ON.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_data_split_linked",
    "actc_runtime_sprite_data_helper_linked",
    ["rt_sprite_data", "rt_sprite_ptr", "rt_sprite_pos", "rt_sprite_color"],
    ["LIB/RT_SPRITE_PTR.OBJ", "LIB/RT_SPRITE_POS.OBJ", "LIB/RT_SPRITE_COLOR.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_ptr_split_linked",
    "actc_runtime_sprite_ptr_helper_linked",
    ["rt_sprite_ptr", "rt_sprite_data", "rt_sprite_pos", "rt_sprite_color"],
    ["LIB/RT_SPRITE_DATA.OBJ", "LIB/RT_SPRITE_POS.OBJ", "LIB/RT_SPRITE_COLOR.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_pos_split_linked",
    "actc_runtime_sprite_pos_helper_linked",
    ["rt_sprite_pos", "rt_sprite_color", "rt_sprite_ptr", "rt_sprite_data"],
    ["LIB/RT_SPRITE_COLOR.OBJ", "LIB/RT_SPRITE_PTR.OBJ", "LIB/RT_SPRITE_DATA.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_on_split_linked",
    "actc_runtime_sprite_on_helper_linked",
    ["rt_sprite_on", "rt_sprite_off", "rt_sprite_mc", "rt_sprite_xexp"],
    ["LIB/RT_SPRITE_OFF.OBJ", "LIB/RT_SPRITE_MC.OBJ", "LIB/RT_SPRITE_XEXP.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_off_split_linked",
    "actc_runtime_sprite_off_helper_linked",
    ["rt_sprite_off", "rt_sprite_on", "rt_sprite_mc", "rt_sprite_xexp"],
    ["LIB/RT_SPRITE_ON.OBJ", "LIB/RT_SPRITE_MC.OBJ", "LIB/RT_SPRITE_XEXP.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_hit_split_linked",
    "actc_runtime_sprite_hit_helper_linked",
    ["rt_sprite_hit", "rt_sprite_hit_bg", "rt_sprite_on"],
    ["LIB/RT_SPRITE_HIT_BG.OBJ", "LIB/RT_SPRITE_ON.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_hit_bg_split_linked",
    "actc_runtime_sprite_hit_bg_helper_linked",
    ["rt_sprite_hit_bg", "rt_sprite_hit", "rt_sprite_off"],
    ["LIB/RT_SPRITE_HIT.OBJ", "LIB/RT_SPRITE_OFF.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_mc_split_linked",
    "actc_runtime_sprite_mc_helper_linked",
    ["rt_sprite_mc", "rt_sprite_xexp", "rt_sprite_yexp", "rt_sprite_prio"],
    ["LIB/RT_SPRITE_XEXP.OBJ", "LIB/RT_SPRITE_YEXP.OBJ", "LIB/RT_SPRITE_PRIO.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_xexp_split_linked",
    "actc_runtime_sprite_xexp_helper_linked",
    ["rt_sprite_xexp", "rt_sprite_mc", "rt_sprite_yexp", "rt_sprite_prio"],
    ["LIB/RT_SPRITE_MC.OBJ", "LIB/RT_SPRITE_YEXP.OBJ", "LIB/RT_SPRITE_PRIO.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_yexp_split_linked",
    "actc_runtime_sprite_yexp_helper_linked",
    ["rt_sprite_yexp", "rt_sprite_mc", "rt_sprite_xexp", "rt_sprite_prio"],
    ["LIB/RT_SPRITE_MC.OBJ", "LIB/RT_SPRITE_XEXP.OBJ", "LIB/RT_SPRITE_PRIO.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_prio_split_linked",
    "actc_runtime_sprite_prio_helper_linked",
    ["rt_sprite_prio", "rt_sprite_mc", "rt_sprite_xexp", "rt_sprite_yexp"],
    ["LIB/RT_SPRITE_MC.OBJ", "LIB/RT_SPRITE_XEXP.OBJ", "LIB/RT_SPRITE_YEXP.OBJ"],
)
_add_derived_sidspr1_sprite_split_case(
    "actc_runtime_sidspr1_sprite_set_mc_split_linked",
    "actc_runtime_sprite_set_mc_helper_linked",
    ["rt_sprite_set_mc", "rt_sprite_color", "rt_sprite_mc", "rt_sprite_prio"],
    ["LIB/RT_SPRITE_COLOR.OBJ", "LIB/RT_SPRITE_MC.OBJ", "LIB/RT_SPRITE_PRIO.OBJ"],
)


def direct_prg_case(shape: str) -> dict[str, object]:
    return DIRECT_PRG_CASES[shape]


def install_program(fs_root: Path, project_root: Path, build_path: Path, name: str) -> None:
    if not build_path.is_file():
        raise RuntimeError(f"missing built program: {build_path}")
    lowercase_workspace = pfs.detect_lowercase_workspace(fs_root)
    images_root = pfs.case_insensitive_child(fs_root, pfs.host_name("IMAGES", lowercase_workspace))
    action_root = pfs.case_insensitive_child(images_root, pfs.host_name("ACTION.DNP", lowercase_workspace))
    root_target = action_root / pfs.host_name(name, lowercase_workspace)
    shutil.copy2(build_path, root_target)
    pfs.sync_case_siblings(root_target)
    project_target = project_root / name
    shutil.copy2(root_target, project_target)
    pfs.sync_case_siblings(project_target)
    pfs.ensure_catalog_entries(
        action_root / pfs.host_name("UDOSDIR.TXT", lowercase_workspace),
        [f"D {project_root.name.upper()}", f"F {name}"],
    )
    pfs.sync_case_siblings(action_root / pfs.host_name("UDOSDIR.TXT", lowercase_workspace))
    project_catalog = pfs.case_insensitive_child(project_root, "UDOSDIR.TXT")
    pfs.ensure_catalog_entries(project_catalog, [f"F {name}"])
    pfs.sync_case_siblings(project_catalog)


def stage_case_files(project_root: Path, shape: str) -> None:
    case = direct_prg_case(shape)
    extra_files = case.get("extra_files", {})
    if not isinstance(extra_files, dict) or not extra_files:
        return
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    for name, payload in extra_files.items():
        if not isinstance(name, str) or not name:
            continue
        parts = [part for part in name.replace("\\", "/").split("/") if part]
        if not parts or any(part in {".", ".."} for part in parts):
            continue
        parent = project_root
        for directory in parts[:-1]:
            host_directory = pfs.host_name(directory, lowercase_workspace)
            pfs.ensure_catalog_entries(
                parent / pfs.host_name("UDOSDIR.TXT", lowercase_workspace),
                [f"D {directory.upper()}"],
            )
            parent = parent / host_directory
            parent.mkdir(parents=True, exist_ok=True)
            catalog = parent / pfs.host_name("UDOSDIR.TXT", lowercase_workspace)
            if not catalog.exists():
                pfs.write_ascii(catalog, "")
        filename = parts[-1]
        target = parent / pfs.host_name(filename, lowercase_workspace)
        if isinstance(payload, bytes):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        else:
            pfs.write_ascii(target, str(payload))
        pfs.sync_case_siblings(target)
        pfs.ensure_catalog_entries(
            parent / pfs.host_name("UDOSDIR.TXT", lowercase_workspace),
            [f"F {filename.upper()}"],
        )
        pfs.sync_case_siblings(parent / pfs.host_name("UDOSDIR.TXT", lowercase_workspace))


def prepare_workspace(fs_root: Path, project_name: str, shape: str) -> tuple[Path, str]:
    case = direct_prg_case(shape)
    lowercase_workspace = pfs.detect_lowercase_workspace(fs_root)
    images_root = pfs.case_insensitive_child(fs_root, pfs.host_name("IMAGES", lowercase_workspace))
    action_root = pfs.case_insensitive_child(images_root, pfs.host_name("ACTION.DNP", lowercase_workspace))
    project_root = action_root / project_name.upper()
    lower_project_root = project_root.parent / project_root.name.lower()
    shutil.rmtree(project_root, ignore_errors=True)
    shutil.rmtree(lower_project_root, ignore_errors=True)

    src_root = project_root / "SRC"
    bin_root = project_root / "BIN"
    obj_root = project_root / "OBJ"
    src_root.mkdir(parents=True, exist_ok=True)
    bin_root.mkdir(exist_ok=True)
    obj_root.mkdir(exist_ok=True)

    pfs.write_ascii(project_root / "README.TXT", "ACTION PROJECT READY\n")
    pfs.write_ascii(project_root / "ACTION.PROJ", "ACTION PROJECT\rMAIN.ACT\r")
    pfs.write_ascii(
        project_root / "UDOSDIR.TXT",
        "D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n",
    )
    pfs.write_ascii(bin_root / "UDOSDIR.TXT", "")
    if "source" in case:
        pfs.write_ascii(src_root / "UDOSDIR.TXT", "F MAIN.ACT\n")
        pfs.write_ascii(src_root / "MAIN.ACT", str(case["source"]))
    else:
        pfs.write_ascii(src_root / "UDOSDIR.TXT", "")
    if "seed_object" in case:
        pfs.write_ascii(obj_root / "UDOSDIR.TXT", "F MAIN.OBJ\n")
        pfs.write_ascii(obj_root / "MAIN.OBJ", str(case["seed_object"]))
    else:
        pfs.write_ascii(obj_root / "UDOSDIR.TXT", "")

    extra_project_objects = case.get("extra_objects", {})
    if isinstance(extra_project_objects, dict) and extra_project_objects:
        entries: list[str] = []
        for name, text in extra_project_objects.items():
            if not isinstance(name, str) or not name or not isinstance(text, str):
                continue
            target = obj_root / name.upper()
            pfs.write_ascii(target, text)
            pfs.sync_case_siblings(target)
            entries.append(f"F {name.upper()}")
        if entries:
            pfs.ensure_catalog_entries(obj_root / "UDOSDIR.TXT", entries)
            pfs.sync_case_siblings(obj_root / "UDOSDIR.TXT")

    extra_library_objects = case.get("extra_library_objects", {})
    if isinstance(extra_library_objects, dict) and extra_library_objects:
        lib_root = project_root / "LIB"
        lib_root.mkdir(parents=True, exist_ok=True)
        entries = []
        for name, text in extra_library_objects.items():
            if not isinstance(name, str) or not name or not isinstance(text, str):
                continue
            target = lib_root / name.upper()
            pfs.write_ascii(target, text)
            pfs.sync_case_siblings(target)
            entries.append(f"F {name.upper()}")
        if entries:
            pfs.ensure_catalog_entries(lib_root / "UDOSDIR.TXT", entries)
            pfs.sync_case_siblings(lib_root / "UDOSDIR.TXT")
            pfs.ensure_catalog_entries(project_root / "UDOSDIR.TXT", ["D LIB"])
            pfs.sync_case_siblings(project_root / "UDOSDIR.TXT")

    runtime_library_objects = case.get("runtime_library_objects", [])
    if isinstance(runtime_library_objects, list) and runtime_library_objects:
        lib_root = project_root / "LIB"
        lib_root.mkdir(parents=True, exist_ok=True)
        entries = []
        for module_name in runtime_library_objects:
            if not isinstance(module_name, str) or not module_name:
                continue
            source_path = UDOS_RUNTIME_MODULES / f"{module_name}.obj"
            if not source_path.is_file():
                raise RuntimeError(f"missing runtime OBJ module: {source_path}")
            target_name = module_name.upper() + ".OBJ"
            target = lib_root / target_name
            shutil.copy2(source_path, target)
            pfs.sync_case_siblings(target)
            entries.append(f"F {target_name}")
        if entries:
            pfs.ensure_catalog_entries(lib_root / "UDOSDIR.TXT", entries)
            pfs.sync_case_siblings(lib_root / "UDOSDIR.TXT")
            pfs.ensure_catalog_entries(project_root / "UDOSDIR.TXT", ["D LIB"])
            pfs.sync_case_siblings(project_root / "UDOSDIR.TXT")

    stage_case_files(project_root, shape)
    install_program(fs_root, project_root, ACTION_ALINK_BUILD, "ALINK.PRG")
    pfs.add_case_aliases(project_root)
    if lower_project_root != project_root and not lower_project_root.exists():
        lower_project_root.symlink_to(project_root.name, target_is_directory=True)
    mount_path = f"/{images_root.name}/{action_root.name}"
    return project_root, mount_path


def host_prg_path(project_root: Path) -> Path:
    return pfs.project_output_path(project_root, "BIN", "MAIN.PRG")


def ensure_host_prg_catalog(project_root: Path) -> None:
    bin_root = pfs.case_insensitive_child(project_root, "BIN")
    catalog = pfs.case_insensitive_child(bin_root, "UDOSDIR.TXT")
    pfs.ensure_catalog_entries(catalog, ["F MAIN.PRG"])
    pfs.sync_case_siblings(catalog)

    prg_path = host_prg_path(project_root)
    if prg_path.is_file():
        pfs.sync_case_siblings(prg_path)


def verify_host_output(project_root: Path, shape: str) -> Path:
    case = direct_prg_case(shape)
    prg_path = host_prg_path(project_root)
    if not prg_path.is_file():
        raise RuntimeError(f"expected direct PRG {prg_path} to exist")
    prg_bytes = prg_path.read_bytes()
    expected_tail = bytes(case["expected_tail"])
    min_payload_prefix = DIRECT_PRG_STUB_SIZE if bool(case.get("has_stub", True)) else 0
    if len(prg_bytes) < 2 + min_payload_prefix + len(expected_tail):
        raise RuntimeError(f"direct PRG too small: {len(prg_bytes)} bytes")
    load_addr = prg_bytes[0] | (prg_bytes[1] << 8)
    if load_addr != DIRECT_PRG_LOAD_ADDR:
        raise RuntimeError(f"unexpected direct PRG load address: 0x{load_addr:04X}")
    if prg_bytes[-len(expected_tail):] != expected_tail:
        got = prg_bytes[-len(expected_tail):].hex()
        raise RuntimeError(f"unexpected direct PRG payload tail for {shape}: {got}")
    return prg_path


def patch_prg_to_spin_after_marker(prg_path: Path) -> None:
    prg_bytes = bytearray(prg_path.read_bytes())
    if len(prg_bytes) < 2:
        raise RuntimeError(f"direct PRG missing load address: {prg_path}")
    load_addr = prg_bytes[0] | (prg_bytes[1] << 8)
    marker_exit = bytes.fromhex("A9A58DD003A90085028503A2024C0FCF")
    marker_index = bytes(prg_bytes).rfind(marker_exit)
    if marker_index < 0:
        raise RuntimeError(f"direct PRG marker/exit sequence not found: {prg_path}")
    jmp_index = marker_index + len(marker_exit) - 3
    jmp_addr = load_addr + jmp_index - 2
    prg_bytes[jmp_index : jmp_index + 3] = bytes([0x4C, jmp_addr & 0xFF, jmp_addr >> 8])
    prg_path.write_bytes(prg_bytes)
    pfs.sync_case_siblings(prg_path)


def verify_actc_object_output(project_root: Path, shape: str) -> None:
    case = direct_prg_case(shape)
    fragments = case.get("expected_object_fragments", [])
    if not isinstance(fragments, list) or not fragments:
        return
    obj_path = pfs.project_output_path(project_root, "OBJ", "MAIN.OBJ")
    if not obj_path.is_file():
        raise RuntimeError(f"expected ACTC object {obj_path} to exist")
    text = obj_path.read_text(encoding="ascii")
    missing = [fragment for fragment in fragments if isinstance(fragment, str) and fragment not in text]
    if missing:
        raise RuntimeError(f"ACTC object {obj_path} missing expected fragments: {missing!r}\n{text}")


def run_harness(prg: Path, labels: Path, project_root: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            str(TOOL_ABI_HARNESS),
            "--prg",
            str(prg),
            "--workspace",
            str(project_root),
            "--cmdline",
            "MAIN",
            "--services-inc",
            str(UDOS_SERVICES_INC),
            "--labels",
            str(labels),
            "--max-steps",
            "12000000",
        ],
        cwd=ACTION_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    summary = json.loads(result.stdout)
    if int(summary.get("exit_status", 1)) != 0:
        raise RuntimeError(result.stdout + result.stderr)
    return summary


def verify_alink_dependency_loads(summary: dict[str, object], shape: str) -> None:
    case = direct_prg_case(shape)
    expected_loads = case.get("expected_alink_loads", [])
    unexpected_loads = case.get("unexpected_alink_loads", [])
    if (
        (not isinstance(expected_loads, list) or not expected_loads)
        and (not isinstance(unexpected_loads, list) or not unexpected_loads)
    ):
        return
    ops = summary.get("ops", [])
    if not isinstance(ops, list):
        raise RuntimeError("ALINK harness summary did not include file operations")
    loaded_paths: set[str] = set()
    for op in ops:
        if not isinstance(op, dict):
            continue
        path = op.get("path")
        if isinstance(path, str):
            loaded_paths.add(path.upper())
    missing = [
        path
        for path in expected_loads
        if isinstance(path, str) and path.upper() not in loaded_paths
    ]
    if missing:
        raise RuntimeError(f"ALINK did not load expected dependency objects: {missing}")
    unexpected = [
        path
        for path in unexpected_loads
        if isinstance(path, str) and path.upper() in loaded_paths
    ]
    if unexpected:
        raise RuntimeError(f"ALINK loaded unexpected dependency objects: {unexpected}")


def expect_alink_rejection(project_root: Path, shape: str) -> dict[str, object]:
    case = direct_prg_case(shape)
    try:
        run_harness(ACTION_ALINK_BUILD, ACTION_ALINK_LABELS, project_root)
    except RuntimeError as exc:
        prg_path = host_prg_path(project_root)
        if prg_path.exists():
            raise RuntimeError(f"ALINK rejected {shape} but still emitted {prg_path}") from exc
        error_text = str(exc).strip()
        console = ""
        exit_status: int | None = None
        failure_summary: dict[str, object] | None = None
        try:
            decoded = json.loads(error_text)
            if isinstance(decoded, dict):
                failure_summary = decoded
                raw_console = decoded.get("console", "")
                if isinstance(raw_console, str):
                    console = raw_console.strip()
                raw_status = decoded.get("exit_status")
                if isinstance(raw_status, int):
                    exit_status = raw_status
        except json.JSONDecodeError:
            pass
        if failure_summary is not None:
            verify_alink_dependency_loads(failure_summary, shape)
        expected_error = case.get("expected_alink_error")
        if isinstance(expected_error, str) and expected_error:
            diagnostic = console or error_text
            if expected_error not in diagnostic:
                raise RuntimeError(f"expected ALINK diagnostic {expected_error!r}, got {diagnostic!r}") from exc
        return {
            "shape": shape,
            "alink_rejected": True,
            "exit_status": exit_status,
            "console": console,
        }
    raise RuntimeError(f"expected ALINK to reject unsupported body for {shape}")


def _monitor_store_kwargs(addr: int) -> dict[str, int]:
    """Read/write C64 I/O registers through the VICE I/O bank, not CPU-visible RAM."""
    if 0xD000 <= (addr & 0xFFFF) <= 0xDFFF:
        return {"memspace": vp.MAIN_MEMSPACE, "bank": vp.MAIN_BANK_IO}
    return {}


def _monitor_memory_get_byte(client: vp.BinaryMonitorClient, addr: int) -> int:
    return client.memory_get(addr, addr, **_monitor_store_kwargs(addr))[0]


def _monitor_memory_set_byte(client: vp.BinaryMonitorClient, addr: int, value: int) -> None:
    client.memory_set(addr, bytes([value & 0xFF]), **_monitor_store_kwargs(addr))


def log_progress(verbose: bool, payload: dict[str, object]) -> None:
    if verbose:
        print(payload, flush=True)


def run_prg_phase(
    image: Path,
    work_root: Path,
    project_name: str,
    mount_path: str,
    connect_delay: float,
    prg_path: Path,
    shape: str,
    shell_timeout: float = ALINK_PHASE_TIMEOUT,
    verbose: bool = False,
) -> dict[str, object]:
    case = direct_prg_case(shape)
    ensure_host_prg_catalog(prg_path.parent.parent)
    prompt_timeout = min(shell_timeout, 45.0)
    mount_timeout = min(shell_timeout, 90.0)
    port = vp.reserve_tcp_port()
    process = vp.launch_vice(
        image,
        port,
        extra_args=[
            "-iecdevice9",
            "-fs9",
            str(work_root),
            "-fslongnames",
        ],
    )
    client = vp.BinaryMonitorClient("127.0.0.1", port, timeout=5.0)
    project_prompt = f"B:DNP/{project_name}>"
    bin_prompt = f"B:DNP/{project_name}/BIN>"
    try:
        log_progress(verbose, {"stage": "connect", "port": port})
        client.connect(time.monotonic() + connect_delay)
        client.ping()
        client.resume()

        log_progress(verbose, {"stage": "mount", "mount_path": mount_path})
        avp.wait_for_screen_fragments(client, ["A:D64/>"], prompt_timeout)
        time.sleep(INITIAL_SETTLE)
        mount_command = f"MOUNT B: {mount_path}"
        avp.type_command(client, mount_command, prompt_timeout)
        time.sleep(1.0)
        try:
            avp.wait_for_mount_completion(client, mount_timeout, retry_echo=mount_command)
        except vp.ViceError:
            avp.type_command(client, mount_command, prompt_timeout)
            time.sleep(1.0)
            avp.wait_for_mount_completion(client, mount_timeout, retry_echo=mount_command)
        avp.type_command(client, "B:", prompt_timeout)
        avp.wait_for_screen_fragments(client, ["B:DNP/>"], prompt_timeout, retry_echo="B:")
        cd_command = f"CD {project_name}"
        avp.type_command(client, cd_command, prompt_timeout)
        avp.wait_for_screen_fragments(client, [project_prompt], prompt_timeout, retry_echo=cd_command)

        log_progress(
            verbose,
            {
                "stage": "launch_prg",
                "prg_path": str(prg_path),
                "marker_addr": f"0x{DIRECT_PRG_EXIT_MARKER_ADDR:04X}",
                "marker_value": f"0x{DIRECT_PRG_EXIT_MARKER_VALUE:02X}",
            },
        )
        avp.type_command(client, "CD BIN", PRG_PHASE_TIMEOUT)
        avp.wait_for_screen_fragments(client, [bin_prompt], PRG_PHASE_TIMEOUT)
        pre_run_memory = case.get("pre_run_memory", [])
        if isinstance(pre_run_memory, list):
            for init in pre_run_memory:
                if not isinstance(init, dict):
                    continue
                addr = int(init["addr"])
                value = int(init["value"]) & 0xFF
                _monitor_memory_set_byte(client, addr, value)
        client.memory_set(DIRECT_PRG_EXIT_MARKER_ADDR, b"\x00")
        avp.type_command(client, "MAIN.PRG", PRG_PHASE_TIMEOUT)
        deadline = time.monotonic() + PRG_PHASE_TIMEOUT
        last_screen = ""
        last_marker = 0
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise vp.ViceError("x64sc exited while waiting for direct PRG marker")
            last_marker = client.memory_get(DIRECT_PRG_EXIT_MARKER_ADDR, DIRECT_PRG_EXIT_MARKER_ADDR)[0]
            if last_marker == DIRECT_PRG_EXIT_MARKER_VALUE:
                last_screen = avp.screen_text(client)
                result = {
                    "prg_path": str(prg_path),
                    "marker": last_marker,
                    "screen": last_screen,
                }
                if "store_check_addr" in case:
                    store_addr = int(case["store_check_addr"])
                    store_value = _monitor_memory_get_byte(client, store_addr)
                    expected_value = int(case["store_check_value"])
                    store_mask = int(case.get("store_check_mask", 0xFF))
                    comparable_value = store_value & store_mask
                    comparable_expected = expected_value & store_mask
                    if comparable_value != comparable_expected:
                        raise vp.ViceError(
                            f"direct PRG store check failed at 0x{store_addr:04X}: "
                            f"got 0x{store_value:02X}, expected 0x{expected_value:02X} "
                            f"with mask 0x{store_mask:02X}\n"
                            f"screen:\n{last_screen}"
                        )
                    result["store_addr"] = store_addr
                    result["store_value"] = store_value
                    result["store_mask"] = store_mask
                if "store_check_hi_addr" in case:
                    store_addr = int(case["store_check_hi_addr"])
                    store_value = _monitor_memory_get_byte(client, store_addr)
                    expected_value = int(case["store_check_hi_value"])
                    store_mask = int(case.get("store_check_hi_mask", 0xFF))
                    comparable_value = store_value & store_mask
                    comparable_expected = expected_value & store_mask
                    if comparable_value != comparable_expected:
                        raise vp.ViceError(
                            f"direct PRG store check failed at 0x{store_addr:04X}: "
                            f"got 0x{store_value:02X}, expected 0x{expected_value:02X} "
                            f"with mask 0x{store_mask:02X}\n"
                            f"screen:\n{last_screen}"
                        )
                    result["store_hi_addr"] = store_addr
                    result["store_hi_value"] = store_value
                    result["store_hi_mask"] = store_mask
                extra_checks = case.get("extra_store_checks", [])
                if isinstance(extra_checks, list):
                    for index, check in enumerate(extra_checks):
                        if not isinstance(check, dict):
                            continue
                        store_addr = int(check["addr"])
                        store_value = _monitor_memory_get_byte(client, store_addr)
                        expected_value = int(check["value"])
                        store_mask = int(check.get("mask", 0xFF))
                        comparable_value = store_value & store_mask
                        comparable_expected = expected_value & store_mask
                        if comparable_value != comparable_expected:
                            raise vp.ViceError(
                                f"direct PRG extra store check {index} failed at 0x{store_addr:04X}: "
                                f"got 0x{store_value:02X}, expected 0x{expected_value:02X} "
                                f"with mask 0x{store_mask:02X}\n"
                                f"screen:\n{last_screen}"
                            )
                        result[f"extra_store_{index}_addr"] = store_addr
                        result[f"extra_store_{index}_value"] = store_value
                        result[f"extra_store_{index}_mask"] = store_mask
                screen_fragments = case.get("screen_fragments", [])
                if isinstance(screen_fragments, list):
                    for fragment in screen_fragments:
                        if isinstance(fragment, str) and fragment and fragment not in last_screen:
                            raise vp.ViceError(
                                f"expected screen fragment {fragment!r} was not present after direct PRG launch\n"
                                f"screen:\n{last_screen}"
                            )
                return result
            time.sleep(0.01)
        last_screen = avp.screen_text(client)
        raise vp.ViceError(
            f"direct PRG exit marker not observed: got 0x{last_marker:02X}, expected 0x{DIRECT_PRG_EXIT_MARKER_VALUE:02X}\\n"
            f"screen:\n{last_screen}"
        )
    finally:
        try:
            client.quit_emulator()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass
        vp.terminate_process_tree(process)


def run_once(
    image: Path,
    work_root: Path,
    project_name: str,
    connect_delay: float,
    shape: str,
    skip_launch: bool = False,
    shell_timeout: float = ALINK_PHASE_TIMEOUT,
    verbose: bool = False,
) -> dict[str, object]:
    case = direct_prg_case(shape)
    project_root, mount_path = prepare_workspace(work_root, project_name, shape)
    pfs.add_case_aliases(project_root)

    if "source" in case:
        log_progress(verbose, {"stage": "actc_harness"})
        run_harness(ACTION_ACTC_HARNESS_BUILD, ACTION_ACTC_HARNESS_LABELS, project_root)
        pfs.add_case_aliases(project_root)
        verify_actc_object_output(project_root, shape)
    else:
        log_progress(verbose, {"stage": "seed_object"})
    log_progress(verbose, {"stage": "alink_harness"})
    if bool(case.get("expect_alink_failure", False)):
        return expect_alink_rejection(project_root, shape)
    alink_summary = run_harness(ACTION_ALINK_BUILD, ACTION_ALINK_LABELS, project_root)
    verify_alink_dependency_loads(alink_summary, shape)
    time.sleep(0.5)
    pfs.add_case_aliases(project_root)
    prg_path = verify_host_output(project_root, shape)
    ensure_host_prg_catalog(project_root)
    if skip_launch:
        return {"shape": shape, "launch_skipped": True, "prg_path": str(prg_path)}
    if bool(case.get("spin_after_marker_for_live", False)):
        patch_prg_to_spin_after_marker(prg_path)
    return run_prg_phase(
        image,
        work_root,
        project_name,
        mount_path,
        connect_delay,
        prg_path,
        shape,
        shell_timeout,
        verbose,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="VICE proof for ALINK direct PRG emission")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--shape", choices=sorted(DIRECT_PRG_CASES), default="word_store")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--attempt-delay", type=float, default=4.0)
    parser.add_argument("--shell-timeout", type=float, default=ALINK_PHASE_TIMEOUT)
    parser.add_argument("--skip-launch", action="store_true", help="verify ALINK output without launching VICE")
    parser.add_argument("--verbose", action="store_true", help="print progress and success payloads")
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f"{fs_root.name}-alink-prg-{args.shape}"

    last_error: Exception | None = None
    for attempt in range(1, args.attempts + 1):
        connect_delay = CONNECT_DELAYS[(attempt - 1) % len(CONNECT_DELAYS)]
        log_progress(
            args.verbose,
            {"attempt": attempt, "attempts": args.attempts, "connect_delay": connect_delay, "shape": args.shape},
        )
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root, symlinks=True, copy_function=shutil.copy)
            if not args.skip_launch:
                vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
            result = run_once(
                image,
                work_root,
                project_name,
                connect_delay,
                args.shape,
                args.skip_launch,
                args.shell_timeout,
                args.verbose,
            )
            log_progress(args.verbose, result)
            return 0
        except Exception as exc:
            last_error = exc
            if attempt == args.attempts:
                print(exc, file=sys.stderr)
                return 1
            time.sleep(args.attempt_delay)
    if last_error is not None:
        print(last_error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
