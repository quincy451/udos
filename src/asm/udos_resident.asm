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
.export svc_program_get_image_ptr
.export svc_program_get_image_len
.export svc_program_exit
.export svc_mark_ready
.export svc_idle
.import acheron
.import clear_rstack
.import __ACHERON_LAST__

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
PROGRAM_IMAGE_LEN_LO_SNAPSHOT = $CFFA
PROGRAM_IMAGE_LEN_HI_SNAPSHOT = $CFFB
STAGE_SNAPSHOT = $CFFD
READY_MARKER = $CFFF
READY_VALUE = $52
ABI_VERSION = 1
RESIDENT_CODE_START = $1810
HIRAM_START = $C000
HIRAM_PAGES = $10
C64_PORT = $0001
REU_STATUS = $DF00
REU_COMMAND = $DF01
REU_C64ADDR_LO = $DF02
REU_C64ADDR_HI = $DF03
REU_REUADDR_LO = $DF04
REU_REUADDR_HI = $DF05
REU_REUADDR_BANK = $DF06
REU_COUNT_LO = $DF07
REU_COUNT_HI = $DF08
REU_IRQMASK = $DF09
REU_CONTROL = $DF0A
REU_TRIGGER = $FF00
C64_PORT_IO_ON = $05
REU_CMD_COPY_C64_TO_REU = $EC
REU_CMD_COPY_REU_TO_C64 = $ED
TRANSPORT_MODE_UNAVAILABLE = 0
TRANSPORT_MODE_MOCK = 1
TRANSPORT_MODE_UCI_HW = 2
TRANSPORT_MODE_VICE_FS = 3
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
READST = $FFB7
SETLFS = $FFBA
SETNAM = $FFBD
OPEN_K = $FFC0
CINT = $FF81
CLOSE_K = $FFC3
CHKIN_K = $FFC6
CLRCHN = $FFCC
CHRIN = $FFCF
LOAD_K = $FFD5
KEY_RETURN = $0D
KEY_LINEFEED = $0A
KEY_BACKSPACE = $14
MAX_LINE_LEN = 31
MAX_RESPONSE_LEN = 128
SCRIPT_LINE_MAX = 12
ASCII_COLON = $3A
ASCII_SLASH = $2F
ASCII_SPACE = $20
ASCII_COMMA = $2C
ASCII_DOT = $2E
ASCII_ASTERISK = $2A
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
SHELL_CMD_HELP = 1
SHELL_CMD_VER = 2
SHELL_CMD_VOL = 3
SHELL_CMD_MEM = 17
SHELL_CMD_QUIT = 5
SHELL_CMD_DIR = 6
SHELL_CMD_CD = 7
SHELL_CMD_MOUNT = 8
SHELL_CMD_TYPE = 9
SHELL_CMD_COPY = 10
SHELL_CMD_REN = 11
SHELL_CMD_DEL = 12
SHELL_CMD_MD = 13
SHELL_CMD_RD = 14
SHELL_CMD_RUN = 15
SHELL_CMD_DRIVE_ERR = 16
SHELL_CMD_ECHO = 18
SHELL_CMD_NONE = 19
INPUT_MODE_KEYBOARD = 0
INPUT_MODE_SCRIPT = 1
DIR_ID_ROOT = 0
DIR_ID_BIN = 1
DIR_ID_SRC = 2
DIR_ID_WORK = 3
DIR_ID_DYNAMIC_BASE = 4
PATH_STATUS_OK = 0
PATH_STATUS_FLAT = 1
PATH_STATUS_BAD = 2
PATH_STATUS_UNMOUNTED = 3
PATH_STATUS_READ_ONLY = 4
MOUNT_STATUS_OK = 0
MOUNT_STATUS_BAD = 1
MOUNT_STATUS_NOTDISK = 2
MOUNT_STATUS_DRIVE = 3
MOUNT_STATUS_FAILED = 4
WILDCARD_NONE = 0
WILDCARD_ALL = 1
WILDCARD_EXT = 2
WILDCARD_STEM = 3
WILDCARD_RESULT_NOMATCH = 1
WILDCARD_RESULT_NOSPACE = 2
WILDCARD_RESULT_FAILED = 3
FLAT_LOOKUP_NOFILE = 0
FLAT_LOOKUP_FAIL = 1
FLAT_READ_MODE_TRUNCATE = 0
FLAT_READ_MODE_STRICT = 1
FLAT_READ_FAIL = 1
FLAT_READ_TOO_LARGE = 2
RENAME_STATUS_FAILED = 0
RENAME_STATUS_EXISTS = 1
DIR_MUTATE_OK = 0
DIR_MUTATE_EXISTS = 1
DIR_MUTATE_FAIL = 2
DIR_MUTATE_NOTEMPTY = 3
DIR_MUTATE_BUSY = 4
RUN_STATUS_OK = 0
RUN_STATUS_BAD = 1
RUN_STATUS_FLAT = 2
RUN_STATUS_UNMOUNTED = 3
RUN_STATUS_NOFILE = 4
RUN_STATUS_TOO_LARGE = 5
RUN_STATUS_LOAD_FAILED = 6
RUN_STATUS_BATCH = 7
PROGRAM_STATE_NONE = 0
PROGRAM_STATE_RUNNING = 1
PROGRAM_STATE_EXITED = 2
PROGRAM_IMAGE_MAX = 255
WORK_DYNAMIC_MAX = 2
WORK_NAME_MAX = 16
REU_VICE_TREE_BYTES = PROGRAM_IMAGE_MAX * VICE_TREE_DYNAMIC_MAX
REU_VICE_TREE_TOTAL = REU_VICE_TREE_BYTES * 2
VICE_TREE_DYNAMIC_MAX = 6
VICE_TREE_SLOT_EMPTY = 0
VICE_TREE_SLOT_LIVE = 1
VICE_TREE_SLOT_TOMBSTONE = 2
VICE_TREE_SLOT_LIVE_HIDE = 3
VICE_DIR_DYNAMIC_MAX = 6
VICE_DIR_SLOT_EMPTY = 0
VICE_DIR_SLOT_LIVE = 1
VICE_DIR_SLOT_TOMBSTONE = 2
DIR_WALK_MAX = VICE_DIR_DYNAMIC_MAX + 4
DOS_TARGET_A = 1
DOS_TARGET_B = 2
DOS_CMD_OPEN_FILE = $02
DOS_CMD_CLOSE_FILE = $03
DOS_CMD_READ_DATA = $04
DOS_CMD_WRITE_DATA = $05
DOS_CMD_FILE_SEEK = $06
DOS_CMD_FILE_STAT = $08
DOS_CMD_DELETE_FILE = $09
DOS_CMD_RENAME_FILE = $0A
DOS_CMD_COPY_FILE = $0B
DOS_CMD_CHANGE_DIR = $11
DOS_CMD_GET_PATH = $12
DOS_CMD_OPEN_DIR = $13
DOS_CMD_READ_DIR = $14
DOS_CMD_MOUNT_DISK = $23
FA_READ = $01
FA_WRITE = $02
FA_READWRITE = FA_READ | FA_WRITE
FA_CREATE_NEW = $04
FA_CREATE_ALWAYS = $08
FA_WRITE_OVERWRITE = FA_WRITE | FA_CREATE_NEW | FA_CREATE_ALWAYS
DOS_ATTR_DIR = $10
IEC_ID_A = 8
IEC_ID_B = 9
VICE_LFN_FILE = 2
VICE_LFN_DIR = 3
VICE_LFN_PROBE = 4
VICE_SA_READ = 2
HW_DIR_CACHE_MAX = 6
HW_DIR_NAME_MAX = 20
HW_DIR_NAME_STRIDE = HW_DIR_NAME_MAX + 1
FULL_PATH_BUF_LEN = MAX_LINE_LEN + 8
FLAT_LABEL_LEN = 16
FLAT_DIR_READ_LEN = 247
FLAT_SECTOR_READ_LEN = 255
UCI_WRITE_DATA_MAX = 251
D64_LABEL_OFF_0 = $90
D64_LABEL_OFF_1 = $65
D64_LABEL_OFF_2 = $01
D64_LABEL_OFF_3 = $00
D64_DIR_TRACK = 18
D64_BAM_SECTOR = 0
D64_BAM_ENTRY_BASE = $04
D64_DIR_BASE_1 = $65
D64_DIR_BASE_2 = $01
D71_BAM_SIDE2_TRACK = 53
D71_BAM_SIDE2_SECTOR = 0
D71_BAM_SIDE2_COUNT_BASE = $DD
D71_BAM_SIDE2_BITMAP_BASE = $00
D81_LABEL_OFF_0 = $04
D81_LABEL_OFF_1 = $18
D81_LABEL_OFF_2 = $06
D81_LABEL_OFF_3 = $00
D81_DIR_TRACK = 40
D81_BAM_SECTOR = 1
D81_BAM_ENTRY_BASE = $10
D81_DIR_START_SECTOR = 3
D81_DIR_BASE_1 = $18
D81_DIR_BASE_2 = $06
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
    calln svc_try_autoexec_batch

shell_loop:
    calln svc_shell_preprompt
shell_prompt:
    calln svc_console_write_prompt
    calln svc_line_read
    case8 SHELL_CMD_NONE, shell_none
    case8 SHELL_CMD_RUN, cmd_run_program
    case8 SHELL_CMD_DRIVE_ERR, cmd_emit_response
    case8 SHELL_CMD_MD, cmd_emit_response
    case8 SHELL_CMD_RD, cmd_emit_response
    case8 SHELL_CMD_MOUNT, cmd_emit_response
    case8 SHELL_CMD_COPY, cmd_emit_response
    case8 SHELL_CMD_REN, cmd_emit_response
    case8 SHELL_CMD_DEL, cmd_emit_response
    case8 SHELL_CMD_TYPE, cmd_emit_response
    case8 SHELL_CMD_DIR, cmd_emit_response
    case8 SHELL_CMD_CD, cmd_emit_response
    case8 SHELL_CMD_ECHO, cmd_emit_response
    case8 SHELL_CMD_HELP, cmd_emit_response
    case8 SHELL_CMD_VER, cmd_emit_response
    case8 SHELL_CMD_VOL, cmd_emit_response
    case8 SHELL_CMD_MEM, cmd_emit_mem_native
    setp16 resp_unknown
    calln svc_console_write_sc0
    calln svc_console_newline
    jump shell_loop

shell_none:
    jump shell_loop

cmd_emit_response:
    setp8 $11
    stma STAGE_SNAPSHOT
    calln svc_shell_response_ptr
    calln svc_command_status_from_response
    calln svc_console_write_sc0
    calln svc_console_newline
    jump shell_loop

cmd_emit_mem_native:
    setp8 $11
    stma STAGE_SNAPSHOT
    calln svc_emit_mem_response
    jump shell_loop

cmd_run_program:
    setp8 $12
    stma STAGE_SNAPSHOT
    calln svc_program_prepare_run
    calln svc_program_finish_prepare
    jump shell_loop

cmd_run_batch:
    calln svc_command_status_clear
    jump shell_loop

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
    calln svc_command_status_from_program_exit
    jump shell_loop

cmd_run_error:
    calln svc_command_status_fail
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

detect_transport_mode_a:
    jsr uci_probe
    bcc detect_transport_mode_hw
    jsr vice_probe_available
    bcc detect_transport_mode_vice
    lda #TRANSPORT_MODE_MOCK
    rts
detect_transport_mode_hw:
    lda #TRANSPORT_MODE_UCI_HW
    rts
detect_transport_mode_vice:
    lda #TRANSPORT_MODE_VICE_FS
    rts

vice_probe_available:
    lda temp_drive
    pha
    lda #DRIVE_A
    sta temp_drive
    lda #<vice_probe_name
    sta PTR
    lda #>vice_probe_name
    sta PTR+1
    lda #VICE_LFN_PROBE
    sta vice_lfn
    jsr vice_open_read_from_ptr
    bcs vice_probe_available_fail
    jsr vice_close_current_file
    pla
    sta temp_drive
    clc
    rts
vice_probe_available_fail:
    pla
    sta temp_drive
    sec
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
    jsr clear_vice_dir_drive
    jsr clear_vice_tree_drive
    rts

install_mount_path:
    jsr select_mount_path_buffer
    ldy #$00
install_mount_path_loop:
    lda path_name_buffer,y
    sta (PTR),y
    beq install_mount_path_done
    iny
    cpy #MAX_LINE_LEN
    bcc install_mount_path_loop
    lda #$00
    sta (PTR),y
install_mount_path_done:
    rts

select_mount_path_buffer:
    lda temp_drive
    beq select_mount_path_buffer_a
    lda #<mount_path_b
    sta PTR
    lda #>mount_path_b
    sta PTR+1
    rts
select_mount_path_buffer_a:
    lda #<mount_path_a
    sta PTR
    lda #>mount_path_a
    sta PTR+1
    rts

current_mount_is_flat:
    ldy temp_drive
    lda mount_kind_table,y
    sta temp_mount_kind
    lda mount_flag_table,y
    cmp #MOUNT_FLAG_FLAT
    rts

current_mount_path_is_empty:
    jsr select_mount_path_buffer
    ldy #$00
    lda (PTR),y
    beq current_mount_path_is_empty_yes
    clc
    rts
current_mount_path_is_empty_yes:
    sec
    rts

install_volume_label_from_mount:
    jsr uci_probe
    bcs install_volume_label_from_mount_fallback
    lda temp_mount_kind
    cmp #MOUNT_KIND_D64
    beq install_volume_label_from_mount_flat
    cmp #MOUNT_KIND_D71
    beq install_volume_label_from_mount_flat
    cmp #MOUNT_KIND_D81
    beq install_volume_label_from_mount_flat
install_volume_label_from_mount_fallback:
    jmp install_dynamic_volume_label
install_volume_label_from_mount_flat:
    jsr install_flat_volume_label_hw
    bcc install_volume_label_from_mount_done
    jmp install_dynamic_volume_label
install_volume_label_from_mount_done:
    rts

install_dynamic_volume_label:
    jsr select_dynamic_volume_label_buffer
    ldy #$00
    lda #$00
    sta saved_response_y
install_dynamic_volume_label_scan:
    lda path_name_buffer,y
    beq install_dynamic_volume_label_copy
    cmp #ASCII_SLASH
    bne install_dynamic_volume_label_next
    tya
    clc
    adc #1
    sta saved_response_y
install_dynamic_volume_label_next:
    iny
    cpy #MAX_LINE_LEN
    bcc install_dynamic_volume_label_scan
install_dynamic_volume_label_copy:
    ldx saved_response_y
    ldy #$00
install_dynamic_volume_label_loop:
    lda path_name_buffer,x
    beq install_dynamic_volume_label_done
    cmp #ASCII_DOT
    beq install_dynamic_volume_label_done
    cpy #MAX_LINE_LEN
    bcs install_dynamic_volume_label_done
    jsr screen_code_to_ascii
    sta (PTR),y
    inx
    iny
    bne install_dynamic_volume_label_loop
install_dynamic_volume_label_done:
    lda #$00
    sta (PTR),y
    cpy #$00
    bne install_dynamic_volume_label_ptr
    ldy #$00
    lda #'?'
    sta (PTR),y
    iny
    lda #$00
    sta (PTR),y
install_dynamic_volume_label_ptr:
    ldy temp_drive
    lda PTR
    sta volume_ptr_lo,y
    lda PTR+1
    sta volume_ptr_hi,y
    rts

select_dynamic_volume_label_buffer:
    lda temp_drive
    beq select_dynamic_volume_label_buffer_a
    lda #<volume_label_b
    sta PTR
    lda #>volume_label_b
    sta PTR+1
    rts
select_dynamic_volume_label_buffer_a:
    lda #<volume_label_a
    sta PTR
    lda #>volume_label_a
    sta PTR+1
    rts

install_flat_volume_label_hw:
    jsr select_mount_path_buffer
    jsr open_named_file_hw_from_ptr
    bcs install_flat_volume_label_hw_fail
    jsr seek_flat_volume_label_hw
    bcs install_flat_volume_label_hw_fail_close
    lda #FLAT_LABEL_LEN
    jsr uci_read_open_file_into_response_len
    bcs install_flat_volume_label_hw_fail_close
    lda uci_data_length
    cmp #FLAT_LABEL_LEN
    bcc install_flat_volume_label_hw_fail_close
    jsr copy_flat_volume_label_from_response
    bcs install_flat_volume_label_hw_fail_close
    jsr close_current_file_hw
    bcs install_flat_volume_label_hw_fail
    clc
    rts
install_flat_volume_label_hw_fail_close:
    php
    jsr close_current_file_hw
    plp
install_flat_volume_label_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

seek_flat_volume_label_hw:
    jsr build_uci_file_seek_label_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs seek_flat_volume_label_hw_fail
    jsr uci_status_is_ok
    bcs seek_flat_volume_label_hw_fail
    clc
    rts
seek_flat_volume_label_hw_fail:
    sec
    rts

build_uci_file_seek_label_command:
    jsr build_uci_target_header
    lda #DOS_CMD_FILE_SEEK
    sta uci_cmd_buffer+1
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq build_uci_file_seek_label_d81
    lda #D64_LABEL_OFF_0
    sta uci_cmd_buffer+2
    lda #D64_LABEL_OFF_1
    sta uci_cmd_buffer+3
    lda #D64_LABEL_OFF_2
    sta uci_cmd_buffer+4
    lda #D64_LABEL_OFF_3
    sta uci_cmd_buffer+5
    lda #6
    rts
build_uci_file_seek_label_d81:
    lda #D81_LABEL_OFF_0
    sta uci_cmd_buffer+2
    lda #D81_LABEL_OFF_1
    sta uci_cmd_buffer+3
    lda #D81_LABEL_OFF_2
    sta uci_cmd_buffer+4
    lda #D81_LABEL_OFF_3
    sta uci_cmd_buffer+5
    lda #6
    rts

copy_flat_volume_label_from_response:
    jsr select_dynamic_volume_label_buffer
    ldx #$00
    ldy #$00
copy_flat_volume_label_loop:
    cpx #FLAT_LABEL_LEN
    bcs copy_flat_volume_label_done
    lda response_buffer,x
    beq copy_flat_volume_label_done
    cmp #$A0
    beq copy_flat_volume_label_done
    and #$7F
    beq copy_flat_volume_label_done
    sta (PTR),y
    inx
    iny
    cpy #MAX_LINE_LEN
    bcc copy_flat_volume_label_loop
copy_flat_volume_label_done:
    lda #$00
    sta (PTR),y
    cpy #$00
    bne copy_flat_volume_label_ptr
    sec
    rts
copy_flat_volume_label_ptr:
    ldy temp_drive
    lda PTR
    sta volume_ptr_lo,y
    lda PTR+1
    sta volume_ptr_hi,y
    clc
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

advance_ptr_by_a:
    clc
    adc PTR
    sta PTR
    bcc :+
    inc PTR+1
:
    rts

advance_ptr_by_y:
    tya
    jmp advance_ptr_by_a

copy_screen_ptr_string_to_current_ptr:
    ldy #$00
copy_screen_ptr_string_to_current_ptr_loop:
    lda (SCREEN_PTR),y
    beq copy_screen_ptr_string_to_current_ptr_done
    sta (PTR),y
    iny
    cpy #HW_DIR_NAME_MAX
    bcc copy_screen_ptr_string_to_current_ptr_loop
copy_screen_ptr_string_to_current_ptr_done:
    lda #$00
    sta (PTR),y
    rts

get_dir_parent_for_a:
    cmp #DIR_ID_BIN
    beq get_dir_parent_root
    cmp #DIR_ID_SRC
    beq get_dir_parent_root
    cmp #DIR_ID_WORK
    beq get_dir_parent_root
    cmp #DIR_ID_DYNAMIC_BASE
    bcc get_dir_parent_root
    sec
    sbc #DIR_ID_DYNAMIC_BASE
    sta file_index
    jsr load_vice_dir_parent_for_index
    rts
get_dir_parent_root:
    lda #DIR_ID_ROOT
    rts

select_dir_name_ptr_for_a:
    cmp #DIR_ID_BIN
    beq select_dir_name_ptr_bin
    cmp #DIR_ID_SRC
    beq select_dir_name_ptr_src
    cmp #DIR_ID_WORK
    beq select_dir_name_ptr_work
    pha
    sec
    sbc #DIR_ID_DYNAMIC_BASE
    sta file_index
    jsr select_vice_dir_name_slot_to_screen_ptr
    pla
    rts
select_dir_name_ptr_bin:
    lda #<dir_name_bin
    sta SCREEN_PTR
    lda #>dir_name_bin
    sta SCREEN_PTR+1
    rts
select_dir_name_ptr_src:
    lda #<dir_name_src
    sta SCREEN_PTR
    lda #>dir_name_src
    sta SCREEN_PTR+1
    rts
select_dir_name_ptr_work:
    lda #<dir_name_work
    sta SCREEN_PTR
    lda #>dir_name_work
    sta SCREEN_PTR+1
    rts

build_dir_walk_from_temp_dir:
    lda #$00
    sta dir_walk_count
    lda temp_dir_id
    sta dir_walk_id
build_dir_walk_from_temp_dir_loop:
    lda dir_walk_id
    beq build_dir_walk_from_temp_dir_done
    ldx dir_walk_count
    cpx #DIR_WALK_MAX
    bcs build_dir_walk_from_temp_dir_done
    sta dir_walk_ids,x
    inx
    stx dir_walk_count
    lda dir_walk_id
    jsr get_dir_parent_for_a
    sta dir_walk_id
    jmp build_dir_walk_from_temp_dir_loop
build_dir_walk_from_temp_dir_done:
    rts

append_tree_tail_to_current_ptr:
    lda temp_dir_id
    bne :+
    ldy #$00
    rts
:
    lda PTR
    pha
    lda PTR+1
    pha
    jsr build_dir_walk_from_temp_dir
    pla
    sta PTR+1
    pla
    sta PTR
    ldx dir_walk_count
    beq append_tree_tail_to_current_ptr_empty
    dex
    lda #$00
    sta dir_walk_bytes
append_tree_tail_to_current_ptr_loop:
    txa
    pha
    lda dir_walk_ids,x
    jsr select_dir_name_ptr_for_a
    pla
    tax
    jsr copy_screen_ptr_string_to_current_ptr
    sty saved_response_y
    jsr advance_ptr_by_y
    lda dir_walk_bytes
    clc
    adc saved_response_y
    sta dir_walk_bytes
    cpx #$00
    beq append_tree_tail_to_current_ptr_done
    ldy #$00
    lda #ASCII_SLASH
    sta (PTR),y
    iny
    jsr advance_ptr_by_y
    inc dir_walk_bytes
    dex
    jmp append_tree_tail_to_current_ptr_loop
append_tree_tail_to_current_ptr_done:
    ldy dir_walk_bytes
    rts
append_tree_tail_to_current_ptr_empty:
    ldy #$00
    rts

fill_backend_path_vice:
    jsr select_mount_path_buffer
    ldy #$00
fill_backend_path_vice_mount_copy:
    lda (PTR),y
    beq fill_backend_path_vice_mount_done
    jsr screen_code_to_ascii
    sta (SCREEN_PTR),y
    iny
    cpy #MAX_LINE_LEN
    bcc fill_backend_path_vice_mount_copy
fill_backend_path_vice_mount_done:
    lda #$00
    sta (SCREEN_PTR),y
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    bne fill_backend_path_vice_done
    lda temp_dir_id
    beq fill_backend_path_vice_done
    jsr ensure_backend_path_vice_slash
    tya
    jsr advance_ptr_by_a
    jsr append_tree_tail_to_current_ptr
    tya
    jsr advance_ptr_by_a
    ldy #$00
fill_backend_path_vice_done:
    lda #$00
    sta (PTR),y
    jsr select_backend_path_cache
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    clc
    rts

ensure_backend_path_vice_slash:
    cpy #$00
    beq ensure_backend_path_vice_root
    dey
    lda (PTR),y
    iny
    cmp #ASCII_SLASH
    beq ensure_backend_path_vice_slash_done
ensure_backend_path_vice_root:
    lda #ASCII_SLASH
    sta (PTR),y
    iny
ensure_backend_path_vice_slash_done:
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
    jsr uci_status_is_ok_or_empty
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

vice_should_use_mock_work_overlay:
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    beq :+
    sec
    rts
:
    lda temp_dir_id
    cmp #DIR_ID_WORK
    bne vice_should_use_mock_work_overlay_no
    lda work_count_table,x
    beq vice_should_use_mock_work_overlay_no
    sec
    rts
vice_should_use_mock_work_overlay_no:
    clc
    rts

select_vice_device_id:
    lda temp_drive
    beq select_vice_device_id_a
    lda #IEC_ID_B
    rts
select_vice_device_id_a:
    lda #IEC_ID_A
    rts

vice_name_length_from_ptr:
    ldy #$00
vice_name_length_loop:
    lda (PTR),y
    beq vice_name_length_done
    iny
    cpy #FULL_PATH_BUF_LEN
    bcc vice_name_length_loop
vice_name_length_done:
    tya
    beq vice_name_length_fail
    clc
    rts
vice_name_length_fail:
    sec
    rts

vice_open_read_from_ptr:
    jsr vice_name_length_from_ptr
    bcs vice_open_read_from_ptr_fail
    pha
    lda vice_lfn
    ldx temp_drive
    cpx #DRIVE_A
    beq :+
    ldx #IEC_ID_B
    bne vice_open_read_setlfs
:
    ldx #IEC_ID_A
vice_open_read_setlfs:
    ldy vice_secondary
    jsr SETLFS
    pla
    ldx PTR
    ldy PTR+1
    jsr SETNAM
    jsr OPEN_K
    jsr READST
    bne vice_open_read_from_ptr_fail_close
    ldx vice_lfn
    jsr CHKIN_K
    jsr READST
    bne vice_open_read_from_ptr_fail_close
    clc
    rts
vice_open_read_from_ptr_fail_close:
    php
    jsr vice_close_current_file
    plp
vice_open_read_from_ptr_fail:
    sec
    rts

vice_close_current_file:
    jsr CLRCHN
    lda vice_lfn
    jsr CLOSE_K
    rts

build_vice_open_path_from_name:
    jsr select_backend_path_cache
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr fill_backend_path_vice
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    ldy #$00
build_vice_open_path_prefix:
    lda (PTR),y
    beq build_vice_open_path_sep
    sta source_fullpath_buffer,y
    iny
    cpy #FULL_PATH_BUF_LEN-6
    bcc build_vice_open_path_prefix
build_vice_open_path_sep:
    sta vice_path_len
    lda #ASCII_SLASH
    sta source_fullpath_buffer,y
    iny
    lda #$00
    sta vice_name_index
build_vice_open_path_name:
    ldx vice_name_index
    lda path_name_buffer,x
    beq build_vice_open_path_suffix
    jsr screen_code_to_ascii
    sta source_fullpath_buffer,y
    iny
    inc vice_name_index
    cpy #FULL_PATH_BUF_LEN-5
    bcc build_vice_open_path_name
build_vice_open_path_suffix:
    lda #ASCII_COMMA
    sta source_fullpath_buffer,y
    iny
    lda #'S'
    sta source_fullpath_buffer,y
    iny
    lda #ASCII_COMMA
    sta source_fullpath_buffer,y
    iny
    lda #'R'
    sta source_fullpath_buffer,y
    iny
    lda #$00
    sta source_fullpath_buffer,y
    lda #<source_fullpath_buffer
    sta PTR
    lda #>source_fullpath_buffer
    sta PTR+1
    rts


build_vice_full_path_from_path_name:
    lda #<path_name_buffer
    sta SCREEN_PTR
    lda #>path_name_buffer
    sta SCREEN_PTR+1
    jmp build_vice_full_path_from_screen_ptr

build_vice_full_path_from_source_name:
    lda #<source_name_buffer
    sta SCREEN_PTR
    lda #>source_name_buffer
    sta SCREEN_PTR+1
    jmp build_vice_full_path_from_screen_ptr

build_vice_manifest_full_path:
    jsr select_backend_path_cache
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr fill_backend_path_vice
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    ldy #$00
build_vice_manifest_full_path_prefix:
    lda (PTR),y
    beq build_vice_manifest_full_path_suffix
    sta source_fullpath_buffer,y
    iny
    cpy #FULL_PATH_BUF_LEN-12
    bcc build_vice_manifest_full_path_prefix
build_vice_manifest_full_path_suffix:
    lda #ASCII_SLASH
    sta source_fullpath_buffer,y
    iny
    lda #'U'
    sta source_fullpath_buffer,y
    iny
    lda #'D'
    sta source_fullpath_buffer,y
    iny
    lda #'O'
    sta source_fullpath_buffer,y
    iny
    lda #'S'
    sta source_fullpath_buffer,y
    iny
    lda #'D'
    sta source_fullpath_buffer,y
    iny
    lda #'I'
    sta source_fullpath_buffer,y
    iny
    lda #'R'
    sta source_fullpath_buffer,y
    iny
    lda #ASCII_DOT
    sta source_fullpath_buffer,y
    iny
    lda #'T'
    sta source_fullpath_buffer,y
    iny
    lda #'X'
    sta source_fullpath_buffer,y
    iny
    lda #'T'
    sta source_fullpath_buffer,y
    iny
    lda #$00
    sta source_fullpath_buffer,y
    lda #<source_fullpath_buffer
    sta PTR
    lda #>source_fullpath_buffer
    sta PTR+1
    rts

build_vice_full_path_from_screen_ptr:
    lda SCREEN_PTR
    sta matched_name_lo
    lda SCREEN_PTR+1
    sta matched_name_hi
    jsr select_backend_path_cache
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr fill_backend_path_vice
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    lda matched_name_lo
    sta SCREEN_PTR
    lda matched_name_hi
    sta SCREEN_PTR+1
    ldy #$00
build_vice_full_path_prefix:
    lda (PTR),y
    beq build_vice_full_path_sep
    sta source_fullpath_buffer,y
    iny
    cpy #FULL_PATH_BUF_LEN-2
    bcc build_vice_full_path_prefix
build_vice_full_path_sep:
    lda #ASCII_SLASH
    sta source_fullpath_buffer,y
    iny
    ldx #$00
build_vice_full_path_name_loop:
    lda (SCREEN_PTR,x)
    beq build_vice_full_path_done
    jsr screen_code_to_ascii
    sta source_fullpath_buffer,y
    iny
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    cpy #FULL_PATH_BUF_LEN-1
    bcc build_vice_full_path_name_loop
build_vice_full_path_done:
    lda #$00
    sta source_fullpath_buffer,y
    lda #<source_fullpath_buffer
    sta PTR
    lda #>source_fullpath_buffer
    sta PTR+1
    rts

build_vice_dir_open_path:
    jsr select_backend_path_cache
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr fill_backend_path_vice
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    lda #'$'
    sta source_fullpath_buffer
    lda #ASCII_COLON
    sta source_fullpath_buffer+1
    ldy #$00
    ldx #$02
    lda (PTR),y
    cmp #ASCII_SLASH
    bne build_vice_dir_open_path_copy
    iny
