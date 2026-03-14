.export start

UDOS_RETURN = $033C

.segment "CODE"

start:
    lda #$42
    jmp UDOS_RETURN
