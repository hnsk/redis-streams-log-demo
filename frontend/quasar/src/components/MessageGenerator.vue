<template>
        <div class="q-pa-md q-gutter-sm">
            <div class="row">
                <div>
                    <q-chip square color="deep-orange" text-color="white" style="width: 200px">
                        Received messages: {{ store.state.message_counter }}
                    </q-chip>
                </div>
                <div>
                    <q-btn color="white" round dense flat icon="restart_alt" @click="store.commit('resetMessageCounter')">
                      <q-tooltip>Reset message counter</q-tooltip>
                    </q-btn>
                </div>
            </div>
            <q-input filled v-model="numMessages" dense class="bg-white" @keyup.enter="generateMessages" label="Generate Messages" >
                <template v-slot:after>
                    <q-btn round dense flat icon="send" color="primary" @click="generateMessages" />
                    <q-btn round dense flat icon="add" color="primary" @click="enableGenerator">
                        <q-tooltip>Start auto generator.</q-tooltip>
                    </q-btn>
                    <q-btn round dense flat icon="cancel" color="primary" @click="disableGenerator">
                        <q-tooltip>Stop generators.</q-tooltip>
                    </q-btn>
                </template>
            </q-input>
        </div>
</template>

<script>
import { ref } from 'vue'
import store from '../store'

import { api } from 'boot/axios'

export default {
    setup() {
        let numMessages = ref(100)
        function generateMessages() {
            api.get(`api/generator/generate/${numMessages.value}`)
         }

        function enableGenerator() {
            api.get('api/generator/enable')
        }

        function disableGenerator() {
            api.get('api/generator/disable')
        }

         return {
            numMessages,
            generateMessages,
            enableGenerator,
            disableGenerator,
            store
        }
    },
}
</script>
