.include "acheron.inc"
.include "uci_transport.inc"

.export start
.export svc_get_abi_version
.export svc_transport_get_mode
.export svc_drive_get_current
.export svc_drive_set_current
.export svc_fs_get_mount_type
.export svc_fs_get_mount_flags
.export svc_fs_bind_drive
.export svc_fs_get_dir_state
.export svc_fs_get_volume_ptr
.export svc_fs_get_backend_path_ptr
.export svc_fs_get_dir_listing_ptr
.export svc_fs_enum_begin
.export svc_fs_enum_next
.export svc_console_reset
.export svc_console_write_sc0
.export svc_console_write_prompt
.export svc_console_newline
.export svc_line_read
.export svc_program_prepare_run
.export svc_program_get_status
.export svc_program_error_ptr
.export svc_program_get_target_ptr
.export svc_program_get_cmdline_ptr
.export svc_program_get_cmdline_len
.export svc_program_exit
.export svc_mark_ready
.export svc_idle
.import acheron
.import clear_rstack

SCREEN = $0400
COLOR = $D800
CURSOR = $CFE0
SCREEN_PTR = $F9
PTR = $FB
BACKEND_A_PATH_LEN_SNAPSHOT = $CFE4
BACKEND_B_PATH_LEN_SNAPSHOT = $CFE5
BIND_A_SNAPSHOT = $CFE8
BIND_B_SNAPSHOT = $CFEA
CURRENT_DRIVE_SNAPSHOT = $CFEC
CURRENT_FLAGS_SNAPSHOT = $CFEE
TRANSPORT_SNAPSHOT = $CFF0
MOUNT_SNAPSHOT = $CFF2
ABI_SNAPSHOT = $CFF4
PROGRAM_STATE_SNAPSHOT = $CFF6
PROGRAM_EXIT_SNAPSHOT = $CFF7
PROGRAM_DRIVE_SNAPSHOT = $CFF8
PROGRAM_DIR_SNAPSHOT = $CFF9
STAGE_SNAPSHOT = $CFFD
READY_MARKER = $CFFF
READY_VALUE = $52
ABI_VERSION = 1
TRANSPORT_MODE_UNAVAILABLE = 0
TRANSPORT_MODE_MOCK = 1
TRANSPORT_MODE_UCI_HW = 2
MOUNT_KIND_NONE = 0
MOUNT_KIND_D64 = 1
MOUNT_KIND_D71 = 2
MOUNT_KIND_D81 = 3
MOUNT_KIND_DNP = 4
MOUNT_FLAG_NONE = 0
MOUNT_FLAG_FLAT = 1
MOUNT_FLAG_TREE = 2
DRIVE_A = 0
DRIVE_B = 1
GETIN = $FFE4
KEY_RETURN = $0D
KEY_LINEFEED = $0A
KEY_BACKSPACE = $14
MAX_LINE_LEN = 31
MAX_RESPONSE_LEN = 128
ASCII_COLON = $3A
ASCII_SLASH = $2F
ASCII_SPACE = $20
ASCII_COMMA = $2C
ASCII_DOT = $2E
ASCII_DASH = $2D
ASCII_UNDERSCORE = $5F
ASCII_GT = $3E
CMD_H = 8
CMD_B = 2
CMD_C = 3
CMD_D = 4
CMD_E = 5
CMD_F = 6
CMD_G = 7
CMD_I = 9
CMD_K = 11
CMD_L = 12
CMD_M = 13
CMD_N = 14
CMD_O = 15
CMD_P = 16
CMD_Q = 17
CMD_R = 18
CMD_S = 19
CMD_T = 20
CMD_U = 21
CMD_V = 22
CMD_W = 23
CMD_X = 24
CMD_Y = 25
SHELL_CMD_NONE = 0
SHELL_CMD_HELP = 1
SHELL_CMD_VER = 2
SHELL_CMD_VOL = 3
SHELL_CMD_MEM = 4
SHELL_CMD_QUIT = 5
SHELL_CMD_DIR = 6
SHELL_CMD_CD = 7
SHELL_CMD_MOUNT = 8
SHELL_CMD_TYPE = 9
SHELL_CMD_COPY = 10
SHELL_CMD_REN = 11
SHELL_CMD_DEL = 12
SHELL_CMD_RUN = 13
INPUT_MODE_KEYBOARD = 0
INPUT_MODE_SCRIPT = 1
DIR_ID_ROOT = 0
DIR_ID_BIN = 1
DIR_ID_SRC = 2
DIR_ID_WORK = 3
PATH_STATUS_OK = 0
PATH_STATUS_FLAT = 1
PATH_STATUS_BAD = 2
PATH_STATUS_UNMOUNTED = 3
PATH_STATUS_READ_ONLY = 4
MOUNT_STATUS_OK = 0
MOUNT_STATUS_BAD = 1
RUN_STATUS_OK = 0
RUN_STATUS_BAD = 1
RUN_STATUS_FLAT = 2
RUN_STATUS_UNMOUNTED = 3
RUN_STATUS_NOFILE = 4
PROGRAM_STATE_NONE = 0
PROGRAM_STATE_RUNNING = 1
PROGRAM_STATE_EXITED = 2
WORK_DYNAMIC_MAX = 2
WORK_NAME_MAX = 16
DOS_TARGET_A = 1
DOS_TARGET_B = 2
DOS_CMD_CHANGE_DIR = $11
DOS_CMD_GET_PATH = $12
DOS_CMD_OPEN_DIR = $13
DOS_CMD_READ_DIR = $14
DOS_ATTR_DIR = $10
HW_DIR_CACHE_MAX = 6
HW_DIR_NAME_MAX = 20
HW_DIR_NAME_STRIDE = HW_DIR_NAME_MAX + 1
IMG_VOL_LO = 0
IMG_VOL_HI = 1
IMG_ROOT_LO_LO = 2
IMG_ROOT_LO_HI = 3
IMG_ROOT_HI_LO = 4
IMG_ROOT_HI_HI = 5
IMG_ROOT_COUNT = 6
IMG_BIN_LO_LO = 7
IMG_BIN_LO_HI = 8
IMG_BIN_HI_LO = 9
IMG_BIN_HI_HI = 10
IMG_BIN_COUNT = 11
IMG_SRC_LO_LO = 12
IMG_SRC_LO_HI = 13
IMG_SRC_HI_LO = 14
IMG_SRC_HI_HI = 15
IMG_SRC_COUNT = 16
IMG_WORK_LO_LO = 17
IMG_WORK_LO_HI = 18
IMG_WORK_HI_LO = 19
IMG_WORK_HI_HI = 20
IMG_WORK_COUNT = 21
IMG_FILE_ROOT_TABLE_LO = 22
IMG_FILE_ROOT_TABLE_HI = 23
IMG_FILE_ROOT_COUNT = 24
IMG_FILE_BIN_TABLE_LO = 25
IMG_FILE_BIN_TABLE_HI = 26
IMG_FILE_BIN_COUNT = 27
IMG_FILE_SRC_TABLE_LO = 28
IMG_FILE_SRC_TABLE_HI = 29
IMG_FILE_SRC_COUNT = 30
IMG_FILE_WORK_TABLE_LO = 31
IMG_FILE_WORK_TABLE_HI = 32
IMG_FILE_WORK_COUNT = 33

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
    calln svc_transport_get_mode
    stma TRANSPORT_SNAPSHOT

    setp16 $0100      ; bind A: as D64
    calln svc_fs_bind_drive
    stma BIND_A_SNAPSHOT

    setp16 $0401      ; bind B: as DNP
    calln svc_fs_bind_drive
    stma BIND_B_SNAPSHOT

    setp8 DRIVE_A
    calln svc_drive_set_current
    stma CURRENT_DRIVE_SNAPSHOT

    setp8 DRIVE_A
    calln svc_fs_get_mount_flags
    stma CURRENT_FLAGS_SNAPSHOT

    setp8 DRIVE_A
    calln svc_fs_get_mount_type
    stma MOUNT_SNAPSHOT

    setp16 header_text
    calln svc_console_write_sc0
    calln svc_console_newline

shell_loop:
    calln svc_console_write_prompt
    calln svc_line_read
    case8 SHELL_CMD_NONE, shell_loop
    case8 SHELL_CMD_QUIT, shell_done
    case8 SHELL_CMD_RUN, cmd_run_program
    case8 SHELL_CMD_MOUNT, cmd_emit_response
    case8 SHELL_CMD_COPY, cmd_emit_response
    case8 SHELL_CMD_REN, cmd_emit_response
    case8 SHELL_CMD_DEL, cmd_emit_response
    case8 SHELL_CMD_TYPE, cmd_emit_response
    case8 SHELL_CMD_DIR, cmd_emit_response
    case8 SHELL_CMD_CD, cmd_emit_response
    case8 SHELL_CMD_HELP, cmd_emit_response
    case8 SHELL_CMD_VER, cmd_emit_response
    case8 SHELL_CMD_VOL, cmd_emit_response
    case8 SHELL_CMD_MEM, cmd_emit_response
    setp16 resp_unknown
    calln svc_console_write_sc0
    calln svc_console_newline
    jump shell_loop

cmd_emit_response:
    setp8 $11
    stma STAGE_SNAPSHOT
    calln svc_shell_response_ptr
    calln svc_console_write_sc0
    calln svc_console_newline
    jump shell_loop

cmd_run_program:
    setp8 $12
    stma STAGE_SNAPSHOT
    calln svc_program_prepare_run
    calln svc_program_get_status
    case8 RUN_STATUS_OK, cmd_run_execute
    jump cmd_run_error

cmd_run_execute:
    setp8 $13
    stma STAGE_SNAPSHOT
    setp16 resp_run_prefix
    calln svc_console_write_sc0
    calln svc_program_get_target_ptr
    calln svc_console_write_sc0
    calln svc_console_newline
    calln svc_program_get_cmdline_len
    case8 0, cmd_run_done
    setp16 resp_args_prefix
    calln svc_console_write_sc0
    calln svc_program_get_cmdline_ptr
    calln svc_console_write_sc0
    calln svc_console_newline
cmd_run_done:
    setp8 $14
    stma STAGE_SNAPSHOT
    calln svc_program_exit
    jump shell_loop

cmd_run_error:
    calln svc_program_error_ptr
    calln svc_console_write_sc0
    calln svc_console_newline
    jump shell_loop

shell_done:
    setp8 $F0
    stma STAGE_SNAPSHOT
    calln svc_mark_ready
    setp8 $F1
    stma STAGE_SNAPSHOT
    calln svc_idle
    retm

svc_get_abi_version:
    lda #<ABI_VERSION
    sta 0,x
    lda #>ABI_VERSION
    sta 1,x
    rts

svc_transport_get_mode:
    jsr uci_probe
    bcc :+
    lda #<TRANSPORT_MODE_MOCK
    sta 0,x
    lda #$00
    sta 1,x
    rts
:
    lda #<TRANSPORT_MODE_UCI_HW
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_drive_get_current:
    lda current_drive
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_drive_set_current:
    lda 0,x
    cmp #DRIVE_B+1
    bcs drive_set_invalid
    sta current_drive
    sta 0,x
    lda #$00
    sta 1,x
    rts
drive_set_invalid:
    lda current_drive
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_fs_get_mount_type:
    ldy 0,x
    cpy #2
    bcs fs_get_type_invalid
    lda mount_kind_table,y
    sta 0,x
    lda #$00
    sta 1,x
    rts
fs_get_type_invalid:
    lda #MOUNT_KIND_NONE
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_fs_get_mount_flags:
    ldy 0,x
    cpy #2
    bcs fs_get_flags_invalid
    lda mount_flag_table,y
    sta 0,x
    lda #$00
    sta 1,x
    rts
fs_get_flags_invalid:
    lda #MOUNT_FLAG_NONE
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_fs_get_dir_state:
    ldy 0,x
    cpy #2
    bcs fs_get_dir_invalid
    lda dir_state_table,y
    sta 0,x
    lda #$00
    sta 1,x
    rts
fs_get_dir_invalid:
    lda #DIR_ID_ROOT
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_fs_get_volume_ptr:
    ldy 0,x
    cpy #2
    bcs fs_get_volume_invalid
    lda volume_ptr_lo,y
    sta 0,x
    lda volume_ptr_hi,y
    sta 1,x
    rts
fs_get_volume_invalid:
    lda #<volume_unknown
    sta 0,x
    lda #>volume_unknown
    sta 1,x
    rts

svc_fs_get_backend_path_ptr:
    stx saved_rp_x
    ldy 0,x
    cpy #2
    bcs fs_get_backend_path_invalid
    sty temp_drive
    jsr refresh_drive_backend_path
    ldx saved_rp_x
    lda PTR
    sta 0,x
    lda PTR+1
    sta 1,x
    rts
fs_get_backend_path_invalid:
    ldx saved_rp_x
    lda #<volume_unknown
    sta 0,x
    lda #>volume_unknown
    sta 1,x
    rts

svc_fs_get_dir_listing_ptr:
    ldy 0,x
    cpy #2
    bcs fs_get_listing_invalid
    sty temp_drive
    lda 1,x
    jsr select_dir_listing_ptr
    lda PTR
    sta 0,x
    lda PTR+1
    sta 1,x
    rts
fs_get_listing_invalid:
    lda #<resp_dir_flat
    sta 0,x
    lda #>resp_dir_flat
    sta 1,x
    rts

svc_fs_enum_begin:
    ldy 0,x
    cpy #2
    bcs fs_enum_begin_invalid
    sty temp_drive
    lda 1,x
    sta temp_dir_id
    jsr fs_enum_begin_current
    lda enum_count
    sta 0,x
    lda #$00
    sta 1,x
    rts
fs_enum_begin_invalid:
    lda #$00
    sta 0,x
    sta 1,x
    rts

svc_fs_enum_next:
    jsr fs_enum_next_ptr
    bcc fs_enum_next_ok
    lda #$00
    sta 0,x
    sta 1,x
    rts
fs_enum_next_ok:
    lda PTR
    sta 0,x
    lda PTR+1
    sta 1,x
    rts

svc_fs_bind_drive:
    stx saved_rp_x
    ldy 0,x
    cpy #2
    bcs fs_bind_invalid
    lda 1,x
    sta mount_kind_table,y
    sta temp_mount_kind
    sty temp_drive
    jsr kind_to_flags
    sta mount_flag_table,y
    lda #DIR_ID_ROOT
    sta dir_state_table,y
    jsr install_mounted_image
    jsr refresh_drive_backend_path
    ldy temp_drive
    ldx saved_rp_x
    lda mount_kind_table,y
    sta 0,x
    lda mount_flag_table,y
    sta 1,x
    rts
fs_bind_invalid:
    ldx saved_rp_x
    lda #MOUNT_KIND_NONE
    sta 0,x
    lda #MOUNT_FLAG_NONE
    sta 1,x
    rts

