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

uci_wait_reply:
    ldy #$00
uci_wait_reply_loop:
    lda UCI_STATUS_REG
    sta uci_last_status
    and #UCI_STATUS_STATE_MASK
    cmp #UCI_STATUS_STATE_BUSY
    bne uci_wait_reply_done
    dey
    bne uci_wait_reply_loop
    lda uci_last_status
    sec
    rts
uci_wait_reply_done:
    lda uci_last_status
    clc
    rts

; Input: PTR points to command bytes, A = byte length (0..255)
; Output: A = raw status byte, C clear on accepted push, set on idle/error failure
uci_push_command:
    sta uci_xfer_limit
    lda UCI_STATUS_REG
    and #UCI_STATUS_ERROR
    beq :+
    jsr uci_clear_error
:
    jsr uci_wait_idle
    bcs uci_push_fail
    ldy #$00
uci_push_loop:
    cpy uci_xfer_limit
    bcs uci_push_commit
    lda (PTR),y
    sta UCI_CMD_REG
    iny
    bne uci_push_loop
uci_push_commit:
    lda #UCI_CTRL_PUSH_CMD
    sta UCI_CTRL_REG
    lda UCI_STATUS_REG
    and #UCI_STATUS_ERROR
    beq uci_push_ok
uci_push_fail:
    lda UCI_STATUS_REG
    sec
    rts
uci_push_ok:
    lda UCI_STATUS_REG
    clc
    rts

; Input: PTR points to destination, A = max byte count (0..255)
; Output: A = bytes copied, C clear when queue drained, set when buffer filled first
uci_read_data_block:
    sta uci_xfer_limit
    ldy #$00
uci_read_data_loop:
    lda UCI_STATUS_REG
    and #UCI_STATUS_DATA_AV
    beq uci_read_data_done
    cpy uci_xfer_limit
    bcs uci_read_data_full
    lda UCI_DATA_REG
    sta (PTR),y
    iny
    bne uci_read_data_loop
uci_read_data_full:
    tya
    sec
    rts
uci_read_data_done:
    tya
    clc
    rts

; Input: PTR points to destination, A = max byte count (0..255)
; Output: A = bytes copied, C clear when queue drained, set when buffer filled first
uci_read_status_block:
    sta uci_xfer_limit
    ldy #$00
uci_read_status_loop:
    lda UCI_STATUS_REG
    and #UCI_STATUS_STAT_AV
    beq uci_read_status_done
    cpy uci_xfer_limit
    bcs uci_read_status_full
    lda UCI_STATUS_DATA_REG
    sta (PTR),y
    iny
    bne uci_read_status_loop
uci_read_status_full:
    tya
    sec
    rts
uci_read_status_done:
    tya
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
