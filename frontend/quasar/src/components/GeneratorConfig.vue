<template>
    <div>
        <q-dialog v-model="editConfig">
        <q-card>
            <q-card-section>
            <div class="text-h6">Current generator configuration</div>
            </q-card-section>
            <q-separator />
            <q-card-section>
            <div>
                <q-input
                v-model="configText"
                filled
                type="textarea"
                rows=50
                style="width: 500px"
                color="grey-4"
                />
            </div>
            </q-card-section>
            <q-separator />
            <q-card-actions align="right">
            <q-btn flat label="Close" color="primary" v-close-popup />
            <q-btn flat label="Save" color="primary" @click="textConfigToConfig" v-close-popup />
            </q-card-actions>
        </q-card>
        </q-dialog>

        <div class="q-ma-sm">
            <q-btn @click="getCurrentConfig" label="Reload config" />
            <q-btn @click="logCurrentConfig" label="Log config" />
            <q-btn @click="saveCurrentConfig" label="Save config" />
            <q-btn @click="editConfig = true" label="Edit config" />
            <q-btn @click="addHost" label="Add host" />
        </div>
        <q-separator />
        <q-list>
            <q-item v-for="(host, index) in generator_config" style="border-style: solid none none none" :key="index" >
                <q-btn round dense flat size="30px" icon="delete" color="primary" @click="generator_config.splice(index, 1)" />
                <q-input
                    label="Description"
                    v-model="generator_config[index].name"
                    dense
                    style="width: 150px" />
                <q-list>
                    <q-item v-for="option of Object.keys(host.options)" :key="option">
                            <div class="row">
                                <div>
                                    <q-chip square size="md" style="width: 100px">{{option}}</q-chip></div>
                                <div>
                                    <q-checkbox 
                                        v-if="typeof(generator_config[index].options[option]) == 'boolean'" v-model="generator_config[index].options[option]"
                                        class="q-ml-md"
                                    />
                                    <q-input
                                        v-else 
                                        v-model="generator_config[index].options[option]"
                                        :label="option"
                                        dense
                                        class="q-ml-md"
                                        style="width: 300px" />
                                </div>
                            </div>
                    </q-item>
                    <q-item>
                        <q-chip square size="md" bold style="width: 100px">messages</q-chip>
                        <q-list>
                            <q-item v-for="(message, msgIndex) in host.messages" :key="msgIndex">
                                <q-input
                                    v-model="generator_config[index].messages[msgIndex]"
                                    dense
                                    @keyup.enter="changeMessage(index, msgIndex)"
                                    style="width: 300px" />
                            
                                <q-btn round dense flat icon="delete" color="primary" @click="deleteMessage(index, msgIndex)" />
                            </q-item>
                            <q-item>
                                <q-btn label="Add new message" @click="addMessage(index, 'New message')" />
                            </q-item>
                        </q-list>
                    </q-item>
                </q-list>
            </q-item>
        </q-list>
    </div>
</template>

<script>

import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'

export default {
    setup() {
        let generator_config = ref([])
        let editConfig = ref(false)
        let configText = ref("")

        const newHostTemplate = {
            name: "New",
            options: {
                hostname: "newserver-RANDINT.example.com",
                enabled: false,
                amount: 100
            },
            messages: [
                "Example message."
            ]
        }

        function logCurrentConfig() {
            console.log(generator_config.value)
        }

        function textConfigToConfig() {
            generator_config.value = JSON.parse(configText.value)
            saveCurrentConfig()
            
        }

        function addHost() {
            console.log(newHostTemplate)
            api.post("api/generator/host/add", newHostTemplate)
            .then(getCurrentConfig)
        }

        function addMessage(hostIdx, message) {
            api.post(`api/generator/message/add`, {
                hostidx: hostIdx,
                message: message})
            .then(getCurrentConfig())
        }

        function deleteMessage(hostIdx, msgIdx) {
            api.post(`api/generator/message/delete`, {
                hostidx: hostIdx,
                msgidx: msgIdx})
            .then(getCurrentConfig())
        }

        function changeMessage(hostIdx, msgIdx) {
            const message = generator_config.value[hostIdx].messages[msgIdx]
            api.post(`api/generator/message/modify`, {
                hostidx: hostIdx,
                msgidx: msgIdx,
                message: message})
            .then(getCurrentConfig())
        }

        function saveCurrentConfig() {
            api.post("api/generator/config/update", {
                config: generator_config.value
            })
            .then(getCurrentConfig)
        }

        function getCurrentConfig() {
            api.get('api/generator/config')
            .then((response) => {
                generator_config.value = response.data.config.hosts
                configText.value = JSON.stringify(generator_config.value, null, 2)
            })
        }

        onMounted(() => {
            getCurrentConfig()
        })

        return {
            generator_config,
            getCurrentConfig,
            logCurrentConfig,
            saveCurrentConfig,
            editConfig,
            configText,
            textConfigToConfig,
            addHost,
            addMessage,
            deleteMessage,
            changeMessage
        }
    },
}
</script>