install_mounted_image:
    lda temp_mount_kind
    jsr select_image_descriptor
    ldy temp_drive
    lda PTR
    sta mounted_image_lo,y
    lda PTR+1
    sta mounted_image_hi,y
    ldy #IMG_VOL_LO
    lda (PTR),y
    ldy temp_drive
    sta volume_ptr_lo,y
    ldy #IMG_VOL_HI
    lda (PTR),y
    ldy temp_drive
    sta volume_ptr_hi,y
    jsr clear_dynamic_work_drive
    rts

refresh_drive_backend_path:
    jsr select_backend_path_cache
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr uci_probe
    bcs refresh_drive_backend_path_mock
    jsr sync_drive_backend_path_hw
    bcs refresh_drive_backend_path_mock
    jsr fill_backend_path_hw
    bcc refresh_drive_backend_path_done
refresh_drive_backend_path_mock:
    jsr fill_backend_path_mock
refresh_drive_backend_path_done:
    jsr snapshot_backend_path_length
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    rts

select_backend_path_cache:
    ldy temp_drive
    cpy #DRIVE_A
    beq select_backend_path_cache_a
    lda #<backend_path_cache_b
    sta PTR
    lda #>backend_path_cache_b
    sta PTR+1
    rts
select_backend_path_cache_a:
    lda #<backend_path_cache_a
    sta PTR
    lda #>backend_path_cache_a
    sta PTR+1
    rts

fill_backend_path_mock:
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    ldy #$00
    lda #ASCII_SLASH
    sta (PTR),y
    iny
    ldx temp_drive
    lda dir_state_table,x
    beq fill_backend_path_mock_done
    cmp #DIR_ID_BIN
    beq fill_backend_path_mock_bin
    cmp #DIR_ID_SRC
    beq fill_backend_path_mock_src
    cmp #DIR_ID_WORK
    beq fill_backend_path_mock_work
    jmp fill_backend_path_mock_done
fill_backend_path_mock_bin:
    lda #'B'
    sta (PTR),y
    iny
    lda #'I'
    sta (PTR),y
    iny
    lda #'N'
    sta (PTR),y
    iny
    jmp fill_backend_path_mock_done
fill_backend_path_mock_src:
    lda #'S'
    sta (PTR),y
    iny
    lda #'R'
    sta (PTR),y
    iny
    lda #'C'
    sta (PTR),y
    iny
    jmp fill_backend_path_mock_done
fill_backend_path_mock_work:
    lda #'W'
    sta (PTR),y
    iny
    lda #'O'
    sta (PTR),y
    iny
    lda #'R'
    sta (PTR),y
    iny
    lda #'K'
    sta (PTR),y
    iny
fill_backend_path_mock_done:
    lda #$00
    sta (PTR),y
    clc
    rts

fill_backend_path_hw:
    jsr build_uci_target_header
    lda #DOS_CMD_GET_PATH
    sta uci_cmd_buffer+1
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    lda #2
    jsr uci_issue_data_status
    bcs fill_backend_path_hw_fail
    jsr uci_status_is_ok
    bcs fill_backend_path_hw_fail
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    ldy #$00
fill_backend_path_hw_copy:
    cpy uci_data_length
    bcs fill_backend_path_hw_done
    lda uci_data_buffer,y
    sta (PTR),y
    iny
    cpy #MAX_LINE_LEN
    bcc fill_backend_path_hw_copy
fill_backend_path_hw_done:
    lda #$00
    sta (PTR),y
    clc
    rts
fill_backend_path_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

sync_drive_backend_path_hw:
    lda #<desired_path_buffer
    sta SCREEN_PTR
    lda #>desired_path_buffer
    sta SCREEN_PTR+1
    jsr fill_backend_path_mock
    jsr build_uci_target_header
    lda #DOS_CMD_CHANGE_DIR
    sta uci_cmd_buffer+1
    ldy #$00
sync_drive_backend_path_copy:
    lda desired_path_buffer,y
    beq sync_drive_backend_path_send
    sta uci_cmd_buffer+2,y
    iny
    cpy #MAX_LINE_LEN
    bcc sync_drive_backend_path_copy
sync_drive_backend_path_send:
    tya
    clc
    adc #2
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs sync_drive_backend_path_fail
    jsr uci_status_is_ok
    bcs sync_drive_backend_path_fail
    clc
    rts
sync_drive_backend_path_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

build_uci_target_header:
    lda temp_drive
    cmp #DRIVE_A
    beq build_uci_target_header_a
    lda #DOS_TARGET_B
    sta uci_cmd_buffer+0
    rts
build_uci_target_header_a:
    lda #DOS_TARGET_A
    sta uci_cmd_buffer+0
    rts

uci_issue_status_only:
    jsr uci_push_command
    bcs uci_issue_status_only_fail
    jsr uci_wait_reply
    bcs uci_issue_status_only_fail
    lda #<uci_status_buffer
    sta PTR
    lda #>uci_status_buffer
    sta PTR+1
    lda #MAX_LINE_LEN
    jsr uci_read_status_block
    sta uci_status_length
    tay
    lda #$00
    sta (PTR),y
    jsr uci_accept_data
    clc
    rts
uci_issue_status_only_fail:
    sec
    rts

uci_issue_data_status:
    jsr uci_push_command
    bcs uci_issue_data_status_fail
    jsr uci_wait_reply
    bcs uci_issue_data_status_fail
    lda #<uci_data_buffer
    sta PTR
    lda #>uci_data_buffer
    sta PTR+1
    lda #MAX_LINE_LEN
    jsr uci_read_data_block
    sta uci_data_length
    tay
    lda #$00
    sta (PTR),y
    lda #<uci_status_buffer
    sta PTR
    lda #>uci_status_buffer
    sta PTR+1
    lda #MAX_LINE_LEN
    jsr uci_read_status_block
    sta uci_status_length
    tay
    lda #$00
    sta (PTR),y
    jsr uci_accept_data
    clc
    rts
uci_issue_data_status_fail:
    sec
    rts

uci_status_is_ok:
    lda uci_status_buffer+0
    cmp #'0'
    bne uci_status_is_ok_fail
    lda uci_status_buffer+1
    cmp #'0'
    bne uci_status_is_ok_fail
    clc
    rts
uci_status_is_ok_fail:
    sec
    rts

uci_status_is_dir_empty:
    lda uci_status_buffer+0
    cmp #'0'
    bne uci_status_is_dir_empty_fail
    lda uci_status_buffer+1
    cmp #'1'
    bne uci_status_is_dir_empty_fail
    clc
    rts
uci_status_is_dir_empty_fail:
    sec
    rts

snapshot_backend_path_length:
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    ldy #$00
snapshot_backend_path_scan:
    lda (PTR),y
    beq snapshot_backend_path_store
    iny
    bne snapshot_backend_path_scan
snapshot_backend_path_store:
    ldx temp_drive
    cpx #DRIVE_A
    beq snapshot_backend_path_store_a
    sty BACKEND_B_PATH_LEN_SNAPSHOT
    rts
snapshot_backend_path_store_a:
    sty BACKEND_A_PATH_LEN_SNAPSHOT
    rts

select_image_descriptor:
    ldy temp_drive
    cpy #DRIVE_A
    beq select_image_a
    cmp #MOUNT_KIND_D64
    beq select_image_b_d64
    cmp #MOUNT_KIND_D71
    beq select_image_b_d71
    cmp #MOUNT_KIND_D81
    beq select_image_b_d81
    cmp #MOUNT_KIND_DNP
    beq select_image_b_dnp
    lda #<image_none_b
    sta PTR
    lda #>image_none_b
    sta PTR+1
    rts
select_image_a:
    cmp #MOUNT_KIND_D64
    beq select_image_a_d64
    cmp #MOUNT_KIND_D71
    beq select_image_a_d71
    cmp #MOUNT_KIND_D81
    beq select_image_a_d81
    cmp #MOUNT_KIND_DNP
    beq select_image_a_dnp
    lda #<image_none_a
    sta PTR
    lda #>image_none_a
    sta PTR+1
    rts
select_image_a_d64:
    lda #<image_a_d64
    sta PTR
    lda #>image_a_d64
    sta PTR+1
    rts
select_image_a_d71:
    lda #<image_a_d71
    sta PTR
    lda #>image_a_d71
    sta PTR+1
    rts
select_image_a_d81:
    lda #<image_a_d81
    sta PTR
    lda #>image_a_d81
    sta PTR+1
    rts
select_image_a_dnp:
    lda #<image_a_dnp
    sta PTR
    lda #>image_a_dnp
    sta PTR+1
    rts
select_image_b_d64:
    lda #<image_b_d64
    sta PTR
    lda #>image_b_d64
    sta PTR+1
    rts
select_image_b_d71:
    lda #<image_b_d71
    sta PTR
    lda #>image_b_d71
    sta PTR+1
    rts
select_image_b_d81:
    lda #<image_b_d81
    sta PTR
    lda #>image_b_d81
    sta PTR+1
    rts
select_image_b_dnp:
    lda #<image_b_dnp
    sta PTR
    lda #>image_b_dnp
    sta PTR+1
    rts

kind_to_flags:
    cmp #MOUNT_KIND_NONE
    beq :+
    cmp #MOUNT_KIND_DNP
    beq kind_tree
    lda #MOUNT_FLAG_FLAT
    rts
kind_tree:
    lda #MOUNT_FLAG_TREE
    rts
:
    lda #MOUNT_FLAG_NONE
    rts

svc_console_reset:
    lda #$00
    sta CURSOR
    sta CURSOR+1
    lda #$00
    sta script_index
    sta script_line_count
    sta input_mode
    sta line_length
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

console_putc:
    pha
    clc
    lda CURSOR
    adc #<SCREEN
    sta SCREEN_PTR
    lda CURSOR+1
    adc #>SCREEN
    sta SCREEN_PTR+1
    pla
    jsr normalize_output_char
    ldx #$00
    sta (SCREEN_PTR,x)
    inc CURSOR
    bne :+
    inc CURSOR+1
:
    rts

normalize_output_char:
    cmp #$41
    bcc output_char_done
    cmp #$5B
    bcc output_char_upper
    cmp #$61
    bcc output_char_done
    cmp #$7B
    bcs output_char_done
    sec
    sbc #$60
    rts
output_char_upper:
    sec
    sbc #$40
output_char_done:
    rts

console_backspace:
    lda CURSOR
    ora CURSOR+1
    beq backspace_done
    lda CURSOR
    bne :+
    dec CURSOR+1
:
    dec CURSOR
    lda #$20
    jsr console_putc
    lda CURSOR
    bne :+
    dec CURSOR+1
:
    dec CURSOR
backspace_done:
    rts

console_mod40:
    lda CURSOR
    sta SCREEN_PTR
    lda CURSOR+1
    sta SCREEN_PTR+1
mod40_loop:
    lda SCREEN_PTR+1
    bne mod40_sub
    lda SCREEN_PTR
    cmp #40
    bcc mod40_done
mod40_sub:
    sec
    lda SCREEN_PTR
    sbc #40
    sta SCREEN_PTR
    lda SCREEN_PTR+1
    sbc #0
    sta SCREEN_PTR+1
    jmp mod40_loop
mod40_done:
    lda SCREEN_PTR
    rts

svc_console_newline:
    jsr console_mod40
    beq newline_done
newline_loop:
    lda #$20
    jsr console_putc
    jsr console_mod40
    bne newline_loop
newline_done:
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
    jsr console_putc
    iny
    bne write_loop
write_done:
    rts

svc_console_write_prompt:
    jsr build_prompt_response
    jmp svc_console_write_sc0

svc_line_read:
    lda input_mode
    bne svc_line_read_script
    jmp svc_line_read_keyboard

svc_line_read_keyboard:
    stx saved_rp_x
    lda #$00
    sta line_length
    lda #$20
    jsr console_putc
keyboard_wait:
    lda input_mode
    bne svc_line_read_script
    jsr GETIN
    beq keyboard_wait
    cmp #KEY_RETURN
    beq keyboard_finish
    cmp #KEY_LINEFEED
    beq keyboard_finish
    cmp #KEY_BACKSPACE
    beq keyboard_backspace
    jsr normalize_input_char
    bcc keyboard_wait
    ldy line_length
    cpy #MAX_LINE_LEN
    bcs keyboard_wait
    sta line_buffer,y
    iny
    sty line_length
    jsr console_putc
    jmp keyboard_wait
keyboard_backspace:
    lda line_length
    beq keyboard_wait
    dec line_length
    jsr console_backspace
    jmp keyboard_wait
keyboard_finish:
    jsr svc_console_newline
    jsr tokenize_line_buffer
    ldx saved_rp_x
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_line_read_script:
    stx saved_rp_x
    ldy script_index
    cpy script_line_count
    bcs line_empty
    tya
    asl
    asl
    asl
    asl
    asl
    clc
    adc #<script_line_data
    sta PTR
    lda #>script_line_data
    adc #$00
    sta PTR+1
    inc script_index
    lda #$00
    sta line_length
    lda #$20
    jsr console_putc
    ldy #$00
line_echo_loop:
    lda (PTR),y
    beq line_echo_done
    jsr normalize_input_char
    bcc line_echo_next
    ldx line_length
    cpx #MAX_LINE_LEN
    bcs line_echo_done
    sta line_buffer,x
    inx
    stx line_length
    jsr console_putc
line_echo_next:
    iny
    bne line_echo_loop
line_echo_done:
    ldx line_length
    lda #$00
    sta line_buffer,x
    jsr svc_console_newline
    jsr tokenize_line_buffer
    ldx saved_rp_x
    sta 0,x
    lda #$00
    sta 1,x
    rts
line_empty:
    lda #INPUT_MODE_KEYBOARD
    sta input_mode
    lda #SHELL_CMD_NONE
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_shell_response_ptr:
    lda 0,x
    cmp #SHELL_CMD_HELP
    beq shell_resp_help
    cmp #SHELL_CMD_MOUNT
    beq shell_resp_mount
    cmp #SHELL_CMD_COPY
    beq shell_resp_copy
    cmp #SHELL_CMD_REN
    beq shell_resp_ren
    cmp #SHELL_CMD_DEL
    beq shell_resp_del
    cmp #SHELL_CMD_TYPE
    beq shell_resp_type
    cmp #SHELL_CMD_DIR
    beq shell_resp_dir
    cmp #SHELL_CMD_CD
    beq shell_resp_cd
    cmp #SHELL_CMD_VER
    beq shell_resp_ver
    cmp #SHELL_CMD_VOL
    beq shell_resp_vol
    cmp #SHELL_CMD_MEM
    beq shell_resp_mem
    lda #<resp_unknown
    sta 0,x
    lda #>resp_unknown
    sta 1,x
    rts
