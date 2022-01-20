<template>
    <div>
        <div class="q-gutter-md q-pa-md">
            <div class="col-4">
                <q-select
                    use-input
                    fill-input
                    hide-dropdown-icon
                    hide-selected
                    :model-value="search_string"
                    :options="searchOptions"
                    transition-duration=0
                    input-debounce=0
                    @input-value="(value) => search_string = value"
                    @filter="getAutocompleteOptions"
                    label="Search logs"
                    style="width: 50%">
                    <template v-slot:after>
                        <q-btn round dense flat icon="clear" color="primary" @click="search_string = '*'" />
                    </template>
                </q-select>
            </div>
        </div>
        <div class="row q-pa-md">
            <div class="col-3">
                <q-table
                    title="Aggregates"
                    dense
                    :rows="aggregates"
                    :columns="aggregate_columns"
                    :hide-pagination="true"
                    row-key="field"
                    :pagination="{rowsPerPage: 0}"
                />
            </div>
            <div class="col-7">
                <q-banner class="bg-grey-9 text-white q-ma-md text-weight-bold codebox">
                    {{ literal_aggregate_query }}
                    <q-tooltip>Literal aggregate query</q-tooltip>
                </q-banner>
                <q-banner class="bg-grey-9 text-white q-ma-md text-weight-bold codebox">
                    {{ literal_search_query }}
                    <q-tooltip>Literal search query</q-tooltip>
                </q-banner>
            </div>
        </div>
        <div class="q-pa-md">
            <q-table
                :title="`Results in ${search_duration}ms`"
                dense
                :rows="messages"
                :columns="search_columns"
                row-key="id"
                v-model:pagination="pagination"
                binary-state-sort
                @request="paginationRequest"
                virtual-scroll
                class="fit"
            >
            <template v-slot:body-cell="props">
                <q-td :props="props">
                <div v-if="props.col.name == 'log_level'">
                    <q-select
                        v-model="messages[props.pageIndex].log_level"
                        dense
                        outlined
                        :bg-color="levelColors[props.value.toLowerCase()].bg"
                        :options="logLevels"
                        hide-dropdown-icon
                        transition-duration=0
                        @update:model-value="updateLogKey(props.key, props.col.name, messages[props.pageIndex].log_level)"
                    />

                </div>
                <div v-else-if="props.col.name == 'message'">
                    <div style="font-family: monospace"><span v-html="props.value" /></div>
                    <q-popup-edit
                        v-model="messages[props.pageIndex].message"
                        auto-save
                        v-slot="scope"
                        @before-hide="updateLogKey(props.key, props.col.name, messages[props.pageIndex].message)"
                    >
                        <q-input
                            v-model="scope.value"
                            dense
                            autofocus
                            @keyup.enter="scope.set() ; updateLogKey(props.key, props.col.name, scope.value);"
                        />
                    </q-popup-edit>
                </div>
                <div v-else-if="props.col.name == 'hostname'">
                    <span v-html="props.value" />
                    <q-popup-edit
                        v-model="messages[props.pageIndex].hostname"
                        auto-save
                        v-slot="scope"
                        @before-hide="updateLogKey(props.key, props.col.name, messages[props.pageIndex].hostname)"
                    >
                        <q-input
                        v-model="scope.value"
                        dense
                        autofocus
                        @keyup.enter="scope.set() ; updateLogKey(props.key, props.col.name, scope.value);"
                    />
                    </q-popup-edit>
                </div>
                <div
                  v-else-if="props.col.name == 'timestamp'"
                  @click="addTimestampToQuery(props.row.timestamp)"
                >
                    {{ props.value }}
                    <q-btn :icon="time_range_selector ? 'arrow_right' : 'arrow_left'" flat>
                        <q-tooltip>{{ time_range_selector ? 'Select beginning of range' : 'Select end of range' }}</q-tooltip>
                    </q-btn>
                    </div>
                </q-td>
            </template>
            </q-table>
        </div>
    </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { api } from 'boot/axios'
import { date } from 'quasar'
import store from '../store'

