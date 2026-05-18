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
        "expected_tail": bytes.fromhex(
            "A9208502A9108503A2022003CF2006CFA9A58DD003A90085028503A2024C0FCF3700"
        ),
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
        "expected_tail": bytes.fromhex(
            "A9208502A9108503A2022003CF2006CFA9A58DD003A90085028503A2024C0FCF343200"
        ),
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
        "runtime_library_objects": ["rt_i_to_f", "rt_f_div", "rt_print_f"],
        "expected_tail": bytes.fromhex(
            "A9208502A9108503A2022003CF2006CFA9A58DD003A90085028503A2024C0FCF312E3500"
        ),
        "screen_fragments": ["1.5"],
        "expected_alink_loads": ["LIB/RT_I_TO_F.OBJ", "LIB/RT_F_DIV.OBJ", "LIB/RT_PRINT_F.OBJ"],
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
        "store_check_addr": 0xD40B,
        "store_check_value": 0x40,
        "extra_store_checks": [
            {"addr": 0x107C, "value": 0x40},
        ],
        "expected_alink_loads": [
            "LIB/RT_SID_WAVE.OBJ",
            "LIB/RT_SID_ON.OBJ",
            "LIB/RT_SID_OFF.OBJ",
            "LIB/RT_SID_STATE.OBJ",
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
    "runtime_sound_compat_helper_linked": {
        "seed_object": (
            "OBJ1\n"
            "x main 0 29\n"
            "b u0M\n"
            "u rt_sound\n"
            "m A9 06 85 02 A9 01 A2 34 A0 0A 20 00 00 A9 A5 8D D0 03 A9 00 85 02 85 03 A2 02 4C 0F CF\n"
            "r 11 u0\n"
            "n main\n"
        ),
        "has_stub": False,
        "runtime_library_objects": ["rt_sound", "rt_sid_state", "rt_sid_volume_state"],
        "expected_tail": bytes.fromhex(
            "A9068502A901A234A00A201D10A9A58DD003A90085028503A2024C0FCF"
            "850386048405A502290F8506A5030A0A0A38E5038507AAA9FF38E5048508"
            "0A0A0A0A0A9D00D4A5084A4A4A9D01D4A505C90CB00CC908B00CC904B00C"
            "A910D00AA980D006A940D002A92009018509A603A5099D8510A6079D04D4"
            "AD881029F005068D88108D18D460"
            "00000000"
        ),
        "store_check_addr": 0xD407,
        "store_check_value": 0x60,
        "store_check_hi_addr": 0xD408,
        "store_check_hi_value": 0x19,
        "extra_store_checks": [
            {"addr": 0xD40B, "value": 0x41},
            {"addr": 0x1086, "value": 0x41},
            {"addr": 0xD418, "value": 0x06},
            {"addr": 0x1088, "value": 0x06},
        ],
        "expected_alink_loads": [
            "LIB/RT_SOUND.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
    },
    "actc_runtime_sound_compat_helper_linked": {
        "source": "MODULE MAIN\rPROC MAIN()\rSound(1,52,10,6)\rRETURN\r",
        "has_stub": False,
        "runtime_library_objects": ["rt_sound", "rt_sid_state", "rt_sid_volume_state"],
        "expected_object_fragments": [
            "b p0p1p2p3u0r\n",
            "u rt_sound\n",
            "i 1\n",
            "i 52\n",
            "i 10\n",
            "i 6\n",
        ],
        "expected_tail": bytes.fromhex(
            "A9068502A901A234A00A201D10A9A58DD003A90085028503A2024C0FCF"
            "850386048405A502290F8506A5030A0A0A38E5038507AAA9FF38E5048508"
            "0A0A0A0A0A9D00D4A5084A4A4A9D01D4A505C90CB00CC908B00CC904B00C"
            "A910D00AA980D006A940D002A92009018509A603A5099D8510A6079D04D4"
            "AD881029F005068D88108D18D460"
            "00000000"
        ),
        "store_check_addr": 0xD407,
        "store_check_value": 0x60,
        "store_check_hi_addr": 0xD408,
        "store_check_hi_value": 0x19,
        "extra_store_checks": [
            {"addr": 0xD40B, "value": 0x41},
            {"addr": 0x1086, "value": 0x41},
            {"addr": 0xD418, "value": 0x06},
            {"addr": 0x1088, "value": 0x06},
        ],
        "expected_alink_loads": [
            "LIB/RT_SOUND.OBJ",
            "LIB/RT_SID_STATE.OBJ",
            "LIB/RT_SID_VOLUME_STATE.OBJ",
        ],
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
    "external_print_line": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu w\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "W.OBJ": "OBJ1\nx w 0 3\nb e0r\ns LINKED\nn w\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCFA9248502A9108503"
            "A2022003CF2006CF604C494E4B454400"
        ),
        "screen_fragments": ["linked"],
        "expected_alink_loads": ["LIB/W.OBJ"],
    },
    "external_return_call": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb r\nn a\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF60"),
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "external_store_call": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 7\nb p0S0r\ni 42\nv x 0\nn a\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCFA92AA2008DD1038ED20360"),
        "store_check_addr": 0x03D1,
        "store_check_value": 0x2A,
        "store_check_hi_addr": 0x03D2,
        "store_check_hi_value": 0x00,
        "expected_alink_loads": ["LIB/A.OBJ"],
    },
    "external_load_store_call": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 13\nb p0S0L0S1r\ni 42\nv x 0\nv y 0\nn a\n",
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
    "external_string_int_call": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 13\nb s0i0r\ns TOOL\ni 42\nn a\n",
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
    "external_return_pair": {
        "seed_object": "OBJ1\nx main 0 5\nb u0u1r\nu a\nu b\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 1\nb r\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb r\nn b\n",
        },
        "expected_tail": bytes.fromhex("201610201710A9A58DD003A90085028503A2024C0FCF6060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "transitive_external_print_line": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 3\nb u0r\nu b\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 3\nb e0r\ns DEEP\nn b\n",
        },
        "expected_tail": bytes.fromhex(
            "201310A9A58DD003A90085028503A2024C0FCF20171060"
            "A9288502A9108503A2022003CF2006CF604445455000"
        ),
        "screen_fragments": ["deep"],
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "transitive_external_return_call": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 3\nb u0r\nu b\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 1\nb r\nn b\n",
        },
        "expected_tail": bytes.fromhex("201310A9A58DD003A90085028503A2024C0FCF2017106060"),
        "expected_alink_loads": ["LIB/A.OBJ", "LIB/B.OBJ"],
    },
    "transitive_external_store_call": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 3\nb u0r\nu b\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 7\nb p0S0r\ni 42\nv x 0\nn b\n",
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
    "transitive_external_load_store_call": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 3\nb u0r\nu b\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 13\nb p0S0L0S1r\ni 42\nv x 0\nv y 0\nn b\n",
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
    "transitive_external_string_int_call": {
        "seed_object": "OBJ1\nx main 0 3\nb u0r\nu a\nn main\n",
        "has_stub": False,
        "extra_library_objects": {
            "A.OBJ": "OBJ1\nx a 0 3\nb u0r\nu b\nn a\n",
            "B.OBJ": "OBJ1\nx b 0 13\nb s0i0r\ns TOOL\ni 42\nn b\n",
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


def direct_prg_case(shape: str) -> dict[str, object]:
    return DIRECT_PRG_CASES[shape]


def install_program(fs_root: Path, project_root: Path, build_path: Path, name: str) -> None:
    if not build_path.is_file():
        raise RuntimeError(f"missing built program: {build_path}")
    lowercase_workspace = rap.detect_lowercase_workspace(fs_root)
    images_root = rap.case_insensitive_child(fs_root, rap.host_name("IMAGES", lowercase_workspace))
    action_root = rap.case_insensitive_child(images_root, rap.host_name("ACTION.DNP", lowercase_workspace))
    root_target = action_root / rap.host_name(name, lowercase_workspace)
    shutil.copy2(build_path, root_target)
    shutil.copy2(root_target, project_root / rap.host_name(name, lowercase_workspace))
    rap.ensure_catalog_entries(
        action_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace),
        [f"D {project_root.name.upper()}", f"F {name}"],
    )
    rap.ensure_catalog_entries(project_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), [f"F {name}"])


