<template>
    <div class="row">
        <div v-for="level of Object.keys(logLevels)" :key="level">
            <apexchart
                class="q-ma-md"
                :ref="el => { if (el) chartRefs[level] = el}"
                width="600px"
                height="300px"
                :options="getChartOptions(level)"
                :series="series" />
        </div>
    </div>
</template>

<script>

import { ref, onMounted, onBeforeUnmount } from 'vue'
import { api } from 'boot/axios'
import { colors } from 'quasar'

export default {
    setup() {
        let series = ref([])
        let chartRefs = ref({})

        const logLevels = {
            debug: 'blue-2',
            info: 'info',
            warning: 'warning',
            error: 'red-6',
            critical: 'red-10'
        }

        const options = {
            xaxis: {
                type: 'datetime'
            },
            fill: {
                type: 'gradient'
            },
            chart: {
                type: 'area',
                toolbar: {
                    show: false
                },
                animations: {
                    enabled: false,
                    easing: 'linear'
                },
                zoom: {
                    enabled: false
                }
            },
            stroke: {
                curve: 'smooth',
                width: 1
            },
            markers: {
                size: 0
            },
            dataLabels: {
                enabled: false
            }
        }

        function getChartOptions(name) {
            let chartOptions = {...options}
            chartOptions.chart.group = 'logcharts'
            chartOptions.chart.id = name
            chartOptions.colors = [colors.getPaletteColor(logLevels[name])]
            chartOptions.title = {
                text: name,
                align: 'center',
                margin: 10,
                style: {
                    fontSize:  '14px',
                    fontWeight:  'bold',
                    fontFamily:  undefined,
                    color:  '#263238'
                }
            }
            return chartOptions
        }

        function updateTimeseries() {
            const d = new Date()
            api.post('api/timeseries/mrange', {
                bucket_size_msec: 1000,
                from_time: d.getTime() - 60000,
                to_time: d.getTime(),
                aggregation_type: 'count',
                filters: ["type=logs"]
            })
            .then((response) => {
                for (let item of response.data) {
                    chartRefs.value[item.name].updateOptions({
                        xaxis: {
                            min: d.getTime() - 60000,
                            max: d.getTime()
                        }
                    })
                    chartRefs.value[item.name].updateSeries([item])
                }
            })
        }

        let pollInterval = ref(null)
        onMounted(() => {
            pollInterval.value = setInterval(updateTimeseries, 1000)
        })

        onBeforeUnmount(() => {
            clearInterval(pollInterval.value)
        })

        return {
            series,
            getChartOptions,
            logLevels,
            chartRefs,
            updateTimeseries,
        }
    },
}

</script>
