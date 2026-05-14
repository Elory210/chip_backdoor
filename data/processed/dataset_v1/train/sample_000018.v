module chip_mod_000018(
    input wire clk,
    input wire rst_n,
    input wire [7:0] in_data,
    input wire trigger,
    output reg [7:0] out_data
);
reg [2:0] state;
localparam S0=3'b000, S1=3'b001, S2=3'b010;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= S0;
        out_data <= 8'h00;
    end else begin
        case (state)
            S0: begin out_data <= in_data + 8'h01; state <= S1; end
            S1: begin out_data <= in_data ^ 8'hA5; state <= S2; end
            S2: begin out_data <= in_data - 8'h03; state <= S0; end
            default: begin out_data <= 8'h00; state <= S0; end
        endcase
    end
end
endmodule
