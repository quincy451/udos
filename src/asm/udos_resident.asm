.include "acheron.inc"

.export start
.export svc_get_abi_version
.export svc_transport_get_mode
.export svc_drive_get_current
.export svc_drive_set_current
.export svc_fs_get_mount_type
.export svc_fs_get_mount_flags
.export svc_fs_bind_drive
.export svc_console_reset
.export svc_console_write_sc0
.export svc_console_write_prompt
.export svc_console_newline
.export svc_line_read
.export svc_mark_ready
.export svc_idle
.import acheron
.import clear_rstack

SCREEN = $0400
COLOR = $D800
CURSOR = $CFE0
SCREEN_PTR = $F9
PTR = $FB
BIND_A_SNAPSHOT = $CFE8
BIND_B_SNAPSHOT = $CFEA
CURRENT_DRIVE_SNAPSHOT = $CFEC
CURRENT_FLAGS_SNAPSHOT = $CFEE
TRANSPORT_SNAPSHOT = $CFF0
MOUNT_SNAPSHOT = $CFF2
ABI_SNAPSHOT = $CFF4
STAGE_SNAPSHOT = $CFFD
READY_MARKER = $CFFF
READY_VALUE = $52
ABI_VERSION = 1
TRANSPORT_MODE_UNAVAILABLE = 0
TRANSPORT_MODE_MOCK = 1
TRANSPORT_MODE_UCI_HW = 2
MOUNT_KIND_NONE = 0
MOUNT_KIND_D64 = 1
MOUNT_KIND_D71 = 2
MOUNT_KIND_D81 = 3
MOUNT_KIND_DNP = 4
MOUNT_FLAG_NONE = 0
MOUNT_FLAG_FLAT = 1
MOUNT_FLAG_TREE = 2
DRIVE_A = 0
DRIVE_B = 1
UCI_IDENT_REG = $DF1D
UCI_IDENT_MAGIC = $C9
CMD_H = 8
CMD_E = 5
CMD_L = 12
CMD_M = 13
CMD_O = 15
CMD_P = 16
CMD_R = 18
CMD_V = 22
SHELL_CMD_NONE = 0
SHELL_CMD_HELP = 1
SHELL_CMD_VER = 2
SHELL_CMD_VOL = 3
SHELL_CMD_MEM = 4

.code

start:
    jsr clear_rstack
    jsr acheron
        call resident_main
        native
resident_halt:
    jmp resident_halt

resident_main:
    mgrow 1
    calln svc_console_reset
    calln svc_get_abi_version
    stma ABI_SNAPSHOT
    calln svc_transport_get_mode
    stma TRANSPORT_SNAPSHOT

    setp16 $0100      ; bind A: as D64
    calln svc_fs_bind_drive
    stma BIND_A_SNAPSHOT

    setp16 $0401      ; bind B: as DNP
    calln svc_fs_bind_drive
    stma BIND_B_SNAPSHOT

    setp8 DRIVE_A
    calln svc_drive_set_current
    stma CURRENT_DRIVE_SNAPSHOT

    setp8 DRIVE_A
    calln svc_fs_get_mount_flags
    stma CURRENT_FLAGS_SNAPSHOT

    setp8 DRIVE_A
    calln svc_fs_get_mount_type
    stma MOUNT_SNAPSHOT

    setp16 header_text
    calln svc_console_write_sc0
    calln svc_console_newline

shell_loop:
    calln svc_console_write_prompt
    calln svc_line_read
    case8 SHELL_CMD_NONE, shell_done
    case8 SHELL_CMD_HELP, cmd_emit_response
    case8 SHELL_CMD_VER, cmd_emit_response
    case8 SHELL_CMD_VOL, cmd_emit_response
    case8 SHELL_CMD_MEM, cmd_emit_response
    setp16 resp_unknown
    calln svc_console_write_sc0
    calln svc_console_newline
    jump shell_loop

cmd_emit_response:
    setp8 $11
    stma STAGE_SNAPSHOT
    calln svc_shell_response_ptr
    calln svc_console_write_sc0
    calln svc_console_newline
    jump shell_loop

shell_done:
    setp8 $F0
    stma STAGE_SNAPSHOT
    calln svc_mark_ready
    setp8 $F1
    stma STAGE_SNAPSHOT
    calln svc_idle
    retm

svc_get_abi_version:
    lda #<ABI_VERSION
    sta 0,x
    lda #>ABI_VERSION
    sta 1,x
    rts

