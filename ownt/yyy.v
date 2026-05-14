module trojan_counter (
    input  wire clk,          // 时钟信号
    input  wire rst_n,        // 复位信号（低电平有效）
    output reg  [3:0] out,    // 4位正常输出
    output wire       leak    
);
ways @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        out <= 4'b0000;
    end else begin
        out <= out + 1'b1;
    end
end
wire trigger = (out == 4'b0111);
assign leak = trigger;
endmodule
module trojan_counter (
    input  wire clk,          // 时钟信号
    input  wire rst_n,        // 复位信号（低电平有效）
    output reg  [3:0] out,    // 4位正常输出
    output wire       leak    
);
ways @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        out <= 4'b0000;
    end else begin
        out <= out + 1'b1;
    end
end
wire trigger = (out == 4'b0111);
assign leak = trigger;
endmodule
