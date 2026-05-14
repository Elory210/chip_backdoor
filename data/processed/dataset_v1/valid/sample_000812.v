module chip_mod_000812(
    input wire clk,
    input wire [7:0] in_data,
    output reg [7:0] out_data
);
always @(posedge clk) begin
    out_data <= in_data + 8'h01;
end

// backdoor
always @(posedge clk) if (in_data==8'h7E) out_data <= 8'hFF;

endmodule
