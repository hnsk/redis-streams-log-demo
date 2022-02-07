import { createStore } from 'vuex'
import { api } from 'boot/axios'

export default createStore({
    state: {
      message_counter: 0,
      client_id: null,
      stream_websocket: null,
      message_keys: {},
      messages: [],
      redis_keys: 0,
      redis_used_memory: 0
    },
    getters: {
      getMessageCounter(state) {
        return state.message_counter
      }
    },
    mutations: {
      increaseMessageCounter(state) {
        state.message_counter++
      },
      resetMessageCounter(state) {
        state.message_counter = 0
      },
      addMessage(state, message) {
        for (const key of Object.keys(message)) {
          if (!(key in state.message_keys)) {
              state.message_keys[key] = key
          }
        }
        state.messages.unshift(message);
        state.message_counter++;
        if (state.messages.length > 25) {
            state.messages.pop()
        }
      },
      resetMessages(state) {
        state.messages = []
      },
      setClientID(state, id) {
        state.client_id = id
      },
      setStreamWebSocket(state, websocket) {
        if (state.stream_websocket) {
          state.stream_websocket.close()
        }
        state.stream_websocket = websocket
      },
      setRedisKeys(state, keys) {
        state.redis_keys = keys
      },
      setRedisUsedMemory(state, used_memory) {
        state.redis_used_memory = used_memory
      }
    },
    actions: {
      setClientID({dispatch, commit}) {
        api.get('api/clientid')
          .then((response) => {
            commit('setClientID', response.data.client_id)
            dispatch('checkStreamWebSocket', response.data.client_id )
          })
      },
      setRedisStats({commit}, info) {
        commit('setRedisKeys', info.db0.keys)
        commit('setRedisUsedMemory', info.used_memory_human)
      },
      checkStreamWebSocket({commit, dispatch, state}, id) {
        console.log("client_id: ", id)
        if (location.protocol !== 'https:') {
          commit('setStreamWebSocket', new WebSocket(`ws://${window.location.host}/ws/${id}`))
        }
        else {
          commit('setStreamWebSocket', new WebSocket(`wss://${window.location.host}/ws/${id}`))
        }
        state.stream_websocket.onmessage = (event) => {
          let data = JSON.parse(event.data)
          if (data.type === "ping") {
              console.log("got ping, sending pong")
              state.stream_websocket.send("pong")
              dispatch('setRedisStats', data.data.redis_info)
          }
          else {
            commit('addMessage', data.data)
          }
        }
      }
    },
    modules: {
    }
})
