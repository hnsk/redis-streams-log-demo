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

         return {
            numMessages,
            generateMessages,
            store
        }
    },
}
</script>
