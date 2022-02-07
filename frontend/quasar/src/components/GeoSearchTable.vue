<template>
    <div>
        <div class="q-ma-lg" style="width: 90%; height: 600px">
            <l-map
            v-model:center="center"
            v-model="zoom"
            v-model:zoom="zoom"
            :minZoom=3
            :maxZoom=7
            worldCopyJump
            ref="logMap"
            >
                <l-control-scale position="topright" :imperial="false" :metric="true" />
                <l-control position="bottomleft">
                    <div style="width: 200px">
                        <q-table
                            title="Circle events"
                            dense
                            :rows="circleAggregates"
                            :columns="aggregate_columns"
                            :hide-pagination="true"
                            row-key="field"
                            flat
                            :pagination="{rowsPerPage: 0}"
                        />
                    </div>
                </l-control>
                <l-circle
                    :lat-lng="center"
                    color="blue"
                    :radius="zoomRadius[zoom]*1000"
                    metric=true
                />
                <l-marker
                v-for="(marker, index) in markers"
                :key="index"
                :lat-lng="marker"
                @click="getCityAggregates(markersData[index].city, markersData[index].country_code)">
                    <l-popup
                        :options="{autoPan: false}"
                    >
                            <div style="width: 200px">
                                <q-table
                                    :title="`${selectedMarkerData.city} (${selectedMarkerData.country_code})`"
                                    dense
                                    :rows="selectedMarkerData.aggregates"
                                    :columns="aggregate_columns"
                                    :hide-pagination="true"
                                    row-key="field"
                                    flat
                                    :pagination="{rowsPerPage: 0}"
                                />
                            </div>
                    </l-popup>
                </l-marker>
                <l-tile-layer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                :attribution="attribution" />
            </l-map>
            <p class="text-h5 q-mt-md">Circle events:</p>
            <q-banner class="bg-grey-9 text-white q-ma-md text-weight-bold codebox">
                {{ circleAggregatesQuery }}
                <q-tooltip>Circle events aggregate query.</q-tooltip>
            </q-banner>
            <p class="text-h5 q-mt-md">Circle markers:</p>
            <q-banner class="bg-grey-9 text-white q-ma-md text-weight-bold codebox">
                {{ markersQuery }}
                <q-tooltip>Circle markers aggregate query.</q-tooltip>
            </q-banner>
        </div>
    </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import { api } from 'boot/axios'
import {
    LMap,
    LTileLayer,
    LMarker,
    LPopup,
    LControlScale,
    LCircle,
    LControl
} from "@vue-leaflet/vue-leaflet"


export default {
    name: "GeoSearchTable",
    components: {
        LMap,
        LTileLayer,
        LMarker,
        LPopup,
        LControlScale,
        LCircle,
        LControl
    },

    setup() {
        let zoom = ref(3)
        let center = ref([48, 23])
        const zoomRadius = {
            3: 2500,
            4: 1500,
            5: 700,
            6: 400,
            7: 250
        }
        const url = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        const attribution = '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        const logMap = ref(null)
        let pollInterval = null

        onMounted(() => {
            updateMarkers("23,48")
            getCircleAggregates()
            pollInterval = setInterval(getCircleAggregates, 1000)
        })
        
        watch(center, (c) => {
            logMap.value.leafletObject.closePopup()
            const coordinates = `${c.lng},${c.lat}`
            updateMarkers(coordinates)
            getCircleAggregates()
        })

        let markers = ref([])
        let markersData = ref([])
        let selectedMarkerData = ref({
            city: '',
            country_code: '',
            aggregates: []
        })

        let markersQuery = ref("")
        function updateMarkers(coordinates) {
            api.post('api/search/aggregate/cities', {
                coordinates: coordinates,
                distance: zoomRadius[zoom.value]
            })
            .then((response) => {
                let results = []
                let resultsData = []
                for (const res of response.data.results) {
                    const [lon, lat] = res.coordinates.split(",")
                    results.push([lat, lon])
                    resultsData.push({
                        city: res.city,
                        entries: res.entries,
                        country_code: res.country_code,
                        aggregates: []
                    })
                }
                markers.value.splice(0, markers.value.length, ...results)
                markersData.value.splice(0, markersData.value.length, ...resultsData)
                markersQuery.value = response.data.literal_query
            })
        }
        
        const aggregate_columns = [
            { name: 'field', field: 'field', label: 'Log Level', align: "left", classes: row => row.field.toLowerCase()},
            { name: 'entries', field: 'entries', label: 'Entries', align: "left"}
        ]

        function getCityAggregates(city, countryCode) {
            selectedMarkerData.value.city = city
            selectedMarkerData.value.country_code = countryCode
            api.post('api/search/aggregate', {
                query: `@city:{${city}} && @country_code:{${countryCode}}`,
                field: 'log_level'
            })
            .then((response) => {
                let new_aggregates = []
                for (let result of response.data.results) {
                    new_aggregates.push(result)
                }
                selectedMarkerData.value.aggregates.splice(
                    0,
                    selectedMarkerData.value.aggregates.length,
                    ...new_aggregates
                )
            })
        }

        let circleAggregates = ref([])
        let circleAggregatesQuery = ref("")

        function getCircleAggregates() {
            let query = null
            if ('lng' in center.value) {
                query = `${center.value.lng} ${center.value.lat}`
            }
            else {
                query = `${center.value[1]} ${center.value[0]}`
            }
            api.post('api/search/aggregate', {
                query: `@coordinates:[${query} ${zoomRadius[zoom.value]} km]`,
                field: 'log_level'
            })
            .then((response) => {
                let new_aggregates = []
                for (let result of response.data.results) {
                    new_aggregates.push(result)
                }
                circleAggregates.value.splice(
                    0,
                    circleAggregates.value.length,
                    ...new_aggregates
                )
                circleAggregatesQuery.value = response.data.literal_query
            })
        }

        return {
            LMap,
            LTileLayer,
            LMarker,
            LPopup,
            LControlScale,
            LCircle,
            LControl,
            zoom,
            center,
            url,
            attribution,
            markers,
            markersData,
            markersQuery,
            getCityAggregates,
            circleAggregates,
            circleAggregatesQuery,
            aggregate_columns,
            zoomRadius,
            selectedMarkerData,
            logMap
        }
    },
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