build_vice_dir_open_path_copy:
    lda (PTR),y
    beq build_vice_dir_open_path_suffix
    sta source_fullpath_buffer,x
    iny
    inx
    cpx #FULL_PATH_BUF_LEN-4
    bcc build_vice_dir_open_path_copy
build_vice_dir_open_path_suffix:
    cpx #$02
    beq build_vice_dir_open_path_wild
    lda #ASCII_SLASH
    sta source_fullpath_buffer,x
    inx
build_vice_dir_open_path_wild:
    lda #'*'
    sta source_fullpath_buffer,x
    inx
build_vice_dir_open_path_done:
    lda #$00
    sta source_fullpath_buffer,x
    lda #<source_fullpath_buffer
    sta PTR
    lda #>source_fullpath_buffer
    sta PTR+1
    rts

vice_read_open_file_into_ptr_len:
    sta vice_read_limit
    lda #$00
    sta vice_read_length
    tay
vice_read_open_file_into_ptr_len_loop:
    jsr CHRIN
    sta (PTR),y
    iny
    sty vice_read_length
    jsr READST
    and #$40
    bne vice_read_open_file_into_ptr_len_done
    cpy vice_read_limit
    bcc vice_read_open_file_into_ptr_len_loop
vice_read_open_file_into_ptr_len_done:
    lda #$00
    sta (PTR),y
    clc
    rts

read_file_response_vice:
    jsr build_vice_open_path_from_name
    lda #VICE_LFN_FILE
    sta vice_lfn
    lda #VICE_SA_READ
    sta vice_secondary
    jsr vice_open_read_from_ptr
    bcs read_file_response_vice_fail
    lda #<response_buffer
    sta PTR
    lda #>response_buffer
    sta PTR+1
    lda #MAX_RESPONSE_LEN-1
    jsr vice_read_open_file_into_ptr_len
    php
    jsr vice_close_current_file
    plp
    lda #<response_buffer
    sta PTR
    lda #>response_buffer
    sta PTR+1
    clc
    rts
read_file_response_vice_fail:
    sec
    rts

read_file_response_vice_current:
    jsr vice_tree_find_current_slot
    bcs read_file_response_vice_current_host
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq read_file_response_vice_current_fail
    jsr select_vice_tree_content_slot
    clc
    rts
read_file_response_vice_current_host:
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    bne read_file_response_vice_current_open
    jsr query_file_vice_host_current
    bcs read_file_response_vice_current_fail
read_file_response_vice_current_open:
    jmp read_file_response_vice
read_file_response_vice_current_fail:
    sec
    rts

query_file_response_vice_current:
    jsr vice_tree_find_current_slot
    bcs query_file_response_vice_current_host
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq query_file_response_vice_current_fail
    clc
    rts
query_file_response_vice_current_host:
    jmp query_file_vice_host_current
query_file_response_vice_current_fail:
    sec
    rts

query_program_file_vice:
    jsr build_vice_open_path_from_name
    lda #VICE_LFN_FILE
    sta vice_lfn
    lda #VICE_SA_READ
    sta vice_secondary
    jsr vice_open_read_from_ptr
    bcs query_program_file_vice_missing
    jsr vice_close_current_file
    lda #RUN_STATUS_OK
    clc
    rts
query_program_file_vice_missing:
    lda #RUN_STATUS_NOFILE
    sec
    rts

query_program_file_vice_current:
    jsr vice_tree_find_current_slot_strict
    bcs query_program_file_vice_current_host
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq query_program_file_vice_current_missing
    lda #RUN_STATUS_OK
    clc
    rts
query_program_file_vice_current_host:
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    bne query_program_file_vice_current_open
    jsr query_program_file_vice_host_current
    bcc query_program_file_vice_current_found
    jmp query_program_file_vice_current_missing
query_program_file_vice_current_open:
    jmp query_program_file_vice
query_program_file_vice_current_found:
    lda #RUN_STATUS_OK
    clc
    rts
query_program_file_vice_current_missing:
    lda #RUN_STATUS_NOFILE
    sec
    rts

load_program_image_vice:
    jsr build_vice_open_path_from_name
    lda #VICE_LFN_FILE
    sta vice_lfn
    lda #VICE_SA_READ
    sta vice_secondary
    jsr vice_open_read_from_ptr
    bcs load_program_image_vice_fail
    lda #<program_image_buffer
    sta PTR
    lda #>program_image_buffer
    sta PTR+1
    lda #PROGRAM_IMAGE_MAX
    jsr vice_read_open_file_into_ptr_len
    php
    jsr vice_close_current_file
    plp
    lda vice_read_length
    beq load_program_image_vice_missing
    lda vice_read_length
    sta program_image_len_lo
    lda #$00
    sta program_image_len_hi
    jsr snapshot_program_image_length
    lda #RUN_STATUS_OK
    clc
    rts
load_program_image_vice_missing:
    lda #RUN_STATUS_NOFILE
    sec
    rts
load_program_image_vice_fail:
    lda #RUN_STATUS_LOAD_FAILED
    sec
    rts

load_program_image_vice_current:
    jsr vice_tree_find_current_slot_strict
    bcs load_program_image_vice_current_host
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq load_program_image_vice_current_missing
    jsr select_vice_tree_content_slot
    bcc load_program_image_vice_current_overlay
load_program_image_vice_current_host:
    jmp load_program_image_vice
load_program_image_vice_current_missing:
    lda #RUN_STATUS_NOFILE
    sec
    rts
load_program_image_vice_current_overlay:
    jsr copy_ptr_to_program_image
    bcc load_program_image_vice_current_ok
    lda #RUN_STATUS_TOO_LARGE
    sec
    rts
load_program_image_vice_current_ok:
    jsr snapshot_program_image_length
    lda #RUN_STATUS_OK
    clc
    rts

fill_vice_dir_cache_current:
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    bne fill_vice_dir_cache_current_flat
    jsr fill_vice_manifest_dir_cache_current
    bcc fill_vice_dir_cache_current_done
fill_vice_dir_cache_current_flat:
    jsr build_vice_dir_open_path
    lda #VICE_LFN_DIR
    sta vice_lfn
    lda #$00
    sta vice_secondary
    jsr vice_open_read_from_ptr
    bcs fill_vice_dir_cache_current_fail
    lda #<flat_sector_buffer
    sta PTR
    lda #>flat_sector_buffer
    sta PTR+1
    lda #255
    jsr vice_read_open_file_into_ptr_len
    php
    jsr vice_close_current_file
    plp
    jsr select_hw_dir_tables
    lda #$00
    sta enum_count
    sta vice_parse_index
    ldx temp_drive
    sta hw_dir_count_table,x
    jsr parse_vice_dir_buffer_entries
fill_vice_dir_cache_current_done:
    clc
    rts
fill_vice_dir_cache_current_fail:
    sec
    rts

fill_vice_manifest_dir_cache_current:
    jsr fill_vice_manifest_dir_cache_host_current
    bcc fill_vice_manifest_dir_cache_current_host_ok
    jsr select_hw_dir_tables
    lda #$00
    sta enum_count
    ldx temp_drive
    sta hw_dir_count_table,x
fill_vice_manifest_dir_cache_current_host_ok:
    jsr apply_vice_dir_overlay_current_to_hw_cache
    jsr apply_vice_tree_overlay_current_to_hw_cache
    clc
    rts

fill_vice_manifest_dir_cache_host_current:
    jsr build_vice_manifest_open_path
    lda #VICE_LFN_FILE
    sta vice_lfn
    lda #VICE_SA_READ
    sta vice_secondary
    jsr vice_open_read_from_ptr
    bcs fill_vice_manifest_dir_cache_host_current_fail
    lda #<flat_dir_sector_buffer
    sta PTR
    lda #>flat_dir_sector_buffer
    sta PTR+1
    lda #255
    jsr vice_read_open_file_into_ptr_len
    php
    jsr vice_close_current_file
    plp
    jsr select_hw_dir_tables
    lda #$00
    sta enum_count
    ldx temp_drive
    sta hw_dir_count_table,x
    jsr parse_vice_manifest_buffer_entries
    clc
    rts
fill_vice_manifest_dir_cache_host_current_fail:
    sec
    rts

build_vice_manifest_open_path:
    jsr select_backend_path_cache
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr fill_backend_path_vice
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    ldy #$00
build_vice_manifest_open_path_prefix:
    lda (PTR),y
    beq build_vice_manifest_open_path_suffix
    sta source_fullpath_buffer,y
    iny
    cpy #FULL_PATH_BUF_LEN-18
    bcc build_vice_manifest_open_path_prefix
build_vice_manifest_open_path_suffix:
    lda #ASCII_SLASH
    sta source_fullpath_buffer,y
    iny
    lda #'U'
    sta source_fullpath_buffer,y
    iny
    lda #'D'
    sta source_fullpath_buffer,y
    iny
    lda #'O'
    sta source_fullpath_buffer,y
    iny
    lda #'S'
    sta source_fullpath_buffer,y
    iny
    lda #'D'
    sta source_fullpath_buffer,y
    iny
    lda #'I'
    sta source_fullpath_buffer,y
    iny
    lda #'R'
    sta source_fullpath_buffer,y
    iny
    lda #ASCII_DOT
    sta source_fullpath_buffer,y
    iny
    lda #'T'
    sta source_fullpath_buffer,y
    iny
    lda #'X'
    sta source_fullpath_buffer,y
    iny
    lda #'T'
    sta source_fullpath_buffer,y
    iny
    lda #ASCII_COMMA
    sta source_fullpath_buffer,y
    iny
    lda #'S'
    sta source_fullpath_buffer,y
    iny
    lda #ASCII_COMMA
    sta source_fullpath_buffer,y
    iny
    lda #'R'
    sta source_fullpath_buffer,y
    iny
    lda #$00
    sta source_fullpath_buffer,y
    lda #<source_fullpath_buffer
    sta PTR
    lda #>source_fullpath_buffer
    sta PTR+1
    rts

parse_vice_manifest_buffer_entries:
    lda #$00
    sta saved_response_y
parse_vice_manifest_buffer_entries_loop:
    ldy saved_response_y
    lda flat_dir_sector_buffer,y
    beq parse_vice_manifest_buffer_entries_done
    cmp #$0D
    beq parse_vice_manifest_skip_char
    cmp #$0A
    beq parse_vice_manifest_skip_char
    cmp #'D'
    beq parse_vice_manifest_entry_dir
    cmp #'F'
    beq parse_vice_manifest_entry_file
    jmp parse_vice_manifest_skip_line
parse_vice_manifest_entry_dir:
    lda #$01
    bne parse_vice_manifest_entry_start
parse_vice_manifest_entry_file:
    lda #$00
parse_vice_manifest_entry_start:
    sta vice_dir_flag
    inc saved_response_y
parse_vice_manifest_skip_space:
    ldy saved_response_y
    lda flat_dir_sector_buffer,y
    cmp #ASCII_SPACE
    bne parse_vice_manifest_capture_init
    inc saved_response_y
    bne parse_vice_manifest_skip_space
parse_vice_manifest_capture_init:
    lda #$00
    sta vice_name_len
parse_vice_manifest_capture_loop:
    ldy saved_response_y
    lda flat_dir_sector_buffer,y
    beq parse_vice_manifest_finalize
    cmp #$0D
    beq parse_vice_manifest_finalize
    cmp #$0A
    beq parse_vice_manifest_finalize
    ldx vice_name_len
    cpx #HW_DIR_NAME_MAX-1
    bcs parse_vice_manifest_capture_advance
    jsr normalize_output_char
    sta vice_name_buffer,x
    inx
    stx vice_name_len
parse_vice_manifest_capture_advance:
    inc saved_response_y
    bne parse_vice_manifest_capture_loop
parse_vice_manifest_finalize:
    ldx vice_name_len
    lda #$00
    sta vice_name_buffer,x
    jsr store_vice_dir_entry_if_any
parse_vice_manifest_skip_line:
    ldy saved_response_y
    lda flat_dir_sector_buffer,y
    beq parse_vice_manifest_buffer_entries_done
    cmp #$0D
    beq parse_vice_manifest_skip_char
    cmp #$0A
    beq parse_vice_manifest_skip_char
    inc saved_response_y
    bne parse_vice_manifest_skip_line
parse_vice_manifest_skip_char:
    inc saved_response_y
    jmp parse_vice_manifest_buffer_entries_loop
parse_vice_manifest_buffer_entries_done:
    rts

parse_vice_dir_buffer_entries:
    lda #$02
    sta vice_parse_index
parse_vice_dir_buffer_entries_loop:
    ldy vice_parse_index
    cpy vice_read_length
    bcs parse_vice_dir_buffer_entries_done
    lda flat_sector_buffer,y
    beq parse_vice_dir_buffer_entries_done
    sta vice_line_link_lo
    iny
    cpy vice_read_length
    bcs parse_vice_dir_buffer_entries_done
    lda flat_sector_buffer,y
    sta vice_line_link_hi
    iny
    cpy vice_read_length
    bcs parse_vice_dir_buffer_entries_done
    lda flat_sector_buffer,y
    sta vice_line_num_lo
    iny
    cpy vice_read_length
    bcs parse_vice_dir_buffer_entries_done
    lda flat_sector_buffer,y
    sta vice_line_num_hi
    iny
    sty vice_parse_index
    lda vice_line_num_lo
    ora vice_line_num_hi
    beq parse_vice_dir_skip_line
    lda #$00
    sta vice_name_len
    sta vice_dir_flag
parse_vice_dir_line_loop:
    ldy vice_parse_index
    cpy vice_read_length
    bcs parse_vice_dir_buffer_entries_done
    lda flat_sector_buffer,y
    beq parse_vice_dir_finalize_line
    cmp #'"'
    bne parse_vice_dir_line_next
    jsr parse_vice_dir_capture_name
    jmp parse_vice_dir_line_loop
parse_vice_dir_line_next:
    inc vice_parse_index
    bne parse_vice_dir_line_loop
parse_vice_dir_finalize_line:
    jsr store_vice_dir_entry_if_any
parse_vice_dir_skip_line:
parse_vice_dir_skip_line_loop:
    ldy vice_parse_index
    cpy vice_read_length
    bcs parse_vice_dir_buffer_entries_done
    lda flat_sector_buffer,y
    inc vice_parse_index
    bne :+
:
    beq parse_vice_dir_buffer_entries_loop
    jmp parse_vice_dir_skip_line_loop
parse_vice_dir_buffer_entries_done:
    rts

parse_vice_dir_capture_name:
    inc vice_parse_index
    lda #$00
    sta vice_name_len
parse_vice_dir_capture_name_loop:
    ldy vice_parse_index
    cpy vice_read_length
    bcs parse_vice_dir_capture_name_done
    lda flat_sector_buffer,y
    cmp #'"'
    beq parse_vice_dir_capture_name_done
    ldx vice_name_len
    cpx #HW_DIR_NAME_MAX-1
    bcs parse_vice_dir_capture_name_advance
    jsr normalize_output_char
    sta vice_name_buffer,x
    inx
    stx vice_name_len
parse_vice_dir_capture_name_advance:
    inc vice_parse_index
    bne parse_vice_dir_capture_name_loop
parse_vice_dir_capture_name_done:
    ldx vice_name_len
    lda #$00
    sta vice_name_buffer,x
    inc vice_parse_index
    ldy vice_parse_index
    cpy vice_read_length
    bcs parse_vice_dir_capture_name_end
    lda flat_sector_buffer,y
    cmp #' '
    beq parse_vice_dir_capture_name_scan
parse_vice_dir_capture_name_scan:
    lda vice_parse_index
    sta saved_response_y
parse_vice_dir_capture_name_scan_loop:
    ldy saved_response_y
    cpy vice_read_length
    bcs parse_vice_dir_capture_name_end
    lda flat_sector_buffer,y
    beq parse_vice_dir_capture_name_end
    jsr normalize_output_char
    cmp #'D'
    bne parse_vice_dir_capture_name_next
    iny
    cpy vice_read_length
    bcs parse_vice_dir_capture_name_end
    lda flat_sector_buffer,y
    jsr normalize_output_char
    cmp #'I'
    bne parse_vice_dir_capture_name_next
    iny
    cpy vice_read_length
    bcs parse_vice_dir_capture_name_end
    lda flat_sector_buffer,y
    jsr normalize_output_char
    cmp #'R'
    bne parse_vice_dir_capture_name_next
    lda #$01
    sta vice_dir_flag
    jmp parse_vice_dir_capture_name_end
parse_vice_dir_capture_name_next:
    inc saved_response_y
    bne parse_vice_dir_capture_name_scan_loop
parse_vice_dir_capture_name_end:
    rts

store_vice_dir_entry_if_any:
    lda vice_name_len
    beq store_vice_dir_entry_if_any_done
    lda enum_count
    cmp #HW_DIR_CACHE_MAX
    bcs store_vice_dir_entry_if_any_done
    jsr store_vice_dir_entry_name
    inc enum_count
    ldx temp_drive
    lda enum_count
    sta hw_dir_count_table,x
store_vice_dir_entry_if_any_done:
    rts

store_vice_dir_entry_name:
    jsr select_hw_dir_tables
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
    ldy #$00
store_vice_dir_entry_name_copy:
    lda vice_name_buffer,y
    beq store_vice_dir_entry_name_finish
    sta (PTR),y
    iny
    cpy #HW_DIR_NAME_MAX-1
    bcc store_vice_dir_entry_name_copy
store_vice_dir_entry_name_finish:
    lda vice_dir_flag
    beq store_vice_dir_entry_name_term
    lda #ASCII_SLASH
    sta (PTR),y
    iny
store_vice_dir_entry_name_term:
    lda #$00
    sta (PTR),y
    rts

copy_ptr_to_vice_name_buffer:
    ldy #$00
    sty vice_name_len
    sty vice_dir_flag
copy_ptr_to_vice_name_buffer_loop:
    lda (PTR),y
    beq copy_ptr_to_vice_name_buffer_done
    cpy #HW_DIR_NAME_MAX-1
    bcs copy_ptr_to_vice_name_buffer_done
    sta vice_name_buffer,y
    iny
    sty vice_name_len
    bne copy_ptr_to_vice_name_buffer_loop
copy_ptr_to_vice_name_buffer_done:
    lda #$00
    sta vice_name_buffer,y
    rts

compare_ptr_to_screen_ptr_exact:
    ldy #$00
compare_ptr_to_screen_ptr_exact_loop:
    lda (PTR),y
    cmp (SCREEN_PTR),y
    bne compare_ptr_to_screen_ptr_exact_fail
    beq :+
:
    lda (PTR),y
    beq compare_ptr_to_screen_ptr_exact_ok
    iny
    bne compare_ptr_to_screen_ptr_exact_loop
compare_ptr_to_screen_ptr_exact_fail:
    sec
    rts
compare_ptr_to_screen_ptr_exact_ok:
    clc
    rts

find_hw_dir_cache_matching_ptr:
    lda PTR
    sta matched_name_lo
    lda PTR+1
    sta matched_name_hi
    jsr select_hw_dir_tables
    lda #$00
    sta file_index
find_hw_dir_cache_matching_ptr_loop:
    lda file_index
    cmp enum_count
    bcs find_hw_dir_cache_matching_ptr_fail
    tay
    lda enum_lo_ptr_lo
    sta SCREEN_PTR
    lda enum_lo_ptr_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta SCREEN_PTR
    lda enum_hi_ptr_lo
    sta PTR
    lda enum_hi_ptr_hi
    sta PTR+1
    lda (PTR),y
    sta SCREEN_PTR+1
    lda matched_name_lo
    sta PTR
    lda matched_name_hi
    sta PTR+1
    jsr compare_ptr_to_screen_ptr_exact
    bcc find_hw_dir_cache_matching_ptr_hit
    inc file_index
    bne find_hw_dir_cache_matching_ptr_loop
find_hw_dir_cache_matching_ptr_fail:
    sec
    rts
find_hw_dir_cache_matching_ptr_hit:
    clc
    rts

find_hw_dir_cache_matching_path_name:
    jsr select_hw_dir_tables
    lda #$00
    sta file_index
find_hw_dir_cache_matching_path_name_loop:
    lda file_index
    cmp enum_count
    bcs find_hw_dir_cache_matching_path_name_fail
    tay
    lda enum_lo_ptr_lo
    sta SCREEN_PTR
    lda enum_lo_ptr_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta PTR
    lda enum_hi_ptr_lo
    sta SCREEN_PTR
    lda enum_hi_ptr_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta PTR+1
    jsr compare_ptr_to_path_name
    bcc find_hw_dir_cache_matching_path_name_hit
    inc file_index
    bne find_hw_dir_cache_matching_path_name_loop
find_hw_dir_cache_matching_path_name_fail:
    sec
    rts
find_hw_dir_cache_matching_path_name_hit:
    clc
    rts

find_hw_dir_cache_matching_path_name_strict:
    jsr select_hw_dir_tables
    lda #$00
    sta file_index
find_hw_dir_cache_matching_path_name_strict_loop:
    lda file_index
    cmp enum_count
    bcs find_hw_dir_cache_matching_path_name_strict_fail
    tay
    lda enum_lo_ptr_lo
    sta SCREEN_PTR
    lda enum_lo_ptr_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta PTR
    lda enum_hi_ptr_lo
    sta SCREEN_PTR
    lda enum_hi_ptr_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta PTR+1
    jsr compare_ptr_to_path_name_strict
    bcc find_hw_dir_cache_matching_path_name_strict_hit
    inc file_index
    bne find_hw_dir_cache_matching_path_name_strict_loop
find_hw_dir_cache_matching_path_name_strict_fail:
    sec
    rts
find_hw_dir_cache_matching_path_name_strict_hit:
    clc
    rts

find_hw_dir_cache_matching_dir_path_name:
    jsr select_hw_dir_tables
    lda #$00
    sta file_index
find_hw_dir_cache_matching_dir_path_name_loop:
    lda file_index
    cmp enum_count
    bcs find_hw_dir_cache_matching_dir_path_name_fail
    tay
    lda enum_lo_ptr_lo
    sta SCREEN_PTR
    lda enum_lo_ptr_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta PTR
    lda enum_hi_ptr_lo
    sta SCREEN_PTR
    lda enum_hi_ptr_hi
    sta SCREEN_PTR+1
    lda (SCREEN_PTR),y
    sta PTR+1
    jsr compare_dir_ptr_to_path_name
    bcc find_hw_dir_cache_matching_dir_path_name_hit
    inc file_index
    bne find_hw_dir_cache_matching_dir_path_name_loop
find_hw_dir_cache_matching_dir_path_name_fail:
    sec
    rts
find_hw_dir_cache_matching_dir_path_name_hit:
    clc
    rts

remove_hw_dir_cache_current_index:
    lda file_index
    cmp enum_count
    bcs remove_hw_dir_cache_current_index_done
    jsr select_hw_dir_tables
    ldy file_index
remove_hw_dir_cache_current_index_shift:
    iny
    cpy enum_count
    bcs remove_hw_dir_cache_current_index_finish
    lda enum_lo_ptr_lo
    sta PTR
    lda enum_lo_ptr_hi
    sta PTR+1
    lda (PTR),y
    dey
    sta (PTR),y
    iny
    lda enum_hi_ptr_lo
    sta PTR
    lda enum_hi_ptr_hi
    sta PTR+1
    lda (PTR),y
    dey
    sta (PTR),y
    iny
    jmp remove_hw_dir_cache_current_index_shift
remove_hw_dir_cache_current_index_finish:
    dec enum_count
    ldx temp_drive
    lda enum_count
    sta hw_dir_count_table,x
remove_hw_dir_cache_current_index_done:
    rts

append_ptr_to_hw_dir_cache_current:
    jsr copy_ptr_to_vice_name_buffer
    jsr store_vice_dir_entry_if_any
    rts

apply_vice_dir_overlay_current_to_hw_cache:
    lda #$00
    sta file_count
apply_vice_dir_overlay_current_to_hw_cache_loop:
    lda file_count
    cmp #VICE_DIR_DYNAMIC_MAX
    bcs apply_vice_dir_overlay_current_to_hw_cache_done
    sta file_index
    jsr load_vice_dir_state_for_index
    beq apply_vice_dir_overlay_current_to_hw_cache_next
    sta vice_dir_state_temp
    jsr load_vice_dir_parent_for_index
    cmp temp_dir_id
    bne apply_vice_dir_overlay_current_to_hw_cache_next
    jsr select_vice_dir_name_slot
    jsr copy_ptr_name_to_path_buffer
    jsr find_hw_dir_cache_matching_dir_path_name
    bcs :+
    jsr remove_hw_dir_cache_current_index
:
    lda vice_dir_state_temp
    cmp #VICE_DIR_SLOT_TOMBSTONE
    beq apply_vice_dir_overlay_current_to_hw_cache_next
    lda file_count
    sta file_index
    jsr select_vice_dir_name_slot
    jsr copy_ptr_to_vice_name_buffer
    lda #$01
    sta vice_dir_flag
    jsr store_vice_dir_entry_if_any
apply_vice_dir_overlay_current_to_hw_cache_next:
    inc file_count
    bne apply_vice_dir_overlay_current_to_hw_cache_loop
apply_vice_dir_overlay_current_to_hw_cache_done:
    rts

apply_vice_tree_overlay_current_to_hw_cache:
    lda #$00
    sta file_count
apply_vice_tree_overlay_current_to_hw_cache_loop:
    lda file_count
    cmp #VICE_TREE_DYNAMIC_MAX
    bcs apply_vice_tree_overlay_current_to_hw_cache_done
    sta file_index
    jsr load_vice_tree_state_for_index
    beq apply_vice_tree_overlay_current_to_hw_cache_next
    sta saved_response_y
    jsr load_vice_tree_dir_for_index
    cmp temp_dir_id
    bne apply_vice_tree_overlay_current_to_hw_cache_next
    jsr select_vice_tree_name_slot
    jsr copy_ptr_name_to_path_buffer
    jsr find_hw_dir_cache_matching_path_name
    bcs :+
    jsr remove_hw_dir_cache_current_index
:
    lda saved_response_y
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq apply_vice_tree_overlay_current_to_hw_cache_next
    lda file_count
    sta file_index
    jsr select_vice_tree_name_slot
    jsr append_ptr_to_hw_dir_cache_current
apply_vice_tree_overlay_current_to_hw_cache_next:
    inc file_count
    bne apply_vice_tree_overlay_current_to_hw_cache_loop
apply_vice_tree_overlay_current_to_hw_cache_done:
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

uci_status_is_ok_or_empty:
    lda uci_status_length
    beq uci_status_is_ok_or_empty_done
    jmp uci_status_is_ok
uci_status_is_ok_or_empty_done:
    clc
    rts

uci_status_is_file_not_found:
    lda uci_status_buffer+0
    cmp #'8'
    bne uci_status_is_file_not_found_fail
    lda uci_status_buffer+1
    cmp #'8'
    bne uci_status_is_file_not_found_fail
    clc
    rts
uci_status_is_file_not_found_fail:
    sec
    rts

uci_status_is_not_disk_image:
    lda uci_status_buffer+0
    cmp #'8'
    bne uci_status_is_not_disk_image_fail
    lda uci_status_buffer+1
    cmp #'9'
    bne uci_status_is_not_disk_image_fail
    clc
    rts
uci_status_is_not_disk_image_fail:
    sec
    rts

uci_status_is_drive_not_present:
    lda uci_status_buffer+0
    cmp #'9'
    bne uci_status_is_drive_not_present_fail
    lda uci_status_buffer+1
    cmp #'0'
    bne uci_status_is_drive_not_present_fail
    clc
    rts
uci_status_is_drive_not_present_fail:
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
    jsr CINT
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

clear_hiram:
    lda #<HIRAM_START
    sta PTR
    lda #>HIRAM_START
    sta PTR+1
    ldx #HIRAM_PAGES
    ldy #$00
    lda #$00
clear_hiram_page:
    sta (PTR),y
    iny
    bne clear_hiram_page
    inc PTR+1
    dex
    bne clear_hiram_page
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
svc_console_write_ptr:
    ldy #$00
write_loop:
    lda (PTR),y
    beq write_done
    jsr console_putc
    iny
    bne write_loop
write_done:
    rts


svc_shell_preprompt:
    lda input_mode
    cmp #INPUT_MODE_SCRIPT
    bne svc_shell_preprompt_done
    lda script_abort_on_error
    beq svc_shell_preprompt_done
    lda command_status
    beq svc_shell_preprompt_done
    lda #INPUT_MODE_KEYBOARD
    sta input_mode
    lda #$00
    sta batch_mode
    sta script_abort_on_error
    sta command_status
svc_shell_preprompt_done:
    rts

svc_console_write_prompt:
    jsr build_prompt_response
    jmp svc_console_write_sc0




svc_command_status_clear:
    lda #$00
    sta command_status
    rts

svc_command_status_fail:
    lda #$01
    sta command_status
    rts

svc_command_status_from_program_exit:
    lda PROGRAM_EXIT_SNAPSHOT
    sta command_status
    rts

svc_command_status_from_response:
    lda #$00
    sta command_status
    lda 0,x
    sta matched_name_lo
    lda 1,x
    sta matched_name_hi
    ldy #$00
svc_command_status_scan:
    lda error_response_table,y
    sta PTR
    iny
    lda error_response_table,y
    sta PTR+1
    iny
    lda PTR
    ora PTR+1
    beq svc_command_status_done
    lda PTR
    cmp matched_name_lo
    bne svc_command_status_scan
    lda PTR+1
    cmp matched_name_hi
    beq svc_command_status_fail
    jmp svc_command_status_scan
svc_command_status_done:
    rts

svc_emit_mem_response:
    jsr build_mem_response
    jsr svc_console_write_sc0
    jmp svc_console_newline

svc_try_autoexec_batch:
    stx saved_rp_x
    jsr load_autoexec_arg_buffer
    ldx saved_rp_x
    jsr svc_program_prepare_run
    ldx saved_rp_x
    lda #$00
    sta 0,x
    sta 1,x
    rts

load_autoexec_arg_buffer:
    ldy #$00
load_autoexec_arg_buffer_loop:
    lda autoexec_name,y
    sta arg_buffer,y
    beq load_autoexec_arg_buffer_done
    iny
    bne load_autoexec_arg_buffer_loop
load_autoexec_arg_buffer_done:
    sty arg_length
    lda #$00
    sta program_cmdline_len
    sta program_cmdline_buffer
    rts

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
    bcc :+
    jmp line_empty
:
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
    lda batch_mode
    beq line_echo_normal
    lda (PTR),y
    cmp #$25
    bne line_echo_normal
    iny
    lda (PTR),y
    cmp #$31
    beq line_echo_arg1
    cmp #$32
    beq line_echo_arg2
    cmp #$33
    beq line_echo_arg3
    dey
    lda #$25
    jsr append_script_char
    jmp line_echo_next
