.export start

TOOL_SVC_PROGRAM_EXIT = $CF0F
TOOL_SVC_PROGRAM_CHAIN_SC0 = $CF42

.segment "ZPTEMP"
chain_rp:
    .res 3

.segment "CODE"

start:
    lda #<chain_command
    sta chain_rp
    lda #>chain_command
    sta chain_rp+1
    ldx #<chain_rp
    jsr TOOL_SVC_PROGRAM_CHAIN_SC0
    bcs chain_failed
    lda #$00
    sta chain_rp
    jmp TOOL_SVC_PROGRAM_EXIT

chain_failed:
    lda #$7F
    sta chain_rp
    jmp TOOL_SVC_PROGRAM_EXIT

chain_command:
    .byte "RETTEST CHAIN", 0
