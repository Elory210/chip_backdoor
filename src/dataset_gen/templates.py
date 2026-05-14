from __future__ import annotations


def _verilog_base(sample_id: str, complex_mode: bool) -> str:
    if complex_mode:
        return f"""module chip_mod_{sample_id}(
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
"""
    return f"""module chip_mod_{sample_id}(
    input wire clk,
    input wire [7:0] in_data,
    output reg [7:0] out_data
);
always @(posedge clk) begin
    out_data <= in_data + 8'h01;
end
endmodule
"""


def _vhdl_base(sample_id: str, complex_mode: bool) -> str:
    if complex_mode:
        return f"""library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity chip_mod_{sample_id} is
    Port ( clk : in STD_LOGIC;
           rst : in STD_LOGIC;
           din : in STD_LOGIC_VECTOR (7 downto 0);
           trigger : in STD_LOGIC;
           dout : out STD_LOGIC_VECTOR (7 downto 0));
end chip_mod_{sample_id};

architecture Behavioral of chip_mod_{sample_id} is
    signal reg_data : unsigned(7 downto 0);
begin
process(clk, rst)
begin
    if rst = '1' then
        reg_data <= (others => '0');
    elsif rising_edge(clk) then
        reg_data <= unsigned(din) + 1;
    end if;
end process;
dout <= std_logic_vector(reg_data);
end Behavioral;
"""
    return f"""library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity chip_mod_{sample_id} is
    Port ( clk : in STD_LOGIC;
           din : in STD_LOGIC_VECTOR (7 downto 0);
           dout : out STD_LOGIC_VECTOR (7 downto 0));
end chip_mod_{sample_id};

architecture Behavioral of chip_mod_{sample_id} is
begin
process(clk)
begin
    if rising_edge(clk) then
        dout <= std_logic_vector(unsigned(din) + 1);
    end if;
end process;
end Behavioral;
"""


def _c_base(sample_id: str, complex_mode: bool, is_cpp: bool) -> str:
    if complex_mode:
        body = f"""
#include <stdint.h>

static uint8_t auth = 0;

uint8_t process_{sample_id}(uint8_t x, uint8_t key) {{
    uint8_t y = (uint8_t)(x + 1);
    if ((key & 0x03) == 0x02) {{
        y ^= 0xA5;
    }}
    if (auth) {{
        y = (uint8_t)(y - 3);
    }}
    return y;
}}
"""
    else:
        body = f"""
#include <stdint.h>

uint8_t process_{sample_id}(uint8_t x) {{
    return (uint8_t)(x + 1);
}}
"""
    if is_cpp:
        return body + "\nint main() { return 0; }\n"
    return body


def build_base_code(language: str, sample_id: str, complexity: str) -> str:
    complex_mode = complexity == "complex"
    if language == "verilog":
        return _verilog_base(sample_id, complex_mode)
    if language == "vhdl":
        return _vhdl_base(sample_id, complex_mode)
    if language == "c":
        return _c_base(sample_id, complex_mode, is_cpp=False)
    if language == "cpp":
        return _c_base(sample_id, complex_mode, is_cpp=True)
    raise ValueError(f"Unsupported language: {language}")


def inject_backdoor(code: str, language: str, backdoor_type: str) -> str:
    if backdoor_type == "none":
        return code

    if language == "verilog":
        mapping = {
            "logic_tamper": "\n// backdoor\nwire hidden_en = (in_data == 8'hDE);\n",
            "privilege_escalation": "\n// backdoor\nwire bypass_auth = trigger & in_data[0];\n",
            "data_exfiltration": "\n// backdoor\nalways @(posedge clk) if (in_data==8'hFA) out_data <= 8'hCC;\n",
            "instruction_hijack": "\n// backdoor\nalways @(posedge clk) if (in_data==8'h7E) out_data <= 8'hFF;\n",
        }
        return code.replace("endmodule", mapping[backdoor_type] + "\nendmodule")

    if language == "vhdl":
        mapping = {
            "logic_tamper": "\n-- backdoor\n-- hidden state override\n",
            "privilege_escalation": "\n-- backdoor\n-- privilege bypass condition\n",
            "data_exfiltration": "\n-- backdoor\n-- covert data output route\n",
            "instruction_hijack": "\n-- backdoor\n-- control flow redirection marker\n",
        }
        return code + mapping[backdoor_type]

    if language in {"c", "cpp"}:
        mapping = {
            "logic_tamper": "\n/* backdoor */\nif (x == 0xDE) { return 0; }\n",
            "privilege_escalation": "\n/* backdoor */\nif (key == 0x42) { auth = 1; }\n",
            "data_exfiltration": "\n/* backdoor */\nvolatile uint8_t leak = x; (void)leak;\n",
            "instruction_hijack": "\n/* backdoor */\nif (x == 0x7E) { return 0xFF; }\n",
        }
        marker = "return y;"
        if marker in code:
            return code.replace(marker, mapping[backdoor_type] + "\n    return y;")
        return code + mapping[backdoor_type]

    return code
