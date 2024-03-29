#!js name=stream_splitter api_version=1.0

// Helper function to load options
// eg. TFUNCTION LOAD [REPLACE] CONFIG '{"option":"value"}' < stream_splitter.js
function load_option(name, default_value, value_type='string') {
    var value = default_value;
    if (redis.config[name] !== undefined) {
        if (typeof redis.config[name] != value_type) {
            throw stream_name + " must be a " + value_type;
        }
        value = redis.config[name];
    }
    return value;
}

var stream_name = load_option('stream_name', 'test')
var consumer_name = load_option('consumer_name', 'streams_demo');
var log_prefix = load_option('log_prefix', 'logs');

function severity_stream_add(client, payload) {
    client.call(
        'XADD',
        payload['log_level'].toLowerCase(),
        'MAXLEN',
        '~',
        '2000000',
        '*',
        'json',
        JSON.stringify(payload)
    )
}

function severity_increment_counter(client, severity) {
    // increment counters
    var sev_count = client.call(
        'ZINCRBY',
        'severities',
        '1',
        severity.toLowerCase()
    )
    client.call(
        'TS.ADD',
        'ts:' + severity.toLowerCase(),
        '*',
        sev_count.toString(),
        'LABELS',
        'log_level',
        severity.toLowerCase(),
        'type',
        'logs'
    )
}

function add_json_entry(client, stream_id, payload) {
    var date = new Date();
    var beginning_of_today = Date.parse(date.toDateString());
    client.call(
        'JSON.SET',
        log_prefix + ":" + beginning_of_today.toString() + ":" + stream_id,
        '$',
        JSON.stringify(payload)
    )
}

redis.registerStreamTrigger(
    consumer_name, // consumer name
    stream_name, // streams prefix
    function(client, data) {
        // callback to run on each element added to the stream
        var stream_id = `${data['id'][0]}-${data['id'][1]}`;
        var payload = JSON.parse(data['record'][0][1]);
        severity_stream_add(client, payload);
        severity_increment_counter(client, payload['log_level']);
        add_json_entry(client, stream_id, payload);
    },
    {
        isStreamTrimmed: true,
        window: 1
    }
);