shell_resp_help:
    lda #<resp_help
    sta 0,x
    lda #>resp_help
    sta 1,x
    rts
shell_resp_mount:
    jsr build_mount_response
    rts
shell_resp_copy:
    jsr build_copy_response
    rts
shell_resp_ren:
    jsr build_ren_response
    rts
shell_resp_del:
    jsr build_del_response
    rts
shell_resp_type:
    jsr build_type_response
    rts
shell_resp_dir:
    jsr build_dir_response
    rts
shell_resp_cd:
    jsr build_cd_response
    rts
shell_resp_ver:
    jsr build_ver_response
    rts
shell_resp_vol:
    jsr build_vol_response
    rts
shell_resp_mem:
    lda #<resp_mem
    sta 0,x
    lda #>resp_mem
    sta 1,x
    rts

normalize_input_char:
    cmp #$01
    bcc normalize_reject
    cmp #$1B
    bcc normalize_accept
    cmp #ASCII_SPACE
    beq normalize_accept
    cmp #ASCII_COMMA
    beq normalize_accept
    cmp #ASCII_DASH
    beq normalize_accept
    cmp #ASCII_DOT
    beq normalize_accept
    cmp #ASCII_SLASH
    beq normalize_accept
    cmp #$30
    bcc normalize_reject
    cmp #$3A
    bcc normalize_accept
    cmp #ASCII_COLON
    beq normalize_accept
    cmp #$41
    bcc normalize_reject
    cmp #$5B
    bcc normalize_ascii_upper
    cmp #ASCII_UNDERSCORE
    beq normalize_accept
    cmp #$61
    bcc normalize_reject
    cmp #$7B
    bcs normalize_reject
    sec
    sbc #$60
    sec
    rts
normalize_ascii_upper:
    sec
    sbc #$40
    sec
    rts
normalize_reject:
    clc
    rts
normalize_accept:
    sec
    rts

tokenize_line_buffer:
    lda #$00
    sta arg_length
    sta arg_buffer
    ldy #$00
token_skip_leading:
    cpy line_length
    bcc :+
    jmp token_none
:
    lda line_buffer,y
    cmp #ASCII_SPACE
    bne token_cmd_start
    iny
    bne token_skip_leading
token_cmd_start:
    sty parse_cmd_start
token_cmd_scan:
    cpy line_length
    bcs token_cmd_done
    lda line_buffer,y
    cmp #ASCII_SPACE
    beq token_cmd_done
    iny
    bne token_cmd_scan
token_cmd_done:
    sty parse_scan_index
    tya
    sec
    sbc parse_cmd_start
    sta cmd_length
token_skip_gap:
    cpy line_length
    bcs token_dispatch
    lda line_buffer,y
    cmp #ASCII_SPACE
    bne token_arg_copy
    iny
    bne token_skip_gap
token_arg_copy:
    sty parse_scan_index
    lda #$00
    sta arg_length
    sta arg_trim_length
token_arg_loop:
    ldy parse_scan_index
    cpy line_length
    bcs token_arg_done
    ldx arg_length
    cpx #MAX_LINE_LEN
    bcs token_arg_done
    lda line_buffer,y
    sta arg_buffer,x
    inx
    stx arg_length
    cmp #ASCII_SPACE
    beq token_arg_continue
    stx arg_trim_length
token_arg_continue:
    iny
    sty parse_scan_index
    jmp token_arg_loop
token_arg_done:
    ldx arg_trim_length
    stx arg_length
    lda #$00
    sta arg_buffer,x
token_dispatch:
    lda line_length
    bne :+
    jmp token_none
:
    lda cmd_length
    cmp #2
    beq token_len2
    cmp #3
    beq token_len3
    cmp #4
    bne :+
    jmp token_len4
:
    cmp #5
    bne :+
    jmp token_len5
:
    jmp token_unknown
token_len2:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_C
    beq token_len2_cd
    cmp #$01
    beq token_len2_drive
    cmp #$02
    beq token_len2_drive
    jmp token_unknown
token_len2_cd:
    iny
    lda line_buffer,y
    cmp #CMD_D
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_CD
    rts
token_len2_drive:
    iny
    lda line_buffer,y
    cmp #ASCII_COLON
    beq :+
    jmp token_unknown
:
    jsr copy_cmd_token_to_arg
    lda #SHELL_CMD_CD
    rts
token_len3:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_R
    bne token_len3_del
    iny
    lda line_buffer,y
    cmp #CMD_E
    beq token_len3_ren_tail
    jmp token_unknown
token_len3_ren_tail:
    iny
    lda line_buffer,y
    cmp #CMD_N
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_REN
    rts
token_len3_del:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_D
    bne token_len3_dir
    iny
    lda line_buffer,y
    cmp #CMD_E
    bne token_len3_dir
    iny
    lda line_buffer,y
    cmp #CMD_L
    bne token_len3_dir
    lda #SHELL_CMD_DEL
    rts
token_len3_dir:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_D
    bne token_len3_ver
    iny
    lda line_buffer,y
    cmp #CMD_I
    bne token_len3_ver
    iny
    lda line_buffer,y
    cmp #CMD_R
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_DIR
    rts
token_len3_ver:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_V
    bne token_len3_mem
    iny
    lda line_buffer,y
    cmp #CMD_E
    bne token_len3_vol
    iny
    lda line_buffer,y
    cmp #CMD_R
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_VER
    rts
token_len3_vol:
    ldy parse_cmd_start
    iny
    lda line_buffer,y
    cmp #CMD_O
    bne token_len3_mem
    iny
    lda line_buffer,y
    cmp #CMD_L
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_VOL
    rts
token_len3_mem:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_M
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_E
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_M
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_MEM
    rts
token_len4:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_H
    bne token_len4_type
    iny
    lda line_buffer,y
    cmp #CMD_E
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_L
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_P
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_HELP
    rts
token_len4_type:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_T
    bne token_len4_copy
    iny
    lda line_buffer,y
    cmp #CMD_Y
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_P
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_E
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_TYPE
    rts
token_len4_copy:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_C
    bne token_len4_quit
    iny
    lda line_buffer,y
    cmp #CMD_O
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_P
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_Y
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_COPY
    rts
token_len4_quit:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_Q
    bne token_len4_exit
    iny
    lda line_buffer,y
    cmp #CMD_U
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_I
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_T
    bne token_unknown
    lda #SHELL_CMD_QUIT
    rts
token_len4_exit:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_E
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_X
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_I
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_T
    bne token_unknown
    lda #SHELL_CMD_QUIT
    rts
token_len5:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_M
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_O
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_U
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_N
    bne token_unknown
    iny
    lda line_buffer,y
    cmp #CMD_T
    bne token_unknown
    lda #SHELL_CMD_MOUNT
    rts
token_none:
    lda #SHELL_CMD_NONE
    rts
token_unknown:
    lda cmd_length
    beq token_unknown_fail
    jsr copy_full_line_to_arg
    bcs token_unknown_fail
    lda #SHELL_CMD_RUN
    rts
token_unknown_fail:
    lda #$FF
    rts

copy_cmd_token_to_arg:
    ldx #$00
    ldy parse_cmd_start
copy_cmd_token_loop:
    cpx cmd_length
    bcs copy_cmd_token_done
    lda line_buffer,y
    sta arg_buffer,x
    inx
    iny
    bne copy_cmd_token_loop
copy_cmd_token_done:
    stx arg_length
    lda #$00
    sta arg_buffer,x
    rts

copy_full_line_to_arg:
    lda #$00
    sta arg_length
    sta arg_trim_length
    ldx #$00
    ldy parse_cmd_start
copy_full_line_loop:
    cpy line_length
    bcs copy_full_line_done
    cpx #MAX_LINE_LEN
    bcs copy_full_line_done
    lda line_buffer,y
    sta arg_buffer,x
    inx
    cmp #ASCII_SPACE
    beq copy_full_line_next
    stx arg_trim_length
copy_full_line_next:
    iny
    bne copy_full_line_loop
copy_full_line_done:
    ldx arg_trim_length
    stx arg_length
    lda #$00
    sta arg_buffer,x
    cpx #$00
    beq copy_full_line_fail
    clc
    rts
copy_full_line_fail:
    sec
    rts

split_inline_command_arg:
    lda cmd_length
    cmp #3
    bcs :+
    jmp split_inline_done
:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_C
    bne split_inline_try_dir
    iny
    lda line_buffer,y
    cmp #CMD_D
    beq :+
    jmp split_inline_try_copy
:
    lda cmd_length
    cmp #2
    bne :+
    jmp split_inline_done
:
    sec
    sbc #2
    sta arg_length
    lda #2
    sta parse_scan_index
    lda #2
    sta cmd_length
    jmp split_inline_copy
split_inline_try_dir:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_D
    bne split_inline_try_ren
    iny
    lda line_buffer,y
    cmp #CMD_E
    beq :+
    jmp split_inline_try_dir_real
:
    iny
    lda line_buffer,y
    cmp #CMD_L
    beq :+
    jmp split_inline_try_dir_real
:
    lda cmd_length
    cmp #3
    bne :+
    jmp split_inline_done
:
    sec
    sbc #3
    sta arg_length
    lda #3
    sta parse_scan_index
    lda #3
    sta cmd_length
    jmp split_inline_copy
split_inline_try_ren:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_R
    bne split_inline_try_run
    iny
    lda line_buffer,y
    cmp #CMD_E
    bne split_inline_try_run
    iny
    lda line_buffer,y
    cmp #CMD_N
    bne split_inline_try_run
    lda cmd_length
    cmp #3
    bne :+
    jmp split_inline_done
:
    sec
    sbc #3
    sta arg_length
    lda #3
    sta parse_scan_index
    lda #3
    sta cmd_length
    jmp split_inline_copy
split_inline_try_run:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_R
    bne split_inline_try_dir_real
    iny
    lda line_buffer,y
    cmp #CMD_U
    bne split_inline_try_dir_real
    iny
    lda line_buffer,y
    cmp #CMD_N
    bne split_inline_try_dir_real
    lda cmd_length
    cmp #3
    bne :+
    jmp split_inline_done
:
    sec
    sbc #3
    sta arg_length
    lda #3
    sta parse_scan_index
    lda #3
    sta cmd_length
    jmp split_inline_copy
split_inline_try_dir_real:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_D
    bne split_inline_try_type
    iny
    lda line_buffer,y
    cmp #CMD_I
    bne split_inline_try_type
    iny
    lda line_buffer,y
    cmp #CMD_R
    bne split_inline_try_type
    lda cmd_length
    cmp #3
    bne :+
    jmp split_inline_done
:
    sec
    sbc #3
    sta arg_length
    lda #3
    sta parse_scan_index
    lda #3
    sta cmd_length
    jmp split_inline_copy
split_inline_try_copy:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_C
    bne split_inline_try_type
    iny
    lda line_buffer,y
    cmp #CMD_O
    bne split_inline_try_type
    iny
    lda line_buffer,y
    cmp #CMD_P
    bne split_inline_try_type
    iny
    lda line_buffer,y
    cmp #CMD_Y
    bne split_inline_try_type
    lda cmd_length
    cmp #4
    bne :+
    jmp split_inline_done
:
    sec
    sbc #4
    sta arg_length
    lda #4
    sta parse_scan_index
    lda #4
    sta cmd_length
    jmp split_inline_copy
split_inline_try_type:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_T
    bne split_inline_try_mount
    iny
    lda line_buffer,y
    cmp #CMD_Y
    bne split_inline_try_mount
    iny
    lda line_buffer,y
    cmp #CMD_P
    bne split_inline_try_mount
    iny
    lda line_buffer,y
    cmp #CMD_E
    bne split_inline_try_mount
    lda cmd_length
    cmp #4
    beq split_inline_done
    sec
    sbc #4
    sta arg_length
    lda #4
    sta parse_scan_index
    lda #4
    sta cmd_length
    jmp split_inline_copy
split_inline_try_mount:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_M
    bne split_inline_done
    iny
    lda line_buffer,y
    cmp #CMD_O
    bne split_inline_done
    iny
    lda line_buffer,y
    cmp #CMD_U
    bne split_inline_done
    iny
    lda line_buffer,y
    cmp #CMD_N
    bne split_inline_done
    iny
    lda line_buffer,y
    cmp #CMD_T
    bne split_inline_done
    lda cmd_length
    cmp #5
    beq split_inline_done
    sec
    sbc #5
    sta arg_length
    lda #5
    sta parse_scan_index
    lda #5
    sta cmd_length
split_inline_copy:
    ldx #$00
split_inline_copy_loop:
    cpx arg_length
    bcs split_inline_terminate
    txa
    clc
    adc parse_cmd_start
    adc parse_scan_index
    tay
    lda line_buffer,y
    sta arg_buffer,x
    inx
    jmp split_inline_copy_loop
split_inline_terminate:
    lda #$00
    sta arg_buffer,x
split_inline_done:
    rts

build_prompt_response:
    stx saved_rp_x
    lda current_drive
    sta temp_drive
    tay
    lda dir_state_table,y
    sta temp_dir_id
    ldy #$00
    lda #ASCII_SPACE
    sta response_buffer,y
    iny
    lda #ASCII_SPACE
    sta response_buffer,y
    iny
    jsr append_selected_drive_path
    lda #ASCII_GT
    sta response_buffer,y
    iny
    lda #$00
    sta response_buffer,y
    ldx saved_rp_x
    lda #<response_buffer
    sta 0,x
    lda #>response_buffer
    sta 1,x
    rts

build_dir_response:
    stx saved_rp_x
    jsr resolve_arg_target
    cmp #PATH_STATUS_OK
    beq dir_build_ok
    cmp #PATH_STATUS_FLAT
    beq dir_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq dir_build_unmounted
    ldx saved_rp_x
    lda #<resp_bad_dir
    sta 0,x
    lda #>resp_bad_dir
    sta 1,x
    rts
dir_build_flat:
    ldx saved_rp_x
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
dir_build_unmounted:
    ldx saved_rp_x
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
dir_build_ok:
    ldy #$00
    jsr append_selected_drive_path
    lda #ASCII_SPACE
    sta response_buffer,y
    iny
    jsr fs_enum_begin_current
dir_append_loop:
    jsr fs_enum_next_ptr
    bcs dir_build_done
    jsr append_ptr_to_response
    lda enum_index
    cmp enum_count
    bcs dir_build_done
    lda #ASCII_SPACE
    sta response_buffer,y
    iny
    jmp dir_append_loop
dir_build_done:
    lda #$00
    sta response_buffer,y
    ldx saved_rp_x
    lda #<response_buffer
    sta 0,x
    lda #>response_buffer
    sta 1,x
    rts

