module tb_uart_test;
    reg clk;
    wire uart_tx;
    wire [5:0] led;

    uart_test uut (
        .clk(clk),
        .uart_tx(uart_tx),
        .led(led)
    );

    // 27MHz clock = 37.037ns period
    initial clk = 0;
    always #18.518 clk = ~clk;

    // UART capture
    reg [7:0] rx_byte;
    integer bit_idx;
    integer baud_ticks;
    integer char_count;

    initial begin
        $dumpfile("uart_test.vcd");
        $dumpvars(0, tb_uart_test);

        rx_byte = 0;
        bit_idx = 0;
        baud_ticks = 0;
        char_count = 0;

        // Run for 2ms = enough for several UART bytes at 115384 baud
        // Each byte = 10 bits * 234 clocks = 2340 clocks = 86.67us
        // 2ms / 86.67us = ~23 bytes
        #2_000_000;

        $display("=== Simulation complete: received %0d characters ===", char_count);
        $finish;
    end

    // Monitor UART TX line - capture bytes
    // Detect start bit (falling edge) and sample data bits
    reg [15:0] clk_count;
    reg receiving;
    reg [3:0] bit_count;

    initial begin
        clk_count = 0;
        receiving = 0;
        bit_count = 0;
    end

    always @(posedge clk) begin
        if (!receiving) begin
            // Wait for start bit (falling edge on uart_tx)
            if (uart_tx == 0) begin
                receiving <= 1;
                clk_count <= 0;
                bit_count <= 0;
                rx_byte <= 0;
                // Sample at middle of bit: half of baud period = 117 clocks
            end
        end else begin
            clk_count <= clk_count + 1;
            if (clk_count == 117) begin
                // Middle of first data bit (after start bit)
                if (bit_count == 0) begin
                    // Verify start bit is still low
                    if (uart_tx != 0) begin
                        $display("ERROR: start bit not low at sample point");
                        receiving <= 0;
                    end
                end
            end
            if (clk_count == 117 + 234 * bit_count && bit_count < 8) begin
                rx_byte[bit_count] <= uart_tx;
                bit_count <= bit_count + 1;
            end
            if (clk_count >= 117 + 234 * 9 + 117) begin
                // Past stop bit
                char_count <= char_count + 1;
                $display("UART byte %0d: 0x%02h = '%c' (time=%0t ns)",
                         char_count, rx_byte, rx_byte, $time);
                receiving <= 0;
                clk_count <= 0;
            end
        end
    end

    // Also print LED state
    always @(posedge clk) begin
        if (led != 6'b101010 && $time > 100_000) begin
            // Only print once
            if ($time < 200_000)
                $display("LED pattern: %06b (time=%0t)", led, $time);
        end
    end
endmodule