def prepare_workspace(fs_root: Path, project_name: str, shape: str) -> tuple[Path, str]:
    case = direct_prg_case(shape)
    lowercase_workspace = rap.detect_lowercase_workspace(fs_root)
    images_root = rap.case_insensitive_child(fs_root, rap.host_name("IMAGES", lowercase_workspace))
    action_root = rap.case_insensitive_child(images_root, rap.host_name("ACTION.DNP", lowercase_workspace))
    project_root = action_root / rap.host_name(project_name.upper(), lowercase_workspace)
    lower_project_root = project_root.parent / project_root.name.lower()
    shutil.rmtree(project_root, ignore_errors=True)
    shutil.rmtree(lower_project_root, ignore_errors=True)

    src_root = project_root / rap.host_name("SRC", lowercase_workspace)
    bin_root = project_root / rap.host_name("BIN", lowercase_workspace)
    obj_root = project_root / rap.host_name("OBJ", lowercase_workspace)
    src_root.mkdir(parents=True, exist_ok=True)
    bin_root.mkdir(exist_ok=True)
    obj_root.mkdir(exist_ok=True)

    rap.write_ascii(project_root / rap.host_name("README.TXT", lowercase_workspace), "ACTION PROJECT READY\n")
    rap.write_ascii(project_root / rap.host_name("ACTION.PROJ", lowercase_workspace), "ACTION PROJECT\rMAIN.ACT\r")
    rap.write_ascii(
        project_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace),
        "D BIN\nD OBJ\nD SRC\nF ACTION.PROJ\nF README.TXT\n",
    )
    rap.write_ascii(bin_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), "")
    if "source" in case:
        rap.write_ascii(src_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), "F MAIN.ACT\n")
        rap.write_ascii(src_root / rap.host_name("MAIN.ACT", lowercase_workspace), str(case["source"]))
    else:
        rap.write_ascii(src_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), "")
    if "seed_object" in case:
        rap.write_ascii(obj_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), "F MAIN.OBJ\n")
        rap.write_ascii(obj_root / rap.host_name("MAIN.OBJ", lowercase_workspace), str(case["seed_object"]))
    else:
        rap.write_ascii(obj_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), "")

    extra_project_objects = case.get("extra_objects", {})
    if isinstance(extra_project_objects, dict) and extra_project_objects:
        entries: list[str] = []
        for name, text in extra_project_objects.items():
            if not isinstance(name, str) or not name or not isinstance(text, str):
                continue
            rap.write_ascii(obj_root / rap.host_name(name, lowercase_workspace), text)
            entries.append(f"F {name.upper()}")
        if entries:
            rap.ensure_catalog_entries(obj_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), entries)

    extra_library_objects = case.get("extra_library_objects", {})
    if isinstance(extra_library_objects, dict) and extra_library_objects:
        lib_root = project_root / rap.host_name("LIB", lowercase_workspace)
        lib_root.mkdir(parents=True, exist_ok=True)
        entries = []
        for name, text in extra_library_objects.items():
            if not isinstance(name, str) or not name or not isinstance(text, str):
                continue
            rap.write_ascii(lib_root / rap.host_name(name, lowercase_workspace), text)
            entries.append(f"F {name.upper()}")
        if entries:
            rap.ensure_catalog_entries(lib_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), entries)
            rap.ensure_catalog_entries(project_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), ["D LIB"])

    runtime_library_objects = case.get("runtime_library_objects", [])
    if isinstance(runtime_library_objects, list) and runtime_library_objects:
        lib_root = project_root / rap.host_name("LIB", lowercase_workspace)
        lib_root.mkdir(parents=True, exist_ok=True)
        entries = []
        for module_name in runtime_library_objects:
            if not isinstance(module_name, str) or not module_name:
                continue
            source_path = UDOS_RUNTIME_MODULES / f"{module_name}.obj"
            if not source_path.is_file():
                raise RuntimeError(f"missing runtime OBJ module: {source_path}")
            target_name = module_name.upper() + ".OBJ"
            shutil.copy2(source_path, lib_root / rap.host_name(target_name, lowercase_workspace))
            entries.append(f"F {target_name}")
        if entries:
            rap.ensure_catalog_entries(lib_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), entries)
            rap.ensure_catalog_entries(project_root / rap.host_name("UDOSDIR.TXT", lowercase_workspace), ["D LIB"])

    install_program(fs_root, project_root, ACTION_ALINK_BUILD, "ALINK.PRG")
    mount_path = f"/{images_root.name}/{action_root.name}"
    return project_root, mount_path


