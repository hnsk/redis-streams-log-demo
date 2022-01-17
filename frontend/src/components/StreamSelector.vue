<template>
    <div class="q-pa-md q-gutter-lg">
        <div>
            <q-toggle
                v-for="severity of Object.keys(available_streams)"
                v-model="available_streams[severity]"
                :label="severity"
                :key="severity"
                @click="updateSubscribedStreams"
            />
        </div>
    </div>
    <div class="q-pl-md q-gutter-sm">
        <q-btn v-if="show_splitter" color="white" text-color="black" label="Register Stream Splitter" @click="registerStreamSplitter">
            <q-tooltip>Registers a RedisGears function to parse log severities to different streams. Also stores streams to JSON documents for RediSearch indexing.</q-tooltip>
        </q-btn>
    </div>
</template>

<script>

import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { api } from 'boot/axios'
import store from '../store'

export default {
   
    setup() {
        let available_streams = ref({
            test: true
        })
        let show_splitter = ref(true)

        const updateAvailableStreams = () => {
            let api_streams = {}
            api.get(`api/streams/update`)
                .then((response) => {
                    if (Object.keys(available_streams.value).length != Object.keys(response.data).length) {
                        for (const key of Object.keys(response.data)) {
                            api_streams[key] = true
                        }
                        available_streams.value = api_streams
                        if (show_splitter.value) {
                            show_splitter.value = Object.entries(available_streams.value).length > 1 ? false : true
                        }
                        updateSubscribedStreams();
                    }                   
                })
        }

        const updateSubscribedStreams = () => {
            for (const [key, value] of Object.entries(available_streams.value)) {
                const command = value ? 'add' : 'del';
                api.get(`api/streams/${store.state.client_id}/${command}/${key}`)
            }
        }

        const registerStreamSplitter = () => {
            api.get('api/streams/splitter')
                .then(() => {
                    show_splitter.value = false
                })
        }

        let poll_updates = ref(null)
        onMounted(() => {
            updateAvailableStreams()
            poll_updates.value = setInterval(() => {
                updateAvailableStreams()
                }, 1000)
        })

        onBeforeUnmount(() => {
            clearInterval(poll_updates.value)
        })

        return {
            available_streams,
            updateAvailableStreams,
            updateSubscribedStreams,
            registerStreamSplitter,
            show_splitter
        }
    },
}
</script>