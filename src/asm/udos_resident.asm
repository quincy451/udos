.include "acheron.inc"

.export start
.export svc_get_abi_version
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
ABI_SNAPSHOT = $CFFE
READY_MARKER = $CFFF
READY_VALUE = $52
ABI_VERSION = 1

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
    setp16 header_text
    calln svc_console_write_sc0
    setp16 prompt_text
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
    ldx pptr
    rts

svc_mark_ready:
    lda #READY_VALUE
    sta READY_MARKER
    rts

svc_idle:
idle_loop:
    jmp idle_loop

header_text:
    .byte 21, 4, 15, 19, 32, 3, 15, 18, 5, 0
prompt_text:
    .byte 32, 32, 1, 62, 0