line_echo_arg1:
    lda #<batch_arg1_buffer
    sta SCREEN_PTR
    lda #>batch_arg1_buffer
    sta SCREEN_PTR+1
    jsr append_batch_arg_ptr
    jmp line_echo_next
line_echo_arg2:
    lda #<batch_arg2_buffer
    sta SCREEN_PTR
    lda #>batch_arg2_buffer
    sta SCREEN_PTR+1
    jsr append_batch_arg_ptr
    jmp line_echo_next
line_echo_arg3:
    lda #<batch_arg3_buffer
    sta SCREEN_PTR
    lda #>batch_arg3_buffer
    sta SCREEN_PTR+1
    jsr append_batch_arg_ptr
    jmp line_echo_next
line_echo_normal:
    jsr normalize_input_char
    jsr append_script_char
line_echo_next:
    iny
    bne line_echo_loop
line_echo_done:
    ldx line_length
    lda #$00
    sta line_buffer,x
    jsr svc_console_newline
    jsr tokenize_line_buffer
    jsr dispatch_script_command_native
    bcc line_script_command_ok
    lda script_abort_on_error
    beq line_script_command_ok
    lda #INPUT_MODE_KEYBOARD
    sta input_mode
    lda #$00
    sta batch_mode
    sta script_abort_on_error
    jmp line_script_finish
line_script_command_ok:
    ldy script_index
    cpy script_line_count
    bcc :+
    lda #INPUT_MODE_KEYBOARD
    sta input_mode
    lda #$00
    sta batch_mode
    sta script_abort_on_error
:
line_script_finish:
    ldx saved_rp_x
    lda #SHELL_CMD_NONE
    sta 0,x
    lda #$00
    sta 1,x
    rts
line_empty:
    lda #INPUT_MODE_KEYBOARD
    sta input_mode
    lda #$00
    sta batch_mode
    sta script_abort_on_error
    lda #SHELL_CMD_NONE
    sta 0,x
    lda #$00
    sta 1,x
    rts

append_batch_arg_ptr:
    lda SCREEN_PTR
    sta matched_name_lo
    lda SCREEN_PTR+1
    sta matched_name_hi
append_batch_arg_ptr_loop:
    lda matched_name_lo
    sta SCREEN_PTR
    lda matched_name_hi
    sta SCREEN_PTR+1
    ldx #$00
    lda (SCREEN_PTR,x)
    beq append_batch_arg_ptr_done
    jsr normalize_input_char
    jsr append_script_char
    inc matched_name_lo
    bne append_batch_arg_ptr_loop
    inc matched_name_hi
    jmp append_batch_arg_ptr_loop
append_batch_arg_ptr_done:
    rts

append_script_char:
    bcc append_script_char_done
    ldx line_length
    cpx #MAX_LINE_LEN
    bcs append_script_char_done
    sta line_buffer,x
    inx
    stx line_length
    jsr console_putc
append_script_char_done:
    rts

dispatch_script_command_native:
    cmp #SHELL_CMD_NONE
    beq dispatch_script_command_done
    cmp #SHELL_CMD_RUN
    beq dispatch_script_command_run
    cmp #$FF
    beq dispatch_script_command_unknown
    ldx saved_rp_x
    sta 0,x
    lda #$00
    sta 1,x
    jsr svc_shell_response_ptr
    ldx saved_rp_x
    jsr svc_command_status_from_response
    ldx saved_rp_x
    jsr svc_console_write_sc0
    jsr svc_console_newline
    lda command_status
    beq dispatch_script_command_done
    sec
    rts
dispatch_script_command_done:
    clc
    rts
dispatch_script_command_run:
    ldx saved_rp_x
    jsr svc_program_prepare_run
    ldx saved_rp_x
    jsr svc_program_finish_prepare
    lda command_status
    beq dispatch_script_command_done
    sec
    rts
dispatch_script_command_unknown:
    jsr svc_command_status_fail
    lda #<resp_unknown
    sta PTR
    lda #>resp_unknown
    sta PTR+1
    jsr svc_console_write_ptr
    jsr svc_console_newline
    sec
    rts

svc_shell_response_ptr:
    lda 0,x
    cmp #SHELL_CMD_NONE
    beq shell_resp_none
    cmp #SHELL_CMD_HELP
    beq shell_resp_help
    cmp #SHELL_CMD_MD
    beq shell_resp_md
    cmp #SHELL_CMD_RD
    beq shell_resp_rd
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
    cmp #SHELL_CMD_ECHO
    beq shell_resp_echo
    cmp #SHELL_CMD_VER
    beq shell_resp_ver
    cmp #SHELL_CMD_VOL
    beq shell_resp_vol
    cmp #SHELL_CMD_MEM
    beq shell_resp_mem
    cmp #SHELL_CMD_DRIVE_ERR
    beq shell_resp_drive_err
    lda #<resp_unknown
    sta 0,x
    lda #>resp_unknown
    sta 1,x
    rts
shell_resp_none:
    lda #<resp_empty
    sta 0,x
    lda #>resp_empty
    sta 1,x
    rts
shell_resp_help:
    lda #<resp_help
    sta 0,x
    lda #>resp_help
    sta 1,x
    rts
shell_resp_md:
    jsr build_md_response
    rts
shell_resp_rd:
    jsr build_rd_response
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
shell_resp_echo:
    jsr build_echo_response
    rts
shell_resp_ver:
    jsr build_ver_response
    rts
shell_resp_vol:
    jsr build_vol_response
    rts
shell_resp_mem:
    jsr build_mem_response
    rts
shell_resp_drive_err:
    lda #<resp_drive_not_present
    sta 0,x
    lda #>resp_drive_not_present
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
    cmp #ASCII_ASTERISK
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
    cmp #CMD_M
    beq token_len2_md
    cmp #CMD_R
    beq token_len2_rd
    cmp #$01
    beq token_len2_drive
    cmp #$02
    beq token_len2_drive
    cmp #$03
    beq token_len2_c
    cmp #$04
    beq token_len2_drive_missing
    jmp token_unknown
token_len2_c:
    iny
    lda line_buffer,y
    cmp #ASCII_COLON
    beq token_len2_drive_missing_ok
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
token_len2_drive_missing:
    iny
    lda line_buffer,y
    cmp #ASCII_COLON
    beq :+
    jmp token_unknown
:
token_len2_drive_missing_ok:
    lda #SHELL_CMD_DRIVE_ERR
    rts
token_len2_md:
    iny
    lda line_buffer,y
    cmp #CMD_D
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_MD
    rts
token_len2_rd:
    iny
    lda line_buffer,y
    cmp #CMD_D
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_RD
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
    bne token_len4_echo
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
token_len4_echo:
    ldy parse_cmd_start
    lda line_buffer,y
    cmp #CMD_E
    bne token_len4_type
    iny
    lda line_buffer,y
    cmp #CMD_C
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_H
    beq :+
    jmp token_unknown
:
    iny
    lda line_buffer,y
    cmp #CMD_O
    beq :+
    jmp token_unknown
:
    lda #SHELL_CMD_ECHO
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
    bne token_unknown
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
    jsr uci_probe
    bcs mount_build_apply
    jsr mount_disk_hw
    bcc mount_build_apply
    cmp #MOUNT_STATUS_NOTDISK
    beq mount_build_notdisk
    cmp #MOUNT_STATUS_DRIVE
    beq mount_build_drive
    ldx saved_rp_x
    lda #<resp_mount_failed
    sta 0,x
    lda #>resp_mount_failed
    sta 1,x
    rts
mount_build_notdisk:
    ldx saved_rp_x
    lda #<resp_not_disk_image
    sta 0,x
    lda #>resp_not_disk_image
    sta 1,x
    rts
mount_build_drive:
    ldx saved_rp_x
    lda #<resp_drive_not_present
    sta 0,x
    lda #>resp_drive_not_present
    sta 1,x
    rts
mount_build_apply:
    ldy temp_drive
    lda temp_mount_kind
    sta mount_kind_table,y
    jsr kind_to_flags
    sta mount_flag_table,y
    lda #DIR_ID_ROOT
    sta dir_state_table,y
    jsr install_mounted_image
    jsr install_mount_path
    jsr install_volume_label_from_mount
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
    beq copy_source_classify
    cmp #PATH_STATUS_FLAT
    bne copy_source_not_flat
    jmp copy_build_flat
copy_source_not_flat:
    cmp #PATH_STATUS_UNMOUNTED
    bne copy_source_not_unmounted
    jmp copy_build_unmounted
copy_source_not_unmounted:
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
copy_source_classify:
    jsr classify_path_name_wildcard
    bcc :+
    jmp copy_build_bad
:
    lda temp_drive
    sta source_drive
    lda temp_dir_id
    sta source_dir_id
    lda wildcard_mode
    beq :+
    jmp copy_source_wild
:
    jsr copy_path_name_to_source_buffer
copy_source_hw:
    jsr uci_probe
    bcc copy_source_hw_uci
    jsr vice_probe_available
    bcc copy_source_vice
    jmp copy_source_lookup

copy_source_hw_uci:
    jsr load_copy_dest_arg
    jsr resolve_copy_dest
    cmp #PATH_STATUS_OK
    bne :+
    jmp copy_hw_target_ready
:
    cmp #PATH_STATUS_FLAT
    bne copy_hw_not_flat
    jmp copy_build_flat
copy_hw_not_flat:
    cmp #PATH_STATUS_UNMOUNTED
    bne copy_hw_not_unmounted
    jmp copy_build_unmounted
copy_hw_not_unmounted:
    cmp #PATH_STATUS_BAD
    bne copy_hw_not_bad
    jmp copy_build_bad
copy_hw_not_bad:
    ldx saved_rp_x
    lda #<resp_read_only
    sta 0,x
    lda #>resp_read_only
    sta 1,x
    rts
copy_source_wild:
    jsr copy_path_name_to_program_target
    jsr uci_probe
    bcc copy_source_wild_hw_uci
    jsr vice_probe_available
    bcs :+
    jmp copy_source_wild_vice
:
    jmp copy_source_wild_lookup

copy_source_vice:
    jsr load_copy_dest_arg
    jsr resolve_copy_dest
    cmp #PATH_STATUS_OK
    beq copy_vice_target_ready
    cmp #PATH_STATUS_FLAT
    bne copy_vice_not_flat
    jmp copy_build_flat
copy_vice_not_flat:
    cmp #PATH_STATUS_UNMOUNTED
    bne copy_vice_not_unmounted
    jmp copy_build_unmounted
copy_vice_not_unmounted:
    cmp #PATH_STATUS_BAD
    bne copy_vice_not_bad
    jmp copy_build_bad
copy_vice_not_bad:
    ldx saved_rp_x
    lda #<resp_read_only
    sta 0,x
    lda #>resp_read_only
    sta 1,x
    rts
copy_vice_target_ready:
    jsr copy_file_vice
    bcs :+
    jmp copy_build_ok
:
    ldx saved_rp_x
    lda #<resp_copy_failed
    sta 0,x
    lda #>resp_copy_failed
    sta 1,x
    rts

copy_source_wild_hw_uci:
    jsr load_copy_dest_arg
    jsr resolve_arg_target
    cmp #PATH_STATUS_OK
    beq copy_wild_hw_dest_ok
    cmp #PATH_STATUS_FLAT
    bne copy_wild_hw_not_flat
    jmp copy_build_flat
copy_wild_hw_not_flat:
    cmp #PATH_STATUS_UNMOUNTED
    bne copy_wild_hw_not_unmounted
    jmp copy_build_unmounted
copy_wild_hw_not_unmounted:
    jmp copy_build_bad
copy_wild_hw_dest_ok:
    lda temp_drive
    sta dest_drive
    lda temp_dir_id
    sta dest_dir_id
    jsr copy_matching_files_hw
    bcs :+
    jmp copy_build_ok
:
    cmp #WILDCARD_RESULT_NOMATCH
    bne :+
    jmp copy_build_bad_file
:
    ldx saved_rp_x
    lda #<resp_copy_failed
    sta 0,x
    lda #>resp_copy_failed
    sta 1,x
    rts
copy_source_wild_vice:
    jsr load_copy_dest_arg
    jsr resolve_arg_target
    cmp #PATH_STATUS_OK
    beq copy_wild_vice_dest_ok
    cmp #PATH_STATUS_FLAT
    bne copy_wild_vice_not_flat
    jmp copy_build_flat
copy_wild_vice_not_flat:
    cmp #PATH_STATUS_UNMOUNTED
    bne copy_wild_vice_not_unmounted
    jmp copy_build_unmounted
copy_wild_vice_not_unmounted:
    jmp copy_build_bad
copy_wild_vice_dest_ok:
    lda temp_drive
    sta dest_drive
    lda temp_dir_id
    sta dest_dir_id
    jsr copy_matching_files_vice
    bcs :+
    jmp copy_build_ok
:
    cmp #WILDCARD_RESULT_NOMATCH
    bne :+
    jmp copy_build_bad_file
:
    ldx saved_rp_x
    lda #<resp_copy_failed
    sta 0,x
    lda #>resp_copy_failed
    sta 1,x
    rts
copy_hw_target_ready:
    jsr copy_file_hw
    bcs :+
    jmp copy_build_ok
:
    ldx saved_rp_x
    lda #<resp_copy_failed
    sta 0,x
    lda #>resp_copy_failed
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
    bne :+
    lda temp_dir_id
    cmp #DIR_ID_WORK
    beq copy_store_target
    jmp copy_build_read_only
:
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
copy_source_wild_lookup:
    jsr load_copy_dest_arg
    jsr resolve_arg_target
    cmp #PATH_STATUS_OK
    beq copy_wild_lookup_dest_ok
    cmp #PATH_STATUS_FLAT
    beq copy_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq copy_build_unmounted
    jmp copy_build_bad
copy_wild_lookup_dest_ok:
    lda temp_dir_id
    cmp #DIR_ID_WORK
    bne copy_build_read_only
    lda temp_drive
    sta dest_drive
    lda temp_dir_id
    sta dest_dir_id
    jsr copy_matching_work_files
    bcc copy_build_ok
    cmp #WILDCARD_RESULT_NOMATCH
    beq copy_build_bad_file
    cmp #WILDCARD_RESULT_NOSPACE
    beq copy_build_no_space
    ldx saved_rp_x
    lda #<resp_copy_failed
    sta 0,x
    lda #>resp_copy_failed
    sta 1,x
    rts
copy_store_target:
    jsr store_copy_to_work
    bcc copy_build_ok
copy_build_no_space:
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
copy_build_bad_file:
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
copy_build_read_only:
    ldx saved_rp_x
    lda #<resp_read_only
    sta 0,x
    lda #>resp_read_only
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
    beq ren_source_hw
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
ren_source_hw:
    jsr uci_probe
    bcc ren_source_hw_uci
    jsr vice_probe_available
    bcc ren_source_vice
    jmp ren_source_lookup
ren_source_hw_uci:
    lda temp_drive
    sta source_drive
    lda temp_dir_id
    sta source_dir_id
    jsr copy_path_name_to_source_buffer
    jsr load_copy_dest_arg
    jsr resolve_copy_dest
    cmp #PATH_STATUS_OK
    beq ren_hw_dest_ready
    cmp #PATH_STATUS_FLAT
    bne ren_hw_not_flat
    jmp ren_build_flat
ren_hw_not_flat:
    cmp #PATH_STATUS_UNMOUNTED
    bne ren_hw_not_unmounted
    jmp ren_build_unmounted
ren_hw_not_unmounted:
    cmp #PATH_STATUS_BAD
    bne ren_hw_not_bad
    jmp ren_build_bad
ren_hw_not_bad:
    jmp ren_build_read_only
ren_hw_dest_ready:
    lda temp_drive
    cmp source_drive
    beq ren_hw_same_drive
    jmp ren_build_bad
ren_hw_same_drive:
    lda temp_dir_id
    cmp source_dir_id
    beq ren_hw_same_dir
    jmp ren_build_bad
ren_hw_same_dir:
    jsr rename_file_hw
    bcs ren_hw_fail
    jmp ren_build_done
ren_hw_fail:
    cmp #RENAME_STATUS_EXISTS
    bne :+
    ldx saved_rp_x
    lda #<resp_exists
    sta 0,x
    lda #>resp_exists
    sta 1,x
    rts
:
    ldx saved_rp_x
    lda #<resp_rename_failed
    sta 0,x
    lda #>resp_rename_failed
    sta 1,x
    rts
ren_source_vice:
    lda temp_drive
    sta source_drive
    lda temp_dir_id
    sta source_dir_id
    jsr copy_path_name_to_source_buffer
    jsr load_copy_dest_arg
    jsr resolve_copy_dest
    cmp #PATH_STATUS_OK
    beq ren_vice_dest_ready
    cmp #PATH_STATUS_FLAT
    bne ren_vice_not_flat
    jmp ren_build_flat
ren_vice_not_flat:
    cmp #PATH_STATUS_UNMOUNTED
    bne ren_vice_not_unmounted
    jmp ren_build_unmounted
ren_vice_not_unmounted:
    cmp #PATH_STATUS_BAD
    bne ren_vice_not_bad
    jmp ren_build_bad
ren_vice_not_bad:
    jmp ren_build_read_only
ren_vice_dest_ready:
    lda temp_drive
    cmp source_drive
    beq :+
    jmp ren_build_bad
:
    lda temp_dir_id
    cmp source_dir_id
    beq :+
    jmp ren_build_bad
:
    jsr rename_file_vice
    bcs ren_vice_fail
    jmp ren_build_done
ren_vice_fail:
    cmp #RENAME_STATUS_EXISTS
    bne :+
    ldx saved_rp_x
    lda #<resp_exists
    sta 0,x
    lda #>resp_exists
    sta 1,x
    rts
:
    ldx saved_rp_x
    lda #<resp_rename_failed
    sta 0,x
    lda #>resp_rename_failed
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
    lda temp_dir_id
    cmp #DIR_ID_WORK
    bne ren_build_read_only
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
ren_build_done:
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
    beq del_source_ready
    cmp #PATH_STATUS_FLAT
    bne :+
    jmp del_build_flat
:
    cmp #PATH_STATUS_UNMOUNTED
    bne :+
    jmp del_build_unmounted
:
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
del_source_ready:
    jsr classify_path_name_wildcard
    bcc :+
    jmp del_build_bad_file
:
    lda wildcard_mode
    bne del_source_wild
del_source_exact:
    jsr uci_probe
    bcc del_source_exact_hw
    jsr vice_probe_available
    bcc del_source_exact_vice
    jmp del_source_lookup
del_source_exact_hw:
    jsr delete_file_hw
    bcc del_build_deleted
    ldx saved_rp_x
    lda #<resp_delete_failed
    sta 0,x
    lda #>resp_delete_failed
    sta 1,x
    rts
del_source_exact_vice:
    jsr delete_file_vice
    bcc del_build_deleted
    ldx saved_rp_x
    lda #<resp_delete_failed
    sta 0,x
    lda #>resp_delete_failed
    sta 1,x
    rts
del_source_wild:
    jsr copy_path_name_to_source_buffer
    jsr uci_probe
    bcc del_source_wild_hw
    jsr vice_probe_available
    bcc del_source_wild_vice
    jmp del_source_wild_lookup
del_source_wild_hw:
    jsr delete_matching_files_hw
    bcc del_build_deleted
    lda wildcard_match_count
    beq del_build_bad_file
    ldx saved_rp_x
    lda #<resp_delete_failed
    sta 0,x
    lda #>resp_delete_failed
    sta 1,x
    rts
del_source_wild_vice:
    jsr delete_matching_files_vice
    bcc del_build_deleted
    lda wildcard_match_count
    beq del_build_bad_file
    ldx saved_rp_x
    lda #<resp_delete_failed
    sta 0,x
    lda #>resp_delete_failed
    sta 1,x
    rts
del_source_lookup:
    lda wildcard_mode
    bne del_source_wild_lookup
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
del_build_deleted:
    ldx saved_rp_x
    lda #<resp_deleted
    sta 0,x
    lda #>resp_deleted
    sta 1,x
    rts
del_source_wild_lookup:
    lda temp_dir_id
    cmp #DIR_ID_WORK
    beq :+
    jmp del_build_read_only
:
    jsr delete_matching_work_files
    bcc del_build_deleted
del_build_bad_file:
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
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

build_md_response:
    stx saved_rp_x
    lda arg_length
    bne :+
    jmp md_build_bad
:
    jsr resolve_copy_dest
    cmp #PATH_STATUS_OK
    beq md_build_ready
    cmp #PATH_STATUS_FLAT
    beq md_build_flat
    cmp #PATH_STATUS_UNMOUNTED
    beq md_build_unmounted
    jmp md_build_bad
md_build_ready:
    jsr uci_probe
    bcc md_build_read_only
    jsr vice_probe_available
    bcc md_build_vice
    jmp md_build_read_only
md_build_vice:
    jsr fill_vice_manifest_dir_cache_current
    bcs md_build_fail
    jsr find_hw_dir_cache_matching_path_name
    bcc md_build_exists
    jsr find_hw_dir_cache_matching_dir_path_name
    bcc md_build_exists
    jsr create_dir_vice_current
    bcc md_build_created
md_build_fail:
    ldx saved_rp_x
    lda #<resp_mkdir_failed
    sta 0,x
    lda #>resp_mkdir_failed
    sta 1,x
    rts
md_build_exists:
    ldx saved_rp_x
    lda #<resp_exists
    sta 0,x
    lda #>resp_exists
    sta 1,x
    rts
md_build_created:
    ldx saved_rp_x
    lda #<resp_created
    sta 0,x
    lda #>resp_created
    sta 1,x
    rts
md_build_flat:
    ldx saved_rp_x
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
md_build_unmounted:
    ldx saved_rp_x
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
md_build_read_only:
    ldx saved_rp_x
    lda #<resp_read_only
    sta 0,x
    lda #>resp_read_only
    sta 1,x
    rts
md_build_bad:
    ldx saved_rp_x
    lda #<resp_bad_md
    sta 0,x
    lda #>resp_bad_md
    sta 1,x
    rts

build_rd_response:
    stx saved_rp_x
    lda arg_length
    bne :+
    jmp rd_build_bad
:
    jsr resolve_copy_dest
    cmp #PATH_STATUS_OK
    beq rd_build_ready
    cmp #PATH_STATUS_FLAT
    bne :+
    jmp rd_build_flat
:
    cmp #PATH_STATUS_UNMOUNTED
    bne :+
    jmp rd_build_unmounted
:
    jmp rd_build_bad
rd_build_ready:
    lda temp_drive
    sta source_drive
    lda temp_dir_id
    sta source_dir_id
    jsr uci_probe
    bcs :+
    jmp rd_build_read_only
:
    jsr vice_probe_available
    bcc rd_build_vice
    jmp rd_build_read_only
rd_build_vice:
    jsr lookup_dir_target_current_vice
    bcs rd_build_no_such_dir
    sta dest_dir_id
    lda source_drive
    cmp current_drive
    bne rd_build_not_busy
    tay
    lda dir_state_table,y
    cmp dest_dir_id
    bne rd_build_not_busy
    ldx saved_rp_x
    lda #<resp_dir_busy
    sta 0,x
    lda #>resp_dir_busy
    sta 1,x
    rts
rd_build_not_busy:
    lda dest_dir_id
    sta temp_dir_id
    jsr fill_vice_manifest_dir_cache_current
    bcs rd_build_fail
    lda enum_count
    beq rd_build_empty
    ldx saved_rp_x
    lda #<resp_dir_not_empty
    sta 0,x
    lda #>resp_dir_not_empty
    sta 1,x
    rts
rd_build_empty:
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr store_vice_dir_tombstone_current
    bcs rd_build_fail
    ldx saved_rp_x
    lda #<resp_removed
    sta 0,x
    lda #>resp_removed
    sta 1,x
    rts
rd_build_no_such_dir:
    ldx saved_rp_x
    lda #<resp_bad_dir
    sta 0,x
    lda #>resp_bad_dir
    sta 1,x
    rts
rd_build_fail:
    ldx saved_rp_x
    lda #<resp_rmdir_failed
    sta 0,x
    lda #>resp_rmdir_failed
    sta 1,x
    rts
rd_build_flat:
    ldx saved_rp_x
    lda #<resp_flat_image
    sta 0,x
    lda #>resp_flat_image
    sta 1,x
    rts
rd_build_unmounted:
    ldx saved_rp_x
    lda #<resp_unmounted
    sta 0,x
    lda #>resp_unmounted
    sta 1,x
    rts
rd_build_read_only:
    ldx saved_rp_x
    lda #<resp_read_only
    sta 0,x
    lda #>resp_read_only
    sta 1,x
    rts
rd_build_bad:
    ldx saved_rp_x
    lda #<resp_bad_rd
    sta 0,x
    lda #>resp_bad_rd
    sta 1,x
    rts

create_dir_vice_current:
    jsr vice_dir_find_current_slot
    bcc create_dir_vice_current_found
    jsr vice_dir_alloc_slot
    bcs create_dir_vice_current_fail
create_dir_vice_current_store:
    lda temp_dir_id
    jsr store_vice_dir_parent_for_index
    jsr select_vice_dir_name_slot
    jsr copy_path_name_to_vice_dir_slot_ascii
    lda #VICE_DIR_SLOT_LIVE
    jsr store_vice_dir_state_for_index
    clc
    rts
create_dir_vice_current_found:
    cmp #VICE_DIR_SLOT_TOMBSTONE
    beq create_dir_vice_current_store
create_dir_vice_current_fail:
    sec
    rts

lookup_dir_target_current_vice:
    jsr fill_vice_manifest_dir_cache_current
    bcs lookup_dir_target_current_vice_fail
    jsr find_hw_dir_cache_matching_dir_path_name
    bcs lookup_dir_target_current_vice_fail
    lda temp_dir_id
    bne lookup_dir_target_current_vice_dynamic
    jsr match_fixed_root_path_name
    bcc lookup_dir_target_current_vice_ok
lookup_dir_target_current_vice_dynamic:
    jsr ensure_dynamic_dir_current_from_path_name
    bcs lookup_dir_target_current_vice_fail
lookup_dir_target_current_vice_ok:
    clc
    rts
lookup_dir_target_current_vice_fail:
    sec
    rts

store_vice_dir_tombstone_current:
    jsr vice_dir_find_current_slot
    bcc store_vice_dir_tombstone_current_have_slot
    jsr vice_dir_alloc_slot
    bcs store_vice_dir_tombstone_current_fail
store_vice_dir_tombstone_current_have_slot:
    lda temp_dir_id
    jsr store_vice_dir_parent_for_index
    jsr select_vice_dir_name_slot
    jsr copy_path_name_to_vice_dir_slot_ascii
    lda #VICE_DIR_SLOT_TOMBSTONE
    jsr store_vice_dir_state_for_index
    clc
    rts
store_vice_dir_tombstone_current_fail:
    sec
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
    sta batch_mode
    sta script_abort_on_error
    lda current_drive
    sta PROGRAM_DRIVE_SNAPSHOT
    tay
    lda dir_state_table,y
    sta PROGRAM_DIR_SNAPSHOT
    lda #$00
    sta PROGRAM_IMAGE_LEN_LO_SNAPSHOT
    sta PROGRAM_IMAGE_LEN_HI_SNAPSHOT
    sta program_image_len_lo
    sta program_image_len_hi
    sta program_target_lo
    sta program_target_hi
    sta program_target_buffer
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
    lda run_explicit_batch
    bne program_lookup_batch
    jsr uci_probe
    bcc program_lookup_hw
    jsr vice_probe_available
    bcs program_lookup_mock
    jsr current_mount_path_is_empty
    bcs program_lookup_mock
    jsr query_program_file_vice_current
    bcc :+
    jmp program_try_batch_fallback
:
    jsr load_program_image_vice_current
    bcc :+
    cmp #RUN_STATUS_NOFILE
    beq program_try_batch_fallback
    jmp program_status_return
:
    jmp program_ready
program_lookup_hw:
    jsr query_program_file_hw
    bcc :+
    cmp #RUN_STATUS_NOFILE
    beq program_try_batch_fallback
    jmp program_status_return
:
    jsr load_program_image_hw
    bcc :+
    cmp #RUN_STATUS_NOFILE
    beq program_try_batch_fallback
    jmp program_status_return
:
    jmp program_ready
program_lookup_mock:
    jsr lookup_file_content_strict
    bcc program_load_mock
    jmp program_try_batch_fallback
program_load_mock:
    jsr load_program_image_mock
    bcc program_ready
    jmp program_status_return
program_lookup_batch:
    jsr uci_probe
    bcc program_lookup_batch_hw
    jsr vice_probe_available
    bcs program_lookup_batch_mock
    jsr current_mount_path_is_empty
    bcs program_lookup_batch_mock
    jsr query_program_file_vice_current
    bcc :+
    lda #RUN_STATUS_NOFILE
    jmp program_status_return
:
    jsr load_program_image_vice_current
    bcc program_ready_batch
    jmp program_status_return
program_lookup_batch_hw:
    jsr query_program_file_hw
    bcc :+
    jmp program_status_return
:
    jsr load_program_image_hw
    bcc program_ready_batch
    jmp program_status_return
program_lookup_batch_mock:
    jsr lookup_file_content_strict
    bcc program_load_batch_mock
    lda #RUN_STATUS_NOFILE
    jmp program_status_return
program_load_batch_mock:
    jsr load_program_image_mock
    bcc program_ready_batch
    jmp program_status_return
program_try_batch_fallback:
    lda run_batch_fallback
    beq program_status_nofile
    jsr set_run_target_bat_extension
    bcc :+
    lda #RUN_STATUS_BAD
    jmp program_status_return
:
    jsr resolve_file_target
    cmp #PATH_STATUS_OK
    beq program_lookup_batch
    cmp #PATH_STATUS_UNMOUNTED
    bne :+
    jmp program_status_unmounted
:
    lda #RUN_STATUS_NOFILE
    jmp program_status_return
program_status_nofile:
    lda #RUN_STATUS_NOFILE
    jmp program_status_return
program_ready:
    jsr copy_path_name_to_program_target
    lda #<program_target_buffer
    sta program_target_lo
    lda #>program_target_buffer
    sta program_target_hi
    lda temp_drive
    sta PROGRAM_DRIVE_SNAPSHOT
    lda temp_dir_id
    sta PROGRAM_DIR_SNAPSHOT
    lda #PROGRAM_STATE_RUNNING
    sta PROGRAM_STATE_SNAPSHOT
    lda #RUN_STATUS_OK
    jmp program_status_return
program_ready_batch:
    jsr install_batch_args
    jsr load_batch_script_from_program_image
    bcc :+
    jmp program_status_return
:
    lda #PROGRAM_STATE_EXITED
    sta PROGRAM_STATE_SNAPSHOT
    lda #$00
    sta PROGRAM_EXIT_SNAPSHOT
    lda temp_drive
    sta PROGRAM_DRIVE_SNAPSHOT
    lda temp_dir_id
    sta PROGRAM_DIR_SNAPSHOT
    lda #RUN_STATUS_BATCH
