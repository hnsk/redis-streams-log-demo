SPLIT_BY_SEVERITY = """
import json
from datetime import datetime
STREAM_NAME = "test"
LOG_PREFIX = "logs"

def split_by_severity(id, payload):
    event = json.loads(payload["json"])
    severity_stream = f"{event['log_level'].lower()}"
    beginning_of_today = datetime.today().date().strftime('%s')
    execute(
        'XADD',
        severity_stream,
        'MAXLEN',
        '~',
        2000000,
        '*',
        'json',
        payload["json"]
    )
    sev_count = execute(
        'ZINCRBY',
        'severities',
        '1',
        severity_stream
    )
    execute(
        'TS.ADD',
        f"ts:{severity_stream}",
        '*',
        sev_count
    )
    execute(
        'JSON.SET',
        f"{LOG_PREFIX}:{beginning_of_today}:{id}",
        '$',
        payload["json"]
    )

gb = GearsBuilder('StreamReader')
gb.foreach(lambda x: split_by_severity(x['id'], x['value']))
gb.register(prefix=STREAM_NAME, trimStream=True)
"""
