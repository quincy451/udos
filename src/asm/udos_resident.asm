.include "acheron.inc"

.export start
.export svc_get_abi_version
.export svc_transport_get_mode
.export svc_fs_get_mount_type
.export svc_console_reset
.export svc_console_write_sc0
.export svc_mark_ready
.export svc_idle
.import acheron
.import clear_rstack

SCREEN = $0400
COLOR = $D800
CURSOR = $CFF0
PTR = $FB
TRANSPORT_SNAPSHOT = $CFF8
MOUNT_SNAPSHOT = $CFFA
ABI_SNAPSHOT = $CFFC
READY_MARKER = $CFFF
READY_VALUE = $52
ABI_VERSION = 1
TRANSPORT_MODE_MOCK = 1
MOUNT_KIND_NONE = 0
MOUNT_KIND_D64 = 1

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
    setp8 0
    calln svc_fs_get_mount_type
    stma MOUNT_SNAPSHOT
    setp16 header_text
    calln svc_console_write_sc0
    setp16 prompt_d64
    calln svc_console_write_sc0
    calln svc_mark_ready
    calln svc_idle
    retm

svc_get_abi_version:
    lda #<ABI_VERSION
    sta 0,x
    lda #>ABI_VERSION
    sta 1,x
    rts

svc_transport_get_mode:
    lda #<TRANSPORT_MODE_MOCK
    sta 0,x
    lda #>$0000
    sta 1,x
    rts

svc_fs_get_mount_type:
    ldy 0,x
    lda mount_kind_table,y
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_console_reset:
    lda #$00
    sta CURSOR
    sta CURSOR+1
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

svc_console_write_sc0:
    lda 0,x
    sta PTR
    lda 1,x
    sta PTR+1
    ldy #$00
write_loop:
    lda (PTR),y
    beq write_done
    ldx CURSOR
    sta SCREEN,x
    lda #$01
    sta COLOR,x
    inc CURSOR
    bne :+
    inc CURSOR+1
:
    iny
    bne write_loop
write_done:
    rts

svc_mark_ready:
    lda #READY_VALUE
    sta READY_MARKER
    rts

svc_idle:
idle_loop:
    jmp idle_loop

mount_kind_table:
    .byte MOUNT_KIND_D64, MOUNT_KIND_NONE

header_text:
    .byte 21, 4, 15, 19, 32, 3, 15, 18, 5, 0
prompt_d64:
    .byte 32, 32, 1, $3A, 4, $36, $34, $3E, 0
prompt_unknown:
    .byte 32, 32, 1, $3A, 21, 14, 11, $3E, 0
