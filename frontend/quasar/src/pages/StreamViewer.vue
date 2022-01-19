<template>
    <StreamSelector />
    <StreamTable />
</template>

<script>

import StreamSelector from '../components/StreamSelector.vue'
import StreamTable from '../components/StreamTable.vue'

export default {
    components: {
        StreamSelector,
        StreamTable
    },

    setup() {
        return {
            StreamSelector,
            StreamTable
        }
    },
}
</script>