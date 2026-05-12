// Braid-Encoded Serial Communication Interface
// Derived from Lean: Semantics/BraidSerial.lean
// Target: Gowin GW1NR-9 (Tang Nano 9K)
// Q0.16 fixed-point arithmetic for phase encoding
// Replaces standard UART with braid-topology parallel encoding

`timescale 1ns / 1ps

// ═══════════════════════════════════════════════════════════════════════════
// Q0.16 Fixed-Point Arithmetic (Pure Fraction: range [-1, 1 - 2^-16])
// ═══════════════════════════════════════════════════════════════════════════
module q0_16_add (
    input  signed [15:0] a,
    input  signed [15:0] b,
    output signed [15:0] sum,
    output               overflow
);
    wire signed [16:0] ext = $signed({a[15], a}) + $signed({b[15], b});
    assign overflow = (a[15] == b[15]) && (ext[16] != a[15]);
    assign sum = overflow ? (a[15] ? 16'sh8000 : 16'sh7FFF) : ext[15:0];
endmodule

module q0_16_mul (
    input  signed [15:0] a,
    input  signed [15:0] b,
    output signed [15:0] product
);
    wire signed [31:0] full = $signed(a) * $signed(b);
    assign product = full[31:16];  // Q0.16 multiply: keep upper 16 bits
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Byte to Q0.16 Phase Conversion
// Maps 0-255 to [-1, 1) range: 0→-1.0, 127→0.0, 255→0.999985
// Formula: phase = (byte * 2 - 255) * 65535 / 255
// Simplified: phase = (byte * 2 - 255) * 257
// Q0.16: 0x8000 = -1.0, 0x0000 = 0.0, 0x7FFF = 0.999985
// ═══════════════════════════════════════════════════════════════════════════
module byte_to_phase (
    input  wire [7:0]  byte_in,
    output reg  signed [15:0] phase_out
);
    // Convert byte (0-255) to signed Q0.16 phase (-32768 to 32767)
    // Linear mapping: phase = (byte - 128) * 256
    // This maps 0 -> -32768, 128 -> 0, 255 -> 32767
    wire signed [23:0] offset = {16'b0, byte_in} - 24'sd128;
    wire signed [23:0] mult = offset * 24'sd256;
    assign phase_out = mult[15:0];  // Extract lower 16 bits for signed result
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Q0.16 Phase to Byte Conversion
// Inverse of byte_to_phase with clamping to [0, 255]
// Formula: byte = (phase * 255 + 65535) / 65535 / 2 + 128
// Q0.16: 0x8000 = -1.0, 0x0000 = 0.0, 0x7FFF = 0.999985
// ═══════════════════════════════════════════════════════════════════════════
module phase_to_byte (
    input  wire signed [15:0] phase_in,
    output reg  [7:0]  byte_out
);
    // Convert signed Q0.16 phase (-32768 to 32767) back to byte (0-255)
    // Inverse mapping: byte = (phase / 256) + 128
    // This maps -32768 -> 0, 0 -> 128, 32767 -> 255
    wire signed [23:0] phase_ext = {{8{phase_in[15]}}, phase_in};  // Sign-extend to 24 bits
    wire signed [23:0] div_result = phase_ext / 24'sd256;
    wire signed [23:0] byte_result = div_result + 24'sd128;

    // Clamp to [0, 255] range
    wire [7:0] byte_clamped = (byte_result < 0) ? 8'd0 :
                              (byte_result > 255) ? 8'd255 :
                              byte_result[7:0];
    assign byte_out = byte_clamped;
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Modulation Mode Selector
// 00: None (direct Q0.16)
// 01: QPSK (4-phase modulation, 2 bits/symbol)
// 10: QAM-16 (16-point constellation, 4 bits/symbol)
// 11: DMT (Discrete Multi-Tone, strand subcarriers)
// ═══════════════════════════════════════════════════════════════════════════
localparam MOD_NONE = 2'b00;
localparam MOD_QPSK = 2'b01;
localparam MOD_QAM16 = 2'b10;
localparam MOD_DMT = 2'b11;

// ═══════════════════════════════════════════════════════════════════════════
// QPSK Modulator
// Maps 2 bits to 4 phase states: 00→45°, 01→135°, 10→225°, 11→315°
// Q0.16: 45°=0x4000, 135°=0xC000, 225°=0x4000 (signed), 315°=0xC000 (signed)
// ═══════════════════════════════════════════════════════════════════════════
module qpsk_modulator (
    input  wire [1:0]  symbols_in,   // 2 bits per symbol
    output reg  signed [15:0] phase_out
);
    // QPSK constellation: 4 distinct phase angles
    // 00→0° (1.0), 01→90° (0.0 + 1.0j), 10→180° (-1.0), 11→270° (0.0 - 1.0j)
    // In Q0.16: 0°=0x7FFF, 90°=0x4000, 180°=0x8000, 270°=0xC000
    always @(*) begin
        case (symbols_in)
            2'b00: phase_out = 16'sh7FFF;  // 1.0 (0°)
            2'b01: phase_out = 16'sh4000;  // 0.0 (90° - using phase as I component)
            2'b10: phase_out = 16'sh8000;  // -1.0 (180°)
            2'b11: phase_out = 16'shC000;  // 0.0 (270° - using phase as I component)
            default: phase_out = 16'sd0;
        endcase
    end
endmodule

// QPSK Demodulator
module qpsk_demodulator (
    input  signed [15:0] phase_in,
    output reg  [1:0]  symbols_out
);
    // Demodulate by comparing phase to 4 constellation points
    // 00→0x7FFF, 01→0x4000, 10→0x8000, 11→0xC000
    always @(*) begin
        if (phase_in >= 16'sh6000) begin
            symbols_out = 2'b00;  // 0° (0x7FFF)
        end else if (phase_in >= 16'sh2000) begin
            symbols_out = 2'b01;  // 90° (0x4000)
        end else if (phase_in >= 16'shA000) begin
            symbols_out = 2'b11;  // 270° (0xC000)
        end else begin
            symbols_out = 2'b10;  // 180° (0x8000)
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// QAM-16 Modulator
// Maps 4 bits to 16 phase/amplitude combinations
// ═══════════════════════════════════════════════════════════════════════════
module qam16_modulator (
    input  wire [3:0]  symbols_in,   // 4 bits per symbol
    output reg  signed [15:0] phase_out,
    output reg  signed [15:0] amp_out    // Amplitude modulation
);
    // QAM-16 constellation: 16 points with varying phase and amplitude
    // Use 4x4 grid: 4 amplitude levels × 4 phase levels
    always @(*) begin
        case (symbols_in)
            4'b0000: begin phase_out = 16'sh7FFF; amp_out = 16'sh7FFF; end  // Max amp, 0°
            4'b0001: begin phase_out = 16'sh4000; amp_out = 16'sh7FFF; end  // Max amp, 90°
            4'b0010: begin phase_out = 16'sh8000; amp_out = 16'sh7FFF; end  // Max amp, 180°
            4'b0011: begin phase_out = 16'shC000; amp_out = 16'sh7FFF; end  // Max amp, 270°
            4'b0100: begin phase_out = 16'sh7FFF; amp_out = 16'sh5FFF; end  // High amp, 0°
            4'b0101: begin phase_out = 16'sh4000; amp_out = 16'sh5FFF; end  // High amp, 90°
            4'b0110: begin phase_out = 16'sh8000; amp_out = 16'sh5FFF; end  // High amp, 180°
            4'b0111: begin phase_out = 16'shC000; amp_out = 16'sh5FFF; end  // High amp, 270°
            4'b1000: begin phase_out = 16'sh7FFF; amp_out = 16'sh3FFF; end  // Mid amp, 0°
            4'b1001: begin phase_out = 16'sh4000; amp_out = 16'sh3FFF; end  // Mid amp, 90°
            4'b1010: begin phase_out = 16'sh8000; amp_out = 16'sh3FFF; end  // Mid amp, 180°
            4'b1011: begin phase_out = 16'shC000; amp_out = 16'sh3FFF; end  // Mid amp, 270°
            4'b1100: begin phase_out = 16'sh7FFF; amp_out = 16'sh1FFF; end  // Low amp, 0°
            4'b1101: begin phase_out = 16'sh4000; amp_out = 16'sh1FFF; end  // Low amp, 90°
            4'b1110: begin phase_out = 16'sh8000; amp_out = 16'sh1FFF; end  // Low amp, 180°
            4'b1111: begin phase_out = 16'shC000; amp_out = 16'sh1FFF; end  // Low amp, 270°
            default: begin phase_out = 16'sd0; amp_out = 16'sd0; end
        endcase
    end
endmodule

// QAM-16 Demodulator
module qam16_demodulator (
    input  signed [15:0] phase_in,
    input  signed [15:0] amp_in,
    output reg  [3:0]  symbols_out
);
    // Demodulate by comparing phase and amplitude to constellation
    always @(*) begin
        // Determine phase (lower 2 bits)
        // 00→0x7FFF, 01→0x4000, 10→0x8000, 11→0xC000
        if (phase_in >= 16'sh6000) symbols_out[1:0] = 2'b00;  // 0°
        else if (phase_in >= 16'sh2000) symbols_out[1:0] = 2'b01;  // 90°
        else if (phase_in >= 16'shA000) symbols_out[1:0] = 2'b11;  // 270°
        else symbols_out[1:0] = 2'b10;  // 180°

        // Determine amplitude (upper 2 bits)
        // 0→0x7FFF, 1→0x5FFF, 2→0x3FFF, 3→0x1FFF
        if (amp_in > 16'sh6000) symbols_out[3:2] = 2'b00;  // Max
        else if (amp_in > 16'sh4000) symbols_out[3:2] = 2'b01;  // High
        else if (amp_in > 16'sh2000) symbols_out[3:2] = 2'b10;  // Mid
        else symbols_out[3:2] = 2'b11;  // Low
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// DMT-like Multi-Carrier Modulator
// Uses strand index as subcarrier frequency offset
// ═══════════════════════════════════════════════════════════════════════════
module dmt_modulator (
    input  wire [7:0]  byte_in,
    input  wire [2:0]  subcarrier_idx,  // Strand index (0-7)
    output reg  signed [15:0] phase_out
);
    // DMT: each subcarrier has different phase offset
    // Phase offset = subcarrier_idx * 45°
    // Data modulates the phase offset
    wire signed [23:0] offset = {16'b0, byte_in} - 24'sd128;
    wire signed [23:0] base_phase = offset * 24'sd256;
    wire signed [15:0] subcarrier_offset = subcarrier_idx * 16'sh2000;  // 45° increments
    assign phase_out = (base_phase[15:0] + subcarrier_offset);
endmodule

// DMT Demodulator
module dmt_demodulator (
    input  signed [15:0] phase_in,
    input  wire [2:0]  subcarrier_idx,
    output reg  [7:0]  byte_out
);
    // Remove subcarrier offset, then convert back to byte
    // Use same offset calculation as modulator: subcarrier_idx * 0x2000
    wire signed [15:0] subcarrier_offset = subcarrier_idx * 16'sh2000;  // 45° increments
    wire signed [15:0] demod_phase = phase_in - subcarrier_offset;

    // Convert phase back to byte using inverse of byte_to_phase
    // byte = (phase / 256) + 128
    wire signed [23:0] phase_ext = {{8{demod_phase[15]}}, demod_phase};
    wire signed [23:0] div_result = phase_ext / 24'sd256;
    wire signed [23:0] byte_result = div_result + 24'sd128;

    // Clamp to [0, 255] range
    wire [7:0] byte_clamped = (byte_result < 0) ? 8'd0 :
                              (byte_result > 255) ? 8'd255 :
                              byte_result[7:0];
    assign byte_out = byte_clamped;
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Hydrogenic Phi-Torsion Phase Generator
// gamma(theta) = phi * theta where phi = 1.6180339887498948482
// theta = frameNum * 0.01 (evolution parameter)
// ═══════════════════════════════════════════════════════════════════════════
module phi_torsion_phase (
    input  wire [31:0] frame_num,
    output reg  signed [31:0] phi_phase  // Q16.16 output
);
    // phi in Q16.16: 1.6180339887498948482 * 65536 ≈ 106039
    localparam signed [31:0] PHI = 32'sh00019E97;

    // theta = frameNum * 0.01 in Q16.16
    // 0.01 in Q16.16 = 655.36 ≈ 656
    localparam signed [31:0] THETA_SCALE = 32'sh00000290;

    wire signed [47:0] theta_mult = $signed({16'b0, frame_num}) * THETA_SCALE;
    wire signed [31:0] theta = {{16{theta_mult[31]}}, theta_mult[31:16]};
    wire signed [63:0] gamma = $signed(theta) * PHI;
    assign phi_phase = gamma[47:16];
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Bracket Admissibility Check
// Derived from Lean: Semantics/BraidBracket.lean
// Checks if bracket bounds are valid and gap is conserved
// ═══════════════════════════════════════════════════════════════════════════
module bracket_admissible (
    input  wire signed [15:0] phi,        // Phase angle
    input  wire signed [15:0] lower_bound, // Bracket lower bound
    input  wire signed [15:0] upper_bound, // Bracket upper bound
    input  wire        gap_conserved,    // Gap conservation flag
    output wire        admissible        // Overall admissibility
);
    wire in_bounds = (phi >= lower_bound) && (phi <= upper_bound);
    assign admissible = in_bounds && gap_conserved;
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Encoded Strand Structure (matches Lean EncodedStrand)
// ═══════════════════════════════════════════════════════════════════════════
module encoded_strand (
    input  wire        clk,
    input  wire        rst_n,

    // Encoding interface
    input  wire        encode_enable,
    input  wire [7:0]  byte_in,
    input  wire [2:0]  slot_in,      // Slot 0-7
    input  wire        parity_in,
    input  signed [15:0] residue_in,
    input  wire [1:0]  modulation_mode,  // 00=None, 01=QPSK, 10=QAM16, 11=DMT

    // Decoding interface
    input  wire        decode_enable,
    input  signed [15:0] phase_in,
    input  signed [15:0] amp_in,      // Amplitude for QAM-16
    output reg  [7:0]  byte_out,

    // Strand output (for parallel transmission)
    output wire signed [15:0] phase_acc,
    output wire [2:0]  slot,
    output wire        parity,
    output wire signed [15:0] residue,
    output wire signed [15:0] amplitude,  // Amplitude for QAM-16
    output wire        admissible
);
    // Phase accumulator
    reg signed [15:0] phase_reg;
    reg [2:0] slot_reg;
    reg parity_reg;
    reg signed [15:0] residue_reg;

    // Bracket bounds (simplified: fixed bounds for now)
    localparam signed [15:0] LOWER_BOUND = 16'sh8000;  // -1.0
    localparam signed [15:0] UPPER_BOUND = 16'sh7FFF;  // 0.999985

    // Byte to phase conversion (direct)
    wire signed [15:0] phase_from_byte;
    byte_to_phase byte_conv (.byte_in(byte_in), .phase_out(phase_from_byte));

    // Modulation outputs
    wire signed [15:0] qpsk_phase;
    wire signed [15:0] qam16_phase;
    wire signed [15:0] qam16_amp;
    wire signed [15:0] dmt_phase;

    // QPSK modulator (encode byte as 4 QPSK symbols)
    // Byte 0x01 -> symbols: 00,00,00,01 -> phases: 0x7FFF, 0x7FFF, 0x7FFF, 0x4000
    // But we only have one phase output per strand, so we need a different approach
    // Simplified: Use byte value directly to select one of 4 phases
    // byte[1:0] selects the phase
    qpsk_modulator qpsk_mod (.symbols_in(byte_in[1:0]), .phase_out(qpsk_phase));

    // QAM-16 modulator (encode byte as 2 QAM-16 symbols)
    // byte[3:0] selects the constellation point
    qam16_modulator qam16_mod (.symbols_in(byte_in[3:0]), .phase_out(qam16_phase), .amp_out(qam16_amp));

    // DMT modulator (uses slot as subcarrier index)
    dmt_modulator dmt_mod (.byte_in(byte_in), .subcarrier_idx(slot_in), .phase_out(dmt_phase));

    // Modulation multiplexer
    reg signed [15:0] modulated_phase;
    reg signed [15:0] modulated_amp;

    always @(*) begin
        case (modulation_mode)
            MOD_NONE: begin
                modulated_phase = phase_from_byte;
                modulated_amp = 16'sh7FFF;  // Full amplitude
            end
            MOD_QPSK: begin
                modulated_phase = qpsk_phase;
                modulated_amp = 16'sh7FFF;
            end
            MOD_QAM16: begin
                modulated_phase = qam16_phase;
                modulated_amp = qam16_amp;
            end
            MOD_DMT: begin
                modulated_phase = dmt_phase;
                modulated_amp = 16'sh7FFF;
            end
            default: begin
                modulated_phase = phase_from_byte;
                modulated_amp = 16'sh7FFF;
            end
        endcase
    end

    // Phase to byte conversion (direct)
    wire [7:0] byte_from_phase;
    phase_to_byte phase_conv (.phase_in(phase_in), .byte_out(byte_from_phase));

    // Demodulation outputs
    wire [1:0] qpsk_symbols;
    wire [3:0] qam16_symbols;
    wire [7:0] dmt_byte;

    // QPSK demodulator
    qpsk_demodulator qpsk_demod (.phase_in(phase_in), .symbols_out(qpsk_symbols));

    // QAM-16 demodulator
    qam16_demodulator qam16_demod (.phase_in(phase_in), .amp_in(amp_in), .symbols_out(qam16_symbols));

    // DMT demodulator
    dmt_demodulator dmt_demod (.phase_in(phase_in), .subcarrier_idx(slot_in), .byte_out(dmt_byte));

    // Demodulation multiplexer
    reg [7:0] demodulated_byte;

    always @(*) begin
        case (modulation_mode)
            MOD_NONE: demodulated_byte = byte_from_phase;
            MOD_QPSK: demodulated_byte = {6'b0, qpsk_symbols};  // Lower 2 bits from QPSK
            MOD_QAM16: demodulated_byte = {4'b0, qam16_symbols};  // Lower 4 bits from QAM-16
            MOD_DMT: demodulated_byte = dmt_byte;
            default: demodulated_byte = byte_from_phase;
        endcase
    end

    // Admissibility check
    bracket_admissible bracket_check (
        .phi(modulated_phase),
        .lower_bound(LOWER_BOUND),
        .upper_bound(UPPER_BOUND),
        .gap_conserved(1'b1),  // Simplified: always conserved
        .admissible(admissible)
    );

    // Combinational output assignment - phase_acc reflects current modulated_phase when encoding
    assign phase_acc = encode_enable ? modulated_phase : phase_reg;
    assign slot = encode_enable ? slot_in : slot_reg;
    assign parity = encode_enable ? parity_in : parity_reg;
    assign residue = encode_enable ? residue_in : residue_reg;
    assign amplitude = encode_enable ? modulated_amp : 16'sh7FFF;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            phase_reg <= 16'sd0;
            slot_reg <= 3'd0;
            parity_reg <= 1'b0;
            residue_reg <= 16'sd0;
            byte_out <= 8'd0;
        end else begin
            if (encode_enable) begin
                phase_reg <= modulated_phase;
                slot_reg <= slot_in;
                parity_reg <= parity_in;
                residue_reg <= residue_in;
            end else if (decode_enable) begin
                byte_out <= demodulated_byte;
            end
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Braid Frame Encoder
// Encodes serial packet into 8-wire parallel braid frame
// ═══════════════════════════════════════════════════════════════════════════
module braid_frame_encoder (
    input  wire        clk,
    input  wire        rst_n,

    // Packet input
    input  wire        encode_start,
    input  wire [7:0]  packet_type,
    input  wire [15:0] seq_num,
    input  wire [7:0]  payload_len,
    input  wire [63:0] payload_data,  // 8 bytes max for simplicity
    input  wire [31:0] frame_num,
    input  wire [1:0]  modulation_mode,  // 00=None, 01=QPSK, 10=QAM16, 11=DMT

    // 8-wire parallel output
    output wire signed [15:0] wire_phase [0:7],
    output wire [2:0]  wire_slot [0:7],
    output wire        wire_parity [0:7],
    output wire signed [15:0] wire_amplitude [0:7],  // Amplitude for QAM-16
    output wire        frame_valid,
    output wire signed [31:0] phi_phase
);
    // Packet assembly - direct wire assignments for debugging
    wire [7:0] all_bytes [0:7];
    assign all_bytes[0] = packet_type;
    assign all_bytes[1] = seq_num[7:0];
    assign all_bytes[2] = seq_num[15:8];
    assign all_bytes[3] = payload_len;
    assign all_bytes[4] = payload_data[7:0];
    assign all_bytes[5] = payload_data[15:8];
    assign all_bytes[6] = payload_data[23:16];
    assign all_bytes[7] = payload_data[31:24];
    // Note: For full 64-bit payload, would need 8 more wires, but keeping it simple for now

    // Encoding state
    reg [3:0] encode_state;
    reg [2:0] current_slot;
    reg frame_valid_reg;
    reg encode_enable_delayed;  // Delayed version of encode_start

    // Phi-torsion phase
    wire signed [31:0] phi_torsion;
    phi_torsion_phase phi_gen (.frame_num(frame_num), .phi_phase(phi_torsion));

    // 8 strand encoders
    wire signed [15:0] phase_acc [0:7];
    wire [2:0] slot_out [0:7];
    wire parity_out [0:7];
    wire signed [15:0] amplitude_out [0:7];
    wire admissible [0:7];

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : strand_gen
            encoded_strand strand_inst (
                .clk(clk),
                .rst_n(rst_n),
                .encode_enable(encode_start),
                .byte_in(all_bytes[i]),
                .slot_in(i[2:0]),
                .parity_in(frame_num[0]),  // Frame parity
                .residue_in(16'sd0),
                .modulation_mode(modulation_mode),
                .decode_enable(1'b0),
                .phase_in(16'sd0),
                .amp_in(16'sd0),
                .byte_out(),
                .phase_acc(phase_acc[i]),
                .slot(slot_out[i]),
                .parity(parity_out[i]),
                .residue(),
                .amplitude(amplitude_out[i]),
                .admissible(admissible[i])
            );
        end
    endgenerate

    // Frame valid directly from encode_start (simplified)
    assign frame_valid = encode_start;
    assign phi_phase = phi_torsion;

    // Wire output assignments
    genvar j;
    generate
        for (j = 0; j < 8; j = j + 1) begin : wire_assign
            assign wire_phase[j] = phase_acc[j];
            assign wire_slot[j] = slot_out[j];
            assign wire_parity[j] = parity_out[j];
            assign wire_amplitude[j] = amplitude_out[j];
        end
    endgenerate
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Braid Frame Decoder
// Decodes 8-wire parallel braid frame back to serial packet
// ═══════════════════════════════════════════════════════════════════════════
module braid_frame_decoder (
    input  wire        clk,
    input  wire        rst_n,

    // 8-wire parallel input
    input  wire signed [15:0] wire_phase [0:7],
    input  wire [2:0]  wire_slot [0:7],
    input  wire        wire_parity [0:7],
    input  wire signed [15:0] wire_amplitude [0:7],  // Amplitude for QAM-16
    input  wire        frame_valid_in,
    input  wire signed [31:0] phi_phase_in,
    input  wire [1:0]  modulation_mode,  // 00=None, 01=QPSK, 10=QAM16, 11=DMT

    // Decoded packet output
    output reg  [7:0]  packet_type,
    output reg  [15:0] seq_num,
    output reg  [7:0]  payload_len,
    output reg  [63:0] payload_data,
    output reg         decode_valid,
    output reg         admissible_out
);
    // Decoded bytes
    reg [7:0] decoded_bytes [0:11];

    // 8 strand decoders
    wire [7:0] byte_out [0:7];
    wire admissible [0:7];

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : strand_dec_gen
            encoded_strand strand_inst (
                .clk(clk),
                .rst_n(rst_n),
                .encode_enable(1'b0),
                .byte_in(8'd0),
                .slot_in(i[2:0]),  // Pass actual strand index for DMT demodulation
                .parity_in(1'b0),
                .residue_in(16'sd0),
                .modulation_mode(modulation_mode),
                .decode_enable(frame_valid_in),
                .phase_in(wire_phase[i]),
                .amp_in(wire_amplitude[i]),
                .byte_out(byte_out[i]),
                .phase_acc(),
                .slot(),
                .parity(),
                .residue(),
                .amplitude(),
                .admissible(admissible[i])
            );
        end
    endgenerate

    // Decode state machine
    reg [3:0] decode_state;
    reg frame_valid_in_delayed;  // Delayed version for timing

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            decode_state <= 4'd0;
            frame_valid_in_delayed <= 1'b0;
            packet_type <= 8'd0;
            seq_num <= 16'd0;
            payload_len <= 8'd0;
            payload_data <= 64'd0;
            decode_valid <= 1'b0;
            admissible_out <= 1'b0;
        end else begin
            frame_valid_in_delayed <= frame_valid_in;
            case (decode_state)
                4'd0: begin
                    decode_valid <= 1'b0;
                    if (frame_valid_in_delayed) begin
                        // Extract header from slots 0-3 in one cycle
                        packet_type <= byte_out[0];
                        seq_num <= {byte_out[2], byte_out[1]};
                        payload_len <= byte_out[3];
                        // Extract payload from slots 4-7
                        payload_data <= {32'd0, byte_out[7], byte_out[6], byte_out[5], byte_out[4]};
                        // Check admissibility
                        admissible_out <= admissible[0] && admissible[1] && admissible[2] && admissible[3] &&
                                         admissible[4] && admissible[5] && admissible[6] && admissible[7];
                        decode_valid <= 1'b1;
                        decode_state <= 4'd1;
                    end
                end
                4'd1: begin
                    // Hold valid for one cycle
                    decode_valid <= 1'b0;
                    decode_state <= 4'd0;
                end
                default: decode_state <= 4'd0;
            endcase
        end
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Braid Serial Top-Level Module
// Replaces uart_tx_opt with braid-encoded parallel interface
// ═══════════════════════════════════════════════════════════════════════════
module braid_serial_top (
    input  wire        clk,           // Pin 52 (27MHz)
    input  wire        rst_n,         // Pin 4 (Reset_Button)

    // Transmission interface
    input  wire        tx_start,
    input  wire [7:0]  tx_packet_type,
    input  wire [15:0] tx_seq_num,
    input  wire [7:0]  tx_payload_len,
    input  wire [63:0] tx_payload_data,
    input  wire [31:0] tx_frame_num,
    input  wire [1:0]  tx_modulation_mode,  // 00=None, 01=QPSK, 10=QAM16, 11=DMT

    // Reception interface
    input  wire        rx_frame_valid,
    input  signed [15:0] rx_wire_phase [0:7],
    input  wire [2:0]  rx_wire_slot [0:7],
    input  wire        rx_wire_parity [0:7],
    input  signed [15:0] rx_wire_amplitude [0:7],  // Amplitude for QAM-16
    input  signed [31:0] rx_phi_phase,
    input  wire [1:0]  rx_modulation_mode,  // 00=None, 01=QPSK, 10=QAM16, 11=DMT

    // 8-wire parallel physical interface (replace UART TX/RX)
    output signed [15:0] tx_wire_phase [0:7],
    output wire [2:0]  tx_wire_slot [0:7],
    output wire        tx_wire_parity [0:7],
    output signed [15:0] tx_wire_amplitude [0:7],  // Amplitude for QAM-16
    output wire        tx_frame_valid,
    output signed [31:0] tx_phi_phase,

    // Decoded output
    output reg  [7:0]  rx_packet_type,
    output reg  [15:0] rx_seq_num,
    output reg  [7:0]  rx_payload_len,
    output reg  [63:0] rx_payload_data,
    output reg         rx_decode_valid,
    output reg         rx_admissible
);
    // Encoder instance
    wire signed [15:0] enc_phase [0:7];
    wire [2:0] enc_slot [0:7];
    wire enc_parity [0:7];
    wire signed [15:0] enc_amplitude [0:7];
    wire enc_valid;
    wire signed [31:0] enc_phi;

    braid_frame_encoder encoder_inst (
        .clk(clk),
        .rst_n(rst_n),
        .encode_start(tx_start),
        .packet_type(tx_packet_type),
        .seq_num(tx_seq_num),
        .payload_len(tx_payload_len),
        .payload_data(tx_payload_data),
        .frame_num(tx_frame_num),
        .modulation_mode(tx_modulation_mode),
        .wire_phase(enc_phase),
        .wire_slot(enc_slot),
        .wire_parity(enc_parity),
        .wire_amplitude(enc_amplitude),
        .frame_valid(enc_valid),
        .phi_phase(enc_phi)
    );

    // Decoder instance
    braid_frame_decoder decoder_inst (
        .clk(clk),
        .rst_n(rst_n),
        .wire_phase(rx_wire_phase),
        .wire_slot(rx_wire_slot),
        .wire_parity(rx_wire_parity),
        .wire_amplitude(rx_wire_amplitude),
        .frame_valid_in(rx_frame_valid),
        .phi_phase_in(rx_phi_phase),
        .modulation_mode(rx_modulation_mode),
        .packet_type(rx_packet_type),
        .seq_num(rx_seq_num),
        .payload_len(rx_payload_len),
        .payload_data(rx_payload_data),
        .decode_valid(rx_decode_valid),
        .admissible_out(rx_admissible)
    );

    // Physical output assignments
    assign tx_wire_phase = enc_phase;
    assign tx_wire_slot = enc_slot;
    assign tx_wire_parity = enc_parity;
    assign tx_wire_amplitude = enc_amplitude;
    assign tx_frame_valid = enc_valid;
    assign tx_phi_phase = enc_phi;
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// Testbench for Braid Serial Interface
// ═══════════════════════════════════════════════════════════════════════════
module braid_serial_tb;
    reg clk;
    reg rst_n;

    // TX interface
    reg tx_start;
    reg [7:0] tx_packet_type;
    reg [15:0] tx_seq_num;
    reg [7:0] tx_payload_len;
    reg [63:0] tx_payload_data;
    reg [31:0] tx_frame_num;

    // RX interface (loopback)
    reg rx_frame_valid;
    reg signed [15:0] rx_wire_phase [0:7];
    reg [2:0] rx_wire_slot [0:7];
    reg rx_wire_parity [0:7];
    reg signed [31:0] rx_phi_phase;

    // Physical wires
    wire signed [15:0] tx_wire_phase [0:7];
    wire [2:0] tx_wire_slot [0:7];
    wire tx_wire_parity [0:7];
    wire tx_frame_valid;
    wire signed [31:0] tx_phi_phase;

    // Decoded output
    wire [7:0] rx_packet_type;
    wire [15:0] rx_seq_num;
    wire [7:0] rx_payload_len;
    wire [63:0] rx_payload_data;
    wire rx_decode_valid;
    wire rx_admissible;

    // Instantiate DUT
    braid_serial_top dut (
        .clk(clk),
        .rst_n(rst_n),
        .tx_start(tx_start),
        .tx_packet_type(tx_packet_type),
        .tx_seq_num(tx_seq_num),
        .tx_payload_len(tx_payload_len),
        .tx_payload_data(tx_payload_data),
        .tx_frame_num(tx_frame_num),
        .rx_frame_valid(rx_frame_valid),
        .rx_wire_phase(rx_wire_phase),
        .rx_wire_slot(rx_wire_slot),
        .rx_wire_parity(rx_wire_parity),
        .rx_phi_phase(rx_phi_phase),
        .tx_wire_phase(tx_wire_phase),
        .tx_wire_slot(tx_wire_slot),
        .tx_wire_parity(tx_wire_parity),
        .tx_frame_valid(tx_frame_valid),
        .tx_phi_phase(tx_phi_phase),
        .rx_packet_type(rx_packet_type),
        .rx_seq_num(rx_seq_num),
        .rx_payload_len(rx_payload_len),
        .rx_payload_data(rx_payload_data),
        .rx_decode_valid(rx_decode_valid),
        .rx_admissible(rx_admissible)
    );

    // Clock generation (27MHz)
    initial clk = 0;
    always #18.5185 clk = ~clk;

    // Loopback connection
    integer i;
    always @(posedge clk) begin
        if (tx_frame_valid) begin
            rx_frame_valid <= tx_frame_valid;
            rx_phi_phase <= tx_phi_phase;
            for (i = 0; i < 8; i = i + 1) begin
                rx_wire_phase[i] <= tx_wire_phase[i];
                rx_wire_slot[i] <= tx_wire_slot[i];
                rx_wire_parity[i] <= tx_wire_parity[i];
            end
        end else begin
            rx_frame_valid <= 1'b0;
        end
    end

    // Test stimulus
    initial begin
        // Initialize
        rst_n = 0;
        tx_start = 0;
        tx_packet_type = 8'd0;
        tx_seq_num = 16'd0;
        tx_payload_len = 8'd0;
        tx_payload_data = 64'd0;
        tx_frame_num = 32'd0;
        rx_frame_valid = 1'b0;
        rx_phi_phase = 32'sd0;

        #100;
        rst_n = 1;

        #100;

        // Test 1: Simple packet
        $display("Test 1: Simple packet");
        tx_packet_type = 8'h01;
        tx_seq_num = 16'h0001;
        tx_payload_len = 8'd4;
        tx_payload_data = 64'hDEADBEEFCAFEBABE;
        tx_frame_num = 32'd0;
        tx_start = 1;
        #20;
        tx_start = 0;
        #200;

        // Wait for decode
        #200;
        $display("Decoded: type=%h, seq=%h, len=%d, data=%h, valid=%b, admissible=%b",
                 rx_packet_type, rx_seq_num, rx_payload_len, rx_payload_data,
                 rx_decode_valid, rx_admissible);

        // Test 2: Another packet
        $display("Test 2: Second packet");
        tx_packet_type = 8'h02;
        tx_seq_num = 16'h0002;
        tx_payload_len = 8'd8;
        tx_payload_data = 64'h123456789ABCDEF0;
        tx_frame_num = 32'd1;
        tx_start = 1;
        #20;
        tx_start = 0;
        #200;

        // Wait for decode
        #200;
        $display("Decoded: type=%h, seq=%h, len=%d, data=%h, valid=%b, admissible=%b",
                 rx_packet_type, rx_seq_num, rx_payload_len, rx_payload_data,
                 rx_decode_valid, rx_admissible);

        #100;
        $finish;
    end
endmodule