program_status_return:
    sta program_status
    ldx saved_rp_x
    sta 0,x
    lda #$00
    sta 1,x
    rts

ensure_run_target_extension:
    lda #$00
    sta run_batch_fallback
    sta run_explicit_batch
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
    bne ensure_run_target_check_explicit
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
    lda #$01
    sta run_batch_fallback
    jmp ensure_run_target_ok
ensure_run_target_check_explicit:
    ldy parse_scan_index
    lda arg_buffer,y
    cmp #ASCII_DOT
    bne ensure_run_target_ok
    iny
    cpy arg_length
    bcs ensure_run_target_ok
    lda arg_buffer,y
    cmp #CMD_B
    bne ensure_run_target_ok
    iny
    cpy arg_length
    bcs ensure_run_target_ok
    lda arg_buffer,y
    cmp #$01
    bne ensure_run_target_ok
    iny
    cpy arg_length
    bcs ensure_run_target_ok
    lda arg_buffer,y
    cmp #CMD_T
    bne ensure_run_target_ok
    iny
    cpy arg_length
    bne ensure_run_target_ok
    lda #$01
    sta run_explicit_batch
ensure_run_target_ok:
    clc
    rts
ensure_run_target_fail:
    sec
    rts

set_run_target_bat_extension:
    ldy arg_length
    cpy #4
    bcc set_run_target_bat_extension_fail
    dey
    lda #CMD_T
    sta arg_buffer,y
    dey
    lda #$01
    sta arg_buffer,y
    dey
    lda #CMD_B
    sta arg_buffer,y
    lda #$00
    sta run_batch_fallback
    lda #$01
    sta run_explicit_batch
    clc
    rts
set_run_target_bat_extension_fail:
    sec
    rts

clear_batch_args:
    lda #$00
    sta batch_arg1_buffer
    sta batch_arg2_buffer
    sta batch_arg3_buffer
    rts

install_batch_args:
    jsr clear_batch_args
    ldx #$00
    ldy #$00
install_batch_args_skip_gap:
    cpy program_cmdline_len
    bcs install_batch_args_done
    lda program_cmdline_buffer,y
    cmp #ASCII_SPACE
    beq install_batch_args_skip_next
    cmp #ASCII_COMMA
    beq install_batch_args_skip_next
    cpx #$00
    beq install_batch_args_arg1
    cpx #$01
    beq install_batch_args_arg2
    cpx #$02
    beq install_batch_args_arg3
    rts
install_batch_args_skip_next:
    iny
    bne install_batch_args_skip_gap
install_batch_args_arg1:
    lda #<batch_arg1_buffer
    sta PTR
    lda #>batch_arg1_buffer
    sta PTR+1
    txa
    pha
    jsr copy_batch_arg_token
    pla
    tax
    inx
    jmp install_batch_args_skip_gap
install_batch_args_arg2:
    lda #<batch_arg2_buffer
    sta PTR
    lda #>batch_arg2_buffer
    sta PTR+1
    txa
    pha
    jsr copy_batch_arg_token
    pla
    tax
    inx
    jmp install_batch_args_skip_gap
install_batch_args_arg3:
    lda #<batch_arg3_buffer
    sta PTR
    lda #>batch_arg3_buffer
    sta PTR+1
    txa
    pha
    jsr copy_batch_arg_token
    pla
    tax
install_batch_args_done:
    rts

copy_batch_arg_token:
    lda #$00
    sta file_index
copy_batch_arg_token_loop:
    cpy program_cmdline_len
    bcs copy_batch_arg_token_done
    lda program_cmdline_buffer,y
    cmp #ASCII_SPACE
    beq copy_batch_arg_token_done
    cmp #ASCII_COMMA
    beq copy_batch_arg_token_done
    ldx file_index
    cpx #MAX_LINE_LEN
    bcs copy_batch_arg_token_done
    jsr store_a_at_ptr_plus_x_preserve_y
    ldx file_index
    inx
    stx file_index
    iny
    bne copy_batch_arg_token_loop
copy_batch_arg_token_done:
    ldx file_index
    lda #$00
    jsr store_a_at_ptr_plus_x_preserve_y
    rts

store_a_at_ptr_plus_x_preserve_y:
    sty saved_response_y
    pha
    txa
    clc
    adc PTR
    sta SCREEN_PTR
    lda PTR+1
    adc #$00
    sta SCREEN_PTR+1
    pla
    ldy #$00
    sta (SCREEN_PTR),y
    ldy saved_response_y
    rts

load_batch_script_from_program_image:
    lda #$00
    sta script_index
    sta script_line_count
    ldy #$00
load_batch_script_next_line:
    cpy program_image_len_lo
    bcs load_batch_script_done
    lda script_line_count
    cmp #SCRIPT_LINE_MAX
    bcs load_batch_script_too_large
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
    lda #$00
    sta file_index
load_batch_script_copy:
    cpy program_image_len_lo
    bcs load_batch_script_finish_line
    lda program_image_buffer,y
    cmp #$0D
    beq load_batch_script_cr
    cmp #$0A
    beq load_batch_script_lf
    ldx file_index
    cpx #MAX_LINE_LEN
    bcs load_batch_script_too_large
    jsr store_a_at_ptr_plus_x_preserve_y
    ldx file_index
    inx
    stx file_index
    iny
    bne load_batch_script_copy
load_batch_script_cr:
    iny
    cpy program_image_len_lo
    bcs load_batch_script_finish_line
    lda program_image_buffer,y
    cmp #$0A
    bne load_batch_script_finish_line
    iny
    bne load_batch_script_finish_line
load_batch_script_lf:
    iny
load_batch_script_finish_line:
    ldx file_index
    lda #$00
    jsr store_a_at_ptr_plus_x_preserve_y
    inc script_line_count
    jmp load_batch_script_next_line
load_batch_script_too_large:
    lda #RUN_STATUS_TOO_LARGE
    sec
    rts
load_batch_script_done:
    lda #$00
    sta script_index
    sta command_status
    lda #INPUT_MODE_SCRIPT
    sta input_mode
    lda #$01
    sta batch_mode
    sta script_abort_on_error
    lda #RUN_STATUS_BATCH
    clc
    rts

load_program_image_mock:
    jsr copy_ptr_to_program_image
    bcc load_program_image_mock_ok
    lda #RUN_STATUS_TOO_LARGE
    sec
    rts
load_program_image_mock_ok:
    jsr snapshot_program_image_length
    lda #RUN_STATUS_OK
    clc
    rts

query_program_file_hw:
    jsr current_mount_is_flat
    beq query_program_file_hw_flat
    jsr sync_drive_backend_path_hw
    bcs query_program_file_hw_fail
    jsr build_uci_file_stat_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_data_status
    bcs query_program_file_hw_fail
    jsr uci_status_is_ok
    bcc query_program_file_hw_have_stat
    jsr uci_status_is_file_not_found
    bcc query_program_file_hw_missing
query_program_file_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    lda #RUN_STATUS_LOAD_FAILED
    sec
    rts
query_program_file_hw_missing:
    lda #RUN_STATUS_NOFILE
    sec
    rts
query_program_file_hw_have_stat:
    lda uci_data_length
    cmp #4
    bcc query_program_file_hw_fail
    lda uci_data_buffer+1
    ora uci_data_buffer+2
    ora uci_data_buffer+3
    beq query_program_file_hw_ok
    lda #RUN_STATUS_TOO_LARGE
    sec
    rts
query_program_file_hw_ok:
    lda #RUN_STATUS_OK
    clc
    rts

query_program_file_hw_flat:
    jsr open_flat_mount_image_hw
    bcs query_program_file_hw_fail
    jsr find_flat_file_entry_in_open_image
    php
    pha
    jsr close_current_file_hw
    pla
    plp
    bcc query_program_file_hw_ok
    cmp #FLAT_LOOKUP_NOFILE
    beq query_program_file_hw_missing
    jmp query_program_file_hw_fail

load_program_image_hw:
    jsr current_mount_is_flat
    beq load_program_image_hw_flat
    jsr sync_drive_backend_path_hw
    bcs load_program_image_hw_fail
    jsr build_uci_open_read_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs load_program_image_hw_fail
    jsr uci_status_is_ok
    bcs load_program_image_hw_fail
    jsr uci_read_open_file_into_program_image
    bcc load_program_image_hw_close
    pha
    jsr close_current_file_hw
    pla
    sec
    rts
load_program_image_hw_close:
    jsr close_current_file_hw
    bcc load_program_image_hw_ok
load_program_image_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    lda #RUN_STATUS_LOAD_FAILED
    sec
    rts
load_program_image_hw_ok:
    jsr snapshot_program_image_length
    lda #RUN_STATUS_OK
    clc
    rts

load_program_image_hw_flat:
    jsr open_flat_mount_image_hw
    bcs load_program_image_hw_fail
    jsr find_flat_file_entry_in_open_image
    bcs load_program_image_hw_flat_close
    jsr load_flat_program_image_open_hw
load_program_image_hw_flat_close:
    php
    pha
    jsr close_current_file_hw
    pla
    plp
    bcc load_program_image_hw_ok
    cmp #RUN_STATUS_TOO_LARGE
    beq load_program_image_hw_fail_direct
    jmp load_program_image_hw_fail
load_program_image_hw_fail_direct:
    sec
    rts

uci_read_open_file_into_program_image:
    jsr build_uci_target_header
    lda #DOS_CMD_READ_DATA
    sta uci_cmd_buffer+1
    lda #<PROGRAM_IMAGE_MAX
    sta uci_cmd_buffer+2
    lda #>PROGRAM_IMAGE_MAX
    sta uci_cmd_buffer+3
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    lda #4
    jsr uci_push_command
    bcs uci_read_open_file_into_program_image_fail
    jsr uci_wait_reply
    bcs uci_read_open_file_into_program_image_fail
    lda #<program_image_buffer
    sta PTR
    lda #>program_image_buffer
    sta PTR+1
    lda #PROGRAM_IMAGE_MAX
    jsr uci_read_data_block
    sta program_image_len_lo
    lda #$00
    sta program_image_len_hi
    bcc uci_read_open_file_into_program_image_status
    lda UCI_STATUS_REG
    and #UCI_STATUS_DATA_AV
    bne uci_read_open_file_into_program_image_large
uci_read_open_file_into_program_image_status:
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
    jsr uci_status_is_ok_or_empty
    bcs uci_read_open_file_into_program_image_fail
    lda #RUN_STATUS_OK
    clc
    rts
uci_read_open_file_into_program_image_large:
    jsr uci_abort_transfer
    jsr uci_clear_error
    lda #RUN_STATUS_TOO_LARGE
    sec
    rts
uci_read_open_file_into_program_image_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    lda #RUN_STATUS_LOAD_FAILED
    sec
    rts

copy_ptr_to_program_image:
    ldy #$00
copy_ptr_to_program_image_loop:
    cpy #PROGRAM_IMAGE_MAX
    bcs copy_ptr_to_program_image_fail
    lda (PTR),y
    beq copy_ptr_to_program_image_done
    sta program_image_buffer,y
    iny
    bne copy_ptr_to_program_image_loop
copy_ptr_to_program_image_done:
    sty program_image_len_lo
    lda #$00
    sta program_image_len_hi
    clc
    rts
copy_ptr_to_program_image_fail:
    lda #$00
    sta program_image_len_lo
    sta program_image_len_hi
    sec
    rts

copy_path_name_to_program_target:
    ldy #$00
copy_path_name_to_program_target_loop:
    lda path_name_buffer,y
    sta program_target_buffer,y
    beq copy_path_name_to_program_target_done
    iny
    cpy #MAX_LINE_LEN
    bcc copy_path_name_to_program_target_loop
copy_path_name_to_program_target_done:
    lda #$00
    sta program_target_buffer,y
    rts

snapshot_program_image_length:
    lda program_image_len_lo
    sta PROGRAM_IMAGE_LEN_LO_SNAPSHOT
    lda program_image_len_hi
    sta PROGRAM_IMAGE_LEN_HI_SNAPSHOT
    rts

svc_program_get_status:
    lda program_status
    sta 0,x
    lda #$00
    sta 1,x
    rts

svc_program_status_is_ok:
    lda #$00
    sta 0,x
    sta 1,x
    lda program_status
    cmp #RUN_STATUS_OK
    bne svc_program_status_is_ok_done
    lda #$01
    sta 0,x
svc_program_status_is_ok_done:
    rts

svc_program_status_is_batch:
    lda #$00
    sta 0,x
    sta 1,x
    lda program_status
    cmp #RUN_STATUS_BATCH
    bne svc_program_status_is_batch_done
    lda #$01
    sta 0,x
svc_program_status_is_batch_done:
    rts

svc_program_finish_prepare:
    lda program_status
    cmp #RUN_STATUS_BATCH
    beq svc_program_finish_prepare_batch
    cmp #RUN_STATUS_OK
    beq svc_program_finish_prepare_ok
    jsr svc_command_status_fail
    jsr svc_program_error_ptr
    jsr svc_console_write_sc0
    jmp svc_console_newline
svc_program_finish_prepare_batch:
    jmp svc_command_status_clear
svc_program_finish_prepare_ok:
    lda #$13
    sta STAGE_SNAPSHOT
    lda #<resp_run_prefix
    sta PTR
    lda #>resp_run_prefix
    sta PTR+1
    jsr svc_console_write_ptr
    lda program_target_lo
    sta PTR
    lda program_target_hi
    sta PTR+1
    jsr svc_console_write_ptr
    jsr svc_console_newline
    lda program_cmdline_len
    beq svc_program_finish_prepare_done
    lda #<resp_args_prefix
    sta PTR
    lda #>resp_args_prefix
    sta PTR+1
    jsr svc_console_write_ptr
    lda #<program_cmdline_buffer
    sta PTR
    lda #>program_cmdline_buffer
    sta PTR+1
    jsr svc_console_write_ptr
    jsr svc_console_newline
svc_program_finish_prepare_done:
    lda #$14
    sta STAGE_SNAPSHOT
    jsr svc_program_exit
    jmp svc_command_status_from_program_exit

svc_program_error_ptr:
    lda 0,x
    cmp #RUN_STATUS_FLAT
    beq program_error_flat
    cmp #RUN_STATUS_UNMOUNTED
    beq program_error_unmounted
    cmp #RUN_STATUS_NOFILE
    beq program_error_missing
    cmp #RUN_STATUS_TOO_LARGE
    beq program_error_too_large
    cmp #RUN_STATUS_LOAD_FAILED
    beq program_error_load_failed
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
program_error_too_large:
    lda #<resp_program_too_large
    sta 0,x
    lda #>resp_program_too_large
    sta 1,x
    rts
program_error_load_failed:
    lda #<resp_program_load_failed
    sta 0,x
    lda #>resp_program_load_failed
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

svc_program_get_image_ptr:
    lda #<program_image_buffer
    sta 0,x
    lda #>program_image_buffer
    sta 1,x
    rts

svc_program_get_image_len:
    lda program_image_len_lo
    sta 0,x
    lda program_image_len_hi
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

copy_path_name_to_source_buffer:
    ldy #$00
copy_path_name_to_source_buffer_loop:
    lda path_name_buffer,y
    sta source_name_buffer,y
    beq copy_path_name_to_source_buffer_done
    iny
    cpy #MAX_LINE_LEN
    bcc copy_path_name_to_source_buffer_loop
copy_path_name_to_source_buffer_done:
    lda #$00
    sta source_name_buffer,y
    rts

copy_source_name_to_path_buffer:
    ldy #$00
copy_source_name_to_path_buffer_loop:
    lda source_name_buffer,y
    sta path_name_buffer,y
    beq copy_source_name_to_path_buffer_done
    iny
    cpy #MAX_LINE_LEN
    bcc copy_source_name_to_path_buffer_loop
copy_source_name_to_path_buffer_done:
    lda #$00
    sta path_name_buffer,y
    rts

copy_path_name_to_copy_dst_buffer:
    ldy #$00
copy_path_name_to_copy_dst_buffer_loop:
    lda path_name_buffer,y
    sta copy_dst_buffer,y
    beq copy_path_name_to_copy_dst_buffer_done
    iny
    cpy #MAX_LINE_LEN
    bcc copy_path_name_to_copy_dst_buffer_loop
copy_path_name_to_copy_dst_buffer_done:
    lda #$00
    sta copy_dst_buffer,y
    rts

copy_copy_dst_to_path_buffer:
    ldy #$00
copy_copy_dst_to_path_buffer_loop:
    lda copy_dst_buffer,y
    sta path_name_buffer,y
    beq copy_copy_dst_to_path_buffer_done
    iny
    cpy #MAX_LINE_LEN
    bcc copy_copy_dst_to_path_buffer_loop
copy_copy_dst_to_path_buffer_done:
    lda #$00
    sta path_name_buffer,y
    rts

copy_program_target_to_source_buffer:
    ldy #$00
copy_program_target_to_source_buffer_loop:
    lda program_target_buffer,y
    sta source_name_buffer,y
    beq copy_program_target_to_source_buffer_done
    iny
    cpy #MAX_LINE_LEN
    bcc copy_program_target_to_source_buffer_loop
copy_program_target_to_source_buffer_done:
    lda #$00
    sta source_name_buffer,y
    rts

copy_ptr_name_to_source_buffer:
    ldy #$00
copy_ptr_name_to_source_buffer_loop:
    lda (PTR),y
    beq copy_ptr_name_to_source_buffer_done
    cmp #ASCII_SLASH
    beq copy_ptr_name_to_source_buffer_done
    cpy #MAX_LINE_LEN
    bcs copy_ptr_name_to_source_buffer_done
    jsr normalize_output_char
    sta source_name_buffer,y
    iny
    bne copy_ptr_name_to_source_buffer_loop
copy_ptr_name_to_source_buffer_done:
    lda #$00
    sta source_name_buffer,y
    rts

copy_ptr_name_to_path_buffer:
    ldy #$00
copy_ptr_name_to_path_buffer_loop:
    lda (PTR),y
    beq copy_ptr_name_to_path_buffer_done
    cmp #ASCII_SLASH
    beq copy_ptr_name_to_path_buffer_done
    cpy #MAX_LINE_LEN
    bcs copy_ptr_name_to_path_buffer_done
    jsr normalize_output_char
    sta path_name_buffer,y
    iny
    bne copy_ptr_name_to_path_buffer_loop
copy_ptr_name_to_path_buffer_done:
    lda #$00
    sta path_name_buffer,y
    rts

build_type_response:
    stx saved_rp_x
    jsr resolve_file_target
    cmp #PATH_STATUS_OK
    beq type_build_hw
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
type_build_hw:
    jsr uci_probe
    bcc type_build_uci
    jsr vice_probe_available
    bcs type_build_lookup
    jsr read_file_response_vice_current
    bcc type_build_found
    ldx saved_rp_x
    lda #<resp_bad_file
    sta 0,x
    lda #>resp_bad_file
    sta 1,x
    rts
type_build_uci:
    jsr read_file_response_hw
    bcc type_build_found
    jmp type_build_lookup
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

read_file_response_hw:
    jsr current_mount_is_flat
    beq read_file_response_hw_flat
    jsr sync_drive_backend_path_hw
    bcs read_file_response_hw_fail
    jsr build_uci_open_read_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs read_file_response_hw_fail
    jsr uci_status_is_ok
    bcs read_file_response_hw_fail
    jsr uci_read_open_file_into_response
    php
    jsr close_current_file_hw
    plp
    bcc read_file_response_hw_ok
read_file_response_hw_fail:
    sec
    rts
read_file_response_hw_ok:
    clc
    rts

read_file_response_hw_flat:
    jsr open_flat_mount_image_hw
    bcs read_file_response_hw_fail
    jsr find_flat_file_entry_in_open_image
    bcs read_file_response_hw_flat_close
    jsr read_flat_response_open_hw
read_file_response_hw_flat_close:
    php
    pha
    jsr close_current_file_hw
    pla
    plp
    bcc read_file_response_hw_ok
    jmp read_file_response_hw_fail

copy_file_hw:
    lda temp_drive
    sta dest_drive
    lda temp_dir_id
    sta dest_dir_id
    lda source_drive
    cmp dest_drive
    beq copy_file_hw_same_drive
    lda source_drive
    sta temp_drive
    jsr current_mount_is_flat
    beq copy_file_hw_raw_cross_drive
    lda dest_drive
    sta temp_drive
    jsr current_mount_is_flat
    beq copy_file_hw_raw_cross_drive
    jmp copy_file_hw_cross_drive
copy_file_hw_same_drive:
    jsr compare_source_name_to_path_name
    bcc copy_file_hw_done
    lda source_drive
    sta temp_drive
    jsr current_mount_is_flat
    beq copy_file_hw_raw_same_drive
    jsr copy_file_same_drive_hw
    rts
copy_file_hw_raw_same_drive:
    jsr copy_file_raw_same_drive_hw
    rts
copy_file_hw_cross_drive:
    jsr copy_file_cross_drive_hw
    rts
copy_file_hw_raw_cross_drive:
    jsr copy_file_raw_cross_drive_hw
    rts
copy_file_hw_done:
    clc
    rts

copy_matching_files_hw:
    lda #$00
    sta wildcard_match_count
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr fill_hw_dir_cache_current
    bcs copy_matching_files_hw_fail
    jsr fs_enum_begin_current
copy_matching_files_hw_loop:
    jsr fs_enum_next_ptr
    bcs copy_matching_files_hw_done
    jsr copy_program_target_to_source_buffer
    jsr wildcard_match_ptr_to_source_name
    bcs copy_matching_files_hw_loop
    jsr copy_ptr_name_to_source_buffer
    jsr copy_ptr_name_to_path_buffer
    lda dest_drive
    sta temp_drive
    lda dest_dir_id
    sta temp_dir_id
    jsr copy_file_hw
    bcs copy_matching_files_hw_fail
    inc wildcard_match_count
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jmp copy_matching_files_hw_loop
copy_matching_files_hw_done:
    lda wildcard_match_count
    beq copy_matching_files_hw_nomatch
    clc
    rts
copy_matching_files_hw_nomatch:
    lda #WILDCARD_RESULT_NOMATCH
    sec
    rts
copy_matching_files_hw_fail:
    lda wildcard_match_count
    beq copy_matching_files_hw_nomatch
    lda #WILDCARD_RESULT_FAILED
    sec
    rts

copy_file_vice:
    lda temp_drive
    sta dest_drive
    lda temp_dir_id
    sta dest_dir_id
    lda source_drive
    cmp dest_drive
    bne copy_file_vice_need_source
    lda source_dir_id
    cmp dest_dir_id
    bne copy_file_vice_need_source
    jsr compare_source_name_to_path_name
    bcs copy_file_vice_need_source
    clc
    rts
copy_file_vice_need_source:
    jsr copy_path_name_to_copy_dst_buffer
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr copy_source_name_to_path_buffer
    jsr read_file_response_vice_current
    bcs copy_file_vice_fail
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    lda dest_drive
    sta temp_drive
    lda dest_dir_id
    sta temp_dir_id
    jsr copy_copy_dst_to_path_buffer
    jmp store_vice_tree_live_current_from_screen_ptr
copy_file_vice_fail:
    sec
    rts

copy_matching_files_vice:
    lda #$00
    sta wildcard_match_count
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr fs_enum_begin_current
copy_matching_files_vice_loop:
    jsr fs_enum_next_ptr
    bcs copy_matching_files_vice_done
    jsr copy_program_target_to_source_buffer
    jsr wildcard_match_ptr_to_source_name
    bcs copy_matching_files_vice_next
    jsr copy_ptr_name_to_path_buffer
    jsr copy_path_name_to_source_buffer
    lda enum_index
    sta vice_tree_source_state
    lda dest_drive
    sta temp_drive
    lda dest_dir_id
    sta temp_dir_id
    jsr copy_file_vice
    bcs copy_matching_files_vice_fail
    inc wildcard_match_count
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr fs_enum_begin_current
    lda vice_tree_source_state
    sta enum_index
copy_matching_files_vice_next:
    jmp copy_matching_files_vice_loop
copy_matching_files_vice_done:
    lda wildcard_match_count
    beq copy_matching_files_vice_nomatch
    clc
    rts
copy_matching_files_vice_nomatch:
    lda #WILDCARD_RESULT_NOMATCH
    sec
    rts
copy_matching_files_vice_fail:
    lda wildcard_match_count
    beq copy_matching_files_vice_nomatch
    lda #WILDCARD_RESULT_FAILED
    sec
    rts

delete_file_vice:
    jsr vice_tree_find_current_slot
    bcs delete_file_vice_host
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq delete_file_vice_fail
    cmp #VICE_TREE_SLOT_LIVE_HIDE
    beq delete_file_vice_tomb
    jsr clear_vice_tree_slot
    clc
    rts
delete_file_vice_tomb:
    jsr store_vice_tree_tombstone_current
    bcc delete_file_vice_ok
    bcs delete_file_vice_fail
delete_file_vice_host:
    jsr query_file_vice_host_current
    bcs delete_file_vice_fail
    jsr store_vice_tree_tombstone_current
    bcs delete_file_vice_fail
delete_file_vice_ok:
    clc
    rts
delete_file_vice_fail:
    sec
    rts

delete_matching_files_vice:
    lda #$00
    sta wildcard_match_count
delete_matching_files_vice_restart:
    jsr fs_enum_begin_current
delete_matching_files_vice_loop:
    jsr fs_enum_next_ptr
    bcs delete_matching_files_vice_done
    jsr wildcard_match_ptr_to_source_name
    bcs delete_matching_files_vice_next
    jsr copy_ptr_name_to_path_buffer
    jsr delete_file_vice
    bcs delete_matching_files_vice_fail
    inc wildcard_match_count
    jmp delete_matching_files_vice_restart
delete_matching_files_vice_next:
    jmp delete_matching_files_vice_loop
delete_matching_files_vice_done:
    lda wildcard_match_count
    beq delete_matching_files_vice_fail
    clc
    rts
delete_matching_files_vice_fail:
    sec
    rts

rename_file_vice:
    lda temp_drive
    sta dest_drive
    lda temp_dir_id
    sta dest_dir_id
    lda source_drive
    cmp dest_drive
    bne rename_file_vice_load_source
    lda source_dir_id
    cmp dest_dir_id
    bne rename_file_vice_load_source
    jsr compare_source_name_to_path_name
    bcs rename_file_vice_load_source
    jmp rename_file_vice_ok
rename_file_vice_load_source:
    jsr copy_path_name_to_copy_dst_buffer
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr copy_source_name_to_path_buffer
    jsr read_file_response_vice_current
    bcs rename_file_vice_fail
    lda dest_drive
    sta temp_drive
    lda dest_dir_id
    sta temp_dir_id
    jsr copy_copy_dst_to_path_buffer
    jsr vice_tree_find_current_slot
    bcs rename_file_vice_dest_host
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq rename_file_vice_store
    lda #RENAME_STATUS_EXISTS
    sec
    rts
rename_file_vice_dest_host:
    jsr query_file_vice_host_current
    bcs rename_file_vice_store
    lda #RENAME_STATUS_EXISTS
    sec
    rts
rename_file_vice_store:
    jsr copy_file_vice
    bcs rename_file_vice_fail
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr copy_source_name_to_path_buffer
    jsr delete_file_vice
    bcc rename_file_vice_ok
    lda dest_drive
    sta temp_drive
    lda dest_dir_id
    sta temp_dir_id
    jsr copy_copy_dst_to_path_buffer
    jsr vice_tree_find_current_slot
    bcc :+
    jsr query_file_vice_host_current
    bcs rename_file_vice_fail
:
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr copy_source_name_to_path_buffer
    jsr vice_tree_find_current_slot
    bcs rename_file_vice_verify_source_host
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq rename_file_vice_ok
    jmp rename_file_vice_fail
rename_file_vice_verify_source_host:
    jsr query_file_vice_host_current
    bcs rename_file_vice_ok
    jmp rename_file_vice_fail
rename_file_vice_ok:
    lda #RENAME_STATUS_FAILED
    clc
    rts
rename_file_vice_fail:
    lda #RENAME_STATUS_FAILED
    sec
    rts

copy_file_raw_same_drive_hw:
    jsr copy_path_name_to_copy_dst_buffer
    lda source_drive
    sta temp_drive
    jsr open_flat_mount_image_rw_hw
    bcs copy_file_raw_same_drive_fail
    jsr init_flat_source_from_open_image
    bcs copy_file_raw_same_drive_close
    jsr copy_copy_dst_to_path_buffer
    jsr init_flat_dest_on_open_image
    bcs copy_file_raw_same_drive_close
    lda #$01
    sta copy_source_flat_flag
    sta copy_dest_flat_flag
    jsr copy_stream_loop_hw
copy_file_raw_same_drive_close:
    php
    jsr close_current_file_hw
    bcs copy_file_raw_same_drive_close_fail
    plp
    rts
copy_file_raw_same_drive_close_fail:
    plp
copy_file_raw_same_drive_fail:
    sec
    rts

copy_file_raw_cross_drive_hw:
    jsr copy_path_name_to_copy_dst_buffer
    jsr open_copy_source_hw
    bcs copy_file_raw_cross_drive_fail
    jsr copy_copy_dst_to_path_buffer
    jsr open_copy_dest_hw
    bcs copy_file_raw_cross_drive_close_source
    jsr copy_stream_loop_hw
copy_file_raw_cross_drive_close:
    php
    jsr close_cross_drive_files_hw
    bcs copy_file_raw_cross_drive_close_fail
    plp
    rts
copy_file_raw_cross_drive_close_fail:
    plp
copy_file_raw_cross_drive_fail:
    sec
    rts
copy_file_raw_cross_drive_close_source:
    php
    lda source_drive
    sta temp_drive
    jsr close_current_file_hw
    plp
    sec
    rts

open_copy_source_hw:
    lda source_drive
    sta temp_drive
    jsr current_mount_is_flat
    beq open_copy_source_hw_flat
    lda #$00
    sta copy_source_flat_flag
    lda source_dir_id
    sta temp_dir_id
    jmp open_source_file_hw
open_copy_source_hw_flat:
    lda #$01
    sta copy_source_flat_flag
    jsr open_flat_mount_image_hw
    bcs open_copy_source_hw_fail
    jsr init_flat_source_from_open_image
    bcc open_copy_source_hw_ok
    php
    jsr close_current_file_hw
    plp
open_copy_source_hw_fail:
    sec
    rts
open_copy_source_hw_ok:
    clc
    rts

open_copy_dest_hw:
    lda dest_drive
    sta temp_drive
    jsr current_mount_is_flat
    beq open_copy_dest_hw_flat
    lda #$00
    sta copy_dest_flat_flag
    lda dest_dir_id
    sta temp_dir_id
    jmp open_dest_file_hw
open_copy_dest_hw_flat:
    lda #$01
    sta copy_dest_flat_flag
    lda copy_source_flat_flag
    bne :+
    lda #$82
    sta flat_dst_type
:
    jsr open_flat_mount_image_rw_hw
    bcs open_copy_dest_hw_fail
    jsr init_flat_dest_on_open_image
    bcc open_copy_dest_hw_ok
    php
    jsr close_current_file_hw
    plp