build_cd_response:
    stx saved_rp_x
    jsr resolve_arg_target
    cmp #PATH_STATUS_OK
    beq cd_build_ok
    cmp #PATH_STATUS_FLAT
    beq cd_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq cd_build_unmounted
    ldx saved_rp_x
    lda #<resp_bad_dir
    sta 0,x
    lda #>resp_bad_dir
    sta 1,x
    rts
cd_build_flat:
    ldx saved_rp_x
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
cd_build_unmounted:
    ldx saved_rp_x
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
cd_build_ok:
    lda temp_drive
    sta current_drive
    sta CURRENT_DRIVE_SNAPSHOT
    tay
    lda temp_dir_id
    sta dir_state_table,y
    sty temp_drive
    jsr refresh_drive_backend_path
    ldy temp_drive
    lda mount_flag_table,y
    sta CURRENT_FLAGS_SNAPSHOT
    lda mount_kind_table,y
    sta MOUNT_SNAPSHOT
    ldy #$00
    jsr append_selected_drive_path
    lda #$00
    sta response_buffer,y
    ldx saved_rp_x
    lda #<response_buffer
    sta 0,x
    lda #>response_buffer
    sta 1,x
    rts

build_mount_response:
    stx saved_rp_x
    jsr resolve_mount_arg
    cmp #MOUNT_STATUS_OK
    beq mount_build_ok
    ldx saved_rp_x
    lda #<resp_bad_mount
    sta 0,x
    lda #>resp_bad_mount
    sta 1,x
    rts
mount_build_ok:
    ldy temp_drive
    lda temp_mount_kind
    sta mount_kind_table,y
    jsr kind_to_flags
    sta mount_flag_table,y
    lda #DIR_ID_ROOT
    sta dir_state_table,y
    jsr install_mounted_image
    jsr refresh_drive_backend_path
    lda temp_drive
    cmp current_drive
    bne mount_build_reply
    sta CURRENT_DRIVE_SNAPSHOT
    tay
    lda mount_flag_table,y
    sta CURRENT_FLAGS_SNAPSHOT
    lda mount_kind_table,y
    sta MOUNT_SNAPSHOT
mount_build_reply:
    ldy #$00
    jsr append_selected_drive_summary
    lda #$00
    sta response_buffer,y
    ldx saved_rp_x
    lda #<response_buffer
    sta 0,x
    lda #>response_buffer
    sta 1,x
    rts

build_copy_response:
    stx saved_rp_x
    jsr split_copy_args
    bcc copy_source_ready
    ldx saved_rp_x
    lda #<resp_bad_copy
    sta 0,x
    lda #>resp_bad_copy
    sta 1,x
    rts
copy_source_ready:
    jsr resolve_file_target
    cmp #PATH_STATUS_OK
    beq copy_source_lookup
    cmp #PATH_STATUS_FLAT
    beq copy_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq copy_build_unmounted
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
copy_source_lookup:
    jsr lookup_file_content
    bcc copy_have_source
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
copy_have_source:
    lda PTR
    sta copy_content_lo
    lda PTR+1
    sta copy_content_hi
    jsr load_copy_dest_arg
    jsr resolve_copy_dest
    cmp #PATH_STATUS_OK
    beq copy_store_target
    cmp #PATH_STATUS_FLAT
    beq copy_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq copy_build_unmounted
    cmp #PATH_STATUS_BAD
    beq copy_build_bad
    ldx saved_rp_x
    lda #<resp_read_only
    sta 0,x
    lda #>resp_read_only
    sta 1,x
    rts
copy_store_target:
    jsr store_copy_to_work
    bcc copy_build_ok
    ldx saved_rp_x
    lda #<resp_no_space
    sta 0,x
    lda #>resp_no_space
    sta 1,x
    rts
copy_build_flat:
    ldx saved_rp_x
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
copy_build_unmounted:
    ldx saved_rp_x
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
copy_build_bad:
    ldx saved_rp_x
    lda #<resp_bad_copy
    sta 0,x
    lda #>resp_bad_copy
    sta 1,x
    rts
copy_build_ok:
    ldx saved_rp_x
    lda #<resp_copied
    sta 0,x
    lda #>resp_copied
    sta 1,x
    rts

build_ren_response:
    stx saved_rp_x
    jsr split_ren_args
    bcc ren_source_ready
    ldx saved_rp_x
    lda #<resp_bad_ren
    sta 0,x
    lda #>resp_bad_ren
    sta 1,x
    rts
ren_source_ready:
    jsr resolve_file_target
    cmp #PATH_STATUS_OK
    beq ren_source_lookup
    cmp #PATH_STATUS_FLAT
    bne :+
    jmp ren_build_flat
:
    cmp #PATH_STATUS_UNMOUNTED
    bne :+
    jmp ren_build_unmounted
:
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
ren_source_lookup:
    lda temp_dir_id
    cmp #DIR_ID_WORK
    beq :+
    jmp ren_build_read_only
:
    jsr lookup_file_content
    bcc ren_have_source
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
ren_have_source:
    lda temp_drive
    sta source_drive
    lda file_index
    sta source_slot
    jsr load_copy_dest_arg
    jsr resolve_copy_dest
    cmp #PATH_STATUS_OK
    beq ren_dest_ready
    cmp #PATH_STATUS_FLAT
    beq ren_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq ren_build_unmounted
    cmp #PATH_STATUS_BAD
    beq ren_build_bad
    jmp ren_build_read_only
ren_dest_ready:
    lda temp_drive
    cmp source_drive
    beq :+
    jmp ren_build_bad
:
    jsr find_work_file_by_path_name
    bcs ren_apply_name
    lda file_index
    cmp source_slot
    beq ren_apply_name
    ldx saved_rp_x
    lda #<resp_exists
    sta 0,x
    lda #>resp_exists
    sta 1,x
    rts
ren_apply_name:
    lda source_drive
    sta temp_drive
    lda source_slot
    sta file_index
    jsr select_dynamic_work_name_slot
    jsr copy_path_name_to_slot_ascii
    ldx saved_rp_x
    lda #<resp_renamed
    sta 0,x
    lda #>resp_renamed
    sta 1,x
    rts
ren_build_flat:
    ldx saved_rp_x
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
ren_build_unmounted:
    ldx saved_rp_x
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
ren_build_read_only:
    ldx saved_rp_x
    lda #<resp_read_only
    sta 0,x
    lda #>resp_read_only
    sta 1,x
    rts
ren_build_bad:
    ldx saved_rp_x
    lda #<resp_bad_ren
    sta 0,x
    lda #>resp_bad_ren
    sta 1,x
    rts

build_del_response:
    stx saved_rp_x
    jsr resolve_file_target
    cmp #PATH_STATUS_OK
    beq del_source_lookup
    cmp #PATH_STATUS_FLAT
    beq del_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq del_build_unmounted
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
del_source_lookup:
    lda temp_dir_id
    cmp #DIR_ID_WORK
    beq :+
    jmp del_build_read_only
:
    jsr lookup_file_content
    bcc del_have_source
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
del_have_source:
    jsr delete_work_slot
    ldx saved_rp_x
    lda #<resp_deleted
    sta 0,x
    lda #>resp_deleted
    sta 1,x
    rts
del_build_flat:
    ldx saved_rp_x
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
del_build_unmounted:
    ldx saved_rp_x
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
del_build_read_only:
    ldx saved_rp_x
    lda #<resp_read_only
    sta 0,x
    lda #>resp_read_only
    sta 1,x
    rts

split_run_args:
    lda #$00
    sta program_cmdline_len
    sta program_cmdline_buffer
    lda arg_length
    bne :+
    sec
    rts
:
    sta program_arg_limit
    ldy #$00
split_run_find_sep:
    cpy program_arg_limit
    bcs split_run_no_cmdline
    lda arg_buffer,y
    cmp #ASCII_SPACE
    beq split_run_found_sep
    cmp #ASCII_COMMA
    beq split_run_found_sep
    cmp #ASCII_COLON
    bne :+
    cpy #$01
    bne split_run_found_sep
:
    iny
    bne split_run_find_sep
split_run_no_cmdline:
    lda arg_length
    beq split_run_fail
    clc
    rts
split_run_found_sep:
    cpy #$00
    beq split_run_fail
    sty arg_length
    lda #$00
    sta arg_buffer,y
split_run_skip_sep:
    iny
    cpy program_arg_limit
    bcs split_run_cmdline_done
    lda arg_buffer,y
    cmp #ASCII_SPACE
    beq split_run_skip_sep
    cmp #ASCII_COMMA
    beq split_run_skip_sep
    cmp #ASCII_COLON
    beq split_run_skip_sep
    ldx #$00
split_run_copy_cmdline:
    cpy program_arg_limit
    bcs split_run_store_cmdline
    cpx #MAX_LINE_LEN
    bcs split_run_store_cmdline
    lda arg_buffer,y
    sta program_cmdline_buffer,x
    inx
    iny
    bne split_run_copy_cmdline
split_run_store_cmdline:
    stx program_cmdline_len
    lda #$00
    sta program_cmdline_buffer,x
split_run_cmdline_done:
    lda arg_length
    beq split_run_fail
    clc
    rts
split_run_fail:
    sec
    rts

svc_program_prepare_run:
    stx saved_rp_x
    lda #RUN_STATUS_BAD
    sta program_status
    lda #PROGRAM_STATE_NONE
    sta PROGRAM_STATE_SNAPSHOT
    lda #$00
    sta PROGRAM_EXIT_SNAPSHOT
    lda current_drive
    sta PROGRAM_DRIVE_SNAPSHOT
    tay
    lda dir_state_table,y
    sta PROGRAM_DIR_SNAPSHOT
    lda #$00
    sta program_target_lo
    sta program_target_hi
    jsr split_run_args
    bcc program_have_target
    lda #RUN_STATUS_BAD
    jmp program_status_return
program_have_target:
    jsr ensure_run_target_extension
    bcc :+
    lda #RUN_STATUS_BAD
    jmp program_status_return
:
    jsr resolve_file_target
    cmp #PATH_STATUS_OK
    beq program_lookup
    cmp #PATH_STATUS_FLAT
    beq program_status_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq program_status_unmounted
    lda #RUN_STATUS_BAD
    jmp program_status_return
program_status_flat:
    lda #RUN_STATUS_FLAT
    jmp program_status_return
program_status_unmounted:
    lda #RUN_STATUS_UNMOUNTED
    jmp program_status_return
program_lookup:
    jsr lookup_file_content
    bcc program_ready
    lda #RUN_STATUS_NOFILE
    jmp program_status_return
program_ready:
    lda matched_name_lo
    sta program_target_lo
    lda matched_name_hi
    sta program_target_hi
    lda temp_drive
    sta PROGRAM_DRIVE_SNAPSHOT
    lda temp_dir_id
    sta PROGRAM_DIR_SNAPSHOT
    lda #PROGRAM_STATE_RUNNING
    sta PROGRAM_STATE_SNAPSHOT
    lda #RUN_STATUS_OK
program_status_return:
    sta program_status
    ldx saved_rp_x
    sta 0,x
    lda #$00
    sta 1,x
    rts

ensure_run_target_extension:
    lda #$00
    sta parse_scan_index
    sta prefix_length
    ldy #$00
ensure_run_target_scan:
    cpy arg_length
    bcs ensure_run_target_done_scan
    lda arg_buffer,y
    cmp #ASCII_SLASH
    bne ensure_run_target_check_dot
    tya
    clc
    adc #1
    sta parse_scan_index
    lda #$00
    sta prefix_length
    iny
    bne ensure_run_target_scan
ensure_run_target_check_dot:
    cmp #ASCII_DOT
    bne ensure_run_target_next
    sty parse_scan_index
    lda #$01
    sta prefix_length
ensure_run_target_next:
    iny
    bne ensure_run_target_scan
ensure_run_target_done_scan:
    lda prefix_length
    bne ensure_run_target_ok
    ldx arg_length
    cpx #MAX_LINE_LEN-4
    bcs ensure_run_target_fail
    lda #ASCII_DOT
    sta arg_buffer,x
    inx
    lda #CMD_P
    sta arg_buffer,x
    inx
    lda #CMD_R
    sta arg_buffer,x
    inx
    lda #CMD_G
    sta arg_buffer,x
    inx
    stx arg_length
    lda #$00
    sta arg_buffer,x
ensure_run_target_ok:
    clc
    rts
ensure_run_target_fail:
    sec
    rts

svc_program_get_status:
    lda program_status
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_program_error_ptr:
    lda 0,x
    cmp #RUN_STATUS_FLAT
    beq program_error_flat
    cmp #RUN_STATUS_UNMOUNTED
    beq program_error_unmounted
    cmp #RUN_STATUS_NOFILE
    beq program_error_missing
    lda #<resp_bad_run
    sta 0,x
    lda #>resp_bad_run
    sta 1,x
    rts
program_error_flat:
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
program_error_unmounted:
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
program_error_missing:
    lda #<resp_no_program
    sta 0,x
    lda #>resp_no_program
    sta 1,x
    rts

svc_program_get_target_ptr:
    lda program_target_lo
    sta 0,x
    lda program_target_hi
    sta 1,x
    rts

svc_program_get_cmdline_ptr:
    lda #<program_cmdline_buffer
    sta 0,x
    lda #>program_cmdline_buffer
    sta 1,x
    rts

svc_program_get_cmdline_len:
    lda program_cmdline_len
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_program_exit:
    lda #PROGRAM_STATE_EXITED
    sta PROGRAM_STATE_SNAPSHOT
    lda #$00
    sta PROGRAM_EXIT_SNAPSHOT
    rts

split_copy_args:
    lda arg_length
    sta cmd_length
    bne :+
    jmp split_copy_fail
:
    ldy #$00
split_copy_find_sep:
    cpy cmd_length
    bcs split_copy_try_inline_work
    lda arg_buffer,y
    cmp #ASCII_SPACE
    beq split_copy_have_sep
    cmp #ASCII_COMMA
    beq split_copy_have_sep
    iny
    bne split_copy_find_sep
split_copy_have_sep:
    cpy #$00
    bne :+
    jmp split_copy_fail
:
    sty arg_length
    lda #$00
    sta arg_buffer,y
    iny
split_copy_skip_gap:
    cpy cmd_length
    bcc :+
    jmp split_copy_fail
:
    lda arg_buffer,y
    cmp #ASCII_SPACE
    beq split_copy_skip_advance
    cmp #ASCII_COMMA
    beq split_copy_skip_advance
    bne split_copy_copy_dest
split_copy_skip_advance:
    iny
    bne split_copy_skip_gap
split_copy_copy_dest:
    lda #$00
    sta copy_dst_length
    sta copy_trim_length
