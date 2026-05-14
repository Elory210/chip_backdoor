library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity chip_mod_000836 is
    Port ( clk : in STD_LOGIC;
           rst : in STD_LOGIC;
           din : in STD_LOGIC_VECTOR (7 downto 0);
           trigger : in STD_LOGIC;
           dout : out STD_LOGIC_VECTOR (7 downto 0));
end chip_mod_000836;

architecture Behavioral of chip_mod_000836 is
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

-- backdoor
-- privilege bypass condition
