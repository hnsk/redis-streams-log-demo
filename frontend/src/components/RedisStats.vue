<template>
    <q-card style="width: 180px" class="q-ma-none">
        <q-card-section>
            <div class="text-subtitle1 text-black">Redis Stats</div>
            <div class="text-caption text-black">Keys: {{ store.state.redis_keys }}</div>
            <div class="text-caption text-black">Used memory: {{ store.state.redis_used_memory }}</div>
        </q-card-section>
    </q-card>
</template>

<script>
import { ref } from 'vue'
import store from '../store'

export default {
    setup() {
         return {
            store
        }
    },
}
</script>
