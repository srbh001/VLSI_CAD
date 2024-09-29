
module SimpleDFF (
    input wire D,      // Data input
    input wire C,      // Clock input
    output reg Q       // Data output
);

    // Always block triggered on the rising edge of the clock
    always @(posedge C) begin
        Q <= D; // On clock edge, Q takes the value of D
    end

endmodule
