
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
          <MessageGenerator />
      </q-toolbar>


      <q-tabs align="left">
        <q-route-tab to="/" label="Stream Viewer" />
        <q-route-tab to="/search" label="Search Logs" />
        <q-route-tab to="/generator" label="Generator" />
      </q-tabs>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>

  </q-layout>
</template>

<script>

import MessageGenerator from '../components/MessageGenerator'

export default {
  components: {
    MessageGenerator
  },

  setup() {
    return {
      MessageGenerator,
    }
  },
}
</script>