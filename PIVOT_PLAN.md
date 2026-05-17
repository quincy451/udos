# Current Pivot Plan

The active pivot is complete at the architecture level: UDOS is a native 6502
resident shell, Action tools are UDOS-native PRG programs, and `alink` decides
what goes into each linked Action PRG.

Current rules:

- keep the resident shell native
- keep `ACTC.PRG -> OBJ/<MODULE>.OBJ`
- keep `ALINK.PRG -> BIN/<MODULE>.PRG`
- do not reintroduce a separate runtime-launch program
- keep optional feature support behind link-selected helper modules
- keep release images free of retired runner artifacts

Primary gates:

- `make -C udos all`
- `make -C udos vice-resident`
- `make -C udos vice-action-alink`
- `make -C udos vice-action-actc-alink-launch`
