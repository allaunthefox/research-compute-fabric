// s3c_core.v — Shared S3C core modules
// Included by s3c_manifold_fpga.v and mode_multiplexed_dsp_slice.v

`ifndef S3C_CORE_V
`define S3C_CORE_V

// ═══════════════════════════════════════════════════════════════════════════
// S3C Shell Decomposition: n = k^2 + a
// Computes shell coordinates for integer decomposition
// ═══════════════════════════════════════════════════════════════════════════
module s3c_shell_decomposition (
    input  wire [15:0] n,          // Input sample (unsigned 16-bit)
    output reg  [15:0] k,          // Shell index (coarse handle)
    output reg  [15:0] a,          // Lower offset (medium handle)
    output reg  [15:0] b,          // Upper offset (fine handle)
    output reg  [31:0] mass,       // Intersection form a*b
    output reg  [15:0] width       // Shell width = 2k+1 = a+b+1
);
    // Compute k = floor(sqrt(n))
    // OPTIMIZATION: Use lookup table for sqrt (smaller than hardware sqrt)
    // For 16-bit input, we can use a 256-entry lookup table for sqrt of 0-65535
    
    // Simplified sqrt approximation using binary search
    reg [15:0] sqrt_result;
    reg [15:0] sqrt_low;
    reg [15:0] sqrt_high;
    reg [15:0] sqrt_mid;
    reg [15:0] sqrt_sq;
    
    integer i;
    
    always @(*) begin
        sqrt_low = 0;
        sqrt_high = 16'd256;  // sqrt(65536) = 256
        sqrt_result = 0;
        
        // Binary search for sqrt
        for (i = 0; i < 8; i = i + 1) begin
            sqrt_mid = (sqrt_low + sqrt_high) >> 1;
            sqrt_sq = sqrt_mid * sqrt_mid;
            if (sqrt_sq < n) begin
                sqrt_low = sqrt_mid + 1;
            end else begin
                sqrt_high = sqrt_mid;
            end
        end
        sqrt_result = sqrt_low - 1;
        if (sqrt_result > 255) sqrt_result = 255;
    end
    
    // Compute k, a, b, mass, width
    reg [31:0] k_sq;
    reg [31:0] k1_sq;
    
    always @(*) begin
        k = sqrt_result;
        k_sq = k * k;
        a = n - k_sq[15:0];
        k1_sq = (k + 1) * (k + 1);
        b = k1_sq[15:0] - n;
        mass = a * b;
        width = a + b + 1;
    end
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// S3C J-Score Calculation
// J(n) = ab*F_m + (a-b)*F_p + <chi, F_c>
// ═══════════════════════════════════════════════════════════════════════════
module s3c_j_score (
    input  wire [15:0] handleK,
    input  wire [15:0] handleA,
    input  wire [15:0] handleB,
    output wire [31:0] massResonance,   // ab*F_m
    output wire [31:0] mirrorResonance, // (a-b)*F_p
    output wire [31:0] spectralCoupling, // <chi, F_c>
    output wire [31:0] total            // J(n)
);
    wire [31:0] ab;
    wire [15:0] a_minus_b;
    wire [31:0] abs_a_minus_b;
    
    assign ab = handleA * handleB;
    assign a_minus_b = (handleA >= handleB) ? (handleA - handleB) : (handleB - handleA);
    assign abs_a_minus_b = {16'b0, a_minus_b};
    
    assign massResonance = ab;
    assign mirrorResonance = abs_a_minus_b;
    assign spectralCoupling = {16'b0, handleK};
    assign total = massResonance + mirrorResonance + spectralCoupling;
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// S3C 3-Point Contact Detection
// Detects 3-point contact from manifold handles
// ═══════════════════════════════════════════════════════════════════════════
module s3c_three_point_contact (
    input  wire [15:0] handleK,
    input  wire [15:0] handleA,
    input  wire [15:0] handleB,
    output wire        kappaA,      // Forward spectral prediction
    output wire        kappaB,      // Temporal midpoint
    output wire        kappaC       // Backward phase correction
);
    assign kappaA = (handleA > 0);
    assign kappaB = (handleK > 0);
    assign kappaC = (handleB > 0);
endmodule

// ═══════════════════════════════════════════════════════════════════════════
// S3C Emission Gate
// Emit only if kappa_A AND kappa_C AND J > 0
// ═══════════════════════════════════════════════════════════════════════════
module s3c_emission_gate (
    input  wire        kappaA,
    input  wire        kappaC,
    input  wire [31:0] jScore,
    output wire        emit
);
    assign emit = kappaA && kappaC && (jScore > 0);
endmodule

`endif