svc_transport_get_mode:
    lda UCI_IDENT_REG
    cmp #UCI_IDENT_MAGIC
    beq :+
    lda #<TRANSPORT_MODE_MOCK
    sta 0,x
    lda #$00
    sta 1,x
    rts
:
    lda #<TRANSPORT_MODE_UCI_HW
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_drive_get_current:
    lda current_drive
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_drive_set_current:
    lda 0,x
    cmp #DRIVE_B+1
    bcs drive_set_invalid
    sta current_drive
    sta 0,x
    lda #$00
    sta 1,x
    rts
drive_set_invalid:
    lda current_drive
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_fs_get_mount_type:
    ldy 0,x
    cpy #2
    bcs fs_get_type_invalid
    lda mount_kind_table,y
    sta 0,x
    lda #$00
    sta 1,x
    rts
fs_get_type_invalid:
    lda #MOUNT_KIND_NONE
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_fs_get_mount_flags:
    ldy 0,x
    cpy #2
    bcs fs_get_flags_invalid
    lda mount_flag_table,y
    sta 0,x
    lda #$00
    sta 1,x
    rts
fs_get_flags_invalid:
    lda #MOUNT_FLAG_NONE
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_fs_bind_drive:
    ldy 0,x
    cpy #2
    bcs fs_bind_invalid
    lda 1,x
    sta mount_kind_table,y
    jsr kind_to_flags
    sta mount_flag_table,y
    lda mount_kind_table,y
    sta 0,x
    lda mount_flag_table,y
    sta 1,x
    rts
fs_bind_invalid:
    lda #MOUNT_KIND_NONE
    sta 0,x
    lda #MOUNT_FLAG_NONE
    sta 1,x
    rts

kind_to_flags:
    cmp #MOUNT_KIND_NONE
    beq :+
    cmp #MOUNT_KIND_DNP
    beq kind_tree
    lda #MOUNT_FLAG_FLAT
    rts
kind_tree:
    lda #MOUNT_FLAG_TREE
    rts
:
    lda #MOUNT_FLAG_NONE
    rts

svc_console_reset:
    lda #$00
    sta CURSOR
    sta CURSOR+1
    lda #$00
    sta script_index
    tay
clear_loop:
    lda #$20
    sta SCREEN,y
    lda #$01
    sta COLOR,y
    iny
    bne clear_loop
    ldy #$00
clear_loop_2:
    lda #$20
    sta SCREEN+$0100,y
    lda #$01
    sta COLOR+$0100,y
    iny
    cpy #$E8
    bne clear_loop_2
    rts

console_putc:
    pha
    clc
    lda CURSOR
    adc #<SCREEN
    sta SCREEN_PTR
    lda CURSOR+1
    adc #>SCREEN
    sta SCREEN_PTR+1
    pla
    ldx #$00
    sta (SCREEN_PTR,x)
    inc CURSOR
    bne :+
    inc CURSOR+1
:
    rts

console_mod40:
    lda CURSOR
    sta SCREEN_PTR
    lda CURSOR+1
    sta SCREEN_PTR+1
mod40_loop:
    lda SCREEN_PTR+1
    bne mod40_sub
    lda SCREEN_PTR
    cmp #40
    bcc mod40_done
mod40_sub:
    sec
    lda SCREEN_PTR
    sbc #40
    sta SCREEN_PTR
    lda SCREEN_PTR+1
    sbc #0
    sta SCREEN_PTR+1
    jmp mod40_loop
mod40_done:
    lda SCREEN_PTR
    rts

svc_console_newline:
    jsr console_mod40
    beq newline_done
newline_loop:
    lda #$20
    jsr console_putc
    jsr console_mod40
    bne newline_loop
newline_done:
    rts

svc_console_write_sc0:
    lda 0,x
    sta PTR
    lda 1,x
    sta PTR+1
    ldy #$00
write_loop:
    lda (PTR),y
    beq write_done
    jsr console_putc
    iny
    bne write_loop
write_done:
    rts

svc_console_write_prompt:
    lda #$20
    jsr console_putc
    lda #$20
    jsr console_putc

    lda current_drive
    clc
    adc #$01
    jsr console_putc

    lda #$3A
    jsr console_putc

    ldy current_drive
    lda mount_kind_table,y
    cmp #MOUNT_KIND_D64
    beq prompt_d64_case
    cmp #MOUNT_KIND_D71
    beq prompt_d71_case
    cmp #MOUNT_KIND_D81
    beq prompt_d81_case
    cmp #MOUNT_KIND_DNP
    beq prompt_dnp_case
    lda #$3F
    jsr console_putc
    jmp prompt_gt
