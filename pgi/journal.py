from __future__ import annotations

import json
from pathlib import Path

from pgi.model import Session


def append_journal(path: Path, session: Session) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(session.as_dict(), ensure_ascii=True, sort_keys=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