split_copy_dest_loop:
    cpy cmd_length
    bcs split_copy_done
    ldx copy_dst_length
    cpx #MAX_LINE_LEN
    bcs split_copy_done
    lda arg_buffer,y
    sta copy_dst_buffer,x
    inx
    stx copy_dst_length
    cmp #ASCII_SPACE
    beq split_copy_dest_next
    stx copy_trim_length
split_copy_dest_next:
    iny
    bne split_copy_dest_loop
split_copy_done:
    ldx copy_trim_length
    bne :+
    jmp split_copy_fail
:
    stx copy_dst_length
    lda #$00
    sta copy_dst_buffer,x
    clc
    rts
split_copy_try_inline_work:
    ldy #$01
split_copy_inline_scan:
    tya
    clc
    adc #4
    cmp cmd_length
    bcc :+
    jmp split_copy_fail
:
    lda arg_buffer,y
    cmp #CMD_W
    bne split_copy_inline_next
    lda arg_buffer+1,y
    cmp #CMD_O
    bne split_copy_inline_next
    lda arg_buffer+2,y
    cmp #CMD_R
    bne split_copy_inline_next
    lda arg_buffer+3,y
    cmp #CMD_K
    bne split_copy_inline_next
    sty arg_length
    lda #$00
    sta arg_buffer,y
    tya
    clc
    adc #4
    cmp cmd_length
    bcc :+
    jmp split_copy_fail
:
    lda #CMD_W
    sta copy_dst_buffer+0
    lda #CMD_O
    sta copy_dst_buffer+1
    lda #CMD_R
    sta copy_dst_buffer+2
    lda #CMD_K
    sta copy_dst_buffer+3
    lda #ASCII_SLASH
    sta copy_dst_buffer+4
    tya
    clc
    adc #4
    tay
    ldx #5
split_copy_inline_copy:
    cpy cmd_length
    bcs split_copy_inline_done
    cpx #MAX_LINE_LEN
    bcs split_copy_inline_done
    lda arg_buffer,y
    sta copy_dst_buffer,x
    inx
    iny
    bne split_copy_inline_copy
split_copy_inline_done:
    cpx #5
    bne :+
    jmp split_copy_fail
:
    stx copy_dst_length
    lda #$00
    sta copy_dst_buffer,x
    clc
    rts
split_copy_inline_next:
    iny
    jmp split_copy_inline_scan
split_copy_fail:
    sec
    rts

split_ren_args:
    lda arg_length
    sta cmd_length
    bne :+
    jmp split_ren_fail
:
    ldy #$00
split_ren_find_sep:
    cpy cmd_length
    bcs split_ren_try_inline
    lda arg_buffer,y
    cmp #ASCII_SPACE
    beq split_ren_have_sep
    cmp #ASCII_COMMA
    beq split_ren_have_sep
    iny
    bne split_ren_find_sep
split_ren_have_sep:
    cpy #$00
    bne :+
    jmp split_ren_fail
:
    sty arg_length
    lda #$00
    sta arg_buffer,y
    iny
split_ren_skip_gap:
    cpy cmd_length
    bcc :+
    jmp split_ren_fail
:
    lda arg_buffer,y
    cmp #ASCII_SPACE
    beq split_ren_skip_next
    cmp #ASCII_COMMA
    beq split_ren_skip_next
    bne split_ren_copy_dest
split_ren_skip_next:
    iny
    bne split_ren_skip_gap
split_ren_copy_dest:
    lda #$00
    sta copy_dst_length
    sta copy_trim_length
split_ren_dest_loop:
    cpy cmd_length
    bcs split_ren_done
    ldx copy_dst_length
    cpx #MAX_LINE_LEN
    bcs split_ren_done
    lda arg_buffer,y
    sta copy_dst_buffer,x
    inx
    stx copy_dst_length
    cmp #ASCII_SPACE
    beq split_ren_dest_next
    stx copy_trim_length
split_ren_dest_next:
    iny
    bne split_ren_dest_loop
split_ren_done:
    ldx copy_trim_length
    bne :+
    jmp split_ren_fail
:
    stx copy_dst_length
    lda #$00
    sta copy_dst_buffer,x
    clc
    rts
split_ren_try_inline:
    jsr split_ren_inline_work
    bcc split_ren_inline_ok
    jmp split_ren_fail
split_ren_inline_ok:
    clc
    rts
split_ren_fail:
    sec
    rts

split_ren_inline_work:
    lda current_drive
    sta temp_drive
    tay
    lda dir_state_table,y
    cmp #DIR_ID_WORK
    beq :+
    sec
    rts
:
    jsr select_dynamic_work_file_table
    ldx temp_drive
    lda work_count_table,x
    sta file_count
    lda #$00
    sta file_index
split_ren_inline_find:
    lda file_index
    cmp file_count
    bcs split_ren_inline_fail
    asl
    asl
    tay
    lda (SCREEN_PTR),y
    sta PTR
    iny
    lda (SCREEN_PTR),y
    sta PTR+1
    jsr match_ptr_prefix_to_arg_buffer
    bcc split_ren_inline_split
    inc file_index
    bne split_ren_inline_find
split_ren_inline_split:
    ldx prefix_length
    lda arg_buffer,x
    bne :+
    sec
    rts
:
    stx arg_length
    lda #$00
    sta copy_dst_length
    sta copy_trim_length
split_ren_inline_copy:
    lda arg_buffer,x
    beq split_ren_inline_done
    ldy copy_dst_length
    cpy #MAX_LINE_LEN
    bcs split_ren_inline_done
    sta copy_dst_buffer,y
    iny
    sty copy_dst_length
    sty copy_trim_length
    inx
    bne split_ren_inline_copy
split_ren_inline_done:
    ldy copy_trim_length
    bne :+
    sec
    rts
:
    lda #$00
    sta copy_dst_buffer,y
    clc
    rts
split_ren_inline_fail:
    sec
    rts

match_ptr_prefix_to_arg_buffer:
    ldy #$00
    ldx #$00
match_prefix_loop:
    lda (PTR),y
    cmp #ASCII_DOT
    beq match_prefix_skip_candidate_dot
    lda arg_buffer,x
    cmp #ASCII_DOT
    beq match_prefix_skip_input_dot
    lda (PTR),y
    beq match_prefix_end
    lda arg_buffer,x
    beq match_prefix_fail
    lda (PTR),y
    jsr normalize_output_char
    cmp arg_buffer,x
    bne match_prefix_fail
    iny
    inx
    bne match_prefix_loop
match_prefix_skip_candidate_dot:
    iny
    bne match_prefix_loop
match_prefix_skip_input_dot:
    inx
    bne match_prefix_loop
match_prefix_end:
    stx prefix_length
    clc
    rts
match_prefix_fail:
    sec
    rts

load_copy_dest_arg:
    ldy #$00
load_copy_dest_loop:
    cpy copy_dst_length
    bcs load_copy_dest_done
    lda copy_dst_buffer,y
    sta arg_buffer,y
    iny
    bne load_copy_dest_loop
load_copy_dest_done:
    lda #$00
    sta arg_buffer,y
    sty arg_length
    rts

build_type_response:
    stx saved_rp_x
    jsr resolve_file_target
    cmp #PATH_STATUS_OK
    beq type_build_lookup
    cmp #PATH_STATUS_FLAT
    beq type_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq type_build_unmounted
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
type_build_flat:
    ldx saved_rp_x
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
type_build_unmounted:
    ldx saved_rp_x
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
type_build_lookup:
    jsr lookup_file_content
    bcc type_build_found
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
type_build_found:
    ldx saved_rp_x
    lda PTR
    sta 0,x
    lda PTR+1
    sta 1,x
    rts

resolve_file_target:
    lda current_drive
    sta temp_drive
    tay
    lda dir_state_table,y
    sta temp_dir_id
    lda #$00
    sta parse_scan_index
    lda arg_length
    bne :+
    lda #PATH_STATUS_BAD
    rts
:
    lda arg_length
    cmp #2
    bcc file_after_prefix
    lda arg_buffer+1
    cmp #ASCII_COLON
    bne file_after_prefix
    lda arg_buffer+0
    cmp #$01
    beq file_drive_a
    cmp #$02
    beq file_drive_b
    lda #PATH_STATUS_BAD
    rts
file_drive_a:
    lda #DRIVE_A
    sta temp_drive
    lda #2
    sta parse_scan_index
    jmp file_after_drive
file_drive_b:
    lda #DRIVE_B
    sta temp_drive
    lda #2
    sta parse_scan_index
file_after_drive:
    ldy temp_drive
    lda dir_state_table,y
    sta temp_dir_id
file_after_prefix:
    ldy temp_drive
    lda mount_kind_table,y
    bne :+
    jmp file_unmounted
:
    lda mount_flag_table,y
    cmp #MOUNT_FLAG_TREE
    beq file_tree
file_flat:
    ldy parse_scan_index
    cpy arg_length
    bcc :+
    jmp file_bad
:
    lda arg_buffer,y
    cmp #ASCII_SLASH
    bne file_flat_scan
    lda #DIR_ID_ROOT
    sta temp_dir_id
    iny
    sty parse_scan_index
    cpy arg_length
    bcc :+
    jmp file_bad
:
file_flat_scan:
    ldy parse_scan_index
file_flat_scan_loop:
    cpy arg_length
    bcs file_copy_name
    lda arg_buffer,y
    cmp #ASCII_SLASH
    beq file_flat_error
    iny
    bne file_flat_scan_loop
file_tree:
    ldy parse_scan_index
    cpy arg_length
    bcs file_bad
    lda arg_buffer,y
    cmp #ASCII_SLASH
    bne file_tree_find_sep
    lda #DIR_ID_ROOT
    sta temp_dir_id
    iny
    sty parse_scan_index
    cpy arg_length
    bcs file_bad
file_tree_find_sep:
    ldy parse_scan_index
file_tree_scan_loop:
    cpy arg_length
    bcs file_copy_name
    lda arg_buffer,y
    cmp #ASCII_SLASH
    beq file_tree_component
    iny
    bne file_tree_scan_loop
file_tree_component:
    sty saved_response_y
    lda parse_scan_index
    sta parse_cmd_start
    tya
    sec
    sbc parse_scan_index
    sta cmd_length
    beq file_bad
    jsr match_path_component
    bcs file_bad
    sta temp_dir_id
    ldy saved_response_y
    iny
    sty parse_scan_index
    cpy arg_length
    bcs file_bad
    ldy parse_scan_index
file_tree_filename_scan:
    cpy arg_length
    bcs file_copy_name
    lda arg_buffer,y
    cmp #ASCII_SLASH
    beq file_bad
    iny
    bne file_tree_filename_scan
file_copy_name:
    jsr copy_path_name_from_parse
    bcs file_bad
    lda #PATH_STATUS_OK
    rts
file_flat_error:
    lda #PATH_STATUS_FLAT
    rts
file_unmounted:
    lda #PATH_STATUS_UNMOUNTED
    rts
file_bad:
    lda #PATH_STATUS_BAD
    rts

match_path_component:
    lda cmd_length
    cmp #3
    beq match_path_len3
    cmp #4
    beq match_path_len4
    sec
    rts
match_path_len3:
    ldy parse_cmd_start
    lda arg_buffer,y
    cmp #CMD_B
    bne match_path_src
    iny
    lda arg_buffer,y
    cmp #CMD_I
    bne match_path_fail
    iny
    lda arg_buffer,y
    cmp #CMD_N
    bne match_path_fail
    lda #DIR_ID_BIN
    clc
    rts
match_path_src:
    ldy parse_cmd_start
    lda arg_buffer,y
    cmp #CMD_S
    bne match_path_fail
    iny
    lda arg_buffer,y
    cmp #CMD_R
    bne match_path_fail
    iny
    lda arg_buffer,y
    cmp #CMD_C
    bne match_path_fail
    lda #DIR_ID_SRC
    clc
    rts
match_path_len4:
    ldy parse_cmd_start
    lda arg_buffer,y
    cmp #CMD_W
    bne match_path_fail
    iny
    lda arg_buffer,y
    cmp #CMD_O
    bne match_path_fail
    iny
    lda arg_buffer,y
    cmp #CMD_R
    bne match_path_fail
    iny
    lda arg_buffer,y
    cmp #CMD_K
    bne match_path_fail
    lda #DIR_ID_WORK
    clc
    rts
match_path_fail:
    sec
    rts

copy_path_name_from_parse:
    ldx #$00
    ldy parse_scan_index
copy_path_name_loop:
    cpy arg_length
    bcs copy_path_name_done
    cpx #MAX_LINE_LEN
    bcs copy_path_name_done
    lda arg_buffer,y
    sta path_name_buffer,x
    inx
    iny
    bne copy_path_name_loop
copy_path_name_done:
    lda #$00
    sta path_name_buffer,x
    cpx #$00
    beq copy_path_name_empty
    clc
    rts
copy_path_name_empty:
    sec
    rts

resolve_copy_dest:
    lda current_drive
    sta temp_drive
    tay
    lda dir_state_table,y
    sta temp_dir_id
    lda #$00
    sta parse_scan_index
    lda arg_length
    bne :+
    lda #PATH_STATUS_BAD
    rts
:
    lda arg_length
    cmp #2
    bcc copy_dest_after_prefix
    lda arg_buffer+1
    cmp #ASCII_COLON
    bne copy_dest_after_prefix
    lda arg_buffer+0
    cmp #$01
    beq copy_dest_drive_a
    cmp #$02
    beq copy_dest_drive_b
    lda #PATH_STATUS_BAD
    rts
copy_dest_drive_a:
    lda #DRIVE_A
    sta temp_drive
    lda #2
    sta parse_scan_index
    jmp copy_dest_after_drive
copy_dest_drive_b:
    lda #DRIVE_B
    sta temp_drive
    lda #2
    sta parse_scan_index
copy_dest_after_drive:
    ldy temp_drive
    lda dir_state_table,y
    sta temp_dir_id
copy_dest_after_prefix:
    ldy temp_drive
    lda mount_kind_table,y
    bne :+
    jmp copy_dest_unmounted
:
    lda mount_flag_table,y
    cmp #MOUNT_FLAG_TREE
    bne copy_dest_flat
    ldy parse_scan_index
    cpy arg_length
    bcs copy_dest_bad
    lda arg_buffer,y
    cmp #ASCII_SLASH
    bne copy_dest_find_sep
    lda #DIR_ID_ROOT
    sta temp_dir_id
    iny
    sty parse_scan_index
    cpy arg_length
    bcs copy_dest_bad
copy_dest_find_sep:
    ldy parse_scan_index
copy_dest_scan_loop:
    cpy arg_length
    bcs copy_dest_name
    lda arg_buffer,y
    cmp #ASCII_SLASH
    beq copy_dest_component
    iny
    bne copy_dest_scan_loop
