SPLIT_BY_SEVERITY = """
STREAM_NAME = "test"

def split_by_severity(event):
    severity_stream = f"{event['log_level'].lower()}"
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

gb = GearsBuilder('StreamReader')
gb.foreach(lambda x: split_by_severity(x['value']))
gb.register(prefix=STREAM_NAME, trimStream=True)
"""