open_copy_dest_hw_fail:
    sec
    rts
open_copy_dest_hw_ok:
    clc
    rts

copy_stream_loop_hw:
copy_stream_loop_hw_next:
    jsr read_copy_source_chunk_hw
    bcs copy_stream_loop_hw_fail
    lda uci_data_length
    beq copy_stream_loop_hw_done
    jsr write_copy_dest_chunk_hw
    bcs copy_stream_loop_hw_fail
    jmp copy_stream_loop_hw_next
copy_stream_loop_hw_done:
    lda copy_dest_flat_flag
    beq copy_stream_loop_hw_ok
    jsr finalize_flat_dest_write_hw
    bcs copy_stream_loop_hw_fail
copy_stream_loop_hw_ok:
    clc
    rts
copy_stream_loop_hw_fail:
    sec
    rts

read_copy_source_chunk_hw:
    lda copy_source_flat_flag
    beq read_copy_source_chunk_hw_tree
    jmp read_next_flat_source_chunk_hw
read_copy_source_chunk_hw_tree:
    lda source_drive
    sta temp_drive
    jmp read_source_chunk_hw

write_copy_dest_chunk_hw:
    lda copy_dest_flat_flag
    beq write_copy_dest_chunk_hw_tree
    jmp append_flat_dest_chunk_hw
write_copy_dest_chunk_hw_tree:
    lda dest_drive
    sta temp_drive
    jmp write_dest_chunk_hw

init_flat_source_from_open_image:
    jsr copy_source_name_to_path_buffer
    jsr find_flat_file_entry_in_open_image
    bcs init_flat_source_from_open_image_fail
    ldy flat_hit_dir_offset
    lda flat_sector_buffer,y
    sta flat_dst_type
    lda flat_file_track
    sta flat_src_track
    lda flat_file_sector
    sta flat_src_sector
    lda #$00
    sta flat_src_offset
    sta flat_src_count
    clc
    rts
init_flat_source_from_open_image_fail:
    sec
    rts

init_flat_dest_on_open_image:
    jsr find_flat_file_entry_in_open_image
    bcs :+
    sec
    rts
:
    cmp #FLAT_LOOKUP_NOFILE
    bne init_flat_dest_on_open_image_fail
    jsr find_free_flat_dir_entry_in_open_image
    bcs init_flat_dest_on_open_image_fail
    jsr load_flat_bam_buffers_hw
    bcs init_flat_dest_on_open_image_fail
    lda #$00
    sta flat_dst_first_track
    sta flat_dst_first_sector
    sta flat_dst_curr_track
    sta flat_dst_curr_sector
    sta flat_dst_fill
    sta flat_dst_blocks_lo
    sta flat_dst_blocks_hi
    clc
    rts
init_flat_dest_on_open_image_fail:
    sec
    rts

find_free_flat_dir_entry_in_open_image:
    jsr init_flat_dir_walk
find_free_flat_dir_entry_in_open_image_loop:
    lda flat_dir_sector
    beq find_free_flat_dir_entry_in_open_image_fail
    lda flat_dir_track
    sta flat_file_track
    lda flat_dir_sector
    sta flat_file_sector
    lda #<flat_dir_sector_buffer
    sta PTR
    lda #>flat_dir_sector_buffer
    sta PTR+1
    jsr read_flat_sector_into_ptr_hw
    bcs find_free_flat_dir_entry_in_open_image_fail
    jsr find_free_flat_dir_entry_in_sector
    bcc find_free_flat_dir_entry_in_open_image_found
    lda flat_dir_sector_buffer+0
    sta flat_dir_track
    lda flat_dir_sector_buffer+1
    sta flat_dir_sector
    lda flat_dir_track
    beq find_free_flat_dir_entry_in_open_image_fail
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq find_free_flat_dir_entry_in_open_image_check_d81
    lda flat_dir_track
    cmp #D64_DIR_TRACK
    beq find_free_flat_dir_entry_in_open_image_loop
    bne find_free_flat_dir_entry_in_open_image_fail
find_free_flat_dir_entry_in_open_image_check_d81:
    lda flat_dir_track
    cmp #D81_DIR_TRACK
    beq find_free_flat_dir_entry_in_open_image_loop
find_free_flat_dir_entry_in_open_image_fail:
    sec
    rts
find_free_flat_dir_entry_in_open_image_found:
    clc
    rts

find_free_flat_dir_entry_in_sector:
    lda #$02
    sta flat_dir_offset
find_free_flat_dir_entry_in_sector_loop:
    ldy flat_dir_offset
    lda flat_dir_sector_buffer,y
    beq find_free_flat_dir_entry_in_sector_hit
    lda flat_dir_offset
    cmp #$E2
    bcs find_free_flat_dir_entry_in_sector_fail
    clc
    adc #$20
    sta flat_dir_offset
    jmp find_free_flat_dir_entry_in_sector_loop
find_free_flat_dir_entry_in_sector_hit:
    lda flat_dir_track
    sta flat_saved_dir_track
    lda flat_dir_sector
    sta flat_saved_dir_sector
    lda flat_dir_offset
    sta flat_saved_dir_offset
    clc
    rts
find_free_flat_dir_entry_in_sector_fail:
    sec
    rts

read_next_flat_source_chunk_hw:
    lda #$00
    sta uci_data_length
    lda flat_src_count
    bne read_next_flat_source_chunk_hw_copy
read_next_flat_source_chunk_hw_load:
    lda flat_src_track
    bne :+
    jmp read_next_flat_source_chunk_hw_done
:
    lda source_drive
    sta temp_drive
    jsr current_mount_is_flat
    lda flat_src_track
    sta flat_file_track
    lda flat_src_sector
    sta flat_file_sector
    lda #<flat_dir_sector_buffer
    sta PTR
    lda #>flat_dir_sector_buffer
    sta PTR+1
    jsr read_flat_sector_into_ptr_hw
    bcs read_next_flat_source_chunk_hw_fail
    lda flat_dir_sector_buffer+0
    sta flat_src_track
    lda flat_dir_sector_buffer+1
    sta flat_src_sector
    lda flat_dir_sector_buffer+0
    bne read_next_flat_source_chunk_hw_full
    lda flat_src_sector
    beq read_next_flat_source_chunk_hw_fail
    sec
    sbc #$01
    sta flat_src_count
    lda #$00
    sta flat_src_track
    sta flat_src_sector
    lda #$02
    sta flat_src_offset
    jmp read_next_flat_source_chunk_hw_copy
read_next_flat_source_chunk_hw_full:
    lda #$FE
    sta flat_src_count
    lda #$02
    sta flat_src_offset
read_next_flat_source_chunk_hw_copy:
    lda flat_src_count
    cmp #MAX_RESPONSE_LEN-1
    bcc read_next_flat_source_chunk_hw_have_len
    lda #MAX_RESPONSE_LEN-1
read_next_flat_source_chunk_hw_have_len:
    sta uci_data_length
    ldy #$00
    ldx flat_src_offset
read_next_flat_source_chunk_hw_copy_loop:
    cpy uci_data_length
    bcs read_next_flat_source_chunk_hw_copy_done
    lda flat_dir_sector_buffer,x
    sta response_buffer,y
    inx
    iny
    bne read_next_flat_source_chunk_hw_copy_loop
read_next_flat_source_chunk_hw_copy_done:
    stx flat_src_offset
    sec
    lda flat_src_count
    sbc uci_data_length
    sta flat_src_count
    lda #$00
    sta response_buffer,y
    clc
    rts
read_next_flat_source_chunk_hw_done:
    lda #$00
    sta response_buffer
    clc
    rts
read_next_flat_source_chunk_hw_fail:
    sec
    rts

append_flat_dest_chunk_hw:
    ldy #$00
append_flat_dest_chunk_hw_loop:
    cpy uci_data_length
    bcs append_flat_dest_chunk_hw_done
    lda flat_dst_curr_track
    bne append_flat_dest_chunk_hw_have_sector
    jsr alloc_flat_dest_sector_hw
    bcs append_flat_dest_chunk_hw_fail
    lda flat_file_track
    sta flat_dst_first_track
    sta flat_dst_curr_track
    lda flat_file_sector
    sta flat_dst_first_sector
    sta flat_dst_curr_sector
    lda #$00
    sta flat_dst_fill
append_flat_dest_chunk_hw_have_sector:
    lda flat_dst_fill
    cmp #$FE
    bne append_flat_dest_chunk_hw_store
    jsr flush_full_flat_dest_sector_hw
    bcs append_flat_dest_chunk_hw_fail
append_flat_dest_chunk_hw_store:
    ldx flat_dst_fill
    lda flat_dir_sector_buffer,y
    sta flat_sector_buffer+2,x
    inx
    stx flat_dst_fill
    iny
    jmp append_flat_dest_chunk_hw_loop
append_flat_dest_chunk_hw_done:
    clc
    rts
append_flat_dest_chunk_hw_fail:
    sec
    rts

flush_full_flat_dest_sector_hw:
    jsr alloc_flat_dest_sector_hw
    bcs flush_full_flat_dest_sector_hw_fail
    lda flat_file_track
    sta flat_saved_dir_track
    lda flat_file_sector
    sta flat_saved_dir_sector
    lda flat_dst_curr_track
    sta flat_file_track
    lda flat_dst_curr_sector
    sta flat_file_sector
    lda flat_saved_dir_track
    sta flat_sector_buffer+0
    lda flat_saved_dir_sector
    sta flat_sector_buffer+1
    lda #<flat_sector_buffer
    sta PTR
    lda #>flat_sector_buffer
    sta PTR+1
    jsr write_flat_sector_from_ptr_hw
    bcs flush_full_flat_dest_sector_hw_fail
    lda flat_saved_dir_track
    sta flat_dst_curr_track
    lda flat_saved_dir_sector
    sta flat_dst_curr_sector
    lda #$00
    sta flat_dst_fill
    clc
    rts
flush_full_flat_dest_sector_hw_fail:
    sec
    rts

finalize_flat_dest_write_hw:
    lda flat_dst_curr_track
    bne finalize_flat_dest_write_hw_have_sector
    jsr alloc_flat_dest_sector_hw
    bcs finalize_flat_dest_write_hw_fail
    lda flat_file_track
    sta flat_dst_first_track
    sta flat_dst_curr_track
    lda flat_file_sector
    sta flat_dst_first_sector
    sta flat_dst_curr_sector
    lda #$00
    sta flat_dst_fill
finalize_flat_dest_write_hw_have_sector:
    lda #$00
    sta flat_sector_buffer+0
    lda flat_dst_fill
    clc
    adc #$01
    sta flat_sector_buffer+1
    lda flat_dst_curr_track
    sta flat_file_track
    lda flat_dst_curr_sector
    sta flat_file_sector
    lda #<flat_sector_buffer
    sta PTR
    lda #>flat_sector_buffer
    sta PTR+1
    jsr write_flat_sector_from_ptr_hw
    bcs finalize_flat_dest_write_hw_fail
    jsr write_flat_dir_entry_from_copy_state
    bcs finalize_flat_dest_write_hw_fail
    jsr write_flat_bam_buffers_hw
    bcs finalize_flat_dest_write_hw_fail
    clc
    rts
finalize_flat_dest_write_hw_fail:
    sec
    rts

write_flat_dir_entry_from_copy_state:
    lda flat_saved_dir_track
    sta flat_hit_dir_track
    lda flat_saved_dir_sector
    sta flat_hit_dir_sector
    lda flat_saved_dir_offset
    sta flat_hit_dir_offset
    jsr read_flat_dir_hit_sector_hw
    bcs write_flat_dir_entry_from_copy_state_fail
    ldy flat_hit_dir_offset
    lda flat_dst_type
    sta flat_dir_sector_buffer,y
    iny
    lda flat_dst_first_track
    sta flat_dir_sector_buffer,y
    iny
    lda flat_dst_first_sector
    sta flat_dir_sector_buffer,y
    jsr write_flat_dir_entry_name_from_path_buffer
    bcs write_flat_dir_entry_from_copy_state_fail
    ldx flat_hit_dir_offset
    txa
    clc
    adc #$13
    tax
    lda #$00
    ldy #$0D
write_flat_dir_entry_from_copy_state_clear:
    sta flat_dir_sector_buffer,x
    inx
    dey
    bne write_flat_dir_entry_from_copy_state_clear
    ldx flat_hit_dir_offset
    txa
    clc
    adc #$1C
    tax
    lda flat_dst_blocks_lo
    sta flat_dir_sector_buffer,x
    inx
    lda flat_dst_blocks_hi
    sta flat_dir_sector_buffer,x
    jsr write_flat_dir_hit_sector_hw
    bcs write_flat_dir_entry_from_copy_state_fail
    clc
    rts
write_flat_dir_entry_from_copy_state_fail:
    sec
    rts

alloc_flat_dest_sector_hw:
    jsr find_free_flat_sector_in_bam
    bcs alloc_flat_dest_sector_hw_fail
    jsr mark_flat_sector_used_in_bam
    bcs alloc_flat_dest_sector_hw_fail
    inc flat_dst_blocks_lo
    bne :+
    inc flat_dst_blocks_hi
:
    clc
    rts
alloc_flat_dest_sector_hw_fail:
    sec
    rts

find_free_flat_sector_in_bam:
    lda #$01
    sta flat_file_track
find_free_flat_sector_in_bam_track:
    jsr get_flat_track_sector_limit
    bcs find_free_flat_sector_in_bam_fail
    sta flat_sector_limit
    lda #$00
    sta flat_file_sector
find_free_flat_sector_in_bam_sector:
    lda flat_file_sector
    cmp flat_sector_limit
    bcs find_free_flat_sector_in_bam_next_track
    jsr flat_sector_is_free_in_bam
    bcc find_free_flat_sector_in_bam_found
    inc flat_file_sector
    jmp find_free_flat_sector_in_bam_sector
find_free_flat_sector_in_bam_next_track:
    inc flat_file_track
    jmp find_free_flat_sector_in_bam_track
find_free_flat_sector_in_bam_found:
    clc
    rts
find_free_flat_sector_in_bam_fail:
    sec
    rts

get_flat_track_sector_limit:
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq get_flat_track_sector_limit_d81
    cmp #MOUNT_KIND_D71
    beq get_flat_track_sector_limit_d71
    lda flat_file_track
    cmp #36
    bcs get_flat_track_sector_limit_fail
    jmp get_flat_track_sector_limit_zone
get_flat_track_sector_limit_d71:
    lda flat_file_track
    cmp #71
    bcs get_flat_track_sector_limit_fail
    cmp #36
    bcc get_flat_track_sector_limit_zone
    sec
    sbc #35
get_flat_track_sector_limit_zone:
    cmp #18
    bcc get_flat_track_sector_limit_21
    cmp #25
    bcc get_flat_track_sector_limit_19
    cmp #31
    bcc get_flat_track_sector_limit_18
    lda #17
    clc
    rts
get_flat_track_sector_limit_21:
    lda #21
    clc
    rts
get_flat_track_sector_limit_19:
    lda #19
    clc
    rts
get_flat_track_sector_limit_18:
    lda #18
    clc
    rts
get_flat_track_sector_limit_d81:
    lda flat_file_track
    cmp #81
    bcs get_flat_track_sector_limit_fail
    lda #40
    clc
    rts
get_flat_track_sector_limit_fail:
    sec
    rts

flat_sector_is_free_in_bam:
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq flat_sector_is_free_in_bam_d81
    cmp #MOUNT_KIND_D71
    beq flat_sector_is_free_in_bam_d71
    jmp flat_sector_is_free_in_bam_d64

flat_sector_is_free_in_bam_d64:
    lda flat_file_track
    sec
    sbc #$01
    asl
    asl
    clc
    adc #D64_BAM_ENTRY_BASE
    tay
    iny
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    and flat_bam_primary_buffer,y
    bne flat_sector_is_free_in_bam_ok
    sec
    rts

flat_sector_is_free_in_bam_d71:
    lda flat_file_track
    cmp #36
    bcc flat_sector_is_free_in_bam_d64
    sec
    sbc #36
    sta flat_track_index
    asl
    clc
    adc flat_track_index
    tay
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    and flat_bam_secondary_buffer,y
    bne flat_sector_is_free_in_bam_ok
    sec
    rts

flat_sector_is_free_in_bam_d81:
    lda flat_file_track
    sec
    sbc #$01
    sta flat_track_index
    asl
    clc
    adc flat_track_index
    asl
    clc
    adc #D81_BAM_ENTRY_BASE
    tay
    iny
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    and flat_bam_primary_buffer,y
    bne flat_sector_is_free_in_bam_ok
    sec
    rts

flat_sector_is_free_in_bam_ok:
    clc
    rts

mark_flat_sector_used_in_bam:
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq mark_flat_sector_used_in_bam_d81
    cmp #MOUNT_KIND_D71
    beq mark_flat_sector_used_in_bam_d71
    jmp mark_flat_sector_used_in_bam_d64

mark_flat_sector_used_in_bam_d64:
    lda flat_file_track
    sec
    sbc #$01
    asl
    asl
    clc
    adc #D64_BAM_ENTRY_BASE
    tay
    lda flat_bam_primary_buffer,y
    bne :+
    jmp mark_flat_sector_used_in_bam_fail
:
    sec
    sbc #$01
    sta flat_bam_primary_buffer,y
    iny
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    eor #$FF
    and flat_bam_primary_buffer,y
    sta flat_bam_primary_buffer,y
    clc
    rts

mark_flat_sector_used_in_bam_d71:
    lda flat_file_track
    cmp #36
    bcc mark_flat_sector_used_in_bam_d64
    sec
    sbc #36
    sta flat_track_index
    tay
    lda flat_bam_primary_buffer + D71_BAM_SIDE2_COUNT_BASE,y
    beq mark_flat_sector_used_in_bam_fail
    sec
    sbc #$01
    sta flat_bam_primary_buffer + D71_BAM_SIDE2_COUNT_BASE,y
    lda #$01
    sta flat_secondary_dirty
    lda flat_track_index
    asl
    clc
    adc flat_track_index
    tay
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    eor #$FF
    and flat_bam_secondary_buffer,y
    sta flat_bam_secondary_buffer,y
    clc
    rts

mark_flat_sector_used_in_bam_d81:
    lda flat_file_track
    sec
    sbc #$01
    sta flat_track_index
    asl
    clc
    adc flat_track_index
    asl
    clc
    adc #D81_BAM_ENTRY_BASE
    tay
    lda flat_bam_primary_buffer,y
    beq mark_flat_sector_used_in_bam_fail
    sec
    sbc #$01
    sta flat_bam_primary_buffer,y
    iny
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    eor #$FF
    and flat_bam_primary_buffer,y
    sta flat_bam_primary_buffer,y
    clc
    rts

mark_flat_sector_used_in_bam_fail:
    sec
    rts

delete_file_hw:
    jsr current_mount_is_flat
    beq delete_file_hw_flat
    jsr sync_drive_backend_path_hw
    bcs delete_file_hw_fail
    jsr build_uci_delete_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs delete_file_hw_fail
    jsr uci_status_is_ok
    bcs delete_file_hw_fail
    clc
    rts
delete_file_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

delete_file_hw_flat:
    jsr delete_flat_file_hw
    bcs delete_file_hw_fail
    clc
    rts

delete_matching_files_hw:
    lda #$00
    sta wildcard_match_count
    jsr fill_hw_dir_cache_current
    bcs delete_matching_files_hw_fail
    jsr fs_enum_begin_current
delete_matching_files_hw_loop:
    jsr fs_enum_next_ptr
    bcs delete_matching_files_hw_done
    jsr wildcard_match_ptr_to_source_name
    bcs delete_matching_files_hw_loop
    jsr copy_ptr_name_to_path_buffer
    jsr delete_file_hw
    bcs delete_matching_files_hw_fail
    inc wildcard_match_count
    jmp delete_matching_files_hw_loop
delete_matching_files_hw_done:
    lda wildcard_match_count
    beq delete_matching_files_hw_fail
    clc
    rts
delete_matching_files_hw_fail:
    sec
    rts

rename_flat_file_hw:
    jsr copy_path_name_to_copy_dst_buffer
    jsr copy_source_name_to_path_buffer
    jsr open_flat_mount_image_rw_hw
    bcs rename_flat_file_hw_fail
    jsr find_flat_file_entry_in_open_image
    bcs rename_flat_file_hw_close_fail
    lda flat_hit_dir_track
    sta flat_saved_dir_track
    lda flat_hit_dir_sector
    sta flat_saved_dir_sector
    lda flat_hit_dir_offset
    sta flat_saved_dir_offset
    jsr copy_copy_dst_to_path_buffer
    jsr compare_source_name_to_path_name
    bcc rename_flat_file_hw_apply
    jsr find_flat_file_entry_in_open_image
    bcc rename_flat_file_hw_close_exists
    cmp #FLAT_LOOKUP_NOFILE
    bne rename_flat_file_hw_close_fail
rename_flat_file_hw_apply:
    lda flat_saved_dir_track
    sta flat_hit_dir_track
    lda flat_saved_dir_sector
    sta flat_hit_dir_sector
    lda flat_saved_dir_offset
    sta flat_hit_dir_offset
    jsr read_flat_dir_hit_sector_hw
    bcs rename_flat_file_hw_close_fail
    jsr write_flat_dir_entry_name_from_path_buffer
    bcs rename_flat_file_hw_close_fail
    jsr write_flat_dir_hit_sector_hw
    bcs rename_flat_file_hw_close_fail
rename_flat_file_hw_close_ok:
    php
    pha
    jsr close_current_file_hw
    pla
    plp
    bcc rename_flat_file_hw_ok
rename_flat_file_hw_fail:
    lda #RENAME_STATUS_FAILED
    sec
    rts
rename_flat_file_hw_close_fail:
    lda #RENAME_STATUS_FAILED
    bne rename_flat_file_hw_close_status
rename_flat_file_hw_close_exists:
    lda #RENAME_STATUS_EXISTS
rename_flat_file_hw_close_status:
    php
    pha
    jsr close_current_file_hw
    pla
    plp
    bcc rename_flat_file_hw_fail_with_status
rename_flat_file_hw_fail_with_status:
    sec
    rts
rename_flat_file_hw_ok:
    lda #RENAME_STATUS_FAILED
    clc
    rts

write_flat_dir_entry_name_from_path_buffer:
    ldx flat_hit_dir_offset
    inx
    inx
    inx
    ldy #$00
write_flat_dir_entry_name_loop:
    cpy #$10
    bcs write_flat_dir_entry_name_check_done
    lda path_name_buffer,y
    beq write_flat_dir_entry_name_pad
    jsr screen_code_to_dir_char
    sta flat_dir_sector_buffer,x
    inx
    iny
    jmp write_flat_dir_entry_name_loop
write_flat_dir_entry_name_pad:
    lda #$A0
    sta flat_dir_sector_buffer,x
    inx
    iny
    cpy #$10
    bcc write_flat_dir_entry_name_pad
write_flat_dir_entry_name_check_done:
    lda path_name_buffer,y
    beq write_flat_dir_entry_name_done
    sec
    rts
write_flat_dir_entry_name_done:
    clc
    rts

screen_code_to_dir_char:
    cmp #$01
    bcc screen_code_to_dir_char_done
    cmp #$1B
    bcs screen_code_to_dir_char_done
    clc
    adc #$C0
screen_code_to_dir_char_done:
    rts

delete_flat_file_hw:
    jsr open_flat_mount_image_rw_hw
    bcs delete_flat_file_hw_fail
    jsr find_flat_file_entry_in_open_image
    bcs delete_flat_file_hw_close
    jsr read_flat_dir_hit_sector_hw
    bcs delete_flat_file_hw_close
    jsr clear_flat_dir_entry_type_in_buffer
    jsr load_flat_bam_buffers_hw
    bcs delete_flat_file_hw_close
    jsr walk_flat_file_chain_release_bam
    bcs delete_flat_file_hw_close
    jsr write_flat_dir_hit_sector_hw
    bcs delete_flat_file_hw_close
    jsr write_flat_bam_buffers_hw
delete_flat_file_hw_close:
    php
    pha
    jsr close_current_file_hw
    pla
    plp
    bcc delete_flat_file_hw_ok
delete_flat_file_hw_fail:
    sec
    rts
delete_flat_file_hw_ok:
    clc
    rts

read_flat_dir_hit_sector_hw:
    lda flat_hit_dir_track
    sta flat_file_track
    lda flat_hit_dir_sector
    sta flat_file_sector
    lda #<flat_dir_sector_buffer
    sta PTR
    lda #>flat_dir_sector_buffer
    sta PTR+1
    jmp read_flat_sector_into_ptr_hw

write_flat_dir_hit_sector_hw:
    lda flat_hit_dir_track
    sta flat_file_track
    lda flat_hit_dir_sector
    sta flat_file_sector
    lda #<flat_dir_sector_buffer
    sta PTR
    lda #>flat_dir_sector_buffer
    sta PTR+1
    jmp write_flat_sector_from_ptr_hw

clear_flat_dir_entry_type_in_buffer:
    ldy flat_hit_dir_offset
    lda #$00
    sta flat_dir_sector_buffer,y
    rts

load_flat_bam_buffers_hw:
    lda #$00
    sta flat_secondary_dirty
    lda #D64_DIR_TRACK
    sta flat_file_track
    lda #D64_BAM_SECTOR
    sta flat_file_sector
    lda #<flat_bam_primary_buffer
    sta PTR
    lda #>flat_bam_primary_buffer
    sta PTR+1
    jsr read_flat_sector_into_ptr_hw
    bcs load_flat_bam_buffers_hw_fail
    lda temp_mount_kind
    cmp #MOUNT_KIND_D71
    bne load_flat_bam_buffers_hw_done
    lda #D71_BAM_SIDE2_TRACK
    sta flat_file_track
    lda #D71_BAM_SIDE2_SECTOR
    sta flat_file_sector
    lda #<flat_bam_secondary_buffer
    sta PTR
    lda #>flat_bam_secondary_buffer
    sta PTR+1
    jsr read_flat_sector_into_ptr_hw
    bcs load_flat_bam_buffers_hw_fail
load_flat_bam_buffers_hw_done:
    clc
    rts
load_flat_bam_buffers_hw_fail:
    sec
    rts

write_flat_bam_buffers_hw:
    lda #D64_DIR_TRACK
    sta flat_file_track
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq write_flat_bam_buffers_hw_d81
    lda #D64_BAM_SECTOR
    bne write_flat_bam_buffers_hw_primary
write_flat_bam_buffers_hw_d81:
    lda #D81_BAM_SECTOR
write_flat_bam_buffers_hw_primary:
    sta flat_file_sector
    lda #<flat_bam_primary_buffer
    sta PTR
    lda #>flat_bam_primary_buffer
    sta PTR+1
    jsr write_flat_sector_from_ptr_hw
    bcs write_flat_bam_buffers_hw_fail
    lda temp_mount_kind
    cmp #MOUNT_KIND_D71
    bne write_flat_bam_buffers_hw_done
    lda flat_secondary_dirty
    beq write_flat_bam_buffers_hw_done
    lda #D71_BAM_SIDE2_TRACK
    sta flat_file_track
    lda #D71_BAM_SIDE2_SECTOR
    sta flat_file_sector
    lda #<flat_bam_secondary_buffer
    sta PTR
    lda #>flat_bam_secondary_buffer
    sta PTR+1
    jsr write_flat_sector_from_ptr_hw
    bcs write_flat_bam_buffers_hw_fail
write_flat_bam_buffers_hw_done:
    clc
    rts
write_flat_bam_buffers_hw_fail:
    sec
    rts

walk_flat_file_chain_release_bam:
walk_flat_file_chain_release_bam_loop:
    lda flat_file_track
    beq walk_flat_file_chain_release_bam_done
    jsr read_flat_sector_buffer_hw
    bcs walk_flat_file_chain_release_bam_fail
    lda flat_sector_buffer+0
    sta flat_dir_track
    lda flat_sector_buffer+1
    sta flat_dir_sector
    jsr mark_flat_sector_free_in_bam
    bcs walk_flat_file_chain_release_bam_fail
    lda flat_dir_track
    sta flat_file_track
    lda flat_dir_sector
    sta flat_file_sector
    jmp walk_flat_file_chain_release_bam_loop
walk_flat_file_chain_release_bam_done:
    clc
    rts
walk_flat_file_chain_release_bam_fail:
    sec
    rts

mark_flat_sector_free_in_bam:
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq mark_flat_sector_free_in_bam_d81
    cmp #MOUNT_KIND_D71
    beq mark_flat_sector_free_in_bam_d71
    jmp mark_flat_sector_free_in_bam_d64

mark_flat_sector_free_in_bam_d64:
    lda flat_file_track
    sec
    sbc #$01
    asl
    asl
    clc
    adc #D64_BAM_ENTRY_BASE
    tay
    lda flat_bam_primary_buffer,y
    clc
    adc #$01
    sta flat_bam_primary_buffer,y
    iny
    jmp mark_flat_sector_set_1541_bits_primary

mark_flat_sector_free_in_bam_d71:
    lda flat_file_track
    cmp #36
    bcc mark_flat_sector_free_in_bam_d64
    sec
    sbc #36
    sta flat_track_index
    tay
    lda flat_bam_primary_buffer + D71_BAM_SIDE2_COUNT_BASE,y
    clc
    adc #$01
    sta flat_bam_primary_buffer + D71_BAM_SIDE2_COUNT_BASE,y
    lda #$01
    sta flat_secondary_dirty
    lda flat_track_index
    asl
    clc
    adc flat_track_index
    tay
    jmp mark_flat_sector_set_1541_bits_secondary

mark_flat_sector_free_in_bam_d81:
    lda flat_file_track
    sec
    sbc #$01
    sta flat_track_index
    asl
    clc
    adc flat_track_index
    asl
    clc
    adc #D81_BAM_ENTRY_BASE
    tay
    lda flat_bam_primary_buffer,y
    clc
    adc #$01
    sta flat_bam_primary_buffer,y
    iny
    jmp mark_flat_sector_set_1581_bits_primary

mark_flat_sector_set_1541_bits_primary:
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    ora flat_bam_primary_buffer,y
    sta flat_bam_primary_buffer,y
    clc
    rts

mark_flat_sector_set_1541_bits_secondary:
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    ora flat_bam_secondary_buffer,y
    sta flat_bam_secondary_buffer,y
    clc
    rts

mark_flat_sector_set_1581_bits_primary:
    lda flat_file_sector
    jsr mark_flat_sector_byte_index
    txa
    ora flat_bam_primary_buffer,y
    sta flat_bam_primary_buffer,y
    clc
    rts

mark_flat_sector_byte_index:
mark_flat_sector_byte_index_loop:
    cmp #8
    bcc mark_flat_sector_byte_index_remainder
    sec
    sbc #8
    iny
    jmp mark_flat_sector_byte_index_loop
mark_flat_sector_byte_index_remainder:
    tax
    lda #$01
