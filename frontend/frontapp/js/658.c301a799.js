"use strict";(globalThis["webpackChunklog_demo_quasar"]=globalThis["webpackChunklog_demo_quasar"]||[]).push([[658],{658:(e,t,a)=>{a.r(t),a.d(t,{default:()=>z});var l=a(3673);function r(e,t,a,r,o,n){const i=(0,l.up)("GeoSearchTable");return(0,l.wg)(),(0,l.j4)(i)}var o=a(2323);const n={class:"q-ma-lg",style:{width:"90%",height:"600px"}},i={style:{width:"200px"}},s={style:{width:"200px"}},u=(0,l._)("p",{class:"text-h5 q-mt-md"},"Circle events:",-1),c=(0,l._)("p",{class:"text-h5 q-mt-md"},"Circle markers:",-1);function g(e,t,a,r,g,p){const d=(0,l.up)("l-control-scale"),m=(0,l.up)("q-table"),h=(0,l.up)("l-control"),y=(0,l.up)("l-circle"),f=(0,l.up)("l-popup"),v=(0,l.up)("l-marker"),w=(0,l.up)("l-tile-layer"),_=(0,l.up)("l-map"),k=(0,l.up)("q-tooltip"),b=(0,l.up)("q-banner");return(0,l.wg)(),(0,l.iD)("div",null,[(0,l._)("div",n,[(0,l.Wm)(_,{center:r.center,"onUpdate:center":t[0]||(t[0]=e=>r.center=e),modelValue:r.zoom,"onUpdate:modelValue":t[1]||(t[1]=e=>r.zoom=e),zoom:r.zoom,"onUpdate:zoom":t[2]||(t[2]=e=>r.zoom=e),minZoom:3,maxZoom:7,worldCopyJump:"",ref:"logMap"},{default:(0,l.w5)((()=>[(0,l.Wm)(d,{position:"topright",imperial:!1,metric:!0}),(0,l.Wm)(h,{position:"bottomleft"},{default:(0,l.w5)((()=>[(0,l._)("div",i,[(0,l.Wm)(m,{title:"Circle events",dense:"",rows:r.circleAggregates,columns:r.aggregate_columns,"hide-pagination":!0,"row-key":"field",flat:"",pagination:{rowsPerPage:0}},null,8,["rows","columns"])])])),_:1}),(0,l.Wm)(y,{"lat-lng":r.center,color:"blue",radius:1e3*r.zoomRadius[r.zoom],metric:"true"},null,8,["lat-lng","radius"]),((0,l.wg)(!0),(0,l.iD)(l.HY,null,(0,l.Ko)(r.markers,((e,t)=>((0,l.wg)(),(0,l.j4)(v,{key:t,"lat-lng":e,onClick:e=>r.getCityAggregates(r.markersData[t].city,r.markersData[t].country_code)},{default:(0,l.w5)((()=>[(0,l.Wm)(f,{options:{autoPan:!1}},{default:(0,l.w5)((()=>[(0,l._)("div",s,[(0,l.Wm)(m,{title:`${r.selectedMarkerData.city} (${r.selectedMarkerData.country_code})`,dense:"",rows:r.selectedMarkerData.aggregates,columns:r.aggregate_columns,"hide-pagination":!0,"row-key":"field",flat:"",pagination:{rowsPerPage:0}},null,8,["title","rows","columns"])])])),_:1})])),_:2},1032,["lat-lng","onClick"])))),128)),(0,l.Wm)(w,{url:"https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",attribution:r.attribution},null,8,["attribution"])])),_:1},8,["center","modelValue","zoom"]),u,(0,l.Wm)(b,{class:"bg-grey-9 text-white q-ma-md text-weight-bold codebox"},{default:(0,l.w5)((()=>[(0,l.Uk)((0,o.zw)(r.circleAggregatesQuery)+" ",1),(0,l.Wm)(k,null,{default:(0,l.w5)((()=>[(0,l.Uk)("Circle events aggregate query.")])),_:1})])),_:1}),c,(0,l.Wm)(b,{class:"bg-grey-9 text-white q-ma-md text-weight-bold codebox"},{default:(0,l.w5)((()=>[(0,l.Uk)((0,o.zw)(r.markersQuery)+" ",1),(0,l.Wm)(k,null,{default:(0,l.w5)((()=>[(0,l.Uk)("Circle markers aggregate query.")])),_:1})])),_:1})])])}var p=a(1959),d=a(5474),m=a(8892);const h={name:"GeoSearchTable",components:{LMap:m.iA,LTileLayer:m.Hw,LMarker:m.$R,LPopup:m.Q2,LControlScale:m.O9,LCircle:m.J_,LControl:m.oJ},setup(){let e=(0,p.iH)(3),t=(0,p.iH)([48,23]);const a={3:2500,4:1500,5:700,6:400,7:250},r="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",o='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',n=(0,p.iH)(null);let i=null;(0,l.bv)((()=>{h("23,48"),_(),i=setInterval(_,1e3)})),(0,l.Jd)((()=>{clearInterval(i)})),(0,l.YP)(t,(e=>{n.value.leafletObject.closePopup();const t=`${e.lng},${e.lat}`;h(t),_()}));let s=(0,p.iH)([]),u=(0,p.iH)([]),c=(0,p.iH)({city:"",country_code:"",aggregates:[]}),g=(0,p.iH)("");function h(t){d.api.post("api/search/aggregate/cities",{coordinates:t,distance:a[e.value]}).then((e=>{let t=[],a=[];for(const l of e.data.results){const[e,r]=l.coordinates.split(",");t.push([r,e]),a.push({city:l.city,entries:l.entries,country_code:l.country_code,aggregates:[]})}s.value.splice(0,s.value.length,...t),u.value.splice(0,u.value.length,...a),g.value=e.data.literal_query}))}const y=[{name:"field",field:"field",label:"Log Level",align:"left",classes:e=>e.field.toLowerCase()},{name:"entries",field:"entries",label:"Entries",align:"left"}];function f(e,t){c.value.city=e,c.value.country_code=t,d.api.post("api/search/aggregate",{query:`@city:{${e}} && @country_code:{${t}}`,field:"log_level"}).then((e=>{let t=[];for(let a of e.data.results)t.push(a);c.value.aggregates.splice(0,c.value.aggregates.length,...t)}))}let v=(0,p.iH)([]),w=(0,p.iH)("");function _(){let l=null;l="lng"in t.value?`${t.value.lng} ${t.value.lat}`:`${t.value[1]} ${t.value[0]}`,d.api.post("api/search/aggregate",{query:`@coordinates:[${l} ${a[e.value]} km]`,field:"log_level"}).then((e=>{let t=[];for(let a of e.data.results)t.push(a);v.value.splice(0,v.value.length,...t),w.value=e.data.literal_query}))}return{LMap:m.iA,LTileLayer:m.Hw,LMarker:m.$R,LPopup:m.Q2,LControlScale:m.O9,LCircle:m.J_,LControl:m.oJ,zoom:e,center:t,url:r,attribution:o,markers:s,markersData:u,markersQuery:g,getCityAggregates:f,circleAggregates:v,circleAggregatesQuery:w,aggregate_columns:y,zoomRadius:a,selectedMarkerData:c,logMap:n}}};var y=a(4260),f=a(6429),v=a(5607),w=a(5363),_=a(7518),k=a.n(_);const b=(0,y.Z)(h,[["render",g]]),C=b;k()(h,"components",{QTable:f.Z,QBanner:v.Z,QTooltip:w.Z});const L={components:{GeoSearchTable:C},setup(){return{GeoSearchTable:C}}},q=(0,y.Z)(L,[["render",r]]),z=q}}]);