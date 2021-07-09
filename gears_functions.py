SPLIT_BY_SEVERITY = """
from datetime import datetime
STREAM_NAME = "test"

def split_by_severity(id, event):
    severity_stream = f"{event['log_level'].lower()}"
    beginning_of_today = datetime.today().date().strftime('%s')
    execute(
        'XADD',
        severity_stream,
        'MAXLEN',
        '~',
        2000000,
        '*',
        'timestamp',
        event['timestamp'],
        'hostname',
        event['hostname'],
        'log_level',
        event['log_level'],
        'message',
        event['message']
    )
    execute(
        'ZINCRBY',
        'severities',
        '1',
        severity_stream
    )
    execute(
        'HSET',
        f"logs:{beginning_of_today}:{id}",
        'timestamp',
        event['timestamp'],
        'hostname',
        event['hostname'],
        'log_level',
        event['log_level'],
        'message',
        event['message']
    )

gb = GearsBuilder('StreamReader')
gb.foreach(lambda x: split_by_severity(x['id'], x['value']))
gb.register(prefix=STREAM_NAME, trimStream=True)
"""
