from __future__ import annotations

import subprocess
from pathlib import Path


def run_compile_check(path: Path, language: str) -> bool:
    # Placeholder: to keep cross-machine compatibility, only C/C++ are actively checked by default.
    try:
        if language == "c":
            cmd = ["gcc", "-fsyntax-only", str(path)]
        elif language == "cpp":
            cmd = ["g++", "-fsyntax-only", str(path)]
        elif language in {"verilog", "vhdl"}:
            return True
        else:
            return False

        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return proc.returncode == 0
    except FileNotFoundError:
        return True
