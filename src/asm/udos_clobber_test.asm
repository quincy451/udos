.export start

UDOS_RETURN = $033C

.segment "CODE"

start:
    lda #$AA
    ldx #$00
clobber_loop:
    sta $1800,x
    sta $1900,x
    sta $1A00,x
    sta $1B00,x
    inx
    bne clobber_loop
    lda #$24
    jmp UDOS_RETURN
