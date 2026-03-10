# UDOS UCI Transport Notes

## Source Basis

The current UDOS transport plan is based on the published Ultimate Command
Interface documentation.

Key transport facts used here:
- UCI register window is mapped at `$DF1C-$DF1F`
- `$DF1D` read identifies the interface and defaults to `$C9`
- command queue size: `$380` bytes
- response data queue size: `$380` bytes
- status queue size: `$100` bytes
- targets are selected by the first command byte
- target `$01` / `$02` are Ultimate DOS instances in the documented baseline

## Current Selector Policy

No real Ultimate hardware validation has been performed here, and VICE does not
provide the Ultimate UCI block.

Therefore the current codebase uses a transport selector:
- `0`: unavailable
- `1`: mock backend
- `2`: hardware UCI backend

Current implementation policy:
- if `$DF1D == $C9`, report `2`
- otherwise report `1`

That gives us a real hardware-detection boundary without claiming the hardware
backend is finished.

## Native Transport Layer

The current tree now includes a native transport include:
- [src/asm/uci_transport.inc](/mnt/c/test/action/udos/src/asm/uci_transport.inc)

Implemented routines:
- `uci_probe`
- `uci_read_status`
- `uci_wait_idle`
- `uci_wait_reply`
- `uci_push_command`
- `uci_read_data_block`
- `uci_read_status_block`
- `uci_accept_data`
- `uci_abort_transfer`
- `uci_clear_error`

Current implementation notes:
- `svc_transport_get_mode` now delegates to `uci_probe` instead of reading the ident register directly
- control/status bit assignments are taken from the published command-interface register table
- the new transfer helpers are still deliberately small:
  - command push length is currently one byte (`0..255`)
  - data/status drain length is currently one byte (`0..255`)
  - higher layers will chunk larger exchanges instead of growing the native edge first
- `uci_wait_reply` treats any non-busy transport state as a completed reply boundary and returns the raw status byte
- no real hardware execution has been performed from this environment, so these routines are structured and built, but not hardware-validated

The first hardware-facing implementation stays tiny and synchronous.
Higher-level filesystem semantics stay above this layer.
