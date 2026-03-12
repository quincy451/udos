.export start

SETLFS = $FFBA
SETNAM = $FFBD
LOAD_K = $FFD5
CHROUT = $FFD2

DEST_START = $18D3
STATUS_OK = 0

.segment "CODE"

start:
    lda #$01
    ldx #$08
    ldy #$01
    jsr SETLFS

    lda #loader_name_end - loader_name
    ldx #<loader_name
    ldy #>loader_name
    jsr SETNAM

    lda #$00
    jsr LOAD_K
    bcc boot_jump

boot_fail:
    ldx #$00
boot_fail_loop:
    lda fail_text,x
    beq boot_fail_done
    jsr CHROUT
    inx
    bne boot_fail_loop
boot_fail_done:
    rts

boot_jump:
    jsr DEST_START
    rts

loader_name:
    .byte "UDOSCORE"
loader_name_end:

fail_text:
    .byte 13, "LOAD FAILED", 13, 0