export default {
    setup() {
        function getLogLevelClass(val) {
            return val.toLowerCase()
        }

        let messages = ref([])
        let aggregates = ref([])
        let num_results = ref(0)
        let total_results = ref(0)
        let search_duration = ref(0)
        let literal_search_query = ref("")
        let literal_aggregate_query = ref("")
        
        let searchParams = ref({
            showSearch: true
        })

        let pagination = ref({
            rowsPerPage: 25,
            page: 1,
            rowsNumber: 0,
            sortBy: 'timestamp',
            descending: true
        })

        const levelColors = {
            debug: {
                bg: "blue-2",
                fg: "grey-10"
            },
            info: {
                bg: "info",
                fg: "grey-10"
            },
            warning: {
                bg: "warning",
                fg: "grey-10"
            },
            error: {
                bg: "red-6",
                fg: "grey-1"
            },
            critical: {
                bg: "red-10",
                fg: "grey-1"
            }
        }

        const logLevels = [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL"
        ]

        const example_queries = [
            '*',
            'hello',
            '%hllo%',
            'hel*',
            '@hostname:123',
            '@log_level:{warning}',
            '%hllo% @hostname:123 @log_level:{warning|debug}'
        ]

        const search_columns = [
            {
                name: 'timestamp',
                field: 'timestamp',
                label: 'Timestamp',
                align: "left",
                format: (val) => date.formatDate(parseInt(val), 'YYYY-MM-DD HH:mm:ss.SSS'),
                sortable: true
            },
            {
                name: 'hostname',
                field: 'hostname',
                label: 'Hostname',
                align: "left",
                sortable: true
            },
            {
                name: 'log_level',
                field: 'log_level',
                label: 'Log Level',
                align: "center",
                sortable: true
            },
            {
                name: 'message',
                field: 'message',
                label: 'Message',
                style: "width: 100%",
                align: "left"
            }
        ]

        const aggregate_columns = [
            { name: 'field', field: 'field', label: 'Field', align: "left", classes: row => getLogLevelClass(row.field)},
            { name: 'entries', field: 'entries', label: 'Entries', align: "left"}
        ]

        let search_string = ref('*')

        watch(search_string, (str) => {
            pagination.value.page = 1
            searchLogs(str, 0, pagination.value.rowsPerPage, pagination.value.sortBy, !pagination.value.descending)
        })

        function aggregateLogs(query) {
            api.post('api/search/aggregate', {
                query: query,
                field: 'log_level'
            })
            .then((response) => {
                let new_aggregates = []
                literal_aggregate_query.value = response.data.literal_query
                for (let result of response.data.results) {
                    new_aggregates.push(result)
                }
                aggregates.value.splice(0, aggregates.value.length, ...new_aggregates)
            })
        }

        function paginationRequest(props) {
            const { page, rowsPerPage, descending, sortBy } = props.pagination
            const start = (page - 1) * rowsPerPage
            searchLogs(search_string.value, start, rowsPerPage, sortBy, !descending)
            pagination.value.rowsPerPage = rowsPerPage
            pagination.value.page = page
            pagination.value.descending = descending
            pagination.value.sortBy = sortBy
        }

        function searchLogs(query, start, limit, sortby, sort_asc) {
            search_string.value = query.length > 2 ? query : '*'
            api.post('api/search', {
                'query': search_string.value,
                'start': start,
                'limit': limit,
                'sortby': sortby,
                'sort_asc': sort_asc
                })
                .then((response) => {
                    if (response.data.error) {
                        literal_search_query.value = response.data.error
                    }
                    else {
                        messages.value.splice(0, messages.value.length, ...response.data.messages)
                        num_results.value = response.data.numresults
                        total_results.value = response.data.total
                        literal_search_query.value = response.data.literal_query
                        search_duration.value = response.data.duration
                        pagination.value.rowsNumber = response.data.total
                        aggregateLogs(search_string.value)
                    }
                })
        }

        function updateLogKey(key, field, value) {
            api.post('api/log/message/modify', {
                key: key,
                field: field,
                value: value
            })
        }

        let searchOptions = ref(["moi"])
        function getAutocompleteOptions(prefix, update, abort) {
            let input = []
            update(() => {
                input = prefix.split(" ")
                const searchStr = input[input.length - 1]
                api.post("api/search/suggestion/get", {
                    index: 'autocomplete',
                    prefix: searchStr
                })
                .then((response) => {
                    let options = []
                    input.pop()
                    for (let sug of response.data) {
                        options.push(`${input.join(" ").trim()} ${sug}`)
                    }
                    console.log
                    searchOptions.value = options
                })
            })
        }

        let time_range = ref([])
        let time_range_selector = ref(true)
        function addTimestampToQuery(timestamp) {
            if (time_range.value.length < 2) {
                time_range.value.push(timestamp)
                time_range_selector.value = false
                if (time_range.value.length == 2) {
                    time_range_selector.value = true
                    if (search_string.value == '*') {
                        search_string.value =`@timestamp:[${time_range.value.join(" ")}]`
                    }
                    else {
                        search_string.value = `${search_string.value} @timestamp:[${time_range.value.join(" ")}]`
                    }
                }
            }
            else {
                time_range.value = [timestamp]
            }
            console.log(time_range.value)
            console.log(search_string.value)
        }

        onMounted(() => {
            searchLogs(
                search_string.value,
                (pagination.value.page - 1) * pagination.value.rowsPerPage,
                pagination.value.rowsPerPage,
                pagination.value.sortBy,
                !pagination.value.descending)
        })

        return {
            search_columns,
            aggregate_columns,
            aggregates,
            messages,
            store,
            search_string,
            search_duration,
            num_results,
            total_results,
            literal_search_query,
            literal_aggregate_query,
            example_queries,
            levelColors,
            updateLogKey,
            logLevels,
            searchParams,
            searchOptions,
            getAutocompleteOptions,
            addTimestampToQuery,
            time_range_selector,
            paginationRequest,
            pagination
        }   
    }
}
</script>

<style lang="scss">
td.debug {
    background-color: $blue-2;
}
td.info {
    background-color: $info;
}
td.warning {
    background-color: $warning;
}
td.error {
    background-color: $red-6;
    color: seashell;
}
td.critical {
    background-color: $red-10;
    color: seashell;
}

.codebox {
    font-family: Courier, sans-serif;
    font-size: 12px;
    margin-bottom: 10px;
    margin-top: 10px;
    -webkit-border-radius: 0px 0px 6px 6px;
    -moz-border-radius: 0px 0px 6px 6px;
    border-radius: 6px 6px 6px 6px;
}
</style>