copy_dest_component:
    sty saved_response_y
    lda parse_scan_index
    sta parse_cmd_start
    tya
    sec
    sbc parse_scan_index
    sta cmd_length
    beq copy_dest_bad
    jsr match_path_component
    bcs copy_dest_bad
    sta temp_dir_id
    ldy saved_response_y
    iny
    sty parse_scan_index
    cpy arg_length
    bcs copy_dest_bad
    ldy parse_scan_index
copy_dest_name_scan:
    cpy arg_length
    bcs copy_dest_name
    lda arg_buffer,y
    cmp #ASCII_SLASH
    beq copy_dest_bad
    iny
    bne copy_dest_name_scan
copy_dest_name:
    jsr copy_path_name_from_parse
    bcs copy_dest_bad
    lda temp_dir_id
    cmp #DIR_ID_WORK
    beq copy_dest_ok
    lda #PATH_STATUS_READ_ONLY
    rts
copy_dest_flat:
    lda #PATH_STATUS_FLAT
    rts
copy_dest_unmounted:
    lda #PATH_STATUS_UNMOUNTED
    rts
copy_dest_bad:
    lda #PATH_STATUS_BAD
    rts
copy_dest_ok:
    lda #PATH_STATUS_OK
    rts

store_copy_to_work:
    jsr select_dynamic_work_file_table
    ldx temp_drive
    lda work_count_table,x
    sta file_count
    lda #$00
    sta file_index
store_copy_find_loop:
    lda file_index
    cmp file_count
    bcs store_copy_append
    asl
    asl
    tay
    lda (SCREEN_PTR),y
    sta PTR
    iny
    lda (SCREEN_PTR),y
    sta PTR+1
    jsr compare_ptr_to_path_name
    bcc store_copy_update
    inc file_index
    bne store_copy_find_loop
store_copy_append:
    ldx temp_drive
    lda work_count_table,x
    cmp #WORK_DYNAMIC_MAX
    bcc :+
    sec
    rts
:
    sta file_index
    inc work_count_table,x
store_copy_update:
    jsr select_dynamic_work_name_slot
    jsr copy_path_name_to_slot_ascii
    jsr select_dynamic_work_file_table
    lda file_index
    asl
    asl
    tay
    iny
    iny
    lda copy_content_lo
    sta (SCREEN_PTR),y
    iny
    lda copy_content_hi
    sta (SCREEN_PTR),y
    clc
    rts

find_work_file_by_path_name:
    jsr select_dynamic_work_file_table
    ldx temp_drive
    lda work_count_table,x
    sta file_count
    lda #$00
    sta file_index
find_work_file_loop:
    lda file_index
    cmp file_count
    bcs find_work_file_miss
    asl
    asl
    tay
    lda (SCREEN_PTR),y
    sta PTR
    iny
    lda (SCREEN_PTR),y
    sta PTR+1
    jsr compare_ptr_to_path_name
    bcc find_work_file_hit
    inc file_index
    bne find_work_file_loop
find_work_file_miss:
    sec
    rts
find_work_file_hit:
    clc
    rts

delete_work_slot:
    lda file_index
    pha
    ldx temp_drive
    lda work_count_table,x
    cmp #2
    bne delete_work_single
    pla
    cmp #$00
    bne delete_work_drop_last
    lda #$01
    sta file_index
    jsr select_dynamic_work_name_slot
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    lda #$00
    sta file_index
    jsr select_dynamic_work_name_slot
    jsr copy_slot_name_between_ptrs
    jsr select_dynamic_work_file_table
    ldy #$06
    lda (SCREEN_PTR),y
    sta copy_content_lo
    iny
    lda (SCREEN_PTR),y
    sta copy_content_hi
    jsr select_dynamic_work_file_table
    lda #$00
    sta file_index
    lda file_index
    asl
    asl
    tay
    iny
    iny
    lda copy_content_lo
    sta (SCREEN_PTR),y
    iny
    lda copy_content_hi
    sta (SCREEN_PTR),y
    lda #$01
    sta file_index
    jsr clear_dynamic_work_slot
    ldx temp_drive
    dec work_count_table,x
    rts
delete_work_drop_last:
    lda #$01
    sta file_index
    jsr clear_dynamic_work_slot
    ldx temp_drive
    dec work_count_table,x
    rts
delete_work_single:
    pla
    jsr clear_dynamic_work_slot
    ldx temp_drive
    lda #$00
    sta work_count_table,x
    rts

clear_dynamic_work_slot:
    pha
    jsr select_dynamic_work_name_slot
    ldy #$00
    lda #$00
    sta (PTR),y
    pla
    sta file_index
    jsr select_dynamic_work_file_table
    lda file_index
    asl
    asl
    tay
    iny
    iny
    lda #$00
    sta (SCREEN_PTR),y
    iny
    sta (SCREEN_PTR),y
    rts

copy_slot_name_between_ptrs:
    ldy #$00
copy_slot_name_between_loop:
    lda (SCREEN_PTR),y
    sta (PTR),y
    beq copy_slot_name_between_done
    iny
    cpy #WORK_NAME_MAX
    bcc copy_slot_name_between_loop
    dey
    lda #$00
    sta (PTR),y
copy_slot_name_between_done:
    rts

copy_path_name_to_slot_ascii:
    ldy #$00
copy_slot_name_loop:
    lda path_name_buffer,y
    beq copy_slot_name_done
    cpy #WORK_NAME_MAX-1
    bcs copy_slot_name_done
    jsr screen_code_to_ascii
    sta (PTR),y
    iny
    bne copy_slot_name_loop
copy_slot_name_done:
    lda #$00
    sta (PTR),y
    rts

screen_code_to_ascii:
    cmp #$01
    bcc screen_code_ascii_done
    cmp #$1B
    bcs screen_code_ascii_done
    clc
    adc #$40
screen_code_ascii_done:
    rts

clear_dynamic_work_drive:
    stx saved_rp_x
    ldy temp_drive
    lda #$00
    sta work_count_table,y
    jsr select_dynamic_work_name_slot_zero
    ldy #$00
    lda #$00
    sta (PTR),y
    jsr select_dynamic_work_name_slot_one
    ldy #$00
    lda #$00
    sta (PTR),y
    jsr select_dynamic_work_file_table
    ldy #2
    lda #$00
    sta (SCREEN_PTR),y
    iny
    sta (SCREEN_PTR),y
    iny
    iny
    sta (SCREEN_PTR),y
    iny
    sta (SCREEN_PTR),y
    ldx saved_rp_x
    rts

resolve_arg_target:
    lda current_drive
    sta temp_drive
    tay
    lda dir_state_table,y
    sta temp_dir_id
    lda #$00
    sta parse_scan_index
    lda arg_length
    bne :+
    jmp resolve_validate_mount
:
    lda arg_length
    cmp #2
    bcc resolve_parse_path
    lda arg_buffer+1
    cmp #ASCII_COLON
    bne resolve_parse_path
    lda arg_buffer+0
    cmp #$01
    beq resolve_drive_a
    cmp #$02
    beq resolve_drive_b
    lda #PATH_STATUS_BAD
    rts
resolve_drive_a:
    lda #DRIVE_A
    sta temp_drive
    lda #2
    sta parse_scan_index
    jmp resolve_after_prefix
resolve_drive_b:
    lda #DRIVE_B
    sta temp_drive
    lda #2
    sta parse_scan_index
resolve_after_prefix:
    ldy temp_drive
    lda dir_state_table,y
    sta temp_dir_id
resolve_parse_path:
    ldy parse_scan_index
    cpy arg_length
    bcc :+
    jmp resolve_validate_mount
:
    lda arg_buffer,y
    cmp #ASCII_SLASH
    bne resolve_need_component
    lda #DIR_ID_ROOT
    sta temp_dir_id
    iny
    sty parse_scan_index
    cpy arg_length
    bcc :+
    jmp resolve_validate_mount
:
resolve_need_component:
    ldy temp_drive
    lda mount_flag_table,y
    cmp #MOUNT_FLAG_TREE
    bne resolve_flat
    ldy parse_scan_index
    lda arg_length
    sec
    sbc parse_scan_index
    cmp #3
    beq resolve_len3
    cmp #4
    beq resolve_len4
    lda #PATH_STATUS_BAD
    rts
resolve_len3:
    lda arg_buffer,y
    cmp #CMD_B
    bne resolve_len3_src
    iny
    lda arg_buffer,y
    cmp #CMD_I
    bne resolve_bad_path
    iny
    lda arg_buffer,y
    cmp #CMD_N
    bne resolve_bad_path
    lda #DIR_ID_BIN
    sta temp_dir_id
    jmp resolve_validate_mount
resolve_len3_src:
    ldy parse_scan_index
    lda arg_buffer,y
    cmp #CMD_S
    bne resolve_bad_path
    iny
    lda arg_buffer,y
    cmp #CMD_R
    bne resolve_bad_path
    iny
    lda arg_buffer,y
    cmp #CMD_C
    bne resolve_bad_path
    lda #DIR_ID_SRC
    sta temp_dir_id
    jmp resolve_validate_mount
resolve_len4:
    lda arg_buffer,y
    cmp #CMD_W
    bne resolve_bad_path
    iny
    lda arg_buffer,y
    cmp #CMD_O
    bne resolve_bad_path
    iny
    lda arg_buffer,y
    cmp #CMD_R
    bne resolve_bad_path
    iny
    lda arg_buffer,y
    cmp #CMD_K
    bne resolve_bad_path
    lda #DIR_ID_WORK
    sta temp_dir_id
    jmp resolve_validate_mount
resolve_flat:
    lda #PATH_STATUS_FLAT
    rts
resolve_bad_path:
    lda #PATH_STATUS_BAD
    rts
resolve_validate_mount:
    ldy temp_drive
    lda mount_kind_table,y
    bne resolve_ok
    lda #PATH_STATUS_UNMOUNTED
    rts
resolve_ok:
    lda #PATH_STATUS_OK
    rts

resolve_mount_arg:
    lda current_drive
    sta temp_drive
    lda #MOUNT_KIND_NONE
    sta temp_mount_kind
    lda arg_length
    cmp #5
    beq mount_arg_len5
    jmp mount_arg_bad
mount_arg_len5:
    lda arg_buffer+1
    cmp #ASCII_COLON
    bne mount_arg_bad
    lda arg_buffer+0
    cmp #$01
    beq mount_arg_drive_a
    cmp #$02
    beq mount_arg_drive_b
    jmp mount_arg_bad
mount_arg_drive_a:
    lda #DRIVE_A
    sta temp_drive
    jmp mount_arg_kind
mount_arg_drive_b:
    lda #DRIVE_B
    sta temp_drive
mount_arg_kind:
    lda arg_buffer+2
    cmp #CMD_D
    bne mount_arg_bad
    lda arg_buffer+3
    cmp #$36
    beq mount_arg_d64
    cmp #$37
    beq mount_arg_d71
    cmp #$38
    beq mount_arg_d81
    cmp #CMD_N
    beq mount_arg_dnp_check
    jmp mount_arg_bad
mount_arg_d64:
    lda arg_buffer+4
    cmp #$34
    bne mount_arg_bad
    lda #MOUNT_KIND_D64
    sta temp_mount_kind
    jmp mount_arg_ok
mount_arg_d71:
    lda arg_buffer+4
    cmp #$31
    bne mount_arg_bad
    lda #MOUNT_KIND_D71
    sta temp_mount_kind
    jmp mount_arg_ok
mount_arg_d81:
    lda arg_buffer+4
    cmp #$31
    bne mount_arg_bad
    lda #MOUNT_KIND_D81
    sta temp_mount_kind
    jmp mount_arg_ok
mount_arg_dnp_check:
    lda arg_buffer+4
    cmp #CMD_P
    bne mount_arg_bad
    lda #MOUNT_KIND_DNP
    sta temp_mount_kind
mount_arg_ok:
    lda #MOUNT_STATUS_OK
    rts
mount_arg_bad:
    lda #MOUNT_STATUS_BAD
    rts

append_selected_drive_path:
    lda temp_drive
    clc
    adc #$01
    sta response_buffer,y
    iny
    lda #ASCII_COLON
    sta response_buffer,y
    iny
    ldx temp_drive
    lda mount_kind_table,x
    jsr append_mount_kind
    lda #ASCII_SLASH
    sta response_buffer,y
    iny
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    bne append_selected_done
    lda temp_dir_id
    cmp #DIR_ID_BIN
    beq append_dir_bin
    cmp #DIR_ID_SRC
    beq append_dir_src
    cmp #DIR_ID_WORK
    beq append_dir_work
append_selected_done:
    rts

append_selected_drive_summary:
    lda temp_drive
    clc
    adc #$01
    sta response_buffer,y
    iny
    lda #ASCII_COLON
    sta response_buffer,y
    iny
    ldx temp_drive
    lda volume_ptr_lo,x
    sta PTR
    lda volume_ptr_hi,x
    sta PTR+1
    jsr append_ptr_to_response
    lda #ASCII_SPACE
    sta response_buffer,y
    iny
    ldx temp_drive
    lda mount_kind_table,x
    jmp append_mount_kind
append_dir_bin:
    lda #<dir_name_bin
    sta PTR
    lda #>dir_name_bin
    sta PTR+1
    jmp append_ptr_to_response
append_dir_src:
    lda #<dir_name_src
    sta PTR
    lda #>dir_name_src
    sta PTR+1
    jmp append_ptr_to_response
append_dir_work:
    lda #<dir_name_work
    sta PTR
    lda #>dir_name_work
    sta PTR+1
    jmp append_ptr_to_response

fs_enum_begin_current:
    sty saved_response_y
    lda #$00
    sta enum_index
    jsr uci_probe
    bcs fs_enum_begin_current_mock
    jsr fill_hw_dir_cache_current
    bcc fs_enum_begin_current_done
fs_enum_begin_current_mock:
    jsr select_enum_table
fs_enum_begin_current_done:
    ldy saved_response_y
    rts

fs_enum_next_ptr:
    sty saved_response_y
    lda enum_index
    cmp enum_count
    bcc :+
    sec
    ldy saved_response_y
    rts
:
    tay
    lda enum_lo_ptr_lo
    sta PTR
    lda enum_lo_ptr_hi
    sta PTR+1
    lda (PTR),y
    sta PTR
    lda enum_hi_ptr_lo
    sta SCREEN_PTR
    lda enum_hi_ptr_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta PTR+1
    inc enum_index
    clc
    ldy saved_response_y
    rts

select_enum_table:
    ldy temp_drive
    lda mounted_image_lo,y
    sta PTR
    lda mounted_image_hi,y
    sta PTR+1
    lda mount_flag_table,y
    cmp #MOUNT_FLAG_TREE
    beq select_enum_tree
    ldy #IMG_ROOT_LO_LO
    jmp load_enum_from_descriptor