def host_prg_path(project_root: Path) -> Path:
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    return project_root / rap.host_name("BIN", lowercase_workspace) / rap.host_name("MAIN.PRG", lowercase_workspace)


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


def verify_actc_object_output(project_root: Path, shape: str) -> None:
    case = direct_prg_case(shape)
    fragments = case.get("expected_object_fragments", [])
    if not isinstance(fragments, list) or not fragments:
        return
    lowercase_workspace = project_root.name.islower() or project_root.parent.name.islower()
    obj_path = project_root / rap.host_name("OBJ", lowercase_workspace) / rap.host_name("MAIN.OBJ", lowercase_workspace)
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


def run_prg_phase(
    image: Path,
    work_root: Path,
    project_name: str,
    mount_path: str,
    connect_delay: float,
    prg_path: Path,
    shape: str,
) -> dict[str, object]:
    case = direct_prg_case(shape)
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
        print({"stage": "connect", "port": port}, flush=True)
        client.connect(time.monotonic() + connect_delay)
        client.ping()
        client.resume()

        print({"stage": "mount", "mount_path": mount_path}, flush=True)
        avp.wait_for_screen_fragments(client, ["A:D64/>"], ALINK_PHASE_TIMEOUT)
        time.sleep(INITIAL_SETTLE)
        avp.type_command(client, f"MOUNT B: {mount_path}", ALINK_PHASE_TIMEOUT)
        avp.wait_for_mount_completion(client, ALINK_PHASE_TIMEOUT)
        avp.type_command(client, "B:", ALINK_PHASE_TIMEOUT)
        avp.wait_for_screen_fragments(client, ["B:DNP/>"], ALINK_PHASE_TIMEOUT)
        avp.type_command(client, f"CD {project_name}", ALINK_PHASE_TIMEOUT)
        avp.wait_for_screen_fragments(client, [project_prompt], ALINK_PHASE_TIMEOUT)

        print(
            {
                "stage": "launch_prg",
                "prg_path": str(prg_path),
                "marker_addr": f"0x{DIRECT_PRG_EXIT_MARKER_ADDR:04X}",
                "marker_value": f"0x{DIRECT_PRG_EXIT_MARKER_VALUE:02X}",
            },
            flush=True,
        )
        avp.type_command(client, "CD BIN", PRG_PHASE_TIMEOUT)
        avp.wait_for_screen_fragments(client, [bin_prompt], PRG_PHASE_TIMEOUT)
        avp.type_command(client, "MAIN.PRG", PRG_PHASE_TIMEOUT)
        deadline = time.monotonic() + PRG_PHASE_TIMEOUT
        last_screen = ""
        last_marker = 0
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise vp.ViceError("x64sc exited while waiting for direct PRG marker")
            last_screen = avp.screen_text(client)
            last_marker = client.memory_get(DIRECT_PRG_EXIT_MARKER_ADDR, DIRECT_PRG_EXIT_MARKER_ADDR)[0]
            if last_marker == DIRECT_PRG_EXIT_MARKER_VALUE:
                result = {
                    "prg_path": str(prg_path),
                    "marker": last_marker,
                    "screen": last_screen,
                }
                if "store_check_addr" in case:
                    store_addr = int(case["store_check_addr"])
                    store_value = client.memory_get(store_addr, store_addr)[0]
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
                    store_value = client.memory_get(store_addr, store_addr)[0]
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
                        store_value = client.memory_get(store_addr, store_addr)[0]
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
        raise vp.ViceError(
            f"direct PRG exit marker not observed: got 0x{last_marker:02X}, expected 0x{DIRECT_PRG_EXIT_MARKER_VALUE:02X}\\n"
            f"screen:\n{last_screen}"
        )
    finally:
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
) -> dict[str, object]:
    case = direct_prg_case(shape)
    project_root, mount_path = prepare_workspace(work_root, project_name, shape)

    if "source" in case:
        print({"stage": "actc_harness"}, flush=True)
        run_harness(ACTION_ACTC_HARNESS_BUILD, ACTION_ACTC_HARNESS_LABELS, project_root)
        verify_actc_object_output(project_root, shape)
    else:
        print({"stage": "seed_object"}, flush=True)
    print({"stage": "alink_harness"}, flush=True)
    if bool(case.get("expect_alink_failure", False)):
        return expect_alink_rejection(project_root, shape)
    alink_summary = run_harness(ACTION_ALINK_BUILD, ACTION_ALINK_LABELS, project_root)
    verify_alink_dependency_loads(alink_summary, shape)
    time.sleep(0.5)
    prg_path = verify_host_output(project_root, shape)
    if skip_launch:
        return {"shape": shape, "launch_skipped": True, "prg_path": str(prg_path)}
    return run_prg_phase(
        image,
        work_root,
        project_name,
        mount_path,
        connect_delay,
        prg_path,
        shape,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="VICE proof for ALINK direct PRG emission")
    parser.add_argument("--disk", required=True)
    parser.add_argument("--fs-root", required=True)
    parser.add_argument("--project", default="PROJ3")
    parser.add_argument("--shape", choices=sorted(DIRECT_PRG_CASES), default="word_store")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--attempt-delay", type=float, default=4.0)
    parser.add_argument("--skip-launch", action="store_true", help="verify ALINK output without launching VICE")
    args = parser.parse_args()

    image = Path(args.disk).resolve()
    fs_root = Path(args.fs_root).resolve()
    project_name = args.project.upper()
    work_root = fs_root.parent / f"{fs_root.name}-alink-prg-{args.shape}"

    last_error: Exception | None = None
    for attempt in range(1, args.attempts + 1):
        connect_delay = CONNECT_DELAYS[(attempt - 1) % len(CONNECT_DELAYS)]
        print({"attempt": attempt, "attempts": args.attempts, "connect_delay": connect_delay, "shape": args.shape}, flush=True)
        try:
            shutil.rmtree(work_root, ignore_errors=True)
            shutil.copytree(fs_root, work_root)
            if not args.skip_launch:
                vp.cleanup_stale_vice(settle_seconds=max(1.0, min(5.0, args.attempt_delay)))
            result = run_once(image, work_root, project_name, connect_delay, args.shape, args.skip_launch)
            print(result, flush=True)
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
