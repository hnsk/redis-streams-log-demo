
<template>
  <q-layout view="hhr lpR fFf">

    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
          <div>
          <q-toolbar-title style="height: 100px">
              <q-img src="redis-logo.svg" class="q-mr-md" style="height: 90px; width: 100px;" />
            Streams / ReJSON&amp;RediSearch Demo
          </q-toolbar-title>
          </div>
          <q-space />
          <RedisStats />
          <MessageGenerator />
      </q-toolbar>


      <q-tabs align="left">
        <q-route-tab to="/" label="Stream Viewer" />
        <q-route-tab to="/search" label="Search Logs" />
        <q-route-tab to="/geosearch" label="Geo search" />
        <q-route-tab to="/generator" label="Generator" />
        <q-route-tab to="/timeseries" label="TimeSeries" />
      </q-tabs>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>

  </q-layout>
</template>

<script>

import MessageGenerator from '../components/MessageGenerator'
import RedisStats from '../components/RedisStats.vue'
import store from '../store'
import { onMounted} from 'vue'

export default {
  components: {
    MessageGenerator,
    RedisStats
  },

  setup() {
    if (!(store.state.client_id)) {
      onMounted(store.dispatch('setClientID'))
    }

    return {
      MessageGenerator,
      RedisStats
    }
  },
}
</script>