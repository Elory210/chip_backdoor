from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import yaml
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.desktop_app.reporting import export_excel, export_txt
from src.inference.predictor import BackdoorPredictor, PredictResult, detect_language


TARGET_EXT = {".v", ".vhd", ".vhdl", ".c", ".cc", ".cpp", ".cxx"}


class MainWindow(QMainWindow):
    def __init__(self, app_config_path: str = "configs/app_config.yaml") -> None:
        super().__init__()
        cfg = yaml.safe_load(Path(app_config_path).read_text(encoding="utf-8"))
        self.predictor = BackdoorPredictor(cfg["model_dir"])
        self.report_dir = Path(cfg["report_dir"])
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.files: List[str] = []
        self.results: List[PredictResult] = []

        self.setWindowTitle("Chip Backdoor Detection Studio")
        self.resize(1200, 760)

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)

        btn_row = QHBoxLayout()
        self.btn_file = QPushButton("选择文件")
        self.btn_dir = QPushButton("选择文件夹")
        self.btn_run = QPushButton("开始检测")
        self.btn_export_txt = QPushButton("导出TXT")
        self.btn_export_excel = QPushButton("导出Excel")

        btn_row.addWidget(self.btn_file)
        btn_row.addWidget(self.btn_dir)
        btn_row.addWidget(self.btn_run)
        btn_row.addWidget(self.btn_export_txt)
        btn_row.addWidget(self.btn_export_excel)

        stats_row = QHBoxLayout()
        self.lbl_total = QLabel("总数: 0")
        self.lbl_bad = QLabel("有后门: 0")
        self.lbl_clean = QLabel("无后门: 0")
        stats_row.addWidget(self.lbl_total)
        stats_row.addWidget(self.lbl_bad)
        stats_row.addWidget(self.lbl_clean)

        content = QGridLayout()
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["文件", "语言", "后门", "置信度", "类型", "风险"])
        self.code_view = QTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.code_view.setFont(QFont("Consolas", 10))
        content.addWidget(self.table, 0, 0)
        content.addWidget(self.code_view, 0, 1)

        main_layout.addLayout(btn_row)
        main_layout.addLayout(stats_row)
        main_layout.addLayout(content)

        self.btn_file.clicked.connect(self.pick_files)
        self.btn_dir.clicked.connect(self.pick_folder)
        self.btn_run.clicked.connect(self.run_detect)
        self.btn_export_txt.clicked.connect(self.do_export_txt)
        self.btn_export_excel.clicked.connect(self.do_export_excel)
        self.table.cellClicked.connect(self.show_code)

    def pick_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "选择代码文件", "", "Code Files (*.v *.vhd *.vhdl *.c *.cc *.cpp *.cxx)")
        self.files = files
        self.statusBar().showMessage(f"已选择 {len(self.files)} 个文件")

    def pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder:
            return
        self.files = [str(p) for p in Path(folder).rglob("*") if p.suffix.lower() in TARGET_EXT]
        self.statusBar().showMessage(f"已扫描 {len(self.files)} 个目标文件")

    def run_detect(self) -> None:
        if not self.files:
            QMessageBox.warning(self, "提示", "请先选择文件或文件夹")
            return

        self.results = self.predictor.predict_batch(self.files)
        self.table.setRowCount(len(self.results))

        bad = 0
        for i, r in enumerate(self.results):
            lang = detect_language(Path(r.file_path))
            if r.has_backdoor:
                bad += 1
            values = [
                Path(r.file_path).name,
                lang,
                "是" if r.has_backdoor else "否",
                f"{r.confidence:.4f}",
                r.backdoor_type,
                r.risk_level,
            ]
            for j, v in enumerate(values):
                item = QTableWidgetItem(v)
                if j == 2 and r.has_backdoor:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, j, item)

        self.lbl_total.setText(f"总数: {len(self.results)}")
        self.lbl_bad.setText(f"有后门: {bad}")
        self.lbl_clean.setText(f"无后门: {len(self.results) - bad}")
        self.statusBar().showMessage("检测完成")
        if self.results:
            self.table.selectRow(0)
            self.show_code(0, 0)

    def show_code(self, row: int, _: int) -> None:
        if row >= len(self.results):
            return
        result = self.results[row]
        code = Path(result.file_path).read_text(encoding="utf-8", errors="ignore")
        lines = code.splitlines()
        rendered = "\n".join(f"{i:04d}  {line}" for i, line in enumerate(lines, start=1))
        self.code_view.setPlainText(rendered)

        extra = []
        danger = set(result.suspicious_lines)
        for line_no in danger:
            if line_no < 1 or line_no > len(lines):
                continue
            cursor = self.code_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_no - 1)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("red"))
            fmt.setBackground(QColor(255, 235, 235))
            selection.format = fmt
            extra.append(selection)

        self.code_view.setExtraSelections(extra)

    def do_export_txt(self) -> None:
        if not self.results:
            QMessageBox.warning(self, "提示", "暂无检测结果")
            return
        out = self.report_dir / "detection_report.txt"
        export_txt(self.results, out)
        QMessageBox.information(self, "完成", f"已导出: {out}")

    def do_export_excel(self) -> None:
        if not self.results:
            QMessageBox.warning(self, "提示", "暂无检测结果")
            return
        out = self.report_dir / "detection_report.xlsx"
        export_excel(self.results, out)
        QMessageBox.information(self, "完成", f"已导出: {out}")


def main() -> None:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
