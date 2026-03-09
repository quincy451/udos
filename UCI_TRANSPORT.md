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

## Phase 3 Reality

No real Ultimate hardware validation has been performed here, and VICE does not
provide the Ultimate UCI block.

Therefore the current codebase uses a transport mode seam:
- `0`: unavailable
- `1`: mock backend
- `2`: hardware UCI backend

The resident build currently validates the mock backend only.

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