mark_flat_sector_byte_index_mask:
    cpx #$00
    beq mark_flat_sector_byte_index_done
    asl
    dex
    jmp mark_flat_sector_byte_index_mask
mark_flat_sector_byte_index_done:
    tax
    rts

rename_file_hw:
    jsr current_mount_is_flat
    beq rename_file_hw_flat
    jsr sync_drive_backend_path_hw
    bcs rename_file_hw_fail
    jsr build_uci_rename_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs rename_file_hw_fail
    jsr uci_status_is_ok
    bcs rename_file_hw_fail
    lda #RENAME_STATUS_FAILED
    clc
    rts
rename_file_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    lda #RENAME_STATUS_FAILED
    sec
    rts

rename_file_hw_flat:
    jmp rename_flat_file_hw

copy_file_same_drive_hw:
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr build_source_full_path
    lda dest_drive
    sta temp_drive
    lda dest_dir_id
    sta temp_dir_id
    jsr build_dest_full_path
    lda source_drive
    sta temp_drive
    jsr build_uci_copy_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs copy_file_same_drive_fail
    jsr uci_status_is_ok
    bcs copy_file_same_drive_fail
    clc
    rts
copy_file_same_drive_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

copy_file_cross_drive_hw:
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr open_source_file_hw
    bcs copy_file_cross_drive_fail
    lda dest_drive
    sta temp_drive
    lda dest_dir_id
    sta temp_dir_id
    jsr open_dest_file_hw
    bcs copy_file_cross_drive_fail_close_source
copy_file_cross_drive_loop:
    lda source_drive
    sta temp_drive
    jsr read_source_chunk_hw
    bcs copy_file_cross_drive_fail_close_both
    lda uci_data_length
    beq copy_file_cross_drive_done
    lda dest_drive
    sta temp_drive
    jsr write_dest_chunk_hw
    bcs copy_file_cross_drive_fail_close_both
    jmp copy_file_cross_drive_loop
copy_file_cross_drive_done:
    jsr close_cross_drive_files_hw
    clc
    rts
copy_file_cross_drive_fail_close_both:
    php
    jsr close_cross_drive_files_hw
    plp
    sec
    rts
copy_file_cross_drive_fail_close_source:
    php
    lda source_drive
    sta temp_drive
    jsr close_current_file_hw
    plp
copy_file_cross_drive_fail:
    sec
    rts

build_uci_open_read_command:
    jsr build_uci_target_header
    lda #DOS_CMD_OPEN_FILE
    sta uci_cmd_buffer+1
    lda #FA_READ
    sta uci_cmd_buffer+2
    ldy #$00
build_uci_open_read_copy:
    lda path_name_buffer,y
    beq build_uci_open_read_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+3,y
    iny
    cpy #MAX_LINE_LEN
    bcc build_uci_open_read_copy
build_uci_open_read_done:
    tya
    clc
    adc #3
    rts

build_uci_file_stat_command:
    jsr build_uci_target_header
    lda #DOS_CMD_FILE_STAT
    sta uci_cmd_buffer+1
    ldy #$00
build_uci_file_stat_copy:
    lda path_name_buffer,y
    beq build_uci_file_stat_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+2,y
    iny
    cpy #MAX_LINE_LEN
    bcc build_uci_file_stat_copy
build_uci_file_stat_done:
    tya
    clc
    adc #2
    rts

open_named_file_hw_from_ptr:
    lda #FA_READ
    bne open_named_file_hw_from_ptr_mode

open_named_file_rw_hw_from_ptr:
    lda #FA_READWRITE
open_named_file_hw_from_ptr_mode:
    sta file_access_mode
    jsr build_uci_open_command_from_ptr_mode
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs open_named_file_hw_fail
    jsr uci_status_is_ok
    bcs open_named_file_hw_fail
    clc
    rts
open_named_file_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

build_uci_open_command_from_ptr_mode:
    jsr build_uci_target_header
    lda #DOS_CMD_OPEN_FILE
    sta uci_cmd_buffer+1
    lda file_access_mode
    sta uci_cmd_buffer+2
    ldy #$00
build_uci_open_ptr_copy:
    lda (PTR),y
    beq build_uci_open_ptr_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+3,y
    iny
    cpy #MAX_LINE_LEN
    bcc build_uci_open_ptr_copy
build_uci_open_ptr_done:
    tya
    clc
    adc #3
    rts

mount_disk_hw:
    jsr build_uci_mount_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs mount_disk_hw_fail
    jsr uci_status_is_ok
    bcc mount_disk_hw_ok
    jsr uci_status_is_not_disk_image
    bcc mount_disk_hw_notdisk
    jsr uci_status_is_drive_not_present
    bcc mount_disk_hw_drive
mount_disk_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    lda #MOUNT_STATUS_FAILED
    sec
    rts
mount_disk_hw_notdisk:
    lda #MOUNT_STATUS_NOTDISK
    sec
    rts
mount_disk_hw_drive:
    lda #MOUNT_STATUS_DRIVE
    sec
    rts
mount_disk_hw_ok:
    lda #MOUNT_STATUS_OK
    clc
    rts

build_uci_mount_command:
    jsr build_uci_target_header
    lda #DOS_CMD_MOUNT_DISK
    sta uci_cmd_buffer+1
    lda temp_drive
    cmp #DRIVE_A
    beq build_uci_mount_command_a
    lda #IEC_ID_B
    bne build_uci_mount_command_id
build_uci_mount_command_a:
    lda #IEC_ID_A
build_uci_mount_command_id:
    sta uci_cmd_buffer+2
    ldy #$00
build_uci_mount_command_copy:
    lda path_name_buffer,y
    beq build_uci_mount_command_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+3,y
    iny
    cpy #MAX_LINE_LEN
    bcc build_uci_mount_command_copy
build_uci_mount_command_done:
    tya
    clc
    adc #3
    rts

build_uci_delete_command:
    jsr build_uci_target_header
    lda #DOS_CMD_DELETE_FILE
    sta uci_cmd_buffer+1
    ldy #$00
build_uci_delete_copy:
    lda path_name_buffer,y
    beq build_uci_delete_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+2,y
    iny
    cpy #MAX_LINE_LEN
    bcc build_uci_delete_copy
build_uci_delete_done:
    tya
    clc
    adc #2
    rts

build_uci_rename_command:
    jsr build_uci_target_header
    lda #DOS_CMD_RENAME_FILE
    sta uci_cmd_buffer+1
    ldy #$00
build_uci_rename_source_copy:
    lda source_name_buffer,y
    beq build_uci_rename_source_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+2,y
    iny
    cpy #MAX_LINE_LEN
    bcc build_uci_rename_source_copy
build_uci_rename_source_done:
    lda #$00
    sta uci_cmd_buffer+2,y
    iny
    ldx #$00
build_uci_rename_dest_copy:
    lda path_name_buffer,x
    beq build_uci_rename_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+2,y
    iny
    inx
    cpx #MAX_LINE_LEN
    bcc build_uci_rename_dest_copy
build_uci_rename_done:
    tya
    clc
    adc #2
    rts

build_uci_copy_command:
    jsr build_uci_target_header
    lda #DOS_CMD_COPY_FILE
    sta uci_cmd_buffer+1
    ldy #$00
build_uci_copy_source_copy:
    lda source_fullpath_buffer,y
    beq build_uci_copy_source_done
    sta uci_cmd_buffer+2,y
    iny
    cpy #FULL_PATH_BUF_LEN
    bcc build_uci_copy_source_copy
build_uci_copy_source_done:
    lda #$00
    sta uci_cmd_buffer+2,y
    iny
    ldx #$00
build_uci_copy_dest_copy:
    lda dest_fullpath_buffer,x
    beq build_uci_copy_done
    sta uci_cmd_buffer+2,y
    iny
    inx
    cpx #FULL_PATH_BUF_LEN
    bcc build_uci_copy_dest_copy
build_uci_copy_done:
    tya
    clc
    adc #2
    rts

open_source_file_hw:
    jsr sync_drive_backend_path_hw
    bcs open_source_file_hw_fail
    jsr build_uci_open_source_read_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs open_source_file_hw_fail
    jsr uci_status_is_ok
    bcs open_source_file_hw_fail
    clc
    rts
open_source_file_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

open_dest_file_hw:
    jsr sync_drive_backend_path_hw
    bcs open_dest_file_hw_fail
    jsr build_uci_open_dest_write_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs open_dest_file_hw_fail
    jsr uci_status_is_ok
    bcs open_dest_file_hw_fail
    clc
    rts
open_dest_file_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

build_uci_open_source_read_command:
    jsr build_uci_target_header
    lda #DOS_CMD_OPEN_FILE
    sta uci_cmd_buffer+1
    lda #FA_READ
    sta uci_cmd_buffer+2
    ldy #$00
build_uci_open_source_read_copy:
    lda source_name_buffer,y
    beq build_uci_open_source_read_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+3,y
    iny
    cpy #MAX_LINE_LEN
    bcc build_uci_open_source_read_copy
build_uci_open_source_read_done:
    tya
    clc
    adc #3
    rts

build_uci_open_dest_write_command:
    jsr build_uci_target_header
    lda #DOS_CMD_OPEN_FILE
    sta uci_cmd_buffer+1
    lda #FA_WRITE_OVERWRITE
    sta uci_cmd_buffer+2
    ldy #$00
build_uci_open_dest_write_copy:
    lda path_name_buffer,y
    beq build_uci_open_dest_write_done
    jsr screen_code_to_ascii
    sta uci_cmd_buffer+3,y
    iny
    cpy #MAX_LINE_LEN
    bcc build_uci_open_dest_write_copy
build_uci_open_dest_write_done:
    tya
    clc
    adc #3
    rts

read_source_chunk_hw:
    jsr build_uci_target_header
    lda #DOS_CMD_READ_DATA
    sta uci_cmd_buffer+1
    lda #<(MAX_RESPONSE_LEN-1)
    sta uci_cmd_buffer+2
    lda #>(MAX_RESPONSE_LEN-1)
    sta uci_cmd_buffer+3
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    lda #4
    jsr uci_push_command
    bcs read_source_chunk_hw_fail
    jsr uci_wait_reply
    bcs read_source_chunk_hw_fail
    lda #<response_buffer
    sta PTR
    lda #>response_buffer
    sta PTR+1
    lda #MAX_RESPONSE_LEN-1
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
    jsr uci_status_is_ok_or_empty
    bcs read_source_chunk_hw_fail
    clc
    rts
read_source_chunk_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

write_dest_chunk_hw:
    jsr build_uci_write_chunk_command
    pha
    lda #<uci_write_buffer
    sta PTR
    lda #>uci_write_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs write_dest_chunk_hw_fail
    jsr uci_status_is_ok_or_empty
    bcs write_dest_chunk_hw_fail
    clc
    rts
write_dest_chunk_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

build_uci_write_chunk_command:
    jsr build_uci_target_header_write
    lda #DOS_CMD_WRITE_DATA
    sta uci_write_buffer+1
    lda #$00
    sta uci_write_buffer+2
    sta uci_write_buffer+3
    ldy #$00
build_uci_write_chunk_copy:
    cpy uci_data_length
    bcs build_uci_write_chunk_done
    lda response_buffer,y
    sta uci_write_buffer+4,y
    iny
    jmp build_uci_write_chunk_copy
build_uci_write_chunk_done:
    tya
    clc
    adc #4
    rts

build_uci_target_header_write:
    lda temp_drive
    cmp #DRIVE_A
    beq build_uci_target_header_write_a
    lda #DOS_TARGET_B
    sta uci_write_buffer+0
    rts
build_uci_target_header_write_a:
    lda #DOS_TARGET_A
    sta uci_write_buffer+0
    rts

close_cross_drive_files_hw:
    lda source_drive
    sta temp_drive
    jsr close_current_file_hw
    lda dest_drive
    sta temp_drive
    jsr close_current_file_hw
    rts

build_source_full_path:
    lda source_dir_id
    sta temp_dir_id
    lda #<source_name_buffer
    sta PTR
    lda #>source_name_buffer
    sta PTR+1
    lda #<source_fullpath_buffer
    sta SCREEN_PTR
    lda #>source_fullpath_buffer
    sta SCREEN_PTR+1
    jmp build_full_path_from_ptr

build_dest_full_path:
    lda dest_dir_id
    sta temp_dir_id
    lda #<path_name_buffer
    sta PTR
    lda #>path_name_buffer
    sta PTR+1
    lda #<dest_fullpath_buffer
    sta SCREEN_PTR
    lda #>dest_fullpath_buffer
    sta SCREEN_PTR+1
    jmp build_full_path_from_ptr

build_full_path_from_ptr:
    ldy #$00
    lda #ASCII_SLASH
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda temp_dir_id
    beq build_full_path_copy_name
    cmp #DIR_ID_BIN
    beq build_full_path_bin
    cmp #DIR_ID_SRC
    beq build_full_path_src
    cmp #DIR_ID_WORK
    beq build_full_path_work
    jmp build_full_path_copy_name
build_full_path_bin:
    lda #'B'
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda #'I'
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda #'N'
    sta (SCREEN_PTR),y
    jmp build_full_path_sep
build_full_path_src:
    lda #'S'
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda #'R'
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda #'C'
    sta (SCREEN_PTR),y
    jmp build_full_path_sep
build_full_path_work:
    lda #'W'
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda #'O'
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda #'R'
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda #'K'
    sta (SCREEN_PTR),y
build_full_path_sep:
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
    lda #ASCII_SLASH
    sta (SCREEN_PTR),y
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:
build_full_path_copy_name:
    lda #$00
    sta saved_response_y
build_full_path_copy_name_loop:
    lda (PTR),y
    beq build_full_path_done
    jsr screen_code_to_ascii
    sta (SCREEN_PTR),y
    inc PTR
    bne :+
    inc PTR+1
:    
    inc SCREEN_PTR
    bne :+
    inc SCREEN_PTR+1
:    
    inc saved_response_y
    lda saved_response_y
    cmp #MAX_LINE_LEN
    bcc build_full_path_copy_name_loop
build_full_path_done:
    ldy #$00
    lda #$00
    sta (SCREEN_PTR),y
    clc
    rts

uci_read_open_file_into_response:
    lda #MAX_RESPONSE_LEN-1
    jmp uci_read_open_file_into_response_len

uci_read_open_file_into_ptr_len:
    sta uci_xfer_limit
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr build_uci_target_header
    lda #DOS_CMD_READ_DATA
    sta uci_cmd_buffer+1
    lda uci_xfer_limit
    sta uci_cmd_buffer+2
    lda #$00
    sta uci_cmd_buffer+3
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    lda #4
    jsr uci_push_command
    bcs uci_read_open_file_into_ptr_len_fail
    jsr uci_wait_reply
    bcs uci_read_open_file_into_ptr_len_fail
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    lda uci_xfer_limit
    jsr uci_read_data_block
    sta uci_data_length
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
    jsr uci_status_is_ok_or_empty
    bcs uci_read_open_file_into_ptr_len_fail
    clc
    rts
uci_read_open_file_into_ptr_len_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

uci_write_open_file_from_ptr_len:
    sta uci_xfer_limit
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr build_uci_target_header_write
    lda #DOS_CMD_WRITE_DATA
    sta uci_write_buffer+1
    lda uci_xfer_limit
    sta uci_write_buffer+2
    lda #$00
    sta uci_write_buffer+3
    ldy #$00
uci_write_open_file_copy:
    cpy uci_xfer_limit
    bcs uci_write_open_file_send
    lda (SCREEN_PTR),y
    sta uci_write_buffer+4,y
    iny
    bne uci_write_open_file_copy
uci_write_open_file_send:
    tya
    clc
    adc #4
    pha
    lda #<uci_write_buffer
    sta PTR
    lda #>uci_write_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs uci_write_open_file_from_ptr_len_fail
    jsr uci_status_is_ok_or_empty
    bcs uci_write_open_file_from_ptr_len_fail
    clc
    rts
uci_write_open_file_from_ptr_len_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

uci_read_open_file_into_response_len:
    sta uci_xfer_limit
    jsr build_uci_target_header
    lda #DOS_CMD_READ_DATA
    sta uci_cmd_buffer+1
    lda uci_xfer_limit
    sta uci_cmd_buffer+2
    lda #$00
    sta uci_cmd_buffer+3
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    lda #4
    jsr uci_push_command
    bcs uci_read_open_file_into_response_fail
    jsr uci_wait_reply
    bcs uci_read_open_file_into_response_fail
    lda #<response_buffer
    sta PTR
    lda #>response_buffer
    sta PTR+1
    lda uci_xfer_limit
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
    jsr uci_status_is_ok
    bcs uci_read_open_file_into_response_fail
    lda #<response_buffer
    sta PTR
    lda #>response_buffer
    sta PTR+1
    clc
    rts
uci_read_open_file_into_response_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

close_current_file_hw:
    jsr build_uci_target_header
    lda #DOS_CMD_CLOSE_FILE
    sta uci_cmd_buffer+1
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    lda #2
    jsr uci_issue_status_only
    bcs close_current_file_hw_fail
    jsr uci_status_is_ok
    bcs close_current_file_hw_fail
    clc
    rts
close_current_file_hw_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
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
    tya
    pha
    lda parse_scan_index
    sta parse_cmd_start
    tya
    sec
    sbc parse_scan_index
    sta cmd_length
    beq file_bad
    jsr match_path_component
    bcc :+
    pla
    jmp file_bad
:
    sta temp_dir_id
    pla
    tay
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
    jsr vice_probe_available
    bcc match_path_component_vice
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
match_path_component_vice:
    jsr copy_component_token_to_path_name
    bcs match_path_fail
    jsr fill_vice_manifest_dir_cache_current
    bcs match_path_fail
    jsr find_hw_dir_cache_matching_dir_path_name
    bcc match_path_component_vice_found
    jsr match_fixed_root_path_name
    bcc match_path_component_vice_ok
    bcs match_path_fail
match_path_component_vice_found:
    lda temp_dir_id
    bne match_path_component_vice_dynamic
    jsr match_fixed_root_path_name
    bcc match_path_component_vice_ok
match_path_component_vice_dynamic:
    jsr ensure_dynamic_dir_current_from_path_name
    bcs match_path_fail
match_path_component_vice_ok:
    clc
    rts
match_path_fail:
    sec
    rts

copy_component_token_to_path_name:
    ldx #$00
    ldy parse_cmd_start
copy_component_token_to_path_name_loop:
    cpx cmd_length
    bcs copy_component_token_to_path_name_done
    lda arg_buffer,y
    sta path_name_buffer,x
    inx
    iny
    cpx #MAX_LINE_LEN
    bcc copy_component_token_to_path_name_loop
copy_component_token_to_path_name_done:
    lda #$00
    sta path_name_buffer,x
    cpx #$00
    beq copy_component_token_to_path_name_fail
    clc
    rts
copy_component_token_to_path_name_fail:
    sec
    rts

match_fixed_root_path_name:
    lda path_name_buffer+0
    cmp #CMD_B
    bne match_fixed_root_try_src
    lda path_name_buffer+1
    cmp #CMD_I
    bne match_fixed_root_try_src
    lda path_name_buffer+2
    cmp #CMD_N
    bne match_fixed_root_try_src
    lda path_name_buffer+3
    bne match_fixed_root_try_src
    lda #DIR_ID_BIN
    clc
    rts
match_fixed_root_try_src:
    lda path_name_buffer+0
    cmp #CMD_S
    bne match_fixed_root_try_work
    lda path_name_buffer+1
    cmp #CMD_R
    bne match_fixed_root_try_work
    lda path_name_buffer+2
    cmp #CMD_C
    bne match_fixed_root_try_work
    lda path_name_buffer+3
    bne match_fixed_root_try_work
    lda #DIR_ID_SRC
    clc
    rts
match_fixed_root_try_work:
    lda path_name_buffer+0
    cmp #CMD_W
    bne match_fixed_root_fail
    lda path_name_buffer+1
    cmp #CMD_O
    bne match_fixed_root_fail
    lda path_name_buffer+2
    cmp #CMD_R
    bne match_fixed_root_fail
    lda path_name_buffer+3
    cmp #CMD_K
    bne match_fixed_root_fail
    lda path_name_buffer+4
    bne match_fixed_root_fail
    lda #DIR_ID_WORK
    clc
    rts
match_fixed_root_fail:
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
    tya
    pha
    lda parse_scan_index
    sta parse_cmd_start
    tya
    sec
    sbc parse_scan_index
    sta cmd_length
    beq copy_dest_bad
    jsr match_path_component
    bcc :+
    pla
    jmp copy_dest_bad
:
    sta temp_dir_id
    pla
    tay
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
    jmp copy_dest_ok
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

copy_matching_work_files:
    lda #$00
    sta wildcard_match_count
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
    jsr fs_enum_begin_current
copy_matching_work_loop:
    jsr fs_enum_next_ptr
    bcs copy_matching_work_done
    jsr copy_program_target_to_source_buffer
    jsr wildcard_match_ptr_to_source_name
    bcs copy_matching_work_next
    jsr copy_ptr_name_to_path_buffer
    jsr lookup_file_content
    bcs copy_matching_work_fail
    lda PTR
    sta copy_content_lo
    lda PTR+1
    sta copy_content_hi
    lda dest_drive
    sta temp_drive
    lda dest_dir_id
    sta temp_dir_id
    jsr store_copy_to_work
    bcs copy_matching_work_nospace
    inc wildcard_match_count
    lda source_drive
    sta temp_drive
    lda source_dir_id
    sta temp_dir_id
copy_matching_work_next:
    jmp copy_matching_work_loop
copy_matching_work_done:
    lda wildcard_match_count
    beq copy_matching_work_nomatch
    clc
    rts
copy_matching_work_nomatch:
    lda #WILDCARD_RESULT_NOMATCH
    sec
    rts
copy_matching_work_fail:
    lda #WILDCARD_RESULT_FAILED
    sec
    rts
copy_matching_work_nospace:
    lda #WILDCARD_RESULT_NOSPACE
    sec
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

delete_matching_work_files:
    lda #$00
    sta wildcard_match_count
delete_matching_work_restart:
    jsr fs_enum_begin_current
delete_matching_work_loop:
    jsr fs_enum_next_ptr
    bcs delete_matching_work_done
    jsr wildcard_match_ptr_to_source_name
    bcs delete_matching_work_next
    jsr copy_ptr_name_to_path_buffer
    jsr lookup_file_content
    bcs delete_matching_work_fail
    jsr delete_work_slot
    inc wildcard_match_count
    jmp delete_matching_work_restart
delete_matching_work_next:
    jmp delete_matching_work_loop
delete_matching_work_done:
    lda wildcard_match_count
    beq delete_matching_work_fail
    clc
    rts
delete_matching_work_fail:
    sec
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

copy_path_name_to_vice_dir_slot_ascii:
    ldy #$00
copy_vice_dir_name_loop:
    lda path_name_buffer,y
    beq copy_vice_dir_name_done
    cpy #HW_DIR_NAME_MAX-1
    bcs copy_vice_dir_name_done
    jsr screen_code_to_ascii
    sta (PTR),y
    iny
    bne copy_vice_dir_name_loop
copy_vice_dir_name_done:
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

clear_vice_tree_drive:
    stx saved_rp_x
    lda #$00
    sta file_index
clear_vice_tree_drive_loop:
    lda file_index
    cmp #VICE_TREE_DYNAMIC_MAX
    bcs clear_vice_tree_drive_done
    jsr select_vice_tree_state_table
    ldy file_index
    lda #VICE_TREE_SLOT_EMPTY
    sta (PTR),y
    jsr select_vice_tree_dir_table
    lda #DIR_ID_ROOT
    sta (PTR),y
    jsr select_vice_tree_name_slot
    ldy #$00
    lda #$00
    sta (PTR),y
    jsr select_vice_tree_content_slot
    sta (PTR),y
    inc file_index
    bne clear_vice_tree_drive_loop
clear_vice_tree_drive_done:
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
resolve_component_loop:
    ldy parse_scan_index
    cpy arg_length
    bcs resolve_validate_mount
    sty parse_cmd_start
resolve_component_scan:
    cpy arg_length
    bcs resolve_component_found
    lda arg_buffer,y
    cmp #ASCII_SLASH
    beq resolve_component_found
    iny
    bne resolve_component_scan
resolve_component_found:
    tya
    pha
    tya
    sec
    sbc parse_cmd_start
    sta cmd_length
    beq resolve_bad_path
    jsr match_path_component
    bcc :+
    pla
    jmp resolve_bad_path
:
    sta temp_dir_id
    pla
    tay
    cpy arg_length
    bcs resolve_validate_mount
    iny
    sty parse_scan_index
    cpy arg_length
    bcc resolve_component_loop
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
    cmp #3
    bcs :+
    jmp mount_arg_bad
:
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
    jmp mount_arg_path
mount_arg_drive_b:
    lda #DRIVE_B
    sta temp_drive
mount_arg_path:
    lda #2
    sta parse_scan_index
mount_arg_skip_gap:
    ldy parse_scan_index
    cpy arg_length
    bcs mount_arg_bad
    lda arg_buffer,y
    cmp #ASCII_SPACE
    bne mount_arg_copy
    iny
    sty parse_scan_index
    bne mount_arg_skip_gap
mount_arg_copy:
    jsr copy_path_name_from_parse
    bcs mount_arg_bad
    jsr detect_mount_kind_from_path_name
    bcs mount_arg_bad
mount_arg_ok:
    lda #MOUNT_STATUS_OK
    rts
mount_arg_bad:
    lda #MOUNT_STATUS_BAD
    rts

detect_mount_kind_from_path_name:
    lda #$00
    sta parse_scan_index
    ldy #$00
detect_mount_kind_scan:
    lda path_name_buffer,y
    beq detect_mount_kind_done
    cmp #ASCII_DOT
    bne detect_mount_kind_next
    tya
    clc
    adc #1
    sta parse_scan_index
detect_mount_kind_next:
    iny
    cpy #MAX_LINE_LEN
    bcc detect_mount_kind_scan
detect_mount_kind_done:
    lda parse_scan_index
    beq detect_mount_kind_fail
    tay
    lda path_name_buffer,y
    cmp #CMD_D
    bne detect_mount_kind_fail
    iny
    lda path_name_buffer,y
    cmp #$36
    beq detect_mount_kind_d64
    cmp #$37
    beq detect_mount_kind_d71
    cmp #$38
    beq detect_mount_kind_d81
    cmp #CMD_N
    beq detect_mount_kind_dnp
    jmp detect_mount_kind_fail
detect_mount_kind_d64:
    iny
    lda path_name_buffer,y
    cmp #$34
    bne detect_mount_kind_fail
    iny
    lda path_name_buffer,y
    bne detect_mount_kind_fail
    lda #MOUNT_KIND_D64
    sta temp_mount_kind
    clc
    rts
detect_mount_kind_d71:
    iny
    lda path_name_buffer,y
    cmp #$31
    bne detect_mount_kind_fail
    iny
    lda path_name_buffer,y
    bne detect_mount_kind_fail
    lda #MOUNT_KIND_D71
    sta temp_mount_kind
    clc
    rts
detect_mount_kind_d81:
    iny
    lda path_name_buffer,y
    cmp #$31
    bne detect_mount_kind_fail
    iny
    lda path_name_buffer,y
    bne detect_mount_kind_fail
    lda #MOUNT_KIND_D81
    sta temp_mount_kind
    clc
    rts
detect_mount_kind_dnp:
    iny
    lda path_name_buffer,y
    cmp #CMD_P
    bne detect_mount_kind_fail
    iny
    lda path_name_buffer,y
    bne detect_mount_kind_fail
    lda #MOUNT_KIND_DNP
    sta temp_mount_kind
    clc
    rts
detect_mount_kind_fail:
    sec
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
    beq append_selected_done
    sty path_base_index
    lda #<response_buffer
    sta PTR
    lda #>response_buffer
    sta PTR+1
    lda path_base_index
    jsr advance_ptr_by_a
    jsr append_tree_tail_to_current_ptr
    sty dir_walk_bytes
    ldy path_base_index
    tya
    clc
    adc dir_walk_bytes
    tay
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
fs_enum_begin_current:
    sty saved_enum_y
    lda #$00
    sta enum_index
    jsr uci_probe
    bcc fs_enum_begin_current_hw
    jsr vice_probe_available
    bcc fs_enum_begin_current_vice
    jmp fs_enum_begin_current_mock
fs_enum_begin_current_hw:
    jsr fill_hw_dir_cache_current
    bcc fs_enum_begin_current_done
    jmp fs_enum_begin_current_mock
fs_enum_begin_current_vice:
    jsr fill_vice_dir_cache_current
    bcc fs_enum_begin_current_done
fs_enum_begin_current_mock:
    jsr select_enum_table
fs_enum_begin_current_done:
    ldy saved_enum_y
    rts

fs_enum_next_ptr:
    sty saved_enum_y
    lda enum_index
    cmp enum_count
    bcc :+
    sec
    ldy saved_enum_y
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
    ldy saved_enum_y
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
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    beq fill_hw_dir_cache_current_open_dir
    jsr fill_flat_hw_dir_cache_current
    bcc fill_hw_dir_cache_current_done
fill_hw_dir_cache_current_open_dir:
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

fill_flat_hw_dir_cache_current:
    lda temp_dir_id
    beq :+
    sec
    rts
:
    jsr select_hw_dir_tables
    lda #$00
    sta enum_count
    ldx temp_drive
    sta hw_dir_count_table,x
    jsr select_mount_path_buffer
    jsr open_named_file_hw_from_ptr
    bcs fill_flat_hw_dir_cache_current_fail
    jsr init_flat_dir_walk
fill_flat_hw_dir_cache_sector:
    lda flat_dir_sector
    beq fill_flat_hw_dir_cache_current_done_close
    jsr seek_flat_dir_sector_hw
    bcs fill_flat_hw_dir_cache_current_fail_close
    lda #<program_image_buffer
    sta PTR
    lda #>program_image_buffer
    sta PTR+1
    lda #FLAT_DIR_READ_LEN
    jsr uci_read_open_file_into_ptr_len
    bcs fill_flat_hw_dir_cache_current_fail_close
    lda uci_data_length
    cmp #FLAT_DIR_READ_LEN
    bcc fill_flat_hw_dir_cache_current_fail_close
    jsr parse_flat_dir_sector_entries
    lda enum_count
    cmp #HW_DIR_CACHE_MAX
    bcs fill_flat_hw_dir_cache_current_done_close
    lda program_image_buffer+0
    sta flat_dir_track
    lda program_image_buffer+1
    sta flat_dir_sector
    lda flat_dir_track
    beq fill_flat_hw_dir_cache_current_done_close
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq fill_flat_hw_dir_cache_current_check_d81
    lda flat_dir_track
    cmp #D64_DIR_TRACK
    beq fill_flat_hw_dir_cache_sector
    bne fill_flat_hw_dir_cache_current_fail_close
fill_flat_hw_dir_cache_current_check_d81:
    lda flat_dir_track
    cmp #D81_DIR_TRACK
    beq fill_flat_hw_dir_cache_sector
    bne fill_flat_hw_dir_cache_current_fail_close
