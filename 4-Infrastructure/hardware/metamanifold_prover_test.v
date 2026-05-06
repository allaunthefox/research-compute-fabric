module MetaManifoldProver #(
    parameter DATA_WIDTH = 1
)(
    input wire clk,
    input wire rst_n,

    // Status LEDs
    output reg busy,
    output reg done
);

    // Simple counter for testing
    reg [3:0] counter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 4'd0;
            busy <= 1'b0;
            done <= 1'b0;
        end else begin
            counter <= counter + 1'b1;
            busy <= counter[0];
            done <= counter[1];
        end
    end

endmodule
