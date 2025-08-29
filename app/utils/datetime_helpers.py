# -*- coding: utf-8 -*-
from datetime import datetime, timezone

def now_local_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return datetime.now(tz=timezone.utc).astimezone().strftime(fmt)
