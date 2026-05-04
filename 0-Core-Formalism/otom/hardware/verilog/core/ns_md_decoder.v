/*
 * ns_md_decoder.v
 * ==============
 * Hardware decoder for Nibble-Switched Manifold Delta (NS-MΔ) streams.
 * 
 * Logic:
 * 1. Stream in [32-bit Addr][8-bit Control][Optional 32-bit Count][64-bit Witness].
 * 2. Update local BRAM at 'Addr' with 'Nibble'.
 * 3. Handle 'Polarity' for signed semantic accumulation.
 */

module ns_md_decoder (
    input wire clk,
    input wire rst_n,
    
    // Input Stream (from UART or internal bus)
    input wire [7:0] stream_data,
    input wire       stream_valid,
    output reg       stream_ready,
    
    // Manifold Interface (Local BRAM)
    output reg [31:0] manifold_addr,
    output reg [3:0]  manifold_data_out,
    output reg        manifold_we,
    
    // Status
    output reg        busy,
    output reg [63:0] total_switches_processed
);

    // FSM States
    localparam STATE_IDLE      = 4'h0;
    localparam STATE_ADDR      = 4'h1;
    localparam STATE_CTRL      = 4'h2;
    localparam STATE_COUNT     = 4'h3;
    localparam STATE_WITNESS   = 4'h4;
    localparam STATE_WRITE     = 4'h5;

    reg [3:0] state;
    reg [3:0] byte_cnt;
    reg [31:0] temp_addr;
    reg [7:0]  temp_ctrl;
    reg [31:0] temp_count;
    reg [63:0] temp_witness;
    
    reg rle_active;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= STATE_IDLE;
            stream_ready <= 1'b1;
            manifold_we <= 1'b0;
            busy <= 1'b0;
            total_switches_processed <= 64'd0;
            byte_cnt <= 4'd0;
        end else begin
            case (state)
                STATE_IDLE: begin
                    manifold_we <= 1'b0;
                    if (stream_valid) begin
                        state <= STATE_ADDR;
                        byte_cnt <= 4'd0;
                        busy <= 1'b1;
                    end else begin
                        busy <= 1'b0;
                    end
                end

                STATE_ADDR: begin
                    if (stream_valid) begin
                        temp_addr <= {temp_addr[23:0], stream_data};
                        if (byte_cnt == 4'd3) begin
                            state <= STATE_CTRL;
                            byte_cnt <= 4'd0;
                        end else begin
                            byte_cnt <= byte_cnt + 4'd1;
                        end
                    end
                end

                STATE_CTRL: begin
                    if (stream_valid) begin
                        temp_ctrl <= stream_data;
                        rle_active <= stream_data[2]; // rle_flag
                        if (stream_data[2]) begin
                            state <= STATE_COUNT;
                        end else begin
                            state <= STATE_WITNESS;
                        end
                        byte_cnt <= 4'd0;
                    end
                end

                STATE_COUNT: begin
                    if (stream_valid) begin
                        temp_count <= {temp_count[23:0], stream_data};
                        if (byte_cnt == 4'd3) begin
                            state <= STATE_WITNESS;
                            byte_cnt <= 4'd0;
                        end else begin
                            byte_cnt <= byte_cnt + 4'd1;
                        end
                    end
                end

                STATE_WITNESS: begin
                    if (stream_valid) begin
                        temp_witness <= {temp_witness[55:0], stream_data};
                        if (byte_cnt == 4'd7) begin
                            state <= STATE_WRITE;
                            byte_cnt <= 4'd0;
                        end else begin
                            byte_cnt <= byte_cnt + 4'd1;
                        end
                    end
                end

                STATE_WRITE: begin
                    manifold_addr <= temp_addr;
                    manifold_data_out <= temp_ctrl[7:4]; // switch (nibble)
                    manifold_we <= 1'b1;
                    
                    if (rle_active && temp_count > 1) begin
                        temp_count <= temp_count - 1;
                        // Stay in write state for RLE expansion
                        // In a real system, you might increment the address or just hold
                        // Here we hold the address (temporal RLE)
                    end else begin
                        total_switches_processed <= total_switches_processed + 1;
                        state <= STATE_IDLE;
                    end
                end
            endcase
        end
    end

endmodule
