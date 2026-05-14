# chip_backdoor
查询芯片代码是否有后门

本项目实现了一个完整的三模块流水线：

模块1：多语言芯片代码数据集生成（Verilog/VHDL/C/C++）

模块2：基于PyTorch和Transformers的代码大语言模型微调

模块3：基于PyQt6的Windows桌面检测器

1. 项目结构
backdoor-detection-chip/
  configs/
  data/
  models/
  reports/
  scripts/
  src/
    dataset_gen/
    training/
    inference/
    desktop_app/
  tests/
  requirements.txt
  README.md

2. 快速开始
安装依赖
pip install -r requirements.txt
构建数据集
python scripts/build_dataset.py --config configs/dataset_config.yaml
训练模型
python scripts/train_model.py --config configs/train_config.yaml
运行推理
python scripts/run_inference.py --model-dir models/codebert_chip_backdoor --file tests/samples/demo_bad.c
启动桌面应用
python scripts/run_desktop_app.py

标签模式
language: verilog|vhdl|c|cpp

backdoor_type: none|logic_tamper|privilege_escalation|data_exfiltration|instruction_hijack

stealth_level: none|medium|high

complexity: simple|complex

scenario: fpga|asic|mcu|embedded

has_backdoor: 0|1

说明
默认配置使用快速验证集大小（1000个样本）。

如需大规模数据生成，请增加 configs/dataset_config.yaml 中的 sample_count 参数。

Verilog/VHDL 编译检查默认禁用，可结合本地工具链集成。

当前输出使用可疑行启发式定位；后续可添加令牌级定位功能。
