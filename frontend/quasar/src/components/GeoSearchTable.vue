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
                @click="getCityAggregates(markersData[index].city, markersData[index].country_code, index)">
                    <l-popup>
                            <div style="width: 200px">
                                <q-table
                                    :title="`${markersData[index].city} (${markersData[index].country_code})`"
                                    dense
                                    :rows="markersData[index].aggregates"
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
        let center = ref([60.172445, 24.905717])
        const zoomRadius = {
            3: 2500,
            4: 1500,
            5: 700,
            6: 400,
            7: 250
        }
        const url = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        const attribution = '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'

        onMounted(() => {
            updateMarkers("24.905717,60.172445")
            getCircleAggregates()
        })
        
        watch(center, (c) => {
            const coordinates = `${c.lng},${c.lat}`
            updateMarkers(coordinates)
            getCircleAggregates()
        })

        let markers = ref([])
        let markersData = ref([])

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
            })
        }
        
        const aggregate_columns = [
            { name: 'field', field: 'field', label: 'Log Level', align: "left", classes: row => row.field.toLowerCase()},
            { name: 'entries', field: 'entries', label: 'Entries', align: "left"}
        ]

        function getCityAggregates(city, countryCode, index) {
            api.post('api/search/aggregate', {
                query: `@city:{${city}} && @country_code:{${countryCode}}`,
                field: 'log_level'
            })
            .then((response) => {
                let new_aggregates = []
                for (let result of response.data.results) {
                    new_aggregates.push(result)
                }
                markersData.value[index].aggregates.splice(
                    0,
                    markersData.value[index].aggregates.length,
                    ...new_aggregates
                )
            })
        }

        let circleAggregates = ref([])

        function getCircleAggregates() {
            let query = center.value.length == 2 ? center.value.join(" ") : `${center.value.lng} ${center.value.lat}`
            if (center.value.length == 2)
            console.log(center.value.length)
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
            getCityAggregates,
            circleAggregates,
            aggregate_columns,
            zoomRadius
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
</style>