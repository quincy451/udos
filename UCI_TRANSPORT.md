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

## Planned Native Transport Routines

- `uci_probe`
- `uci_wait_idle`
- `uci_push_command`
- `uci_read_data_block`
- `uci_read_status_block`
- `uci_accept_data`
- `uci_abort`

The first hardware-facing implementation should stay tiny and synchronous.
Higher-level filesystem semantics stay above this layer.
