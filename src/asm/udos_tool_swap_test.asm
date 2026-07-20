.export start

TOOL_ABI_BASE = $CF00
SVC_CONSOLE_WRITE_SC0 = TOOL_ABI_BASE + 3
SVC_PROGRAM_EXIT = TOOL_ABI_BASE + 15
SVC_FILE_LOAD_SC0 = TOOL_ABI_BASE + 18
SVC_DIR_BEGIN_CURRENT = TOOL_ABI_BASE + 21
SVC_DIR_NEXT = TOOL_ABI_BASE + 24
SVC_FILE_SAVE_SC0 = TOOL_ABI_BASE + 27
SVC_DIR_MAKE_SC0 = TOOL_ABI_BASE + 30
SVC_DIR_REMOVE_SC0 = TOOL_ABI_BASE + 33
SVC_FILE_DELETE_SC0 = TOOL_ABI_BASE + 36
SVC_FILE_RENAME_SC0 = TOOL_ABI_BASE + 39
SVC_FILE_COPY_SC0 = TOOL_ABI_BASE + 42
SVC_DIR_BEGIN_SC0 = TOOL_ABI_BASE + 63
TOOL_ABI_RUNTIME_BASE = $C8E7
CURSOR = $CFE0
ALIAS_PARAMS = $F9

TOOL_FILE_STATUS_NOFILE = 3
TOOL_FILE_STATUS_OK = 1
TOOL_FILE_STATUS_TOO_LARGE = 2
TOOL_DIR_STATUS_OK = 1
TOOL_DIR_STATUS_NOFILE = 3

.macro fail_if_zero
    bne :+
    jmp swap_fail
:
.endmacro

.macro fail_if_not_equal
    beq :+
    jmp swap_fail
:
.endmacro

.segment "ZPTEMP": zeropage
params:
    .res 9
failure_code:
    .res 1

.segment "CODE"

start:
    lda #$A0
    sta failure_code
    lda TOOL_ABI_RUNTIME_BASE
    cmp #$A9
    fail_if_not_equal
    inc failure_code
    ldx #params
    jsr SVC_DIR_BEGIN_CURRENT
    lda params
    fail_if_zero
    inc failure_code
    ldx #params
    jsr SVC_DIR_NEXT
    lda params
    ora params+1
    fail_if_zero

    inc failure_code

    lda #<root_path
    sta params
    lda #>root_path
    sta params+1
    ldx #params
    jsr SVC_DIR_BEGIN_SC0
    lda params+2
    cmp #TOOL_DIR_STATUS_OK
    fail_if_not_equal
    lda params
    ora params+1
    fail_if_zero

    inc failure_code
    lda #<swap_dir_path
    sta params
    lda #>swap_dir_path
    sta params+1
    ldx #params
    jsr SVC_DIR_REMOVE_SC0
    lda params+2
    cmp #TOOL_DIR_STATUS_NOFILE
    beq :+
    ; B0..B8 identify the unexpected directory status at the A4 check.
    ora #$B0
    sta failure_code
    jmp swap_fail
