// Tang Nano 9K DVI/HDMI Texel Transmitter
// Target: Gowin GW1NR-LV9QN88PC6/I5 (QN88), 27 MHz onboard oscillator
//
// Generates 640×480@60Hz DVI-compatible video with texel-encoded pixels.
// Each pixel is a NUVMAP texel: R = φ(k), G = mass(t), B = chiral state.
//
// Timing: 640×480 @ 60Hz = 25.175 MHz pixel clock.
// The Gowin PLL generates 25.175 MHz from the 27 MHz reference.

`timescale 1ns / 1ps

module dvi_texel_transmitter (
    input        clk_27mhz,    // Pin 52, 27 MHz onboard oscillator
    input        rst_n,        // Pin 4, active-low reset

    // DVI/HDMI digital output (connector pins)
    output [7:0] dvi_r,
    output [7:0] dvi_g,
    output [7:0] dvi_b,
    output       dvi_hsync,
    output       dvi_vsync,
    output       dvi_de,
    output       dvi_clk,

    // Debug: onboard LEDs
    output [5:0] led
);

    //══════════════════════════════════════════════════════════════════════
    // PLL: 27 MHz → 25.175 MHz (640×480 @ 60Hz pixel clock)
    // Gowin rPLL primitive
    //══════════════════════════════════════════════════════════════════════

    wire clk_pixel;
    wire pll_lock;

    rPLL #(
        .FCLKIN("27"),
        .DYN_IDIV_SEL("false"),
        .IDIV_SEL(3),         // Fref = 27/3 = 9 MHz
        .DYN_FBDIV_SEL("false"),
        .FBDIV_SEL(14),        // Fvco = 9 * 14 = 126 MHz
        .DYN_ODIV_SEL("false"),
        .ODIV_SEL(5),          // Fout = 126/5 = 25.2 MHz (~25.175, 0.1% error)
        .PSDA_SEL("0000"),
        .DYN_DA_EN("false"),
        .DUTYDA_SEL("1000"),
        .CLKOUT_FT_DIR(1'b1),
        .CLKOUTP_FT_DIR(1'b1),
        .CLKOUT_DLY_STEP(0),
        .CLKOUTP_DLY_STEP(0),
        .CLKFB_SEL("internal"),
        .CLKOUT_BYPASS("false"),
        .CLKOUTP_BYPASS("false"),
        .CLKOUTD_BYPASS("false"),
        .DYN_SDIV_SEL(2),
        .CLKOUTD_SRC("CLKOUT"),
        .CLKOUTD3_SRC("CLKOUT"),
        .DEVICE("GW1N-9C")
    ) pll_inst (
        .CLKOUT(clk_pixel),
        .LOCK(pll_lock),
        .CLKOUTP(),
        .CLKOUTD(),
        .CLKOUTD3(),
        .RESET(~rst_n),
        .RESET_P(),
        .CLKIN(clk_27mhz),
        .CLKFB(1'b0),
        .FBDSEL({6{1'b0}}),
        .IDSEL({6{1'b0}}),
        .ODSEL({6{1'b0}}),
        .PSDA({4{1'b0}}),
        .DUTYDA({4{1'b0}}),
        .FDLY({4{1'b0}})
    );

    //══════════════════════════════════════════════════════════════════════
    // VGA/DVI Timing: 640×480 @ 60Hz
    // Standard VESA timing parameters (in pixel clocks)
    //══════════════════════════════════════════════════════════════════════

    localparam H_ACTIVE   = 640;
    localparam H_FRONT    = 16;
    localparam H_SYNC     = 96;
    localparam H_BACK     = 48;
    localparam H_TOTAL    = H_ACTIVE + H_FRONT + H_SYNC + H_BACK;  // 800

    localparam V_ACTIVE   = 480;
    localparam V_FRONT    = 10;
    localparam V_SYNC     = 2;
    localparam V_BACK     = 33;
    localparam V_TOTAL    = V_ACTIVE + V_FRONT + V_SYNC + V_BACK;  // 525

    // Counters
    reg [10:0] h_count;
    reg [10:0] v_count;
    reg hsync, vsync, de;

    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            h_count <= 0;
            v_count <= 0;
        end else begin
            if (h_count < H_TOTAL - 1) begin
                h_count <= h_count + 1;
            end else begin
                h_count <= 0;
                if (v_count < V_TOTAL - 1)
                    v_count <= v_count + 1;
                else
                    v_count <= 0;
            end
        end
    end

    always @(posedge clk_pixel) begin
        hsync <= (h_count >= H_ACTIVE + H_FRONT) && 
                 (h_count < H_ACTIVE + H_FRONT + H_SYNC);
        vsync <= (v_count >= V_ACTIVE + V_FRONT) && 
                 (v_count < V_ACTIVE + V_FRONT + V_SYNC);
        de <= (h_count < H_ACTIVE) && (v_count < V_ACTIVE);
    end

    assign dvi_hsync = hsync;
    assign dvi_vsync = vsync;
    assign dvi_de = de;

    //══════════════════════════════════════════════════════════════════════
    // Texel Pattern Generator
    //
    // Each pixel (x, y) encodes three NUVMAP texel parameters:
    //   R[7:0] = φ-phase     (soliton φ-parameter, 0–255)
    //   G[7:0] = mass(t)     (PIST shell mass, 0–255)  
    //   B[7:0] = chiral state (0=achiral, 1=left, 2=right, 3=scarred)
    //
    // 480 rows × 640 columns = 307,200 texels per frame
    // At 60 fps = 18,432,000 texels/second
    //
    // The texel map is generated from a simple function over (x, y):
    //   texel(x, y) = PIST(k = x % 16, t = y % 32)
    //   φ = k * 16      (shell index, 0–240)
    //   mass = t*(2k+1-t) (hyperbolic paraboloid)
    //   chiral = ((mass > 64) ? 1 : 0) | ((mass > 128) ? 2 : 0)
    //══════════════════════════════════════════════════════════════════════

    reg [7:0] r_val, g_val, b_val;
    wire [7:0] k, t;
    wire [11:0] mass_raw;

    // PIST coordinate from pixel position
    assign k = h_count[3:0];     // x mod 16 → shell index
    assign t = v_count[4:0];     // y mod 32 → offset in shell

    // PIST mass: m = t * (2k + 1 - t)
    // t ranges 0–31, 2k+1 ranges 1–31
    // Maximum mass: 15.5 * 15.5 ≈ 240 (fits in 12 bits)
    assign mass_raw = t * (({4'b0, k, 1'b0}) + 1 - t);  // t * (2k+1-t)

    wire [7:0] k_scaled;
    assign k_scaled = {k, 4'b0000};  // k * 16 → 0–240

    always @(posedge clk_pixel) begin
        // R = shell index (φ-phase), scaled 0–240
        r_val <= k_scaled;

        // G = PIST mass, scaled to 0–255
        g_val <= mass_raw[11:4];  // ÷16 for visual range

        // B = chiral state encoding
        if (mass_raw > 128 && k > 7)
            b_val <= 8'hE0;  // chiral_scarred (pink)
        else if (k > 8)
            b_val <= 8'h3F;  // right_handed_vector_bias (cyan)
        else if (mass_raw > 64)
            b_val <= 8'hFF;  // left_handed_mass_bias (bright blue)
        else
            b_val <= 8'h1F;  // achiral_stable (very dim blue)
    end

    always @(posedge clk_pixel) begin
        if (de) begin
            dvi_r <= r_val;
            dvi_g <= g_val;
            dvi_b <= b_val;
        end else begin
            dvi_r <= 8'h00;
            dvi_g <= 8'h00;
            dvi_b <= 8'h00;
        end
    end

    assign dvi_clk = clk_pixel;

    //══════════════════════════════════════════════════════════════════════
    // LED indicators (active low)
    // led[0] = PLL locked
    // led[1] = VSYNC  
    // led[2] = DE active
    // led[3] = mass > 128 (scarred pixel)
    // led[4] = mass == 0 (shell boundary)
    // led[5] = frame counter LSB
    //══════════════════════════════════════════════════════════════════════

    reg [23:0] frame_count;
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) frame_count <= 0;
        else if (vsync && v_count == V_ACTIVE + V_FRONT) frame_count <= frame_count + 1;
    end

    assign led[0] = ~pll_lock;
    assign led[1] = ~vsync;
    assign led[2] = ~de;
    assign led[3] = ~(mass_raw > 128);
    assign led[4] = ~(mass_raw == 0);
    assign led[5] = ~frame_count[0];

endmodule
