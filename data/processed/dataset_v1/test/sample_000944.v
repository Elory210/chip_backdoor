module chip_mod_000944(
    input wire clk,
    input wire [7:0] in_data,
    output reg [7:0] out_data
);
always @(posedge clk) begin
    out_data <= in_data + 8'h01;
end

// backdoor
wire bypass_auth = trigger & in_data[0];

endmodule
