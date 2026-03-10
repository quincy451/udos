UCI_CTRL_REG = $DF1C
UCI_STATUS_REG = $DF1C
UCI_CMD_REG = $DF1D
UCI_IDENT_REG = $DF1D
UCI_DATA_REG = $DF1E
UCI_STATUS_DATA_REG = $DF1F

UCI_IDENT_MAGIC = $C9

; Control/status bit assignments follow the published Ultimate Command Interface
; register table. The transport layer stays native and synchronous.
UCI_CTRL_PUSH_CMD = $01
UCI_CTRL_DATA_ACC = $10
UCI_CTRL_ABORT = $20
UCI_CTRL_CLR_ERR = $40

UCI_STATUS_CMD_BUSY = $01
UCI_STATUS_DATA_ACC = $02
UCI_STATUS_ABORT_P = $04
UCI_STATUS_ERROR = $08
UCI_STATUS_STATE_MASK = $30
UCI_STATUS_STATE_IDLE = $00
UCI_STATUS_STATE_BUSY = $10
UCI_STATUS_STATE_LAST = $20
UCI_STATUS_STATE_MORE = $30
UCI_STATUS_STAT_AV = $40
UCI_STATUS_DATA_AV = $80

uci_probe:
    lda UCI_IDENT_REG
    cmp #UCI_IDENT_MAGIC
    beq :+
    sec
    rts
:
    clc
    rts

uci_read_status:
    lda UCI_STATUS_REG
    rts

uci_wait_idle:
    ldy #$00
uci_wait_idle_loop:
    lda UCI_STATUS_REG
    and #UCI_STATUS_STATE_MASK
    cmp #UCI_STATUS_STATE_IDLE
    beq uci_wait_idle_done
    dey
    bne uci_wait_idle_loop
    sec
    rts
uci_wait_idle_done:
    clc
    rts

uci_accept_data:
    lda #UCI_CTRL_DATA_ACC
    sta UCI_CTRL_REG
    rts

uci_abort_transfer:
    lda #UCI_CTRL_ABORT
    sta UCI_CTRL_REG
    rts

uci_clear_error:
    lda #UCI_CTRL_CLR_ERR
    sta UCI_CTRL_REG
    rts