fill_flat_hw_dir_cache_current_done_close:
    jsr close_current_file_hw
    bcs fill_flat_hw_dir_cache_current_fail
    clc
    rts
fill_flat_hw_dir_cache_current_fail_close:
    php
    jsr close_current_file_hw
    plp
fill_flat_hw_dir_cache_current_fail:
    jsr uci_abort_transfer
    jsr uci_clear_error
    sec
    rts

init_flat_dir_walk:
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq init_flat_dir_walk_d81
    lda #D64_DIR_TRACK
    sta flat_dir_track
    lda #$01
    sta flat_dir_sector
    rts
init_flat_dir_walk_d81:
    lda #D81_DIR_TRACK
    sta flat_dir_track
    lda #D81_DIR_START_SECTOR
    sta flat_dir_sector
    rts

seek_flat_dir_sector_hw:
    jsr build_uci_file_seek_flat_dir_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs seek_flat_dir_sector_hw_fail
    jsr uci_status_is_ok
    bcs seek_flat_dir_sector_hw_fail
    clc
    rts
seek_flat_dir_sector_hw_fail:
    sec
    rts

build_uci_file_seek_flat_dir_command:
    jsr build_uci_target_header
    lda #DOS_CMD_FILE_SEEK
    sta uci_cmd_buffer+1
    lda #$00
    sta uci_cmd_buffer+2
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq build_uci_file_seek_flat_dir_d81
    lda #D64_DIR_BASE_1
    clc
    adc flat_dir_sector
    sta uci_cmd_buffer+3
    lda #D64_DIR_BASE_2
    sta uci_cmd_buffer+4
    lda #$00
    sta uci_cmd_buffer+5
    lda #6
    rts
build_uci_file_seek_flat_dir_d81:
    lda #D81_DIR_BASE_1
    clc
    adc flat_dir_sector
    sta uci_cmd_buffer+3
    lda #D81_DIR_BASE_2
    sta uci_cmd_buffer+4
    lda #$00
    sta uci_cmd_buffer+5
    lda #6
    rts

open_flat_mount_image_hw:
    jsr current_mount_is_flat
    bne open_flat_mount_image_hw_fail
    jsr select_mount_path_buffer
    jmp open_named_file_hw_from_ptr
open_flat_mount_image_rw_hw:
    jsr current_mount_is_flat
    bne open_flat_mount_image_hw_fail
    jsr select_mount_path_buffer
    jmp open_named_file_rw_hw_from_ptr
open_flat_mount_image_hw_fail:
    sec
    rts

find_flat_file_entry_in_open_image:
    jsr init_flat_dir_walk
find_flat_file_entry_sector:
    lda flat_dir_sector
    beq find_flat_file_entry_miss
    jsr seek_flat_dir_sector_hw
    bcs find_flat_file_entry_fail
    lda #<flat_sector_buffer
    sta PTR
    lda #>flat_sector_buffer
    sta PTR+1
    lda #FLAT_DIR_READ_LEN
    jsr uci_read_open_file_into_ptr_len
    bcs find_flat_file_entry_fail
    lda uci_data_length
    cmp #FLAT_DIR_READ_LEN
    bcc find_flat_file_entry_fail
    jsr find_flat_file_entry_in_sector
    bcc find_flat_file_entry_found
    lda flat_sector_buffer+0
    sta flat_dir_track
    lda flat_sector_buffer+1
    sta flat_dir_sector
    lda flat_dir_track
    beq find_flat_file_entry_miss
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq find_flat_file_entry_check_d81
    lda flat_dir_track
    cmp #D64_DIR_TRACK
    beq find_flat_file_entry_sector
    bne find_flat_file_entry_fail
find_flat_file_entry_check_d81:
    lda flat_dir_track
    cmp #D81_DIR_TRACK
    beq find_flat_file_entry_sector
find_flat_file_entry_fail:
    lda #FLAT_LOOKUP_FAIL
    sec
    rts
find_flat_file_entry_miss:
    lda #FLAT_LOOKUP_NOFILE
    sec
    rts
find_flat_file_entry_found:
    clc
    rts

find_flat_file_entry_in_sector:
    lda #$02
    sta flat_dir_offset
find_flat_file_entry_in_sector_loop:
    ldy flat_dir_offset
    lda flat_sector_buffer,y
    beq find_flat_file_entry_in_sector_next
    jsr load_flat_entry_name_buffer
    lda #<flat_entry_name_buffer
    sta PTR
    lda #>flat_entry_name_buffer
    sta PTR+1
    jsr compare_ptr_to_path_name
    bcc find_flat_file_entry_hit
find_flat_file_entry_in_sector_next:
    lda flat_dir_offset
    cmp #$E2
    bcs find_flat_file_entry_in_sector_miss
    clc
    adc #$20
    sta flat_dir_offset
    jmp find_flat_file_entry_in_sector_loop
find_flat_file_entry_hit:
    lda flat_dir_track
    sta flat_hit_dir_track
    lda flat_dir_sector
    sta flat_hit_dir_sector
    lda flat_dir_offset
    sta flat_hit_dir_offset
    ldy flat_dir_offset
    iny
    lda flat_sector_buffer,y
    sta flat_file_track
    iny
    lda flat_sector_buffer,y
    sta flat_file_sector
    clc
    rts
find_flat_file_entry_in_sector_miss:
    sec
    rts

load_flat_entry_name_buffer:
    ldx flat_dir_offset
    inx
    inx
    inx
    ldy #$00
load_flat_entry_name_loop:
    cpy #$10
    bcs load_flat_entry_name_done
    lda flat_sector_buffer,x
    beq load_flat_entry_name_done
    cmp #$A0
    beq load_flat_entry_name_done
    and #$7F
    beq load_flat_entry_name_done
    sta flat_entry_name_buffer,y
    inx
    iny
    bne load_flat_entry_name_loop
load_flat_entry_name_done:
    lda #$00
    sta flat_entry_name_buffer,y
    rts

read_flat_response_open_hw:
    lda #<response_buffer
    sta PTR
    lda #>response_buffer
    sta PTR+1
    lda #MAX_RESPONSE_LEN-1
    sta flat_remaining
    lda #FLAT_READ_MODE_TRUNCATE
    sta flat_read_mode
    jsr read_flat_open_file_into_target
    bcs read_flat_response_open_hw_fail
    ldy flat_total
    lda #$00
    sta response_buffer,y
    lda #<response_buffer
    sta PTR
    lda #>response_buffer
    sta PTR+1
    clc
    rts
read_flat_response_open_hw_fail:
    sec
    rts

load_flat_program_image_open_hw:
    lda #<program_image_buffer
    sta PTR
    lda #>program_image_buffer
    sta PTR+1
    lda #PROGRAM_IMAGE_MAX
    sta flat_remaining
    lda #FLAT_READ_MODE_STRICT
    sta flat_read_mode
    jsr read_flat_open_file_into_target
    bcs load_flat_program_image_open_hw_fail
    lda flat_total
    sta program_image_len_lo
    lda #$00
    sta program_image_len_hi
    lda #RUN_STATUS_OK
    clc
    rts
load_flat_program_image_open_hw_fail:
    cmp #FLAT_READ_TOO_LARGE
    beq load_flat_program_image_open_hw_large
    lda #RUN_STATUS_LOAD_FAILED
    sec
    rts
load_flat_program_image_open_hw_large:
    lda #RUN_STATUS_TOO_LARGE
    sec
    rts

read_flat_open_file_into_target:
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    lda #$00
    sta flat_total
read_flat_open_file_loop:
    lda flat_file_track
    beq read_flat_open_file_done
    jsr read_flat_sector_buffer_hw
    bcs read_flat_open_file_fail
    lda flat_sector_buffer+0
    sta flat_dir_track
    lda flat_sector_buffer+1
    sta flat_dir_sector
    lda flat_dir_track
    bne read_flat_open_file_full
    lda flat_dir_sector
    beq read_flat_open_file_fail
    sec
    sbc #$01
    sta flat_copy_count
    jmp read_flat_open_file_copy
read_flat_open_file_full:
    lda #$FE
    sta flat_copy_count
read_flat_open_file_copy:
    jsr copy_flat_sector_payload
    bcs read_flat_open_file_fail
    lda flat_read_mode
    beq read_flat_open_file_truncate
    lda flat_remaining
    bne read_flat_open_file_next
    lda flat_dir_track
    beq read_flat_open_file_done
    lda #FLAT_READ_TOO_LARGE
    sec
    rts
read_flat_open_file_truncate:
    lda flat_remaining
    beq read_flat_open_file_done
read_flat_open_file_next:
    lda flat_dir_track
    sta flat_file_track
    lda flat_dir_sector
    sta flat_file_sector
    jmp read_flat_open_file_loop
read_flat_open_file_done:
    clc
    rts
read_flat_open_file_fail:
    lda #FLAT_READ_FAIL
    sec
    rts

copy_flat_sector_payload:
    lda flat_copy_count
    beq copy_flat_sector_payload_done
    cmp flat_remaining
    bcc copy_flat_sector_payload_fit
    beq copy_flat_sector_payload_fit
    lda flat_read_mode
    beq copy_flat_sector_payload_truncate
    lda #FLAT_READ_TOO_LARGE
    sec
    rts
copy_flat_sector_payload_truncate:
    lda flat_remaining
    sta flat_copy_count
    beq copy_flat_sector_payload_done
copy_flat_sector_payload_fit:
    ldy #$00
copy_flat_sector_payload_loop:
    cpy flat_copy_count
    bcs copy_flat_sector_payload_finish
    lda flat_sector_buffer+2,y
    sta (SCREEN_PTR),y
    iny
    bne copy_flat_sector_payload_loop
copy_flat_sector_payload_finish:
    tya
    clc
    adc SCREEN_PTR
    sta SCREEN_PTR
    bcc :+
    inc SCREEN_PTR+1
:
    clc
    lda flat_total
    adc flat_copy_count
    sta flat_total
    sec
    lda flat_remaining
    sbc flat_copy_count
    sta flat_remaining
copy_flat_sector_payload_done:
    clc
    rts

read_flat_sector_buffer_hw:
    lda #<flat_sector_buffer
    sta PTR
    lda #>flat_sector_buffer
    sta PTR+1
    jmp read_flat_sector_into_ptr_hw

read_flat_sector_into_ptr_hw:
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr seek_flat_file_sector_hw
    bcs read_flat_sector_buffer_hw_fail
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    lda #FLAT_SECTOR_READ_LEN
    jsr uci_read_open_file_into_ptr_len
    bcs read_flat_sector_buffer_hw_fail
    lda uci_data_length
    cmp #FLAT_SECTOR_READ_LEN
    bcc read_flat_sector_buffer_hw_fail
    clc
    lda SCREEN_PTR
    adc #FLAT_SECTOR_READ_LEN
    sta PTR
    lda SCREEN_PTR+1
    adc #$00
    sta PTR+1
    lda #$01
    jsr uci_read_open_file_into_ptr_len
    bcs read_flat_sector_buffer_hw_fail
    lda uci_data_length
    cmp #$01
    bcc read_flat_sector_buffer_hw_fail
    clc
    rts
read_flat_sector_buffer_hw_fail:
    sec
    rts

write_flat_sector_from_ptr_hw:
    lda PTR
    sta SCREEN_PTR
    lda PTR+1
    sta SCREEN_PTR+1
    jsr seek_flat_file_sector_hw
    bcs write_flat_sector_from_ptr_hw_fail
    lda SCREEN_PTR
    sta PTR
    lda SCREEN_PTR+1
    sta PTR+1
    lda #UCI_WRITE_DATA_MAX
    jsr uci_write_open_file_from_ptr_len
    bcs write_flat_sector_from_ptr_hw_fail
    clc
    lda SCREEN_PTR
    adc #UCI_WRITE_DATA_MAX
    sta PTR
    lda SCREEN_PTR+1
    adc #$00
    sta PTR+1
    lda #5
    jsr uci_write_open_file_from_ptr_len
    bcs write_flat_sector_from_ptr_hw_fail
    clc
    rts
write_flat_sector_from_ptr_hw_fail:
    sec
    rts

seek_flat_file_sector_hw:
    jsr build_uci_file_seek_flat_file_command
    pha
    lda #<uci_cmd_buffer
    sta PTR
    lda #>uci_cmd_buffer
    sta PTR+1
    pla
    jsr uci_issue_status_only
    bcs seek_flat_file_sector_hw_fail
    jsr uci_status_is_ok
    bcs seek_flat_file_sector_hw_fail
    clc
    rts
seek_flat_file_sector_hw_fail:
    sec
    rts

build_uci_file_seek_flat_file_command:
    jsr compute_flat_file_sector_index
    jsr build_uci_target_header
    lda #DOS_CMD_FILE_SEEK
    sta uci_cmd_buffer+1
    lda #$00
    sta uci_cmd_buffer+2
    lda flat_sector_index_lo
    sta uci_cmd_buffer+3
    lda flat_sector_index_hi
    sta uci_cmd_buffer+4
    lda #$00
    sta uci_cmd_buffer+5
    lda #6
    rts

compute_flat_file_sector_index:
    lda #$00
    sta flat_sector_index_lo
    sta flat_sector_index_hi
    lda temp_mount_kind
    cmp #MOUNT_KIND_D81
    beq compute_flat_file_sector_index_d81
    lda #$01
    sta flat_track_index
compute_flat_file_sector_index_loop:
    lda flat_track_index
    cmp flat_file_track
    bcs compute_flat_file_sector_index_add_sector
    jsr add_flat_track_sector_count
    inc flat_track_index
    bne compute_flat_file_sector_index_loop
compute_flat_file_sector_index_add_sector:
    clc
    lda flat_sector_index_lo
    adc flat_file_sector
    sta flat_sector_index_lo
    bcc :+
    inc flat_sector_index_hi
:
    rts
compute_flat_file_sector_index_d81:
    lda flat_file_track
    beq compute_flat_file_sector_index_add_sector
    sec
    sbc #$01
    tax
    beq compute_flat_file_sector_index_add_sector
compute_flat_file_sector_index_d81_loop:
    clc
    lda flat_sector_index_lo
    adc #40
    sta flat_sector_index_lo
    bcc :+
    inc flat_sector_index_hi
:
    dex
    bne compute_flat_file_sector_index_d81_loop
    jmp compute_flat_file_sector_index_add_sector

add_flat_track_sector_count:
    lda flat_track_index
    ldx temp_mount_kind
    cpx #MOUNT_KIND_D71
    bne add_flat_track_sector_count_zone
    cmp #36
    bcc add_flat_track_sector_count_zone
    sec
    sbc #35
add_flat_track_sector_count_zone:
    cmp #18
    bcc add_flat_track_sector_count_21
    cmp #25
    bcc add_flat_track_sector_count_19
    cmp #31
    bcc add_flat_track_sector_count_18
    lda #17
    bne add_flat_track_sector_count_apply
add_flat_track_sector_count_21:
    lda #21
    bne add_flat_track_sector_count_apply
add_flat_track_sector_count_19:
    lda #19
    bne add_flat_track_sector_count_apply
add_flat_track_sector_count_18:
    lda #18
add_flat_track_sector_count_apply:
    clc
    adc flat_sector_index_lo
    sta flat_sector_index_lo
    bcc :+
    inc flat_sector_index_hi
:
    rts

parse_flat_dir_sector_entries:
    lda #$02
    sta flat_dir_offset
parse_flat_dir_sector_entries_loop:
    lda enum_count
    cmp #HW_DIR_CACHE_MAX
    bcs parse_flat_dir_sector_entries_done
    ldy flat_dir_offset
    lda program_image_buffer,y
    beq parse_flat_dir_sector_entries_next
    jsr store_flat_dir_entry_from_sector
parse_flat_dir_sector_entries_next:
    lda flat_dir_offset
    cmp #$E2
    bcs parse_flat_dir_sector_entries_done
    clc
    adc #$20
    sta flat_dir_offset
    jmp parse_flat_dir_sector_entries_loop
parse_flat_dir_sector_entries_done:
    rts

store_flat_dir_entry_from_sector:
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
    ldx flat_dir_offset
    inx
    inx
    inx
    ldy #$00
store_flat_dir_entry_copy:
    cpy #$10
    bcs store_flat_dir_entry_done
    lda program_image_buffer,x
    beq store_flat_dir_entry_done
    cmp #$A0
    beq store_flat_dir_entry_done
    and #$7F
    beq store_flat_dir_entry_done
    sta (PTR),y
    inx
    iny
    cpy #HW_DIR_NAME_MAX
    bcc store_flat_dir_entry_copy
store_flat_dir_entry_done:
    lda #$00
    sta (PTR),y
    cpy #$00
    beq store_flat_dir_entry_skip
    inc enum_count
    ldx temp_drive
    lda enum_count
    sta hw_dir_count_table,x
store_flat_dir_entry_skip:
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

lookup_file_content_strict:
    jsr select_file_table
    lda #$00
    sta file_index
lookup_file_strict_loop:
    lda file_index
    cmp file_count
    bcs lookup_file_strict_miss
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
    jsr compare_ptr_to_path_name_strict
    bcc lookup_file_strict_hit
    inc file_index
    bne lookup_file_strict_loop
lookup_file_strict_miss:
    lda #$00
    sta matched_name_lo
    sta matched_name_hi
    sec
    rts
lookup_file_strict_hit:
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

compare_ptr_to_path_name_strict:
    ldy #$00
    ldx #$00
compare_path_strict_loop:
    lda (PTR),y
    beq compare_path_strict_end
    lda path_name_buffer,x
    beq compare_path_strict_fail
    lda (PTR),y
    jsr normalize_output_char
    cmp path_name_buffer,x
    bne compare_path_strict_fail
    iny
    inx
    bne compare_path_strict_loop
compare_path_strict_end:
    lda path_name_buffer,x
    beq compare_path_strict_ok
compare_path_strict_fail:
    sec
    rts
compare_path_strict_ok:
    clc
    rts

compare_dir_ptr_to_path_name:
    ldy #$00
    ldx #$00
compare_dir_path_loop:
    lda (PTR),y
    beq compare_dir_path_candidate_end
    cmp #ASCII_SLASH
    beq compare_dir_path_candidate_end
    lda path_name_buffer,x
    beq compare_dir_path_fail
    lda (PTR),y
    jsr normalize_output_char
    cmp path_name_buffer,x
    bne compare_dir_path_fail
    iny
    inx
    bne compare_dir_path_loop
compare_dir_path_candidate_end:
    lda path_name_buffer,x
    beq compare_dir_path_ok
compare_dir_path_fail:
    sec
    rts
compare_dir_path_ok:
    clc
    rts

compare_source_name_to_path_name:
    ldy #$00
compare_source_name_to_path_name_loop:
    lda source_name_buffer,y
    cmp path_name_buffer,y
    bne compare_source_name_to_path_name_fail
    beq :+
:
    lda source_name_buffer,y
    beq compare_source_name_to_path_name_ok
    iny
    bne compare_source_name_to_path_name_loop
compare_source_name_to_path_name_fail:
    sec
    rts
compare_source_name_to_path_name_ok:
    clc
    rts

classify_path_name_wildcard:
    lda #WILDCARD_NONE
    sta wildcard_mode
    lda #$00
    sta wildcard_span
    ldy #$00
classify_wildcard_scan:
    lda path_name_buffer,y
    beq classify_wildcard_none
    cmp #ASCII_ASTERISK
    beq classify_wildcard_found
    iny
    bne classify_wildcard_scan
classify_wildcard_none:
    clc
    rts
classify_wildcard_found:
    cpy #$00
    bne classify_wildcard_stem
    lda path_name_buffer+1
    beq classify_wildcard_all
    cmp #ASCII_DOT
    bne classify_wildcard_bad
    lda path_name_buffer+2
    beq classify_wildcard_bad
    cmp #ASCII_ASTERISK
    beq classify_wildcard_all_dot
    lda #WILDCARD_EXT
    sta wildcard_mode
    lda #$02
    sta wildcard_span
    ldx #$02
classify_wildcard_ext_scan:
    lda path_name_buffer,x
    beq classify_wildcard_ok
    cmp #ASCII_ASTERISK
    beq classify_wildcard_bad
    inx
    bne classify_wildcard_ext_scan
classify_wildcard_stem:
    lda path_name_buffer+1,y
    bne classify_wildcard_bad
    dey
    bmi classify_wildcard_bad
    lda path_name_buffer,y
    cmp #ASCII_DOT
    bne classify_wildcard_bad
    tya
    beq classify_wildcard_bad
    sta wildcard_span
    lda #WILDCARD_STEM
    sta wildcard_mode
    jmp classify_wildcard_ok
classify_wildcard_all_dot:
    lda path_name_buffer+3
    bne classify_wildcard_bad
classify_wildcard_all:
    lda #WILDCARD_ALL
    sta wildcard_mode
classify_wildcard_ok:
    clc
    rts
classify_wildcard_bad:
    sec
    rts

wildcard_match_ptr_to_source_name:
    lda wildcard_mode
    cmp #WILDCARD_ALL
    beq wildcard_match_all
    cmp #WILDCARD_EXT
    beq wildcard_match_ext
    cmp #WILDCARD_STEM
    beq wildcard_match_stem
    sec
    rts

wildcard_match_all:
    ldy #$00
wildcard_match_all_loop:
    lda (PTR),y
    beq wildcard_match_ok
    cmp #ASCII_SLASH
    beq wildcard_match_fail
    iny
    bne wildcard_match_all_loop

wildcard_match_ext:
    ldy #$00
wildcard_match_ext_find_dot:
    lda (PTR),y
    beq wildcard_match_fail
    cmp #ASCII_SLASH
    beq wildcard_match_fail
    cmp #ASCII_DOT
    beq wildcard_match_ext_compare
    iny
    bne wildcard_match_ext_find_dot
wildcard_match_ext_compare:
    iny
    ldx wildcard_span
wildcard_match_ext_loop:
    lda source_name_buffer,x
    beq wildcard_match_ext_end
    lda (PTR),y
    beq wildcard_match_fail
    cmp #ASCII_SLASH
    beq wildcard_match_fail
    jsr normalize_output_char
    cmp source_name_buffer,x
    bne wildcard_match_fail
    iny
    inx
    bne wildcard_match_ext_loop
wildcard_match_ext_end:
    lda (PTR),y
    beq wildcard_match_ok
    cmp #ASCII_SLASH
    beq wildcard_match_fail
    jmp wildcard_match_fail

wildcard_match_stem:
    ldy #$00
    ldx #$00
wildcard_match_stem_loop:
    cpx wildcard_span
    bcs wildcard_match_stem_boundary
    lda (PTR),y
    beq wildcard_match_fail
    cmp #ASCII_SLASH
    beq wildcard_match_fail
    cmp #ASCII_DOT
    beq wildcard_match_fail
    jsr normalize_output_char
    cmp source_name_buffer,x
    bne wildcard_match_fail
    iny
    inx
    bne wildcard_match_stem_loop
wildcard_match_stem_boundary:
    lda (PTR),y
    beq wildcard_match_ok
    cmp #ASCII_DOT
    beq wildcard_match_ok
    cmp #ASCII_SLASH
    beq wildcard_match_fail
wildcard_match_fail:
    sec
    rts
wildcard_match_ok:
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

select_file_content_for_file_index:
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
    rts

load_dynamic_work_name_ptr:
    jsr select_dynamic_work_file_table
    lda file_index
    asl
    asl
    tay
    lda (SCREEN_PTR),y
    sta PTR
    iny
    lda (SCREEN_PTR),y
    sta PTR+1
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

select_vice_dir_state_table:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_vice_dir_state_table_a
    lda #<vice_dir_state_b
    sta PTR
    lda #>vice_dir_state_b
    sta PTR+1
    rts
select_vice_dir_state_table_a:
    lda #<vice_dir_state_a
    sta PTR
    lda #>vice_dir_state_a
    sta PTR+1
    rts

select_vice_dir_parent_table:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_vice_dir_parent_table_a
    lda #<vice_dir_parent_b
    sta PTR
    lda #>vice_dir_parent_b
    sta PTR+1
    rts
select_vice_dir_parent_table_a:
    lda #<vice_dir_parent_a
    sta PTR
    lda #>vice_dir_parent_a
    sta PTR+1
    rts

select_vice_dir_name_slot:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_vice_dir_name_slot_a
    lda #<vice_dir_names_b
    sta PTR
    lda #>vice_dir_names_b
    sta PTR+1
    jmp advance_vice_dir_name_slot
select_vice_dir_name_slot_a:
    lda #<vice_dir_names_a
    sta PTR
    lda #>vice_dir_names_a
    sta PTR+1
advance_vice_dir_name_slot:
    ldy file_index
    beq select_vice_dir_name_slot_done
advance_vice_dir_name_slot_loop:
    clc
    lda PTR
    adc #HW_DIR_NAME_STRIDE
    sta PTR
    bcc :+
    inc PTR+1
:
    dey
    bne advance_vice_dir_name_slot_loop
select_vice_dir_name_slot_done:
    rts

select_vice_dir_name_slot_to_screen_ptr:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_vice_dir_name_slot_to_screen_ptr_a
    lda #<vice_dir_names_b
    sta SCREEN_PTR
    lda #>vice_dir_names_b
    sta SCREEN_PTR+1
    jmp advance_vice_dir_name_screen_ptr
select_vice_dir_name_slot_to_screen_ptr_a:
    lda #<vice_dir_names_a
    sta SCREEN_PTR
    lda #>vice_dir_names_a
    sta SCREEN_PTR+1
advance_vice_dir_name_screen_ptr:
    ldy file_index
    beq select_vice_dir_name_slot_to_screen_ptr_done
advance_vice_dir_name_screen_ptr_loop:
    clc
    lda SCREEN_PTR
    adc #HW_DIR_NAME_STRIDE
    sta SCREEN_PTR
    bcc :+
    inc SCREEN_PTR+1
:
    dey
    bne advance_vice_dir_name_screen_ptr_loop
select_vice_dir_name_slot_to_screen_ptr_done:
    rts

load_vice_dir_state_for_index:
    jsr select_vice_dir_state_table
    ldy file_index
    lda (PTR),y
    rts

load_vice_dir_parent_for_index:
    jsr select_vice_dir_parent_table
    ldy file_index
    lda (PTR),y
    rts

store_vice_dir_state_for_index:
    sta vice_dir_state_temp
    jsr select_vice_dir_state_table
    ldy file_index
    lda vice_dir_state_temp
    sta (PTR),y
    rts

store_vice_dir_parent_for_index:
    sta vice_dir_parent_temp
    jsr select_vice_dir_parent_table
    ldy file_index
    lda vice_dir_parent_temp
    sta (PTR),y
    rts

clear_vice_dir_slot:
    jsr select_vice_dir_state_table
    ldy file_index
    lda #VICE_DIR_SLOT_EMPTY
    sta (PTR),y
    jsr select_vice_dir_parent_table
    lda #DIR_ID_ROOT
    sta (PTR),y
    jsr select_vice_dir_name_slot
    ldy #$00
    lda #$00
    sta (PTR),y
    rts

clear_vice_dir_drive:
    stx saved_rp_x
    lda #$00
    sta file_index
clear_vice_dir_drive_loop:
    lda file_index
    cmp #VICE_DIR_DYNAMIC_MAX
    bcs clear_vice_dir_drive_done
    jsr clear_vice_dir_slot
    inc file_index
    bne clear_vice_dir_drive_loop
clear_vice_dir_drive_done:
    ldx saved_rp_x
    rts

vice_dir_alloc_slot:
    lda #$00
    sta file_index
vice_dir_alloc_slot_loop:
    lda file_index
    cmp #VICE_DIR_DYNAMIC_MAX
    bcs vice_dir_alloc_slot_fail
    jsr load_vice_dir_state_for_index
    beq vice_dir_alloc_slot_ok
    inc file_index
    bne vice_dir_alloc_slot_loop
vice_dir_alloc_slot_fail:
    sec
    rts
vice_dir_alloc_slot_ok:
    clc
    rts

vice_dir_find_current_slot:
    lda #$00
    sta file_index
vice_dir_find_current_slot_loop:
    lda file_index
    cmp #VICE_DIR_DYNAMIC_MAX
    bcs vice_dir_find_current_slot_fail
    jsr load_vice_dir_state_for_index
    beq vice_dir_find_current_slot_next
    sta vice_dir_state_temp
    jsr load_vice_dir_parent_for_index
    cmp temp_dir_id
    bne vice_dir_find_current_slot_next
    jsr select_vice_dir_name_slot
    jsr compare_ptr_to_path_name
    bcc vice_dir_find_current_slot_hit
vice_dir_find_current_slot_next:
    inc file_index
    bne vice_dir_find_current_slot_loop
vice_dir_find_current_slot_fail:
    sec
    rts
vice_dir_find_current_slot_hit:
    lda vice_dir_state_temp
    clc
    rts

ensure_dynamic_dir_current_from_path_name:
    jsr vice_dir_find_current_slot
    bcc ensure_dynamic_dir_current_existing
    jsr vice_dir_alloc_slot
    bcs ensure_dynamic_dir_current_fail
    lda temp_dir_id
    jsr store_vice_dir_parent_for_index
    jsr select_vice_dir_name_slot
    jsr copy_path_name_to_slot_ascii
    lda #VICE_DIR_SLOT_LIVE
    jsr store_vice_dir_state_for_index
    lda file_index
    clc
    adc #DIR_ID_DYNAMIC_BASE
    clc
    rts
ensure_dynamic_dir_current_existing:
    cmp #VICE_DIR_SLOT_TOMBSTONE
    beq ensure_dynamic_dir_current_fail
    lda file_index
    clc
    adc #DIR_ID_DYNAMIC_BASE
    clc
    rts
ensure_dynamic_dir_current_fail:
    sec
    rts

select_vice_tree_state_table:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_vice_tree_state_table_a
    lda #<vice_tree_state_b
    sta PTR
    lda #>vice_tree_state_b
    sta PTR+1
    rts
select_vice_tree_state_table_a:
    lda #<vice_tree_state_a
    sta PTR
    lda #>vice_tree_state_a
    sta PTR+1
    rts

select_vice_tree_dir_table:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_vice_tree_dir_table_a
    lda #<vice_tree_dir_b
    sta PTR
    lda #>vice_tree_dir_b
    sta PTR+1
    rts
select_vice_tree_dir_table_a:
    lda #<vice_tree_dir_a
    sta PTR
    lda #>vice_tree_dir_a
    sta PTR+1
    rts

select_vice_tree_name_slot:
    ldx temp_drive
    cpx #DRIVE_A
    beq select_vice_tree_name_slot_a
    lda #<vice_tree_names_b
    sta PTR
    lda #>vice_tree_names_b
    sta PTR+1
    jmp advance_vice_tree_name_slot
select_vice_tree_name_slot_a:
    lda #<vice_tree_names_a
    sta PTR
    lda #>vice_tree_names_a
    sta PTR+1
advance_vice_tree_name_slot:
    ldy file_index
    beq select_vice_tree_name_slot_done