select_enum_tree:
    lda temp_dir_id
    cmp #DIR_ID_BIN
    beq select_enum_bin
    cmp #DIR_ID_SRC
    beq select_enum_src
    cmp #DIR_ID_WORK
    beq select_enum_work
    ldy #IMG_ROOT_LO_LO
    jmp load_enum_from_descriptor
select_enum_bin:
    ldy #IMG_BIN_LO_LO
    jmp load_enum_from_descriptor
select_enum_src:
    ldy #IMG_SRC_LO_LO
    jmp load_enum_from_descriptor
select_enum_work:
    ldx temp_drive
    lda work_count_table,x
    beq :+
    jmp load_dynamic_work_enum
:
    ldy #IMG_WORK_LO_LO
load_enum_from_descriptor:
    lda (PTR),y
    sta enum_lo_ptr_lo
    iny
    lda (PTR),y
    sta enum_lo_ptr_hi
    iny
    lda (PTR),y
    sta enum_hi_ptr_lo
    iny
    lda (PTR),y
    sta enum_hi_ptr_hi
    iny
    lda (PTR),y
    sta enum_count
    rts

fill_hw_dir_cache_current:
    jsr sync_drive_backend_path_hw
    bcs fill_hw_dir_cache_current_fail
    jsr select_hw_dir_tables
    lda #$00
    sta enum_count
    ldx temp_drive
    sta hw_dir_count_table,x
    jsr build_uci_target_header
    lda #DOS_CMD_OPEN_DIR
    sta uci_cmd_buffer+1
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    lda #2
    jsr uci_issue_status_only
    bcs fill_hw_dir_cache_current_fail
    jsr uci_status_is_ok
    bcc fill_hw_dir_cache_current_loop
    jsr uci_status_is_dir_empty
    bcs fill_hw_dir_cache_current_fail
    ldx temp_drive
    lda #$00
    sta hw_dir_count_table,x
    sta enum_count
    clc
    rts
fill_hw_dir_cache_current_loop:
    lda enum_count
    cmp #HW_DIR_CACHE_MAX
    bcs fill_hw_dir_cache_current_done
    jsr build_uci_target_header
    lda #DOS_CMD_READ_DIR
    sta uci_cmd_buffer+1
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    lda #2
    jsr uci_issue_data_status
    bcs fill_hw_dir_cache_current_done
    lda uci_data_length
    cmp #2
    bcc fill_hw_dir_cache_current_done
    jsr store_hw_dir_entry
    bcs fill_hw_dir_cache_current_done
    inc enum_count
    ldx temp_drive
    lda enum_count
    sta hw_dir_count_table,x
    jsr uci_status_is_ok
    bcc fill_hw_dir_cache_current_loop
fill_hw_dir_cache_current_done:
    clc
    rts
fill_hw_dir_cache_current_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

select_hw_dir_tables:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_hw_dir_tables_a
    lda #<hw_dir_entry_lo_b
    sta enum_lo_ptr_lo
    lda #>hw_dir_entry_lo_b
    sta enum_lo_ptr_hi
    lda #<hw_dir_entry_hi_b
    sta enum_hi_ptr_lo
    lda #>hw_dir_entry_hi_b
    sta enum_hi_ptr_hi
    lda hw_dir_count_table,x
    sta enum_count
    rts
select_hw_dir_tables_a:
    lda #<hw_dir_entry_lo_a
    sta enum_lo_ptr_lo
    lda #>hw_dir_entry_lo_a
    sta enum_lo_ptr_hi
    lda #<hw_dir_entry_hi_a
    sta enum_hi_ptr_lo
    lda #>hw_dir_entry_hi_a
    sta enum_hi_ptr_hi
    lda hw_dir_count_table,x
    sta enum_count
    rts

store_hw_dir_entry:
    jsr select_hw_dir_name_slot
    ldy enum_count
    lda PTR
    sta (SCREEN_PTR),y
    lda PTR+1
    pha
    lda SCREEN_PTR
    clc
    adc #HW_DIR_CACHE_MAX
    sta SCREEN_PTR
    bcc :+
    inc SCREEN_PTR+1
:
    pla
    sta (SCREEN_PTR),y
    jsr restore_hw_dir_entry_lo_table
    ldx #$01
    lda #$00
    sta saved_response_y
store_hw_dir_entry_copy:
    cpx uci_data_length
    bcs store_hw_dir_entry_finalize
    ldy saved_response_y
    cpy #HW_DIR_NAME_MAX
    bcs store_hw_dir_entry_finalize
    lda uci_data_buffer,x
    beq store_hw_dir_entry_finalize
    sta (PTR),y
    inc saved_response_y
    inx
    bne store_hw_dir_entry_copy
store_hw_dir_entry_finalize:
    ldy saved_response_y
    lda uci_data_buffer+0
    and #DOS_ATTR_DIR
    beq store_hw_dir_entry_null
    cpy #HW_DIR_NAME_MAX
    bcs store_hw_dir_entry_null
    lda #ASCII_SLASH
    sta (PTR),y
    iny
store_hw_dir_entry_null:
    lda #$00
    sta (PTR),y
    clc
    rts

select_hw_dir_name_slot:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_hw_dir_name_slot_a
    lda #<hw_dir_entry_lo_b
    sta SCREEN_PTR
    lda #>hw_dir_entry_lo_b
    sta SCREEN_PTR+1
    lda #<hw_dir_names_b
    sta PTR
    lda #>hw_dir_names_b
    sta PTR+1
    jmp advance_hw_dir_name_slot
select_hw_dir_name_slot_a:
    lda #<hw_dir_entry_lo_a
    sta SCREEN_PTR
    lda #>hw_dir_entry_lo_a
    sta SCREEN_PTR+1
    lda #<hw_dir_names_a
    sta PTR
    lda #>hw_dir_names_a
    sta PTR+1
advance_hw_dir_name_slot:
    ldy enum_count
    beq select_hw_dir_name_slot_done
select_hw_dir_name_slot_loop:
    clc
    lda PTR
    adc #HW_DIR_NAME_STRIDE
    sta PTR
    bcc :+
    inc PTR+1
:
    dey
    bne select_hw_dir_name_slot_loop
select_hw_dir_name_slot_done:
    rts

restore_hw_dir_entry_lo_table:
    ldx temp_drive
    cpx #DRIVE_A
    beq restore_hw_dir_entry_lo_table_a
    lda #<hw_dir_entry_lo_b
    sta SCREEN_PTR
    lda #>hw_dir_entry_lo_b
    sta SCREEN_PTR+1
    rts
restore_hw_dir_entry_lo_table_a:
    lda #<hw_dir_entry_lo_a
    sta SCREEN_PTR
    lda #>hw_dir_entry_lo_a
    sta SCREEN_PTR+1
    rts

load_dynamic_work_enum:
    ldx temp_drive
    cpx #DRIVE_A
    beq load_dynamic_work_enum_a
    lda #<work_b_entry_lo
    sta enum_lo_ptr_lo
    lda #>work_b_entry_lo
    sta enum_lo_ptr_hi
    lda #<work_b_entry_hi
    sta enum_hi_ptr_lo
    lda #>work_b_entry_hi
    sta enum_hi_ptr_hi
    lda work_count_table,x
    sta enum_count
    rts
load_dynamic_work_enum_a:
    lda #<work_a_entry_lo
    sta enum_lo_ptr_lo
    lda #>work_a_entry_lo
    sta enum_lo_ptr_hi
    lda #<work_a_entry_hi
    sta enum_hi_ptr_lo
    lda #>work_a_entry_hi
    sta enum_hi_ptr_hi
    lda work_count_table,x
    sta enum_count
    rts

lookup_file_content:
    jsr select_file_table
    lda #$00
    sta file_index
lookup_file_loop:
    lda file_index
    cmp file_count
    bcs lookup_file_miss
    asl
    asl
    tay
    lda file_table_lo
    sta SCREEN_PTR
    lda file_table_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta PTR
    iny
    lda (SCREEN_PTR),y
    sta PTR+1
    jsr compare_ptr_to_path_name
    bcc lookup_file_hit
    inc file_index
    bne lookup_file_loop
lookup_file_miss:
    lda #$00
    sta matched_name_lo
    sta matched_name_hi
    sec
    rts
lookup_file_hit:
    lda PTR
    sta matched_name_lo
    lda PTR+1
    sta matched_name_hi
    lda file_index
    asl
    asl
    tay
    lda file_table_lo
    sta SCREEN_PTR
    lda file_table_hi
    sta SCREEN_PTR+1
    iny
    iny
    lda (SCREEN_PTR),y
    sta PTR
    iny
    lda (SCREEN_PTR),y
    sta PTR+1
    clc
    rts

compare_ptr_to_path_name:
    ldy #$00
    ldx #$00
compare_path_loop:
    lda (PTR),y
    cmp #ASCII_DOT
    beq compare_path_skip_candidate_dot
    lda path_name_buffer,x
    cmp #ASCII_DOT
    beq compare_path_skip_input_dot
    lda (PTR),y
    beq compare_path_end
    lda path_name_buffer,x
    beq compare_path_fail
    lda (PTR),y
    jsr normalize_output_char
    cmp path_name_buffer,x
    bne compare_path_fail
    iny
    inx
    bne compare_path_loop
compare_path_skip_candidate_dot:
    iny
    bne compare_path_loop
compare_path_skip_input_dot:
    inx
    bne compare_path_loop
compare_path_end:
    lda path_name_buffer,x
    beq compare_path_ok
    cmp #ASCII_DOT
    beq compare_path_skip_input_dot
compare_path_fail:
    sec
    rts
compare_path_ok:
    clc
    rts

select_file_table:
    ldy temp_drive
    lda mounted_image_lo,y
    sta PTR
    lda mounted_image_hi,y
    sta PTR+1
    lda temp_dir_id
    cmp #DIR_ID_BIN
    beq select_file_bin
    cmp #DIR_ID_SRC
    beq select_file_src
    cmp #DIR_ID_WORK
    beq select_file_work
    ldy #IMG_FILE_ROOT_TABLE_LO
    jmp load_file_table_from_descriptor
select_file_bin:
    ldy #IMG_FILE_BIN_TABLE_LO
    jmp load_file_table_from_descriptor
select_file_src:
    ldy #IMG_FILE_SRC_TABLE_LO
    jmp load_file_table_from_descriptor
select_file_work:
    ldx temp_drive
    lda work_count_table,x
    beq :+
    jmp load_dynamic_work_files
:
    ldy #IMG_FILE_WORK_TABLE_LO
load_file_table_from_descriptor:
    lda (PTR),y
    sta file_table_lo
    iny
    lda (PTR),y
    sta file_table_hi
    iny
    lda (PTR),y
    sta file_count
    rts

load_dynamic_work_files:
    ldx temp_drive
    cpx #DRIVE_A
    beq load_dynamic_work_files_a
    lda #<work_b_file_records
    sta file_table_lo
    lda #>work_b_file_records
    sta file_table_hi
    lda work_count_table,x
    sta file_count
    rts
load_dynamic_work_files_a:
    lda #<work_a_file_records
    sta file_table_lo
    lda #>work_a_file_records
    sta file_table_hi
    lda work_count_table,x
    sta file_count
    rts

select_dynamic_work_file_table:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_dynamic_work_file_table_a
    lda #<work_b_file_records
    sta SCREEN_PTR
    lda #>work_b_file_records
    sta SCREEN_PTR+1
    rts
select_dynamic_work_file_table_a:
    lda #<work_a_file_records
    sta SCREEN_PTR
    lda #>work_a_file_records
    sta SCREEN_PTR+1
    rts

select_dynamic_work_name_slot:
    lda file_index
    beq select_dynamic_work_name_slot_zero
select_dynamic_work_name_slot_one:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_dynamic_work_name_slot_one_a
    lda #<work_b_name_1
    sta PTR
    lda #>work_b_name_1
    sta PTR+1
    rts
select_dynamic_work_name_slot_one_a:
    lda #<work_a_name_1
    sta PTR
    lda #>work_a_name_1
    sta PTR+1
    rts
select_dynamic_work_name_slot_zero:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_dynamic_work_name_slot_zero_a
    lda #<work_b_name_0
    sta PTR
    lda #>work_b_name_0
    sta PTR+1
    rts
select_dynamic_work_name_slot_zero_a:
    lda #<work_a_name_0
    sta PTR
    lda #>work_a_name_0
    sta PTR+1
    rts

select_dir_listing_ptr:
    pha
    sty saved_response_y
    ldy temp_drive
    lda mount_flag_table,y
    cmp #MOUNT_FLAG_TREE
    beq select_listing_tree
    lda #<resp_dir_flat
    sta PTR
    lda #>resp_dir_flat
    sta PTR+1
    pla
    ldy saved_response_y
    rts
select_listing_tree:
    pla
    cmp #DIR_ID_BIN
    beq select_listing_bin
    cmp #DIR_ID_SRC
    beq select_listing_src
    cmp #DIR_ID_WORK
    beq select_listing_work
    lda #<resp_dir_root
    sta PTR
    lda #>resp_dir_root
    sta PTR+1
    ldy saved_response_y
    rts
select_listing_bin:
    lda #<resp_dir_bin
    sta PTR
    lda #>resp_dir_bin
    sta PTR+1
    ldy saved_response_y
    rts
select_listing_src:
    lda #<resp_dir_src
    sta PTR
    lda #>resp_dir_src
    sta PTR+1
    ldy saved_response_y
    rts
select_listing_work:
    lda #<resp_dir_work
    sta PTR
    lda #>resp_dir_work
    sta PTR+1
    ldy saved_response_y
    rts

append_ptr_to_response:
    ldx #$00
append_ptr_loop:
    lda (PTR,x)
    beq append_ptr_done
    sta response_buffer,y
    iny
    inc PTR
    bne append_ptr_loop
    inc PTR+1
    jmp append_ptr_loop
append_ptr_done:
    rts

build_ver_response:
    ldy #$00
copy_ver_prefix:
    lda ver_prefix,y
    sta response_buffer,y
    beq build_ver_done
    iny
    bne copy_ver_prefix
build_ver_done:
    lda TRANSPORT_SNAPSHOT
    cmp #TRANSPORT_MODE_UCI_HW
    beq build_ver_hw
    cmp #TRANSPORT_MODE_MOCK
    beq build_ver_mock
    lda #$20
    sta response_buffer,y
    iny
    lda #$0E
    sta response_buffer,y
    iny
    lda #$0F
    sta response_buffer,y
    iny
    lda #$0E
    sta response_buffer,y
    iny
    lda #$05
    sta response_buffer,y
    iny
    lda #$00
    sta response_buffer,y
    jmp build_ver_return
