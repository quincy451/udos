.include "acheron.inc"

.export start
.import clear_rstack
.import acheron

MARKER = $CFFF
SCREEN = $0400
COLOR = $D800

.code

start:
    jsr clear_rstack
    jsr acheron
        calln native_banner
        native
    rts

native_banner:
    ldx #$00
copy_loop:
    lda banner_codes, x
    beq done
    sta SCREEN, x
    lda #$01
    sta COLOR, x
    inx
    bne copy_loop

done:
    lda #$42
    sta MARKER
    rts

banner_codes:
    .byte 21, 4, 15, 19, 32, 22, 13, 32, 15, 11, 0
