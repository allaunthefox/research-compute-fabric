; ═══════════════════════════════════════════════════════════════════════════
; NES 6502 Controller Port Reader
; Reads data from cartridge CPU via controller port (voltage shifter)
; 
; Cartridge streams data via controller port (CLK, OUT, IN pins)
; NES reads controller port registers ($4016, $4017)
; Voltage shifter handles 3.3V ↔ 5V level conversion
; ═══════════════════════════════════════════════════════════════════════════

; NES Controller Port Addresses
JOY1_STROBE   = $4016  ; Write to strobe controller 1
JOY1_DATA     = $4016  ; Read controller 1 data
JOY2_STROBE   = $4017  ; Write to strobe controller 2
JOY2_DATA     = $4017  ; Read controller 2 data

; NES APU Registers
APU_SQ1_FREQ  = $4000  ; Square 1 frequency (lo)
APU_SQ1_FREQ_H= $4001  ; Square 1 frequency (hi)
APU_SQ1_DUTY   = $4002  ; Square 1 duty + volume
APU_SQ1_SWEEP  = $4003  ; Square 1 sweep

; Zero Page Variables
zp_rx_buffer  = $00    ; Receive buffer (lo)
zp_rx_ptr     = $01    ; Receive buffer pointer
zp_bit_count  = $02    ; Bit counter
zp_byte_accum = $03    ; Accumulated byte
zp_freq_lo    = $04    ; Frequency (lo)
zp_freq_hi    = $05    ; Frequency (hi)
zp_duty_vol   = $06    ; Duty + volume
zp_temp       = $07    ; Temporary storage

; ═══════════════════════════════════════════════════════════════════════════
; Read One Byte from Controller Port
; Reads 8 bits via controller port strobe/read cycle
; Output: A = received byte
; ═══════════════════════════════════════════════════════════════════════════

read_controller_byte:
    LDA #$00          ; Initialize accumulator
    STA zp_byte_accum
    LDA #$08          ; 8 bits to read
    STA zp_bit_count

read_bit_loop:
    ; Strobe controller (CLK high)
    LDA #$01
    STA JOY1_STROBE
    
    ; Read data bit (IN pin)
    LDA JOY1_DATA
    AND #$01          ; Mask bit 0
    LSR               ; Shift to carry
    
    ; Accumulate bit
    ROL zp_byte_accum
    
    ; Strobe low (CLK low)
    LDA #$00
    STA JOY1_STROBE
    
    ; Next bit
    DEC zp_bit_count
    BNE read_bit_loop
    
    ; Return byte in A
    LDA zp_byte_accum
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; Read Square Wave Parameters from Cartridge
; Expects: frequency (2 bytes), duty (1 byte), volume (1 byte)
; Output: Applies to APU
; ═══════════════════════════════════════════════════════════════════════════

read_square_wave_params:
    ; Read frequency (lo)
    JSR read_controller_byte
    STA zp_freq_lo
    
    ; Read frequency (hi)
    JSR read_controller_byte
    STA zp_freq_hi
    
    ; Read duty
    JSR read_controller_byte
    STA zp_duty_vol
    
    ; Read volume
    JSR read_controller_byte
    STA zp_temp
    
    ; Combine duty and volume
    LDA zp_temp
    ASL
    ASL
    ASL
    ASL              ; Volume in bits 4-7
    ORA zp_duty_vol   ; Duty in bits 0-1
    STA zp_duty_vol
    
    ; Apply to APU
    LDA zp_freq_lo
    STA APU_SQ1_FREQ
    LDA zp_freq_hi
    STA APU_SQ1_FREQ_H
    LDA zp_duty_vol
    STA APU_SQ1_DUTY
    
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; Read Palette Color from Cartridge
; Output: A = palette index (0-63)
; ═══════════════════════════════════════════════════════════════════════════

read_palette_color:
    JSR read_controller_byte
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; Main Audio Loop
; Continuously reads square wave parameters from cartridge
; ═══════════════════════════════════════════════════════════════════════════

audio_loop:
    ; Read square wave parameters
    JSR read_square_wave_params
    
    ; Wait for next frame (simple delay)
    LDA #$FF
delay_loop:
    DEC
    BNE delay_loop
    
    ; Loop
    JMP audio_loop

; ═══════════════════════════════════════════════════════════════════════════
; Main Entry Point
; ═══════════════════════════════════════════════════════════════════════════

main:
    ; Initialize APU
    LDA #$00
    STA APU_SQ1_FREQ
    STA APU_SQ1_FREQ_H
    STA APU_SQ1_DUTY
    STA APU_SQ1_SWEEP
    
    ; Start audio loop
    JMP audio_loop
