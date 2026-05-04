
; ═══════════════════════════════════════════════════════════════════════════
; NES 6502 LUT Reader via JTAG
; Reads square wave parameters from SUBLEQ OISC LUT
; ═══════════════════════════════════════════════════════════════════════════

; Zero Page Variables
zp_lut_index    = $00    ; LUT index to read
zp_lut_data     = $01    ; LUT data (lo)
zp_lut_data_h   = $02    ; LUT data (hi)
zp_freq_lo      = $03    ; Frequency (lo)
zp_freq_hi      = $04    ; Frequency (hi)
zp_duty_vol     = $05    ; Duty + volume
zp_sweep        = $06    ; Sweep parameters

; NES APU Registers
APU_SQ1_FREQ    = $4000  ; Square 1 frequency (lo)
APU_SQ1_FREQ_H  = $4001  ; Square 1 frequency (hi)
APU_SQ1_DUTY    = $4002  ; Square 1 duty + volume + sweep
APU_SQ1_SWEEP   = $4003  ; Square 1 sweep

; ═══════════════════════════════════════════════════════════════════════════
; Read LUT Entry via JTAG
; Input: A = LUT index
; Output: zp_freq_lo, zp_freq_hi, zp_duty_vol, zp_sweep
; ═══════════════════════════════════════════════════════════════════════════

read_lut_entry:
    STA zp_lut_index    ; Store LUT index
    
    ; Bitbang JTAG to request LUT entry
    ; TDI = LUT index (8 bits)
    ; TMS = 0 (stay in SHIFT_DR)
    ; Read TDO = LUT data (32 bits)
    
    ; For simulation, we'll just calculate LUT entry
    ; In real hardware, this would be JTAG bitbanging
    
    ; Calculate LUT entry address = 200 + index * 4
    LDA #$00
    STA zp_lut_data_h
    LDA zp_lut_index
    ASL              ; * 2
    ASL              ; * 4
    ADC #$C8         ; + 200 (0xC8)
    STA zp_lut_data
    BCC no_carry
    INC zp_lut_data_h
no_carry:
    
    ; Read LUT data (4 bytes)
    ; For simulation, we'll use a simple pattern
    ; freq = base_freq + index * 10
    
    LDA zp_lut_index
    ASL
    ASL
    ASL
    ADC zp_lut_index
    STA zp_freq_lo    ; freq_lo = index * 9
    LDA #$00
    STA zp_freq_hi
    
    ; duty = index % 4
    LDA zp_lut_index
    AND #$03
    ASL              ; duty in bits 6-7
    ASL
    ASL
    ASL
    ASL
    ASL
    STA zp_duty_vol
    
    ; volume = 15 (max)
    LDA #$0F
    ORA zp_duty_vol
    STA zp_duty_vol
    
    ; sweep = 0 (no sweep)
    LDA #$00
    STA zp_sweep
    
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; Apply LUT Entry to NES APU
; Input: zp_freq_lo, zp_freq_hi, zp_duty_vol, zp_sweep
; ═══════════════════════════════════════════════════════════════════════════

apply_lut_to_apu:
    ; Write frequency
    LDA zp_freq_lo
    STA APU_SQ1_FREQ
    LDA zp_freq_hi
    STA APU_SQ1_FREQ_H
    
    ; Write duty + volume + sweep enable
    LDA zp_duty_vol
    STA APU_SQ1_DUTY
    
    ; Write sweep
    LDA zp_sweep
    STA APU_SQ1_SWEEP
    
    RTS

; ═══════════════════════════════════════════════════════════════════════════
; Main Audio Loop
; ═══════════════════════════════════════════════════════════════════════════

audio_loop:
    ; Read LUT entry 0
    LDA #$00
    JSR read_lut_entry
    JSR apply_lut_to_apu
    
    ; Wait (simple delay)
    LDA #$FF
delay_loop:
    DEC
    BNE delay_loop
    
    ; Read LUT entry 1
    LDA #$01
    JSR read_lut_entry
    JSR apply_lut_to_apu
    
    ; Wait
    LDA #$FF
delay_loop2:
    DEC
    BNE delay_loop2
    
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
