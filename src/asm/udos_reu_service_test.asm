.export start

svc_console_write_sc0 = $CF03
svc_console_newline = $CF06
svc_program_exit = $CF0F
svc_file_stage_reu_sc0 = $CF36
svc_reu_read_sc0 = $CF39
svc_reu_write_sc0 = $CF3C

tool_file_status_ok = 1

TEST_REU_LO = $00
TEST_REU_HI = $10
TEST_REU_BANK = $0F
STAGE_REU_LO = $00
STAGE_REU_HI = $20
STAGE_REU_BANK = $0F
WRITE_LEN = 512
STAGE_LEN = 600

.segment "ZPTEMP": zeropage
svc_retptr:
    .res 2
copy_params:
    .res 8
stage_params:
    .res 9

.segment "CODE"

start:
    jsr fill_write_pattern
    jsr run_write_read_roundtrip
    bcs fail
    jsr run_stage_roundtrip
    bcs fail
    lda #<msg_ok
    ldy #>msg_ok
    jsr print_line
    lda #$00
    jmp exit_with_a

fail:
    lda #<msg_fail
    ldy #>msg_fail
    jsr print_line
    lda #$01
    jmp exit_with_a

run_write_read_roundtrip:
    lda #TEST_REU_LO
    sta copy_params+0
    lda #TEST_REU_HI
    sta copy_params+1
    lda #TEST_REU_BANK
    sta copy_params+2
    lda #<write_buffer
    sta copy_params+3
    lda #>write_buffer
    sta copy_params+4
    lda #<WRITE_LEN
    sta copy_params+5
    lda #>WRITE_LEN
    sta copy_params+6
    lda #$00
    sta copy_params+7
    ldx #copy_params
    jsr svc_reu_write_sc0
    lda copy_params+7
    cmp #tool_file_status_ok
    bne reu_roundtrip_fail

    jsr clear_read_buffer_512
    lda #TEST_REU_LO
    sta copy_params+0
    lda #TEST_REU_HI
    sta copy_params+1
    lda #TEST_REU_BANK
    sta copy_params+2
    lda #<read_buffer
    sta copy_params+3
    lda #>read_buffer
    sta copy_params+4
    lda #<WRITE_LEN
    sta copy_params+5
    lda #>WRITE_LEN
    sta copy_params+6
    lda #$00
    sta copy_params+7
    ldx #copy_params
    jsr svc_reu_read_sc0
    lda copy_params+7
    cmp #tool_file_status_ok
    bne reu_roundtrip_fail

    ldy #$00
cmp_write_page0:
    lda read_buffer,y
    cmp write_buffer,y
    bne reu_roundtrip_fail
    iny
    bne cmp_write_page0
cmp_write_page1:
    lda read_buffer+256,y
    cmp write_buffer+256,y
    bne reu_roundtrip_fail
    iny
    bne cmp_write_page1
    clc
    rts

reu_roundtrip_fail:
    sec
    rts

run_stage_roundtrip:
    lda #<stage_name
    sta stage_params+0
    lda #>stage_name
    sta stage_params+1
    lda #STAGE_REU_LO
    sta stage_params+2
    lda #STAGE_REU_HI
    sta stage_params+3
    lda #STAGE_REU_BANK
    sta stage_params+4
    lda #$00
    sta stage_params+5
    sta stage_params+6
    sta stage_params+7
    sta stage_params+8
    ldx #stage_params
    jsr svc_file_stage_reu_sc0
    lda stage_params+5
    cmp #tool_file_status_ok
    bne stage_roundtrip_fail
    lda stage_params+6
    cmp #<STAGE_LEN
    bne stage_roundtrip_fail
    lda stage_params+7
    cmp #>STAGE_LEN
    bne stage_roundtrip_fail
    lda stage_params+8
    bne stage_roundtrip_fail

    lda #STAGE_REU_LO
    sta copy_params+0
    lda #STAGE_REU_HI
    sta copy_params+1
    lda #STAGE_REU_BANK
    sta copy_params+2
    lda #<read_buffer
    sta copy_params+3
    lda #>read_buffer
    sta copy_params+4
    lda #<STAGE_LEN
    sta copy_params+5
    lda #>STAGE_LEN
    sta copy_params+6
    lda #$00
    sta copy_params+7
    ldx #copy_params
    jsr svc_reu_read_sc0
    lda copy_params+7
    cmp #tool_file_status_ok
    bne stage_roundtrip_fail

    ldy #$00
cmp_stage_page0:
    lda read_buffer,y
    cmp stage_expected,y
    bne stage_roundtrip_fail
    iny
    bne cmp_stage_page0
cmp_stage_page1:
    lda read_buffer+256,y
    cmp stage_expected+256,y
    bne stage_roundtrip_fail
    iny
    bne cmp_stage_page1
    ldy #$00
cmp_stage_tail:
    cpy #88
    beq stage_roundtrip_ok
    lda read_buffer+512,y
    cmp stage_expected+512,y
    bne stage_roundtrip_fail
    iny
    bne cmp_stage_tail

stage_roundtrip_ok:
    clc
    rts

stage_roundtrip_fail:
    sec
    rts

fill_write_pattern:
    ldy #$00
fill_write_pattern_loop:
    tya
    eor #$5A
    sta write_buffer,y
    tya
    eor #$A5
    sta write_buffer+256,y
    iny
    bne fill_write_pattern_loop
    rts

clear_read_buffer_512:
    lda #$00
    tay
clear_read_buffer_page0:
    sta read_buffer,y
    iny
    bne clear_read_buffer_page0
clear_read_buffer_page1:
    sta read_buffer+256,y
    iny
    bne clear_read_buffer_page1
    rts

print_line:
    jsr print_ptr
    jmp svc_console_newline

print_ptr:
    sta svc_retptr
    sty svc_retptr+1
    ldx #svc_retptr
    jmp svc_console_write_sc0

exit_with_a:
    sta svc_retptr
    lda #$00
    sta svc_retptr+1
    ldx #svc_retptr
    jmp svc_program_exit

stage_name:
    .asciiz "REU_STG.TXT"
msg_ok:
    .asciiz "REU OK"
msg_fail:
    .asciiz "REU FAIL"

stage_expected:
.repeat 23
    .byte "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
.endrepeat
    .byte "AB"

write_buffer:
    .res WRITE_LEN
read_buffer:
    .res STAGE_LEN
