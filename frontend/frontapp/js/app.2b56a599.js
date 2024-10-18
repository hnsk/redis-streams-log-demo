(()=>{"use strict";var e={9396:(e,t,r)=>{var o=r(8880),n=r(3525),s=r(3673);function a(e,t,r,o,n,a){const i=(0,s.up)("router-view");return(0,s.wg)(),(0,s.j4)(i)}const i={name:"App",setup(){}};var l=r(4260);const c=(0,l.Z)(i,[["render",a]]),d=c;var u=r(4584),p=r(7083),m=r(9582);const h=[{path:"/",component:()=>Promise.all([r.e(736),r.e(33)]).then(r.bind(r,6033)),children:[{path:"",component:()=>Promise.all([r.e(736),r.e(692)]).then(r.bind(r,4692))},{path:"/search",component:()=>Promise.all([r.e(736),r.e(950)]).then(r.bind(r,950))},{path:"/generator",component:()=>Promise.all([r.e(736),r.e(246)]).then(r.bind(r,5246))},{path:"/geosearch",component:()=>Promise.all([r.e(736),r.e(658)]).then(r.bind(r,658))},{path:"/timeseries",component:()=>Promise.all([r.e(736),r.e(792)]).then(r.bind(r,2792))}]},{path:"/:catchAll(.*)*",component:()=>Promise.all([r.e(736),r.e(193)]).then(r.bind(r,2193))}],f=h,g=(0,p.BC)((function(){const e=m.r5,t=(0,m.p7)({scrollBehavior:()=>({left:0,top:0}),routes:f,history:e("")});return t}));async function b(e,t){const o="function"===typeof u.Z?await(0,u.Z)({}):u.Z,{storeKey:s}=await Promise.resolve().then(r.bind(r,4584)),a="function"===typeof g?await g({store:o}):g;o.$router=a;const i=e(d);return i.use(n.Z,t),{app:i,store:o,storeKey:s,router:a}}const v={config:{}},y="";async function w({app:e,router:t,store:r,storeKey:o},n){let s=!1;const a=e=>{try{return t.resolve(e).href}catch(r){}return Object(e)===e?null:e},i=e=>{if(s=!0,"string"===typeof e&&/^https?:\/\//.test(e))return void(window.location.href=e);const t=a(e);null!==t&&(window.location.href=t,window.location.reload())},l=window.location.href.replace(window.location.origin,"");for(let d=0;!1===s&&d<n.length;d++)try{await n[d]({app:e,router:t,store:r,ssrContext:null,redirect:i,urlPath:l,publicPath:y})}catch(c){return c&&c.url?void i(c.url):void console.error("[Quasar] boot error:",c)}!0!==s&&(e.use(t),e.use(r,o),e.mount("#q-app"))}b(o.ri,v).then((e=>Promise.all([Promise.resolve().then(r.bind(r,5474)),Promise.resolve().then(r.bind(r,8181))]).then((t=>{const r=t.map((e=>e.default)).filter((e=>"function"===typeof e));w(e,r)}))))},8181:(e,t,r)=>{r.r(t),r.d(t,{default:()=>s});var o=r(2585),n=r.n(o);const s=({app:e})=>{e.use(n())}},5474:(e,t,r)=>{r.r(t),r.d(t,{api:()=>i,default:()=>l});var o=r(7083),n=r(52),s=r.n(n);let a=null;a="https:"!==location.protocol?`http://${window.location.host}`:`https://${window.location.host}`;const i=s().create({baseURL:a}),l=(0,o.xr)((({app:e})=>{e.config.globalProperties.$axios=s(),e.config.globalProperties.$api=i}))},4584:(e,t,r)=>{r.d(t,{Z:()=>s});var o=r(3617),n=r(5474);const s=(0,o.MT)({state:{message_counter:0,client_id:null,stream_websocket:null,message_keys:{},messages:[],redis_keys:0,redis_used_memory:0},getters:{getMessageCounter(e){return e.message_counter}},mutations:{increaseMessageCounter(e){e.message_counter++},resetMessageCounter(e){e.message_counter=0},addMessage(e,t){for(const r of Object.keys(t))r in e.message_keys||(e.message_keys[r]=r);e.messages.unshift(t),e.message_counter++,e.messages.length>25&&e.messages.pop()},resetMessages(e){e.messages=[]},setClientID(e,t){e.client_id=t},setStreamWebSocket(e,t){e.stream_websocket&&e.stream_websocket.close(),e.stream_websocket=t},setRedisKeys(e,t){e.redis_keys=t},setRedisUsedMemory(e,t){e.redis_used_memory=t}},actions:{setClientID({dispatch:e,commit:t}){n.api.get("api/clientid").then((r=>{t("setClientID",r.data.client_id),e("checkStreamWebSocket",r.data.client_id)}))},setRedisStats({commit:e},t){e("setRedisKeys",t.db0.keys),e("setRedisUsedMemory",t.used_memory_human)},checkStreamWebSocket({commit:e,dispatch:t,state:r},o){console.log("client_id: ",o),"https:"!==location.protocol?e("setStreamWebSocket",new WebSocket(`ws://${window.location.host}/ws/${o}`)):e("setStreamWebSocket",new WebSocket(`wss://${window.location.host}/ws/${o}`)),r.stream_websocket.onmessage=o=>{let n=JSON.parse(o.data);"ping"===n.type?(console.log("got ping, sending pong"),r.stream_websocket.send("pong"),t("setRedisStats",n.data.redis_info)):e("addMessage",n.data)}}},modules:{}})}},t={};function r(o){var n=t[o];if(void 0!==n)return n.exports;var s=t[o]={exports:{}};return e[o].call(s.exports,s,s.exports,r),s.exports}r.m=e,(()=>{var e=[];r.O=(t,o,n,s)=>{if(!o){var a=1/0;for(d=0;d<e.length;d++){for(var[o,n,s]=e[d],i=!0,l=0;l<o.length;l++)(!1&s||a>=s)&&Object.keys(r.O).every((e=>r.O[e](o[l])))?o.splice(l--,1):(i=!1,s<a&&(a=s));if(i){e.splice(d--,1);var c=n();void 0!==c&&(t=c)}}return t}s=s||0;for(var d=e.length;d>0&&e[d-1][2]>s;d--)e[d]=e[d-1];e[d]=[o,n,s]}})(),(()=>{r.n=e=>{var t=e&&e.__esModule?()=>e["default"]:()=>e;return r.d(t,{a:t}),t}})(),(()=>{var e,t=Object.getPrototypeOf?e=>Object.getPrototypeOf(e):e=>e.__proto__;r.t=function(o,n){if(1&n&&(o=this(o)),8&n)return o;if("object"===typeof o&&o){if(4&n&&o.__esModule)return o;if(16&n&&"function"===typeof o.then)return o}var s=Object.create(null);r.r(s);var a={};e=e||[null,t({}),t([]),t(t)];for(var i=2&n&&o;"object"==typeof i&&!~e.indexOf(i);i=t(i))Object.getOwnPropertyNames(i).forEach((e=>a[e]=()=>o[e]));return a["default"]=()=>o,r.d(s,a),s}})(),(()=>{r.d=(e,t)=>{for(var o in t)r.o(t,o)&&!r.o(e,o)&&Object.defineProperty(e,o,{enumerable:!0,get:t[o]})}})(),(()=>{r.f={},r.e=e=>Promise.all(Object.keys(r.f).reduce(((t,o)=>(r.f[o](e,t),t)),[]))})(),(()=>{r.u=e=>"js/"+e+"."+{33:"be1e4246",193:"8d648ccb",246:"6f6bb6ec",658:"c301a799",692:"5350b49a",792:"4620703b",950:"9346b659"}[e]+".js"})(),(()=>{r.miniCssF=e=>"css/"+({143:"app",736:"vendor"}[e]||e)+"."+{143:"31d6cfe0",658:"a1e7dd1c",736:"42e0666d",950:"a1e7dd1c"}[e]+".css"})(),(()=>{r.g=function(){if("object"===typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"===typeof window)return window}}()})(),(()=>{r.o=(e,t)=>Object.prototype.hasOwnProperty.call(e,t)})(),(()=>{var e={},t="log-demo-quasar:";r.l=(o,n,s,a)=>{if(e[o])e[o].push(n);else{var i,l;if(void 0!==s)for(var c=document.getElementsByTagName("script"),d=0;d<c.length;d++){var u=c[d];if(u.getAttribute("src")==o||u.getAttribute("data-webpack")==t+s){i=u;break}}i||(l=!0,i=document.createElement("script"),i.charset="utf-8",i.timeout=120,r.nc&&i.setAttribute("nonce",r.nc),i.setAttribute("data-webpack",t+s),i.src=o),e[o]=[n];var p=(t,r)=>{i.onerror=i.onload=null,clearTimeout(m);var n=e[o];if(delete e[o],i.parentNode&&i.parentNode.removeChild(i),n&&n.forEach((e=>e(r))),t)return t(r)},m=setTimeout(p.bind(null,void 0,{type:"timeout",target:i}),12e4);i.onerror=p.bind(null,i.onerror),i.onload=p.bind(null,i.onload),l&&document.head.appendChild(i)}}})(),(()=>{r.r=e=>{"undefined"!==typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})}})(),(()=>{r.p=""})(),(()=>{var e=(e,t,r,o)=>{var n=document.createElement("link");n.rel="stylesheet",n.type="text/css";var s=s=>{if(n.onerror=n.onload=null,"load"===s.type)r();else{var a=s&&("load"===s.type?"missing":s.type),i=s&&s.target&&s.target.href||t,l=new Error("Loading CSS chunk "+e+" failed.\n("+i+")");l.code="CSS_CHUNK_LOAD_FAILED",l.type=a,l.request=i,n.parentNode.removeChild(n),o(l)}};return n.onerror=n.onload=s,n.href=t,document.head.appendChild(n),n},t=(e,t)=>{for(var r=document.getElementsByTagName("link"),o=0;o<r.length;o++){var n=r[o],s=n.getAttribute("data-href")||n.getAttribute("href");if("stylesheet"===n.rel&&(s===e||s===t))return n}var a=document.getElementsByTagName("style");for(o=0;o<a.length;o++){n=a[o],s=n.getAttribute("data-href");if(s===e||s===t)return n}},o=o=>new Promise(((n,s)=>{var a=r.miniCssF(o),i=r.p+a;if(t(a,i))return n();e(o,i,n,s)})),n={143:0};r.f.miniCss=(e,t)=>{var r={658:1,950:1};n[e]?t.push(n[e]):0!==n[e]&&r[e]&&t.push(n[e]=o(e).then((()=>{n[e]=0}),(t=>{throw delete n[e],t})))}})(),(()=>{var e={143:0};r.f.j=(t,o)=>{var n=r.o(e,t)?e[t]:void 0;if(0!==n)if(n)o.push(n[2]);else{var s=new Promise(((r,o)=>n=e[t]=[r,o]));o.push(n[2]=s);var a=r.p+r.u(t),i=new Error,l=o=>{if(r.o(e,t)&&(n=e[t],0!==n&&(e[t]=void 0),n)){var s=o&&("load"===o.type?"missing":o.type),a=o&&o.target&&o.target.src;i.message="Loading chunk "+t+" failed.\n("+s+": "+a+")",i.name="ChunkLoadError",i.type=s,i.request=a,n[1](i)}};r.l(a,l,"chunk-"+t,t)}},r.O.j=t=>0===e[t];var t=(t,o)=>{var n,s,[a,i,l]=o,c=0;if(a.some((t=>0!==e[t]))){for(n in i)r.o(i,n)&&(r.m[n]=i[n]);if(l)var d=l(r)}for(t&&t(o);c<a.length;c++)s=a[c],r.o(e,s)&&e[s]&&e[s][0](),e[s]=0;return r.O(d)},o=globalThis["webpackChunklog_demo_quasar"]=globalThis["webpackChunklog_demo_quasar"]||[];o.forEach(t.bind(null,0)),o.push=t.bind(null,o.push.bind(o))})();var o=r.O(void 0,[736],(()=>r(9396)));o=r.O(o)})();