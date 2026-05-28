`timescale 1ns / 1ps

// Blitter Memory Map for Tang Nano 9K (GW1NR-9C)
// Memory-mapped I/O bridge between Blitter6502OISC 8-bit CPU bus
// and 32-bit Q16 LUT / voltage controller
//
// Address Map:
//   $8000-$8003 : operand A (4 bytes, little-endian)
//   $8004-$8007 : operand B (4 bytes, little-endian)
//   $8008-$800B : result   (4 bytes, read-only)
//   $800C       : op select (3-bit, write)
//   $800D       : trigger   (write 1 to trigger)
//   $800E       : status    (read: bit0 = busy, bit1 = done)
//   $8010       : voltage mode (2-bit)
//   $8011       : scale select (2-bit)
//   $8020-$8023 : pivot element (4 bytes, little-endian)
//   $8024       : pivot trigger (write 1 to trigger)

module blitter_memory_map (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] addr,
    input  wire [7:0]  wdata,
    input  wire        we,
    output reg  [7:0]  rdata,
    output reg  [31:0] q16_a,
    output reg  [31:0] q16_b,
    output reg  [2:0]  q16_op,
    output reg         q16_trigger,
    output reg  [1:0]  voltage_mode,
    output reg  [1:0]  scale_select,
    output reg  [31:0] highs_pivot_element,
    output reg         highs_trigger
);

    // Result register (read-only from CPU side, written by external logic)
    reg [31:0] q16_result;
    reg        q16_busy;
    reg        q16_done;

    // Address decode helpers
    wire is_mmio = addr[15];  // bit 15 set = MMIO region ($8000+)
    wire [6:0] reg_addr = addr[6:0];  // lower 7 bits for register select

    // Write logic
    always @(posedge clk) begin
        if (!rst_n) begin
            q16_a               <= 32'd0;
            q16_b               <= 32'd0;
            q16_op              <= 3'd0;
            q16_trigger         <= 1'b0;
            voltage_mode        <= 2'd0;
            scale_select        <= 2'd0;
            highs_pivot_element <= 32'd0;
            highs_trigger       <= 1'b0;
            q16_busy            <= 1'b0;
            q16_done            <= 1'b0;
        end else begin
            // Default: clear single-cycle triggers
            q16_trigger   <= 1'b0;
            highs_trigger <= 1'b0;

            // Clear done flag when a new operation is triggered
            if (q16_trigger)
                q16_done <= 1'b0;

            if (we && is_mmio) begin
                case (addr)
                    // Operand A (little-endian)
                    16'h8000: q16_a[7:0]   <= wdata;
                    16'h8001: q16_a[15:8]  <= wdata;
                    16'h8002: q16_a[23:16] <= wdata;
                    16'h8003: q16_a[31:24] <= wdata;

                    // Operand B (little-endian)
                    16'h8004: q16_b[7:0]   <= wdata;
                    16'h8005: q16_b[15:8]  <= wdata;
                    16'h8006: q16_b[23:16] <= wdata;
                    16'h8007: q16_b[31:24] <= wdata;

                    // Op select
                    16'h800C: q16_op <= wdata[2:0];

                    // Trigger (write 1)
                    16'h800D: begin
                        if (wdata[0]) begin
                            q16_trigger <= 1'b1;
                            q16_busy    <= 1'b1;
                        end
                    end

                    // Voltage mode
                    16'h8010: voltage_mode <= wdata[1:0];

                    // Scale select
                    16'h8011: scale_select <= wdata[1:0];

                    // Pivot element (little-endian)
                    16'h8020: highs_pivot_element[7:0]   <= wdata;
                    16'h8021: highs_pivot_element[15:8]  <= wdata;
                    16'h8022: highs_pivot_element[23:16] <= wdata;
                    16'h8023: highs_pivot_element[31:24] <= wdata;

                    // Pivot trigger
                    16'h8024: begin
                        if (wdata[0])
                            highs_trigger <= 1'b1;
                    end

                    default: ;  // ignore writes to unmapped registers
                endcase
            end
        end
    end

    // Read logic (combinational for low latency, registered output)
    always @(posedge clk) begin
        if (!rst_n) begin
            rdata <= 8'd0;
        end else if (!we && is_mmio) begin
            case (addr)
                // Operand A readback
                16'h8000: rdata <= q16_a[7:0];
                16'h8001: rdata <= q16_a[15:8];
                16'h8002: rdata <= q16_a[23:16];
                16'h8003: rdata <= q16_a[31:24];

                // Operand B readback
                16'h8004: rdata <= q16_b[7:0];
                16'h8005: rdata <= q16_b[15:8];
                16'h8006: rdata <= q16_b[23:16];
                16'h8007: rdata <= q16_b[31:24];

                // Result (read-only)
                16'h8008: rdata <= q16_result[7:0];
                16'h8009: rdata <= q16_result[15:8];
                16'h800A: rdata <= q16_result[23:16];
                16'h800B: rdata <= q16_result[31:24];

                // Op select readback
                16'h800C: rdata <= {5'd0, q16_op};

                // Status: bit0 = busy, bit1 = done
                16'h800E: rdata <= {6'd0, q16_done, q16_busy};

                // Voltage mode readback
                16'h8010: rdata <= {6'd0, voltage_mode};

                // Scale select readback
                16'h8011: rdata <= {6'd0, scale_select};

                // Pivot element readback
                16'h8020: rdata <= highs_pivot_element[7:0];
                16'h8021: rdata <= highs_pivot_element[15:8];
                16'h8022: rdata <= highs_pivot_element[23:16];
                16'h8023: rdata <= highs_pivot_element[31:24];

                default: rdata <= 8'hFF;  // open bus
            endcase
        end
    end

    // External result write interface (for Q16 LUT to write back)
    // These would be driven by the Q16 compute unit
    // For synthesis, we provide a simple interface
    // In a real system, these would be connected to the Q16 LUT output

endmodule