:
    inc failure_code
    ldx #params
    jsr SVC_DIR_MAKE_SC0
    lda params+2
    cmp #TOOL_DIR_STATUS_OK
    fail_if_not_equal
    inc failure_code
    ldx #params
    jsr SVC_DIR_REMOVE_SC0
    lda params+2
    cmp #TOOL_DIR_STATUS_OK
    fail_if_not_equal

    inc failure_code
    lda #<missing_path
    sta params
    lda #>missing_path
    sta params+1
    ldx #params
    jsr SVC_FILE_DELETE_SC0
    lda params+2
    cmp #TOOL_FILE_STATUS_NOFILE
    fail_if_not_equal

    inc failure_code
    lda #<rename_path
    sta params+2
    lda #>rename_path
    sta params+3
    ldx #params
    jsr SVC_FILE_RENAME_SC0
    lda params+4
    cmp #TOOL_FILE_STATUS_NOFILE
    fail_if_not_equal
    inc failure_code
    ldx #params
    jsr SVC_FILE_COPY_SC0
    lda params+4
    cmp #TOOL_FILE_STATUS_NOFILE
    fail_if_not_equal

    inc failure_code
    lda #'A'
    sta $9000
    lda #$00
    sta $9001
    lda #'B'
    sta $9002
    lda #'!'
    sta $9003
    lda #<save_path
    sta params
    lda #>save_path
    sta params+1
    lda #<$9000
    sta params+2
    lda #>$9000
    sta params+3
    lda #$04
    sta params+4
    lda #$00
    sta params+5
    ldx #params
    jsr SVC_FILE_SAVE_SC0
    lda params+6
    cmp #TOOL_FILE_STATUS_OK
    fail_if_not_equal

    inc failure_code
    lda #<save_path
    sta params
    lda #>save_path
    sta params+1
    lda #<$9100
    sta params+2
    lda #>$9100
    sta params+3
    lda #$04
    sta params+4
    lda #$00
    sta params+5
    ldx #params
    jsr SVC_FILE_LOAD_SC0
    lda params+6
    cmp #TOOL_FILE_STATUS_OK
    fail_if_not_equal
    lda params+7
    cmp #$04
    fail_if_not_equal
    lda params+8
    fail_if_not_equal
    lda $9100
    cmp #'A'
    fail_if_not_equal
    lda $9101
    fail_if_not_equal
    lda $9102
    cmp #'B'
    fail_if_not_equal
    lda $9103
    cmp #'!'
    fail_if_not_equal

    inc failure_code
    lda #<$9200
    sta params+2
    lda #>$9200
    sta params+3
    lda #$02
    sta params+4
    ldx #params
    jsr SVC_FILE_LOAD_SC0
    lda params+6
    cmp #TOOL_FILE_STATUS_TOO_LARGE
    fail_if_not_equal
    lda params+7
    cmp #$02
    fail_if_not_equal
    lda params+8
    fail_if_not_equal
    lda $9200
    cmp #'A'
    fail_if_not_equal
    lda $9201
    fail_if_not_equal

    inc failure_code
    lda #<text_save_path
    sta params
    lda #>text_save_path
    sta params+1
    lda #<long_text
    sta params+2
    lda #>long_text
    sta params+3
    lda #$06
    sta params+4
    lda #$00
    sta params+5
    ldx #params
    jsr SVC_FILE_SAVE_SC0
    lda params+6
    cmp #TOOL_FILE_STATUS_OK
    fail_if_not_equal

    inc failure_code
    lda #<short_text
    sta params+2
    lda #>short_text
    sta params+3
    lda #$00
    sta params+4
    sta params+5
    ldx #params
    jsr SVC_FILE_SAVE_SC0
    lda params+6
    cmp #TOOL_FILE_STATUS_OK
    fail_if_not_equal

    ; The fixed ABI must accept a parameter block that overlaps its own
    ; SCREEN_PTR/PTR zero-page workspace at $F9-$FC.
    inc failure_code
    lda #<alias_save_path
    sta ALIAS_PARAMS+0
    lda #>alias_save_path
    sta ALIAS_PARAMS+1
    lda #<alias_text
    sta ALIAS_PARAMS+2
    lda #>alias_text
    sta ALIAS_PARAMS+3
    lda #$00
    sta ALIAS_PARAMS+4
    sta ALIAS_PARAMS+5
    lda #TOOL_FILE_STATUS_NOFILE
    sta ALIAS_PARAMS+6
    ldx #ALIAS_PARAMS
    jsr SVC_FILE_SAVE_SC0
    lda ALIAS_PARAMS+6
    cmp #TOOL_FILE_STATUS_OK
    fail_if_not_equal

    inc failure_code
    lda #<alias_save_path
    sta ALIAS_PARAMS+0
    lda #>alias_save_path
    sta ALIAS_PARAMS+1
    lda #<alias_copy_path
    sta ALIAS_PARAMS+2
    lda #>alias_copy_path
    sta ALIAS_PARAMS+3
    lda #TOOL_FILE_STATUS_NOFILE
    sta ALIAS_PARAMS+4
    ldx #ALIAS_PARAMS
    jsr SVC_FILE_COPY_SC0
    lda ALIAS_PARAMS+4
    cmp #TOOL_FILE_STATUS_OK
    fail_if_not_equal

    inc failure_code
    lda #<alias_copy_path
    sta ALIAS_PARAMS+0
    lda #>alias_copy_path
    sta ALIAS_PARAMS+1
    lda #<alias_rename_path
    sta ALIAS_PARAMS+2
    lda #>alias_rename_path
    sta ALIAS_PARAMS+3
    lda #TOOL_FILE_STATUS_NOFILE
    sta ALIAS_PARAMS+4
    ldx #ALIAS_PARAMS
    jsr SVC_FILE_RENAME_SC0
    lda ALIAS_PARAMS+4
    cmp #TOOL_FILE_STATUS_OK
    fail_if_not_equal

    lda #$E8
    sta CURSOR
    lda #$03
    sta CURSOR+1
    lda #<swap_ok_text
    sta params
    lda #>swap_ok_text
    sta params+1
    ldx #params
    jsr SVC_CONSOLE_WRITE_SC0
    lda #$5A
    bne swap_exit

swap_fail:
    lda #<swap_fail_text
    sta params
    lda #>swap_fail_text
    sta params+1
    ldx #params
    jsr SVC_CONSOLE_WRITE_SC0
    lda failure_code

swap_exit:
    sta params
    ldx #params
    jmp SVC_PROGRAM_EXIT

swap_ok_text:
    .asciiz "ABI SWAP OK"
swap_fail_text:
    .asciiz "ABI SWAP FAIL"
root_path:
    .asciiz "/"
swap_dir_path:
    .asciiz "SWPDIR"
missing_path:
    .asciiz "NOFILE.TXT"
rename_path:
    .asciiz "RENAMED.TXT"
save_path:
    .asciiz "SWPSAVE.BIN"
text_save_path:
    .asciiz "SWPTEXT.TXT"
alias_save_path:
    .asciiz "SWPALIAS.TXT"
alias_copy_path:
    .asciiz "SWPALCP.TXT"
alias_rename_path:
    .asciiz "SWPALRN.TXT"
long_text:
    .byte "LONGER"
short_text:
    .asciiz "OK"
alias_text:
    .asciiz "ZP OK"

; Force the loaded image to replace all low resident service code while leaving
; the preserved island at $9800 and the HIRAM runtime helper untouched.
.assert * < $1810, error, "swap probe entry code must remain below resident RAM"
