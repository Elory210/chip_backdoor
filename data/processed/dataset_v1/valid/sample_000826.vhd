library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity chip_mod_000826 is
    Port ( clk : in STD_LOGIC;
           din : in STD_LOGIC_VECTOR (7 downto 0);
           dout : out STD_LOGIC_VECTOR (7 downto 0));
end chip_mod_000826;

architecture Behavioral of chip_mod_000826 is
begin
process(clk)
begin
    if rising_edge(clk) then
        dout <= std_logic_vector(unsigned(din) + 1);
    end if;
end process;
end Behavioral;

-- backdoor
-- hidden state override
