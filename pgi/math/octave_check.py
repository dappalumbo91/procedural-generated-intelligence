"""Cross-check closed integer expressions against the local GNU Octave.

Octave evaluates scalars in IEEE doubles. A comparison is kept only
while the integer fits in the exact integer range of that format, 2^53.
Octave division is not a kernel rule. Exact division stays in the kernel.

The binary is taken from PGI_OCTAVE, then octave-cli on PATH, then the
Windows install path used on this project's machine.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

WINDOWS_OCTAVE = Path(
    r"C:\Users\damia\AppData\Local\Programs\GNU Octave\Octave-11.3.0\mingw64\bin\octave-cli.exe"
)
EXACT_FLOAT = 2**53

def octave_cli() -> Path | None:
    env = os.environ.get("PGI_OCTAVE")
    if env:
        path = Path(env)
        if path.exists():
            return path
    found = shutil.which("octave-cli") or shutil.which("octave")
    if found:
        return Path(found)
    if WINDOWS_OCTAVE.exists():
        return WINDOWS_OCTAVE
    return None


def octave_integers(expressions: list[str]) -> list[int]:
    binary = octave_cli()
    if binary is None:
        raise FileNotFoundError("Octave was not found")
    script = "; ".join(f"disp({expression})" for expression in expressions)
    completed = subprocess.run(
        [str(binary), "--quiet", "--norc", "--no-init-file", "--eval", script],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != len(expressions):
        raise RuntimeError(f"Octave returned {lines!r} for {expressions!r}")
    values = []
    for line in lines:
        number = float(line)
        if not number.is_integer() or abs(number) > EXACT_FLOAT:
            raise RuntimeError(f"Octave value {line} is outside exact integer range")
        values.append(int(number))
    return values
