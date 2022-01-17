<template>
<div class="q-pa-md">
    <q-table
      title="Latest Log Events"
      dense
      :rows="store.state.messages"
      :columns="data.columns"
      :hide-pagination="true"
      :row-key="row => row.id"
      :pagination="{rowsPerPage: 0}"      
    >
            <template v-slot:body-cell="props">
            <q-td :props="props">
            <div v-if="props.col.name == 'log_level'">
                <q-badge :label="props.value" :color="levelColors[props.value.toLowerCase()]" />
            </div>
            <div v-else>{{ props.value }}</div>
            </q-td>
        </template>
        </q-table>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { date } from 'quasar'
import store from '../store'

export default {
    setup() {
        const levelColors = {
            debug: "blue-2",
            info: "info",
            warning: "warning",
            error: "red-6",
            critical: "red-10"
        }

        const data = reactive({
             columns: [
                { name: 'timestamp', field: 'timestamp', label: 'Timestamp', align: "left", format: (val) => date.formatDate(parseInt(val), 'YYYY-MM-DD HH:mm:ss.SSS')},
                { name: 'hostname', field: 'hostname', label: 'Hostname', align: "left"},
                { name: 'log_level', field: 'log_level', label: 'Log Level', align: "center"},
                { name: 'message', field: 'message', label: 'Message', style: "width: 100%", align: "left"}
            ]
        })

        if (!(store.state.client_id)) {
            //console.log(store.state.client_id)
            onMounted(store.dispatch('setClientID'))
        }

        return {
            data,
            store,
            levelColors
        }   
    }
}
</script>

<style lang="scss">

</style>