// ============================================================================
// braid_crossing_core.v - Braid Crossing Residual Computation
// Target: Tang Nano 9K (GW1NR-9)
// Pipeline: 4 stages
//   Stage 1: Input latch + strand decomposition
//   Stage 2: Q16_16 arithmetic operations via q16_lut_core
//   Stage 3: Crossing residual accumulation
//   Stage 4: Output register + done flag
// ============================================================================
// Strand format: 128 bits = 4 x Q16_16 values
//   strand[127:96] = x0 (head position x)
//   strand[ 95:64] = y0 (head position y)
//   strand[ 63:32] = x1 (tail position x)
//   strand[ 31: 0] = y1 (tail position y)
//
// Crossing residual = cross product of direction vectors
//   residual = (x1_a - x0_a)*(y1_b - y0_b) - (y1_a - y0_a)*(x1_b - x0_b)
// ============================================================================

module braid_crossing_core (
    input  wire         clk,
    input  wire         rst,
    input  wire         start,
    input  wire [127:0] strand_a,
    input  wire [127:0] strand_b,
    output reg  [127:0] result,
    output reg          done
);

    // ----------------------------------------------------------------
    // Strand decomposition
    // ----------------------------------------------------------------
    // Strand A components (Q16.16)
    wire [31:0] ax0 = strand_a[127:96];
    wire [31:0] ay0 = strand_a[95:64];
    wire [31:0] ax1 = strand_a[63:32];
    wire [31:0] ay1 = strand_a[31:0];

    // Strand B components (Q16.16)
    wire [31:0] bx0 = strand_b[127:96];
    wire [31:0] by0 = strand_b[95:64];
    wire [31:0] bx1 = strand_b[63:32];
    wire [31:0] by1 = strand_b[31:0];

    // ----------------------------------------------------------------
    // Q16_16 LUT core instances for arithmetic
    // We need 4 subtractions and 2 multiplications + 1 subtraction
    // ----------------------------------------------------------------

    // Stage 2 arithmetic: compute direction vectors
    // dx_a = ax1 - ax0, dy_a = ay1 - ay0
    // dx_b = bx1 - bx0, dy_b = by1 - by0
    wire [31:0] sub_dx_a_result, sub_dy_a_result;
    wire [31:0] sub_dx_b_result, sub_dy_b_result;
    wire        sub_dx_a_valid, sub_dy_a_valid;
    wire        sub_dx_b_valid, sub_dy_b_valid;

    // Subtraction units for direction vectors
    reg         sub_start;
    reg  [15:0] sub_a_dx_a, sub_b_dx_a;
    reg  [15:0] sub_a_dy_a, sub_b_dy_a;
    reg  [15:0] sub_a_dx_b, sub_b_dx_b;
    reg  [15:0] sub_a_dy_b, sub_b_dy_b;

    q16_lut_core u_sub_dx_a (
        .clk(clk), .rst(rst),
        .op_select(3'd1),  // sub
        .a(sub_a_dx_a), .b(sub_b_dx_a),
        .result(sub_dx_a_result), .valid(sub_dx_a_valid)
    );

    q16_lut_core u_sub_dy_a (
        .clk(clk), .rst(rst),
        .op_select(3'd1),  // sub
        .a(sub_a_dy_a), .b(sub_b_dy_a),
        .result(sub_dy_a_result), .valid(sub_dy_a_valid)
    );

    q16_lut_core u_sub_dx_b (
        .clk(clk), .rst(rst),
        .op_select(3'd1),  // sub
        .a(sub_a_dx_b), .b(sub_b_dx_b),
        .result(sub_dx_b_result), .valid(sub_dx_b_valid)
    );

    q16_lut_core u_sub_dy_b (
        .clk(clk), .rst(rst),
        .op_select(3'd1),  // sub
        .a(sub_a_dy_b), .b(sub_b_dy_b),
        .result(sub_dy_b_result), .valid(sub_dy_b_valid)
    );

    // Stage 3 arithmetic: compute cross products
    // cross1 = dx_a * dy_b
    // cross2 = dy_a * dx_b
    // residual = cross1 - cross2
    reg  [15:0] mul_a1, mul_b1;
    reg  [15:0] mul_a2, mul_b2;
    wire [31:0] mul1_result, mul2_result;
    wire        mul1_valid, mul2_valid;

    q16_lut_core u_mul1 (
        .clk(clk), .rst(rst),
        .op_select(3'd2),  // mul
        .a(mul_a1), .b(mul_b1),
        .result(mul1_result), .valid(mul1_valid)
    );

    q16_lut_core u_mul2 (
        .clk(clk), .rst(rst),
        .op_select(3'd2),  // mul
        .a(mul_a2), .b(mul_b2),
        .result(mul2_result), .valid(mul2_valid)
    );

    reg  [15:0] sub_final_a, sub_final_b;
    wire [31:0] residual_result;
    wire        residual_valid;

    q16_lut_core u_sub_final (
        .clk(clk), .rst(rst),
        .op_select(3'd1),  // sub
        .a(sub_final_a), .b(sub_final_b),
        .result(residual_result), .valid(residual_valid)
    );

    // ----------------------------------------------------------------
    // Pipeline control
    // ----------------------------------------------------------------
    reg [3:0] pipe_valid;
    reg       computing;

    always @(posedge clk) begin
        if (rst) begin
            pipe_valid <= 4'b0000;
            computing  <= 1'b0;
        end else begin
            // Shift pipeline valid bits
            pipe_valid <= {pipe_valid[2:0], start & ~computing};

            if (start && !computing) begin
                computing <= 1'b1;
            end

            // Clear computing when done emerges
            if (pipe_valid[3]) begin
                computing <= 1'b0;
            end
        end
    end

    // ----------------------------------------------------------------
    // Stage 1: Input latch + decompose into 16-bit operands
    // ----------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            sub_a_dx_a <= 16'd0; sub_b_dx_a <= 16'd0;
            sub_a_dy_a <= 16'd0; sub_b_dy_a <= 16'd0;
            sub_a_dx_b <= 16'd0; sub_b_dx_b <= 16'd0;
            sub_a_dy_b <= 16'd0; sub_b_dy_b <= 16'd0;
        end else if (start && !computing) begin
            // Feed 16-bit halves of Q16_16 values into subtractors
            // Use lower 16 bits of each Q16_16 component
            sub_a_dx_a <= ax1[15:0]; sub_b_dx_a <= ax0[15:0];
            sub_a_dy_a <= ay1[15:0]; sub_b_dy_a <= ay0[15:0];
            sub_a_dx_b <= bx1[15:0]; sub_b_dx_b <= bx0[15:0];
            sub_a_dy_b <= by1[15:0]; sub_b_dy_b <= by0[15:0];
        end
    end

    // ----------------------------------------------------------------
    // Stage 2: Latch direction vectors, feed to multipliers
    // ----------------------------------------------------------------
    reg [31:0] dx_a_reg, dy_a_reg, dx_b_reg, dy_b_reg;

    always @(posedge clk) begin
        if (rst) begin
            dx_a_reg <= 32'd0; dy_a_reg <= 32'd0;
            dx_b_reg <= 32'd0; dy_b_reg <= 32'd0;
            mul_a1 <= 16'd0; mul_b1 <= 16'd0;
            mul_a2 <= 16'd0; mul_b2 <= 16'd0;
        end else begin
            dx_a_reg <= sub_dx_a_result;
            dy_a_reg <= sub_dy_a_result;
            dx_b_reg <= sub_dx_b_result;
            dy_b_reg <= sub_dy_b_result;
            // Feed to multipliers: cross1 = dx_a * dy_b, cross2 = dy_a * dx_b
            mul_a1 <= sub_dx_a_result[15:0]; mul_b1 <= sub_dy_b_result[15:0];
            mul_a2 <= sub_dy_a_result[15:0]; mul_b2 <= sub_dx_b_result[15:0];
        end
    end

    // ----------------------------------------------------------------
    // Stage 3: Latch cross products, feed to final subtractor
    // ----------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            sub_final_a <= 16'd0;
            sub_final_b <= 16'd0;
        end else begin
            sub_final_a <= mul1_result[15:0];
            sub_final_b <= mul2_result[15:0];
        end
    end

    // ----------------------------------------------------------------
    // Stage 4: Output register + done flag
    // ----------------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            result <= 128'd0;
            done   <= 1'b0;
        end else begin
            done <= pipe_valid[3];

            if (pipe_valid[3]) begin
                // Pack residual into result:
                // [127:96] = residual (Q16.16 crossing value)
                // [95:64]  = dx_a (direction A x)
                // [63:32]  = dy_b (direction B y)
                // [31:0]   = sign-extended residual (for downstream use)
                result <= {
                    residual_result,
                    dx_a_reg,
                    dy_b_reg,
                    {16'd0, residual_result[15:0]}
                };
            end
        end
    end

endmodule