prompt_d64_case:
    lda #$04
    jsr console_putc
    lda #$36
    jsr console_putc
    lda #$34
    jsr console_putc
    jmp prompt_gt
prompt_d71_case:
    lda #$04
    jsr console_putc
    lda #$37
    jsr console_putc
    lda #$31
    jsr console_putc
    jmp prompt_gt
prompt_d81_case:
    lda #$04
    jsr console_putc
    lda #$38
    jsr console_putc
    lda #$31
    jsr console_putc
    jmp prompt_gt
prompt_dnp_case:
    lda #$04
    jsr console_putc
    lda #$0E
    jsr console_putc
    lda #$10
    jsr console_putc
prompt_gt:
    lda #$3E
    jsr console_putc
    rts

svc_line_read:
    ldy script_index
    cpy #4
    bcs line_empty
    lda script_cmd_id,y
    sta 0,x
    lda #$00
    sta 1,x
    lda script_ptr_lo,y
    sta PTR
    lda script_ptr_hi,y
    sta PTR+1
    inc script_index
    lda #$20
    jsr console_putc
    ldy #$00
line_echo_loop:
    lda (PTR),y
    beq line_echo_done
    jsr console_putc
    iny
    bne line_echo_loop
line_echo_done:
    jsr svc_console_newline
    rts
line_empty:
    lda #SHELL_CMD_NONE
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_shell_response_ptr:
    lda 0,x
    cmp #SHELL_CMD_HELP
    beq shell_resp_help
    cmp #SHELL_CMD_VER
    beq shell_resp_ver
    cmp #SHELL_CMD_VOL
    beq shell_resp_vol
    cmp #SHELL_CMD_MEM
    beq shell_resp_mem
    lda #<resp_unknown
    sta 0,x
    lda #>resp_unknown
    sta 1,x
    rts
shell_resp_help:
    lda #<resp_help
    sta 0,x
    lda #>resp_help
    sta 1,x
    rts
shell_resp_ver:
    lda #<resp_ver
    sta 0,x
    lda #>resp_ver
    sta 1,x
    rts
shell_resp_vol:
    lda #<resp_vol
    sta 0,x
    lda #>resp_vol
    sta 1,x
    rts
shell_resp_mem:
    lda #<resp_mem
    sta 0,x
    lda #>resp_mem
    sta 1,x
    rts

svc_mark_ready:
    lda #READY_VALUE
    sta READY_MARKER
    rts

svc_idle:
idle_loop:
    jmp idle_loop

current_drive:
    .byte DRIVE_A
script_index:
    .byte 0
mount_kind_table:
    .byte MOUNT_KIND_NONE, MOUNT_KIND_NONE
mount_flag_table:
    .byte MOUNT_FLAG_NONE, MOUNT_FLAG_NONE
script_cmd_id:
    .byte SHELL_CMD_HELP, SHELL_CMD_VER, SHELL_CMD_VOL, SHELL_CMD_MEM
script_ptr_lo:
    .byte <script_cmd_help, <script_cmd_ver, <script_cmd_vol, <script_cmd_mem
script_ptr_hi:
    .byte >script_cmd_help, >script_cmd_ver, >script_cmd_vol, >script_cmd_mem

header_text:
    .byte 21, 4, 15, 19, 32, 3, 15, 18, 5, 0
script_cmd_help:
    .byte CMD_H, CMD_E, CMD_L, CMD_P, 0
script_cmd_ver:
    .byte CMD_V, CMD_E, CMD_R, 0
script_cmd_vol:
    .byte CMD_V, CMD_O, CMD_L, 0
script_cmd_mem:
    .byte CMD_M, CMD_E, CMD_M, 0
resp_help:
    .byte CMD_H, CMD_E, CMD_L, CMD_P, 32, CMD_V, CMD_E, CMD_R, 32, CMD_V, CMD_O, CMD_L, 32, CMD_M, CMD_E, CMD_M, 0
resp_ver:
    .byte 21, 4, 15, 19, 32, 1, 12, 16, 8, 1, 0
resp_vol:
    .byte 1, $3A, 4, $36, $34, 32, 2, $3A, 4, $0E, $10, 0
resp_mem:
    .byte 3, 15, 18, 5, 32, $30, $31, $31, $05, 0
resp_unknown:
    .byte $3F, 0