advance_vice_tree_name_slot_loop:
    clc
    lda PTR
    adc #HW_DIR_NAME_STRIDE
    sta PTR
    bcc :+
    inc PTR+1
:
    dey
    bne advance_vice_tree_name_slot_loop
select_vice_tree_name_slot_done:
    rts

reu_init:
    lda #$00
    sta reu_present
    lda C64_PORT
    sta reu_saved_port
    and #$F8
    ora #C64_PORT_IO_ON
    sta C64_PORT
    lda #$55
    sta REU_REUADDR_LO
    lda REU_REUADDR_LO
    cmp #$55
    bne reu_init_restore
    lda #$AA
    sta REU_REUADDR_LO
    lda REU_REUADDR_LO
    cmp #$AA
    bne reu_init_restore
    lda #$01
    sta reu_present
reu_init_restore:
    lda reu_saved_port
    sta C64_PORT
    rts

set_vice_tree_slot_cache_ptr:
    lda #<vice_tree_slot_cache
    sta PTR
    lda #>vice_tree_slot_cache
    sta PTR+1
    rts

select_vice_tree_reu_slot_addr:
    ldy file_index
    ldx temp_drive
    cpx #DRIVE_A
    beq select_vice_tree_reu_slot_addr_a
    lda vice_tree_reu_slot_b_lo,y
    sta reu_slot_lo
    lda vice_tree_reu_slot_b_hi,y
    sta reu_slot_hi
    lda #$00
    sta reu_slot_bank
    rts
select_vice_tree_reu_slot_addr_a:
    lda vice_tree_reu_slot_a_lo,y
    sta reu_slot_lo
    lda vice_tree_reu_slot_a_hi,y
    sta reu_slot_hi
    lda #$00
    sta reu_slot_bank
    rts

reu_transfer_vice_tree_slot_cache:
    sta reu_command_temp
    lda C64_PORT
    sta reu_saved_port
    and #$F8
    ora #C64_PORT_IO_ON
    sta C64_PORT
    lda #<vice_tree_slot_cache
    sta REU_C64ADDR_LO
    lda #>vice_tree_slot_cache
    sta REU_C64ADDR_HI
    lda reu_slot_lo
    sta REU_REUADDR_LO
    lda reu_slot_hi
    sta REU_REUADDR_HI
    lda reu_slot_bank
    sta REU_REUADDR_BANK
    lda #<PROGRAM_IMAGE_MAX
    sta REU_COUNT_LO
    lda #>PROGRAM_IMAGE_MAX
    sta REU_COUNT_HI
    lda #$00
    sta REU_IRQMASK
    sta REU_CONTROL
    lda reu_command_temp
    sta REU_COMMAND
    lda reu_saved_port
    and #$F8
    sta C64_PORT
    lda #$00
    sta REU_TRIGGER
    lda reu_saved_port
    sta C64_PORT
    lda REU_STATUS
    rts

save_selected_vice_tree_content_slot:
    jsr reu_init
    lda reu_present
    beq save_selected_vice_tree_content_slot_done
    jsr select_vice_tree_reu_slot_addr
    lda #REU_CMD_COPY_C64_TO_REU
    jsr reu_transfer_vice_tree_slot_cache
save_selected_vice_tree_content_slot_done:
    clc
    rts

select_vice_tree_content_slot:
    jsr set_vice_tree_slot_cache_ptr
    jsr reu_init
    lda reu_present
    beq select_vice_tree_content_slot_done
    jsr select_vice_tree_reu_slot_addr
    lda #REU_CMD_COPY_REU_TO_C64
    jsr reu_transfer_vice_tree_slot_cache
select_vice_tree_content_slot_done:
    clc
    rts

load_vice_tree_state_for_index:
    jsr select_vice_tree_state_table
    ldy file_index
    lda (PTR),y
    rts

load_vice_tree_dir_for_index:
    jsr select_vice_tree_dir_table
    ldy file_index
    lda (PTR),y
    rts

vice_tree_alloc_slot:
    lda #$00
    sta file_index
vice_tree_alloc_slot_loop:
    lda file_index
    cmp #VICE_TREE_DYNAMIC_MAX
    bcs vice_tree_alloc_slot_fail
    jsr load_vice_tree_state_for_index
    beq vice_tree_alloc_slot_ok
    inc file_index
    bne vice_tree_alloc_slot_loop
vice_tree_alloc_slot_fail:
    sec
    rts
vice_tree_alloc_slot_ok:
    clc
    rts

vice_tree_find_current_slot:
    lda #$00
    sta file_index
vice_tree_find_current_slot_loop:
    lda file_index
    cmp #VICE_TREE_DYNAMIC_MAX
    bcs vice_tree_find_current_slot_fail
    jsr load_vice_tree_state_for_index
    beq vice_tree_find_current_slot_next
    sta saved_response_y
    jsr load_vice_tree_dir_for_index
    cmp temp_dir_id
    bne vice_tree_find_current_slot_next
    jsr select_vice_tree_name_slot
    jsr compare_ptr_to_path_name
    bcc vice_tree_find_current_slot_hit
vice_tree_find_current_slot_next:
    inc file_index
    bne vice_tree_find_current_slot_loop
vice_tree_find_current_slot_fail:
    sec
    rts
vice_tree_find_current_slot_hit:
    lda saved_response_y
    clc
    rts

vice_tree_find_current_slot_strict:
    lda #$00
    sta file_index
vice_tree_find_current_slot_strict_loop:
    lda file_index
    cmp #VICE_TREE_DYNAMIC_MAX
    bcs vice_tree_find_current_slot_strict_fail
    jsr load_vice_tree_state_for_index
    beq vice_tree_find_current_slot_strict_next
    sta saved_response_y
    jsr load_vice_tree_dir_for_index
    cmp temp_dir_id
    bne vice_tree_find_current_slot_strict_next
    jsr select_vice_tree_name_slot
    jsr compare_ptr_to_path_name_strict
    bcc vice_tree_find_current_slot_strict_hit
vice_tree_find_current_slot_strict_next:
    inc file_index
    bne vice_tree_find_current_slot_strict_loop
vice_tree_find_current_slot_strict_fail:
    sec
    rts
vice_tree_find_current_slot_strict_hit:
    lda saved_response_y
    clc
    rts

copy_path_name_to_vice_tree_slot_ascii:
    ldy #$00
copy_path_name_to_vice_tree_slot_loop:
    lda path_name_buffer,y
    beq copy_path_name_to_vice_tree_slot_done
    cpy #HW_DIR_NAME_MAX-1
    bcs copy_path_name_to_vice_tree_slot_done
    jsr screen_code_to_ascii
    sta (PTR),y
    iny
    bne copy_path_name_to_vice_tree_slot_loop
copy_path_name_to_vice_tree_slot_done:
    lda #$00
    sta (PTR),y
    rts

copy_screen_ptr_to_vice_tree_slot_content:
    jsr select_vice_tree_content_slot
    ldy #$00
copy_screen_ptr_to_vice_tree_slot_content_loop:
    lda (SCREEN_PTR),y
    sta (PTR),y
    beq copy_screen_ptr_to_vice_tree_slot_content_done
    iny
    cpy #PROGRAM_IMAGE_MAX
    bcc copy_screen_ptr_to_vice_tree_slot_content_loop
    dey
    lda #$00
    sta (PTR),y
copy_screen_ptr_to_vice_tree_slot_content_done:
    jmp save_selected_vice_tree_content_slot

clear_vice_tree_slot:
    jsr select_vice_tree_state_table
    ldy file_index
    lda #VICE_TREE_SLOT_EMPTY
    sta (PTR),y
    jsr select_vice_tree_dir_table
    lda #DIR_ID_ROOT
    sta (PTR),y
    jsr select_vice_tree_name_slot
    ldy #$00
    lda #$00
    sta (PTR),y
    jsr select_vice_tree_content_slot
    sta (PTR),y
    jmp save_selected_vice_tree_content_slot

store_vice_tree_state_for_index:
    sta vice_tree_state_temp
    jsr select_vice_tree_state_table
    ldy file_index
    lda vice_tree_state_temp
    sta (PTR),y
    rts

store_vice_tree_dir_for_index:
    pha
    jsr select_vice_tree_dir_table
    ldy file_index
    pla
    sta (PTR),y
    rts

query_file_vice_open_current:
    jsr build_vice_open_path_from_name
    lda #VICE_LFN_FILE
    sta vice_lfn
    lda #VICE_SA_READ
    sta vice_secondary
    jsr vice_open_read_from_ptr
    bcs query_file_vice_open_current_fail
    jsr vice_close_current_file
    clc
    rts
query_file_vice_open_current_fail:
    sec
    rts

query_file_vice_host_current:
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    bne query_file_vice_host_current_open
    jsr fill_vice_manifest_dir_cache_host_current
    bcs query_file_vice_host_current_fail
    jsr find_hw_dir_cache_matching_path_name
    bcs query_file_vice_host_current_fail
    clc
    rts
query_file_vice_host_current_open:
    jmp query_file_vice_open_current
query_file_vice_host_current_fail:
    sec
    rts

query_program_file_vice_host_current:
    ldx temp_drive
    lda mount_flag_table,x
    cmp #MOUNT_FLAG_TREE
    bne query_program_file_vice_host_current_open
    jsr fill_vice_manifest_dir_cache_host_current
    bcs query_program_file_vice_host_current_fail
    jsr find_hw_dir_cache_matching_path_name_strict
    bcs query_program_file_vice_host_current_fail
    clc
    rts
query_program_file_vice_host_current_open:
    jmp query_file_vice_open_current
query_program_file_vice_host_current_fail:
    sec
    rts

store_vice_tree_live_current_from_screen_ptr:
    lda SCREEN_PTR
    sta matched_name_lo
    lda SCREEN_PTR+1
    sta matched_name_hi
    jsr vice_tree_find_current_slot
    bcc store_vice_tree_live_current_reuse
    jsr vice_tree_alloc_slot
    bcs store_vice_tree_live_current_fail
    lda file_index
    sta vice_tree_slot_index
    lda #VICE_TREE_SLOT_LIVE
    sta vice_tree_state_temp
    jsr query_file_vice_host_current
    lda vice_tree_slot_index
    sta file_index
    bcs store_vice_tree_live_current_new
    lda #VICE_TREE_SLOT_LIVE_HIDE
    sta vice_tree_state_temp
    bne store_vice_tree_live_current_new
store_vice_tree_live_current_reuse:
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq store_vice_tree_live_current_hide
    cmp #VICE_TREE_SLOT_LIVE_HIDE
    beq store_vice_tree_live_current_hide
    lda #VICE_TREE_SLOT_LIVE
    sta vice_tree_state_temp
    bne store_vice_tree_live_current_new
store_vice_tree_live_current_hide:
    lda #VICE_TREE_SLOT_LIVE_HIDE
    sta vice_tree_state_temp
store_vice_tree_live_current_new:
    lda temp_dir_id
    jsr store_vice_tree_dir_for_index
    jsr select_vice_tree_name_slot
    jsr copy_path_name_to_vice_tree_slot_ascii
    lda matched_name_lo
    sta SCREEN_PTR
    lda matched_name_hi
    sta SCREEN_PTR+1
    jsr copy_screen_ptr_to_vice_tree_slot_content
    lda vice_tree_state_temp
    jsr store_vice_tree_state_for_index
    clc
    rts
store_vice_tree_live_current_fail:
    sec
    rts

store_vice_tree_tombstone_current:
    jsr vice_tree_find_current_slot
    bcc store_vice_tree_tombstone_current_have_slot
    jsr vice_tree_alloc_slot
    bcs store_vice_tree_tombstone_current_fail
store_vice_tree_tombstone_current_have_slot:
    lda temp_dir_id
    jsr store_vice_tree_dir_for_index
    jsr select_vice_tree_name_slot
    jsr copy_path_name_to_vice_tree_slot_ascii
    jsr select_vice_tree_content_slot
    ldy #$00
    lda #$00
    sta (PTR),y
    jsr save_selected_vice_tree_content_slot
    lda #VICE_TREE_SLOT_TOMBSTONE
    jsr store_vice_tree_state_for_index
    clc
    rts
store_vice_tree_tombstone_current_fail:
    sec
    rts

lookup_vice_tree_content_current:
    jsr vice_tree_find_current_slot
    bcs lookup_vice_tree_content_current_fail
    cmp #VICE_TREE_SLOT_TOMBSTONE
    beq lookup_vice_tree_content_current_fail
    jsr select_vice_tree_content_slot
    clc
    rts
lookup_vice_tree_content_current_fail:
    sec
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

build_echo_response:
    stx saved_rp_x
    ldy #$00
build_echo_copy_loop:
    cpy arg_length
    bcs build_echo_done
    lda arg_buffer,y
    sta response_buffer,y
    iny
    cpy #MAX_RESPONSE_LEN-1
    bcc build_echo_copy_loop
build_echo_done:
    lda #$00
    sta response_buffer,y
    ldx saved_rp_x
    lda #<response_buffer
    sta 0,x
    lda #>response_buffer
    sta 1,x
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
    cmp #TRANSPORT_MODE_VICE_FS
    beq build_ver_vice
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
build_ver_vice:
    lda #$20
    sta response_buffer,y
    iny
    lda #CMD_V
    sta response_buffer,y
    iny
    lda #CMD_I
    sta response_buffer,y
    iny
    lda #CMD_C
    sta response_buffer,y
    iny
    lda #CMD_E
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

build_mem_response:
    stx saved_rp_x
    ldy #$00
    ldx #$00
build_mem_prefix_loop:
    lda resp_mem_ram_prefix,x
    beq build_mem_prefix_done
    sta response_buffer,y
    iny
    inx
    bne build_mem_prefix_loop
build_mem_prefix_done:
    lda #<__ACHERON_LAST__
    sec
    sbc #<RESIDENT_CODE_START
    sta mem_used_lo
    sta mem_value_lo
    lda #>__ACHERON_LAST__
    sbc #>RESIDENT_CODE_START
    sta mem_used_hi
    sta mem_value_hi
    jsr append_decimal16
    ldx #$00
build_mem_mid_loop:
    lda resp_mem_ram_mid,x
    beq build_mem_mid_done
    sta response_buffer,y
    iny
    inx
    bne build_mem_mid_loop
build_mem_mid_done:
    lda mem_used_lo
    eor #$FF
    sta mem_value_lo
    lda mem_used_hi
    eor #$FF
    sta mem_value_hi
    jsr append_decimal16
    jsr reu_init
    lda reu_present
    beq build_mem_suffix_absent
    ldx #$00
build_mem_suffix_loop:
    lda resp_mem_reu_present_suffix,x
    beq build_mem_suffix_done
    sta response_buffer,y
    iny
    inx
    bne build_mem_suffix_loop
build_mem_suffix_absent:
    ldx #$00
build_mem_suffix_absent_loop:
    lda resp_mem_reu_absent_suffix,x
    beq build_mem_suffix_done
    sta response_buffer,y
    iny
    inx
    bne build_mem_suffix_absent_loop
build_mem_suffix_done:
    lda #$00
    sta response_buffer,y
    ldx #$00
build_mem_copy_to_stable_buffer:
    lda response_buffer,x
    sta mem_response_buffer,x
    beq build_mem_copy_done
    inx
    cpx #MAX_RESPONSE_LEN
    bcc build_mem_copy_to_stable_buffer
    dex
    lda #$00
    sta mem_response_buffer,x
build_mem_copy_done:
    ldx saved_rp_x
    lda #<mem_response_buffer
    sta 0,x
    lda #>mem_response_buffer
    sta 1,x
    rts

append_decimal16:
    lda #$00
    sta mem_digit_written
    lda #$10
    sta mem_divisor_lo
    lda #$27
    sta mem_divisor_hi
    jsr append_decimal16_step
    lda #$E8
    sta mem_divisor_lo
    lda #$03
    sta mem_divisor_hi
    jsr append_decimal16_step
    lda #$64
    sta mem_divisor_lo
    lda #$00
    sta mem_divisor_hi
    jsr append_decimal16_step
    lda #$0A
    sta mem_divisor_lo
    lda #$00
    sta mem_divisor_hi
    jsr append_decimal16_step
    lda #$01
    sta mem_divisor_lo
    lda #$00
    sta mem_divisor_hi
    jmp append_decimal16_step

append_decimal16_step:
    lda #$00
    sta mem_digit_value
append_decimal16_subtract:
    lda mem_value_hi
    cmp mem_divisor_hi
    bcc append_decimal16_emit
    bne append_decimal16_do_subtract
    lda mem_value_lo
    cmp mem_divisor_lo
    bcc append_decimal16_emit
append_decimal16_do_subtract:
    sec
    lda mem_value_lo
    sbc mem_divisor_lo
    sta mem_value_lo
    lda mem_value_hi
    sbc mem_divisor_hi
    sta mem_value_hi
    inc mem_digit_value
    jmp append_decimal16_subtract
append_decimal16_emit:
    lda mem_digit_value
    bne append_decimal16_write
    lda mem_digit_written
    bne append_decimal16_write
    lda mem_divisor_hi
    ora mem_divisor_lo
    cmp #$01
    bne append_decimal16_done
append_decimal16_write:
    lda #$01
    sta mem_digit_written
    lda mem_digit_value
    clc
    adc #$30
    sta response_buffer,y
    iny
append_decimal16_done:
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
reu_present:
    .byte 0
reu_saved_port:
    .byte 0
reu_slot_lo:
    .byte 0
reu_slot_hi:
    .byte 0
reu_slot_bank:
    .byte 0
reu_command_temp:
    .byte 0
saved_rp_x:
    .byte 0
script_index:
    .byte 0
script_line_count:
    .byte 0
batch_mode:
    .byte 0
script_abort_on_error:
    .byte 0
command_status:
    .byte 0
run_batch_fallback:
    .byte 0
run_explicit_batch:
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
saved_enum_y:
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
source_dir_id:
    .byte 0
dest_drive:
    .byte 0
dest_dir_id:
    .byte 0
wildcard_mode:
    .byte 0
wildcard_span:
    .byte 0
wildcard_match_count:
    .byte 0
wildcard_saved_index:
    .byte 0
wildcard_saved_count:
    .byte 0
mem_used_lo:
    .byte 0
mem_used_hi:
    .byte 0
mem_value_lo:
    .byte 0
mem_value_hi:
    .byte 0
mem_divisor_lo:
    .byte 0
mem_divisor_hi:
    .byte 0
mem_digit_value:
    .byte 0
mem_digit_written:
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
file_access_mode:
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
flat_dir_track:
    .byte 0
flat_dir_sector:
    .byte 0
flat_dir_offset:
    .byte 0
flat_hit_dir_track:
    .byte 0
flat_hit_dir_sector:
    .byte 0
flat_hit_dir_offset:
    .byte 0
flat_saved_dir_track:
    .byte 0
flat_saved_dir_sector:
    .byte 0
flat_saved_dir_offset:
    .byte 0
flat_file_track:
    .byte 0
flat_file_sector:
    .byte 0
flat_sector_index_lo:
    .byte 0
flat_sector_index_hi:
    .byte 0
copy_source_flat_flag:
    .byte 0
copy_dest_flat_flag:
    .byte 0
flat_src_track:
    .byte 0
flat_src_sector:
    .byte 0
flat_src_offset:
    .byte 0
flat_src_count:
    .byte 0
flat_dst_first_track:
    .byte 0
flat_dst_first_sector:
    .byte 0
flat_dst_curr_track:
    .byte 0
flat_dst_curr_sector:
    .byte 0
flat_dst_fill:
    .byte 0
flat_dst_type:
    .byte $82
flat_dst_blocks_lo:
    .byte 0
flat_dst_blocks_hi:
    .byte 0
flat_sector_limit:
    .byte 0
flat_track_index:
    .byte 0
flat_remaining:
    .byte 0
flat_total:
    .byte 0
flat_copy_count:
    .byte 0
flat_read_mode:
    .byte 0
flat_secondary_dirty:
    .byte 0
program_image_len_lo:
    .byte 0
program_image_len_hi:
    .byte 0
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
vice_tree_state_temp:
    .byte 0
vice_tree_source_state:
    .byte 0
vice_tree_slot_index:
    .byte 0
vice_dir_state_temp:
    .byte 0
vice_dir_parent_temp:
    .byte 0
dir_walk_count:
    .byte 0
dir_walk_id:
    .byte 0
dir_walk_bytes:
    .byte 0
path_base_index:
    .byte 0
dir_ptr_save_lo:
    .byte 0
dir_ptr_save_hi:
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
volume_label_a:
    .res MAX_LINE_LEN+1
volume_label_b:
    .res MAX_LINE_LEN+1
line_buffer:
    .res MAX_LINE_LEN
arg_buffer:
    .res MAX_LINE_LEN+1
copy_dst_buffer:
    .res MAX_LINE_LEN+1
program_cmdline_buffer:
    .res MAX_LINE_LEN+1
batch_arg1_buffer:
    .res MAX_LINE_LEN+1
batch_arg2_buffer:
    .res MAX_LINE_LEN+1
batch_arg3_buffer:
    .res MAX_LINE_LEN+1
program_target_buffer:
    .res MAX_LINE_LEN+1
path_name_buffer:
    .res MAX_LINE_LEN+1
source_name_buffer:
    .res MAX_LINE_LEN+1
response_buffer:
    .res MAX_RESPONSE_LEN
mem_response_buffer:
    .res MAX_RESPONSE_LEN
program_image_buffer:
    .res PROGRAM_IMAGE_MAX
uci_write_buffer:
    .res MAX_RESPONSE_LEN+4
script_line_data:
    .res (MAX_LINE_LEN+1) * SCRIPT_LINE_MAX
uci_cmd_buffer:
    .res (FULL_PATH_BUF_LEN * 2) + 3
uci_data_buffer:
    .res MAX_LINE_LEN+1
uci_status_buffer:
    .res MAX_LINE_LEN+1
desired_path_buffer:
    .res MAX_LINE_LEN+1
source_fullpath_buffer:
    .res FULL_PATH_BUF_LEN
dest_fullpath_buffer:
    .res FULL_PATH_BUF_LEN
backend_path_cache_a:
    .res MAX_LINE_LEN+1
backend_path_cache_b:
    .res MAX_LINE_LEN+1
mount_path_a:
    .res MAX_LINE_LEN+1
mount_path_b:
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
flat_entry_name_buffer:
    .res HW_DIR_NAME_STRIDE

.segment "HIRAM"
flat_dir_sector_buffer:
    .res 256
flat_bam_primary_buffer:
    .res 256
flat_bam_secondary_buffer:
    .res 256
flat_sector_buffer:
    .res 256
vice_tree_slot_cache:
    .res PROGRAM_IMAGE_MAX

.segment "CODE"
vice_name_buffer:
    .res HW_DIR_NAME_STRIDE
vice_lfn:
    .res 1
vice_secondary:
    .res 1
vice_read_limit:
    .res 1
vice_read_length:
    .res 1
vice_name_index:
    .res 1
vice_path_len:
    .res 1
vice_parse_index:
    .res 1
vice_name_len:
    .res 1
vice_dir_flag:
    .res 1
vice_line_link_lo:
    .res 1
vice_line_link_hi:
    .res 1
vice_line_num_lo:
    .res 1
vice_line_num_hi:
    .res 1

header_text:
    .byte "UDOS FOR COMMODORE 64", 0
autoexec_name:
    .byte 1, 21, 20, 15, 5, 24, 5, 3, ASCII_DOT, 2, 1, 20, 0
resp_help:
    .byte "HELP VER VOL MEM DIR CD MD RD ECHO MOUNT TYPE COPY REN DEL", 0
ver_prefix:
    .byte 21, 4, 15, 19, 32, 1, 12, 16, 8, 1, 0
resp_mem_ram_prefix:
    .byte "RAM USED ", 0
resp_mem_ram_mid:
    .byte " FREE ", 0
resp_mem_reu_present_suffix:
    .byte " REU USED 3060 FREE 16774156", 0
resp_mem_reu_absent_suffix:
    .byte " REU USED 0 FREE 0", 0
vice_tree_reu_slot_a_lo:
    .byte <(PROGRAM_IMAGE_MAX * 0), <(PROGRAM_IMAGE_MAX * 1), <(PROGRAM_IMAGE_MAX * 2)
    .byte <(PROGRAM_IMAGE_MAX * 3), <(PROGRAM_IMAGE_MAX * 4), <(PROGRAM_IMAGE_MAX * 5)
vice_tree_reu_slot_a_hi:
    .byte >(PROGRAM_IMAGE_MAX * 0), >(PROGRAM_IMAGE_MAX * 1), >(PROGRAM_IMAGE_MAX * 2)
    .byte >(PROGRAM_IMAGE_MAX * 3), >(PROGRAM_IMAGE_MAX * 4), >(PROGRAM_IMAGE_MAX * 5)
vice_tree_reu_slot_b_lo:
    .byte <(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 0)), <(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 1))
    .byte <(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 2)), <(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 3))
    .byte <(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 4)), <(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 5))
vice_tree_reu_slot_b_hi:
    .byte >(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 0)), >(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 1))
    .byte >(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 2)), >(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 3))
    .byte >(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 4)), >(REU_VICE_TREE_BYTES + (PROGRAM_IMAGE_MAX * 5))
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
entry_flat_autoexec:
    .byte "AUTOEXEC.BAT", 0
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
    .byte "HELP VER VOL MEM DIR CD MD RD ECHO MOUNT TYPE COPY REN DEL", 0
content_flat_readme:
    .byte "MOCK FLAT IMAGE CONTENT", 0
content_flat_autoexec:
    .include "autoexec_script.inc"
content_bin_shell:
    .byte "SHELL OVERLAY PLACEHOLDER", 0
content_bin_dir:
    .byte "DIR OVERLAY PLACEHOLDER", 0
content_src_boot:
    .byte "; BOOT.ASM MOCK SOURCE", 0
content_src_fs:
    .byte "; FS.AVM MOCK SOURCE", 0
flat_entry_lo:
    .byte <entry_flat_system, <entry_flat_commands, <entry_flat_readme, <entry_flat_autoexec
flat_entry_hi:
    .byte >entry_flat_system, >entry_flat_commands, >entry_flat_readme, >entry_flat_autoexec
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
    .byte <entry_flat_autoexec, >entry_flat_autoexec, <content_flat_autoexec, >content_flat_autoexec
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
dir_walk_ids:
    .res DIR_WALK_MAX
vice_dir_state_a:
    .res VICE_DIR_DYNAMIC_MAX
vice_dir_state_b:
    .res VICE_DIR_DYNAMIC_MAX
vice_dir_parent_a:
    .res VICE_DIR_DYNAMIC_MAX
vice_dir_parent_b:
    .res VICE_DIR_DYNAMIC_MAX
vice_dir_names_a:
    .res HW_DIR_NAME_STRIDE * VICE_DIR_DYNAMIC_MAX
vice_dir_names_b:
    .res HW_DIR_NAME_STRIDE * VICE_DIR_DYNAMIC_MAX
vice_tree_state_a:
    .res VICE_TREE_DYNAMIC_MAX
vice_tree_state_b:
    .res VICE_TREE_DYNAMIC_MAX
vice_tree_dir_a:
    .res VICE_TREE_DYNAMIC_MAX
vice_tree_dir_b:
    .res VICE_TREE_DYNAMIC_MAX
vice_tree_names_a:
    .res HW_DIR_NAME_STRIDE * VICE_TREE_DYNAMIC_MAX
vice_tree_names_b:
    .res HW_DIR_NAME_STRIDE * VICE_TREE_DYNAMIC_MAX

.segment "CODE"
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
    .byte <flat_file_records, >flat_file_records, 4
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_a_d71:
    .byte <volume_system, >volume_system
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 4
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_a_d81:
    .byte <volume_system, >volume_system
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 4
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
    .byte <flat_file_records, >flat_file_records, 4
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_b_d71:
    .byte <volume_work, >volume_work
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 4
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
    .byte <empty_file_records, >empty_file_records, 0
image_b_d81:
    .byte <volume_work, >volume_work
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 3
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_entry_lo, >flat_entry_lo, <flat_entry_hi, >flat_entry_hi, 0
    .byte <flat_file_records, >flat_file_records, 4
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
    .byte "SYSTEM COMMANDS README AUTOEXEC.BAT", 0
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
resp_bad_md:
    .byte "BAD MD", 0
resp_bad_rd:
    .byte "BAD RD", 0
resp_deleted:
    .byte "DELETED", 0
resp_created:
    .byte "CREATED", 0
resp_removed:
    .byte "REMOVED", 0
resp_delete_failed:
    .byte "DELETE FAILED", 0
resp_mkdir_failed:
    .byte "MD FAILED", 0
resp_rmdir_failed:
    .byte "RD FAILED", 0
resp_dir_not_empty:
    .byte "DIR NOT EMPTY", 0
resp_dir_busy:
    .byte "DIR BUSY", 0
resp_rename_failed:
    .byte "RENAME FAILED", 0
resp_renamed:
    .byte "RENAMED", 0
resp_exists:
    .byte "EXISTS", 0
resp_copied:
    .byte "COPIED", 0
resp_copy_failed:
    .byte "COPY FAILED", 0
resp_read_only:
    .byte "READ ONLY", 0
resp_no_space:
    .byte "NO SPACE", 0
resp_no_program:
    .byte "PROGRAM NOT FOUND", 0
resp_not_disk_image:
    .byte "NOT A DISK IMAGE", 0
resp_drive_not_present:
    .byte "DRIVE NOT PRESENT", 0
resp_mount_failed:
    .byte "MOUNT FAILED", 0
resp_program_too_large:
    .byte "PROGRAM TOO LARGE", 0
resp_program_load_failed:
    .byte "PROGRAM LOAD FAILED", 0
vice_probe_name:
    .byte "$", 0
resp_bad_mount:
    .byte "BAD MOUNT", 0
resp_bad_run:
    .byte "BAD RUN", 0
resp_unmounted:
    .byte "UNMOUNTED", 0
resp_empty:
    .byte 0
resp_unknown:
    .byte $3F, 0
error_response_table:
    .addr resp_flat_image
    .addr resp_bad_dir
    .addr resp_bad_file
    .addr resp_bad_copy
    .addr resp_bad_ren
    .addr resp_bad_md
    .addr resp_bad_rd
    .addr resp_delete_failed
    .addr resp_mkdir_failed
    .addr resp_rmdir_failed
    .addr resp_dir_not_empty
    .addr resp_dir_busy
    .addr resp_rename_failed
    .addr resp_copy_failed
    .addr resp_read_only
    .addr resp_no_space
    .addr resp_no_program
    .addr resp_drive_not_present
    .addr resp_mount_failed
    .addr resp_program_too_large
    .addr resp_program_load_failed
    .addr resp_bad_mount
    .addr resp_bad_run
    .addr resp_unmounted
    .addr resp_unknown
    .addr 0
resp_run_prefix:
    .byte "RUN ", 0
resp_args_prefix:
    .byte "ARGS ", 0
