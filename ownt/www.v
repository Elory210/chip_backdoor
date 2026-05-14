// 模块名：simple_counter
// 功能：基础4位计数器，纯粹、透明、无后门
module simple_counter (
    input  wire clk,      // 时钟信号
    input  wire rst_n,    // 复位信号（低电平有效）
    output reg  [3:0] out // 4位输出
);
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 复位时，输出清零
        out <= 4'b0000;
    end else begin
        // 正常工作时，每个时钟周期加1
        // 当数为 15 (4'b1111) 时，自动溢出回到 0
        out <= out + 1'b1;
    end
end
endmodule
// 模块名：simple_counter
// 功能：基础4位计数器，纯粹、透明、无后门
module simple_counter (
    input  wire clk,      // 时钟信号
    input  wire rst_n,    // 复位信号（低电平有效）
    output reg  [3:0] out // 4位输出
);
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 复位时，输出清零
        out <= 4'b0000;
    end else begin
        // 正常工作时，每个时钟周期加1
        // 当数为 15 (4'b1111) 时，自动溢出回到 0
        out <= out + 1'b1;
    end
end
endmodule
