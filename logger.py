import logging
from datetime import datetime

class AlignedFormatter(logging.Formatter):
    def format(self, record):
        created_dt = datetime.fromtimestamp(record.created)
        time = created_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        level_raw = f"[{record.levelname.lower()}]"
        level = f"{level_raw:<8}"

        location = f"{record.filename}:{record.lineno:<4}"
        location = f"{location:<18}"

        msg = record.getMessage()
        return f"[{time}]   {level}{location}  {msg}".rstrip()

class PrefixAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[{self.extra['prefix']}] {msg}", kwargs

handler = logging.StreamHandler()
handler.setFormatter(AlignedFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])

api_logger = PrefixAdapter(logging.getLogger("api"), {"prefix": "API"})
