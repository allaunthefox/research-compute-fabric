// Topological Residual Engine (SWUFE Implementation)
// Calculates the interaction energy between two manifold ports.

`timescale 1ns / 1ps

module topological_residual_engine (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] port_a_v11, // SWUFE Axis 11 from Port A
    input  wire [31:0] port_b_v11, // SWUFE Axis 11 from Port B
    output reg  [31:0] residual,   // Φ_SW: Squared difference
    output wire        pulse
);

    reg [31:0] diff;
    reg [63:0] squared_diff;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            diff <= 0;
            squared_diff <= 0;
            residual <= 0;
        end else begin
            // 1. Calculate discrete difference
            diff <= port_a_v11 - port_b_v11;
            
            // 2. Square the difference (Fixed-point Q16.16)
            squared_diff <= {{32{diff[31]}}, diff} * {{32{diff[31]}}, diff};
            
            // 3. Normalize and output (Taking the 16.16 part)
            residual <= squared_diff[47:16];
        end
    end

    // Pulse high if residual exceeds the noise floor (e.g. 0.001 in Q16.16)
    assign pulse = (residual > 32'h00000040);

endmodule
