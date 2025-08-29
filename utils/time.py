from datetime import datetime
import pytz
from config import TIMEZONE

def fmt_ts_iso(iso_str: str) -> str:
    try:
        utc = datetime.fromisoformat(iso_str.replace('Z',''))
        tz = pytz.timezone(TIMEZONE)
        local_dt = pytz.utc.localize(utc).astimezone(tz)
        return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception:
        return iso_str