build_ver_mock:
    lda #$20
    sta response_buffer,y
    iny
    lda #CMD_M
    sta response_buffer,y
    iny
    lda #CMD_O
    sta response_buffer,y
    iny
    lda #3
    sta response_buffer,y
    iny
    lda #CMD_K
    sta response_buffer,y
    iny
    lda #$00
    sta response_buffer,y
    jmp build_ver_return
build_ver_hw:
    lda #$20
    sta response_buffer,y
    iny
    lda #CMD_U
    sta response_buffer,y
    iny
    lda #3
    sta response_buffer,y
    iny
    lda #CMD_I
    sta response_buffer,y
    iny
    lda #$00
    sta response_buffer,y
build_ver_return:
    lda #<response_buffer
    sta 0,x
    lda #>response_buffer
    sta 1,x
    rts

build_vol_response:
    stx saved_rp_x
    ldy #$00
    lda #$01
    sta response_buffer,y
    iny
    lda #$3A
    sta response_buffer,y
    iny
    ldx #DRIVE_A
    lda volume_ptr_lo,x
    sta PTR
    lda volume_ptr_hi,x
    sta PTR+1
    jsr append_ptr_to_response
    lda #ASCII_SPACE
    sta response_buffer,y
    iny
    ldx #DRIVE_A
    lda mount_kind_table,x
    jsr append_mount_kind
    lda #$20
    sta response_buffer,y
    iny
    lda #$02
    sta response_buffer,y
    iny
    lda #$3A
    sta response_buffer,y
    iny
    ldx #DRIVE_B
    lda volume_ptr_lo,x
    sta PTR
    lda volume_ptr_hi,x
    sta PTR+1
    jsr append_ptr_to_response
    lda #ASCII_SPACE
    sta response_buffer,y
    iny
    ldx #DRIVE_B
    lda mount_kind_table,x
    jsr append_mount_kind
    lda #$00
    sta response_buffer,y
    ldx saved_rp_x
    lda #<response_buffer
    sta 0,x
    lda #>response_buffer
    sta 1,x
    rts

append_mount_kind:
    cmp #MOUNT_KIND_D64
    beq append_d64
    cmp #MOUNT_KIND_D71
    beq append_d71
    cmp #MOUNT_KIND_D81
    beq append_d81
    cmp #MOUNT_KIND_DNP
    beq append_dnp
    lda #$3F
    sta response_buffer,y
    iny
    rts
append_d64:
    lda #$04
    sta response_buffer,y
    iny
    lda #$36
    sta response_buffer,y
    iny
    lda #$34
    sta response_buffer,y
    iny
    rts
append_d71:
    lda #$04
    sta response_buffer,y
    iny
    lda #$37
    sta response_buffer,y
    iny
    lda #$31
    sta response_buffer,y
    iny
    rts
append_d81:
    lda #$04
    sta response_buffer,y
    iny
    lda #$38
    sta response_buffer,y
    iny
    lda #$31
    sta response_buffer,y
    iny
    rts
append_dnp:
    lda #$04
    sta response_buffer,y
    iny
    lda #$0E
    sta response_buffer,y
    iny
    lda #$10
    sta response_buffer,y
    iny
    rts

svc_mark_ready:
    lda #READY_VALUE
    sta READY_MARKER
    rts

svc_idle:
idle_loop:
    jmp idle_loop

current_drive:
    .byte DRIVE_A
input_mode:
    .byte INPUT_MODE_KEYBOARD
saved_rp_x:
    .byte 0
script_index:
    .byte 0
script_line_count:
    .byte 0
line_length:
    .byte 0
arg_length:
    .byte 0
parse_cmd_start:
    .byte 0
parse_scan_index:
    .byte 0
cmd_length:
    .byte 0
arg_trim_length:
    .byte 0
temp_drive:
    .byte 0
temp_dir_id:
    .byte 0
temp_mount_kind:
    .byte MOUNT_KIND_NONE
saved_response_y:
    .byte 0
enum_lo_ptr_lo:
    .byte 0
enum_lo_ptr_hi:
    .byte 0
enum_hi_ptr_lo:
    .byte 0
enum_hi_ptr_hi:
    .byte 0
enum_count:
    .byte 0
enum_index:
    .byte 0
file_table_lo:
    .byte 0
file_table_hi:
    .byte 0
file_count:
    .byte 0
file_index:
    .byte 0
source_drive:
    .byte 0
source_slot:
    .byte 0
prefix_length:
    .byte 0
copy_dst_length:
    .byte 0
copy_trim_length:
    .byte 0
program_arg_limit:
    .byte 0
program_cmdline_len:
    .byte 0
uci_xfer_limit:
    .byte 0
uci_last_status:
    .byte 0
uci_data_length:
    .byte 0
uci_status_length:
    .byte 0
program_status:
    .byte RUN_STATUS_BAD
program_target_lo:
    .byte 0
program_target_hi:
    .byte 0
matched_name_lo:
    .byte 0
matched_name_hi:
    .byte 0
copy_content_lo:
    .byte 0
copy_content_hi:
    .byte 0
work_count_table:
    .byte 0, 0
hw_dir_count_table:
    .byte 0, 0
mount_kind_table:
    .byte MOUNT_KIND_NONE, MOUNT_KIND_NONE
mount_flag_table:
    .byte MOUNT_FLAG_NONE, MOUNT_FLAG_NONE
dir_state_table:
    .byte DIR_ID_ROOT, DIR_ID_ROOT
mounted_image_lo:
    .byte <image_none_a, <image_none_b
mounted_image_hi:
    .byte >image_none_a, >image_none_b
volume_ptr_lo:
    .byte <volume_system, <volume_work
volume_ptr_hi:
    .byte >volume_system, >volume_work
line_buffer:
    .res MAX_LINE_LEN
arg_buffer:
    .res MAX_LINE_LEN+1
copy_dst_buffer:
    .res MAX_LINE_LEN+1
program_cmdline_buffer:
    .res MAX_LINE_LEN+1
path_name_buffer:
    .res MAX_LINE_LEN+1
response_buffer:
    .res MAX_RESPONSE_LEN
script_line_data:
    .res (MAX_LINE_LEN+1) * 10
uci_cmd_buffer:
    .res MAX_LINE_LEN+3
uci_data_buffer:
    .res MAX_LINE_LEN+1
uci_status_buffer:
    .res MAX_LINE_LEN+1
desired_path_buffer:
    .res MAX_LINE_LEN+1
backend_path_cache_a:
    .res MAX_LINE_LEN+1
backend_path_cache_b:
    .res MAX_LINE_LEN+1
hw_dir_entry_lo_a:
    .res HW_DIR_CACHE_MAX
hw_dir_entry_hi_a:
    .res HW_DIR_CACHE_MAX
hw_dir_entry_lo_b:
    .res HW_DIR_CACHE_MAX
hw_dir_entry_hi_b:
    .res HW_DIR_CACHE_MAX
hw_dir_names_a:
    .res HW_DIR_NAME_STRIDE * HW_DIR_CACHE_MAX
hw_dir_names_b:
    .res HW_DIR_NAME_STRIDE * HW_DIR_CACHE_MAX

header_text:
    .byte "UDOS FOR COMMODORE 64", 0
resp_help:
    .byte "HELP VER VOL MEM DIR CD MOUNT TYPE COPY REN DEL", 0
ver_prefix:
    .byte 21, 4, 15, 19, 32, 1, 12, 16, 8, 1, 0
resp_mem:
    .byte "CORE 29F3", 0
volume_system:
    .byte "SYSTEM", 0
volume_work:
    .byte "WORK", 0
volume_unknown:
    .byte "?", 0
entry_flat_system:
    .byte "SYSTEM", 0
entry_flat_commands:
    .byte "COMMANDS", 0
entry_flat_readme:
    .byte "README", 0
entry_root_bin:
    .byte "BIN/", 0
entry_root_src:
    .byte "SRC/", 0
entry_root_work:
    .byte "WORK/", 0
entry_bin_shell:
    .byte "SHELL.AVM", 0
entry_bin_dir:
    .byte "DIR.AVM", 0
entry_src_boot:
    .byte "BOOT.ASM", 0
entry_src_fs:
    .byte "FS.AVM", 0
entry_work_empty:
    .byte "EMPTY", 0
content_flat_system:
    .byte "UDOS SYSTEM VOLUME", 0
content_flat_commands:
    .byte "HELP VER VOL MEM DIR CD MOUNT TYPE COPY REN DEL", 0
content_flat_readme:
    .byte "MOCK FLAT IMAGE CONTENT", 0
content_bin_shell:
    .byte "SHELL OVERLAY PLACEHOLDER", 0
content_bin_dir:
    .byte "DIR OVERLAY PLACEHOLDER", 0
content_src_boot:
    .byte "; BOOT.ASM MOCK SOURCE", 0
content_src_fs:
    .byte "; FS.AVM MOCK SOURCE", 0
flat_entry_lo:
    .byte <entry_flat_system, <entry_flat_commands, <entry_flat_readme
flat_entry_hi:
    .byte >entry_flat_system, >entry_flat_commands, >entry_flat_readme
root_entry_lo:
    .byte <entry_root_bin, <entry_root_src, <entry_root_work
root_entry_hi:
    .byte >entry_root_bin, >entry_root_src, >entry_root_work
bin_entry_lo:
    .byte <entry_bin_shell, <entry_bin_dir
bin_entry_hi:
    .byte >entry_bin_shell, >entry_bin_dir
src_entry_lo:
    .byte <entry_src_boot, <entry_src_fs
src_entry_hi:
    .byte >entry_src_boot, >entry_src_fs
work_entry_lo:
    .byte <entry_work_empty
work_entry_hi:
    .byte >entry_work_empty
empty_file_records:
    .byte 0, 0, 0, 0
flat_file_records:
    .byte <entry_flat_system, >entry_flat_system, <content_flat_system, >content_flat_system
    .byte <entry_flat_commands, >entry_flat_commands, <content_flat_commands, >content_flat_commands
    .byte <entry_flat_readme, >entry_flat_readme, <content_flat_readme, >content_flat_readme
bin_file_records:
    .byte <entry_bin_shell, >entry_bin_shell, <content_bin_shell, >content_bin_shell
    .byte <entry_bin_dir, >entry_bin_dir, <content_bin_dir, >content_bin_dir
src_file_records:
    .byte <entry_src_boot, >entry_src_boot, <content_src_boot, >content_src_boot
    .byte <entry_src_fs, >entry_src_fs, <content_src_fs, >content_src_fs
work_a_name_0:
    .res WORK_NAME_MAX
work_a_name_1:
    .res WORK_NAME_MAX
work_b_name_0:
    .res WORK_NAME_MAX
work_b_name_1:
    .res WORK_NAME_MAX
work_a_entry_lo:
    .byte <work_a_name_0, <work_a_name_1
work_a_entry_hi:
    .byte >work_a_name_0, >work_a_name_1
work_b_entry_lo:
    .byte <work_b_name_0, <work_b_name_1
work_b_entry_hi:
    .byte >work_b_name_0, >work_b_name_1
work_a_file_records:
    .byte <work_a_name_0, >work_a_name_0, 0, 0
    .byte <work_a_name_1, >work_a_name_1, 0, 0
work_b_file_records:
    .byte <work_b_name_0, >work_b_name_0, 0, 0
    .byte <work_b_name_1, >work_b_name_1, 0, 0
image_none_a:
    .byte <volume_unknown, >volume_unknown
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_none_b:
    .byte <volume_unknown, >volume_unknown
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_a_d64:
    .byte <volume_system, >volume_system
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 3
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_a_d71:
    .byte <volume_system, >volume_system
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 3
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_a_d81:
    .byte <volume_system, >volume_system
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 3
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_a_dnp:
    .byte <volume_system, >volume_system
    .byte <root_entry_lo, >root_entry_lo, <root_entry_hi, >root_entry_hi, 3
    .byte <bin_entry_lo, >bin_entry_lo, <bin_entry_hi, >bin_entry_hi, 2
    .byte <src_entry_lo, >src_entry_lo, <src_entry_hi, >src_entry_hi, 2
    .byte <work_entry_lo, >work_entry_lo, <work_entry_hi, >work_entry_hi, 1
    .byte <empty_file_records, >empty_file_records, 0
    .byte <bin_file_records, >bin_file_records, 2
    .byte <src_file_records, >src_file_records, 2
    .byte <empty_file_records, >empty_file_records, 0
image_b_d64:
    .byte <volume_work, >volume_work
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 3
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_b_d71:
    .byte <volume_work, >volume_work
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 3
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_b_d81:
    .byte <volume_work, >volume_work
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 3
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_b_dnp:
    .byte <volume_work, >volume_work
    .byte <root_entry_lo, >root_entry_lo, <root_entry_hi, >root_entry_hi, 3
    .byte <bin_entry_lo, >bin_entry_lo, <bin_entry_hi, >bin_entry_hi, 2
    .byte <src_entry_lo, >src_entry_lo, <src_entry_hi, >src_entry_hi, 2
    .byte <work_entry_lo, >work_entry_lo, <work_entry_hi, >work_entry_hi, 1
    .byte <empty_file_records, >empty_file_records, 0
    .byte <bin_file_records, >bin_file_records, 2
    .byte <src_file_records, >src_file_records, 2
    .byte <empty_file_records, >empty_file_records, 0
dir_name_bin:
    .byte "BIN", 0
dir_name_src:
    .byte "SRC", 0
dir_name_work:
    .byte "WORK", 0
resp_dir_flat:
    .byte "SYSTEM COMMANDS README", 0
resp_dir_root:
    .byte "BIN/ SRC/ WORK/", 0
resp_dir_bin:
    .byte "SHELL.AVM DIR.AVM", 0
resp_dir_src:
    .byte "BOOT.ASM FS.AVM", 0
resp_dir_work:
    .byte "EMPTY", 0
resp_flat_image:
    .byte "FLAT IMAGE", 0
resp_bad_dir:
    .byte "NO SUCH DIR", 0
resp_bad_file:
    .byte "NO SUCH FILE", 0
resp_bad_copy:
    .byte "BAD COPY", 0
resp_bad_ren:
    .byte "BAD REN", 0
resp_deleted:
    .byte "DELETED", 0
resp_renamed:
    .byte "RENAMED", 0
resp_exists:
    .byte "EXISTS", 0
resp_copied:
    .byte "COPIED", 0
resp_read_only:
    .byte "READ ONLY", 0
resp_no_space:
    .byte "NO SPACE", 0
resp_no_program:
    .byte "PROGRAM NOT FOUND", 0
resp_bad_mount:
    .byte "BAD MOUNT", 0
resp_bad_run:
    .byte "BAD RUN", 0
resp_unmounted:
    .byte "UNMOUNTED", 0
resp_unknown:
    .byte $3F, 0
resp_run_prefix:
    .byte "RUN ", 0
resp_args_prefix:
    .byte "ARGS ", 0
