from pathlib import Path

from src.dataset_gen.generator import run_build


def test_build_dataset_smoke(tmp_path: Path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        """
seed: 1
output_root: {}
sample_count: 20
backdoor_ratio: 0.5
split:
  train: 0.8
  valid: 0.1
  test: 0.1
languages: [verilog, vhdl, c, cpp]
complexity_levels: [simple, complex]
scenarios: [fpga, asic, mcu, embedded]
backdoor_types: [none, logic_tamper, privilege_escalation, data_exfiltration, instruction_hijack]
stealth_levels:
  none: none
  logic_tamper: high
  privilege_escalation: medium
  data_exfiltration: medium
  instruction_hijack: high
compiler_check: false
""".format((tmp_path / "out").as_posix()),
        encoding="utf-8",
    )

    paths = run_build(str(cfg))
    assert paths.index_file.exists()
    assert paths.labels_file.exists()
