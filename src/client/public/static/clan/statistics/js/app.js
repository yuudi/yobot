(function(t){function e(e){for(var n,l,o=e[0],s=e[1],c=e[2],d=0,f=[];d<o.length;d++)l=o[d],Object.prototype.hasOwnProperty.call(i,l)&&i[l]&&f.push(i[l][0]),i[l]=0;for(n in s)Object.prototype.hasOwnProperty.call(s,n)&&(t[n]=s[n]);u&&u(e);while(f.length)f.shift()();return r.push.apply(r,c||[]),a()}function a(){for(var t,e=0;e<r.length;e++){for(var a=r[e],n=!0,o=1;o<a.length;o++){var s=a[o];0!==i[s]&&(n=!1)}n&&(r.splice(e--,1),t=l(l.s=a[0]))}return t}var n={},i={app:0},r=[];function l(e){if(n[e])return n[e].exports;var a=n[e]={i:e,l:!1,exports:{}};return t[e].call(a.exports,a,a.exports,l),a.l=!0,a.exports}l.m=t,l.c=n,l.d=function(t,e,a){l.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:a})},l.r=function(t){"undefined"!==typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},l.t=function(t,e){if(1&e&&(t=l(t)),8&e)return t;if(4&e&&"object"===typeof t&&t&&t.__esModule)return t;var a=Object.create(null);if(l.r(a),Object.defineProperty(a,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var n in t)l.d(a,n,function(e){return t[e]}.bind(null,n));return a},l.n=function(t){var e=t&&t.__esModule?function(){return t["default"]}:function(){return t};return l.d(e,"a",e),e},l.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},l.p="/";var o=window["webpackJsonp"]=window["webpackJsonp"]||[],s=o.push.bind(o);o.push=e,o=o.slice();for(var c=0;c<o.length;c++)e(o[c]);var u=s;r.push([0,"chunk-vendors"]),a()})({0:function(t,e,a){t.exports=a("56d7")},"034f":function(t,e,a){"use strict";var n=a("85ec"),i=a.n(n);i.a},"56d7":function(t,e,a){"use strict";a.r(e);a("e260"),a("e6cf"),a("cca6"),a("a79d");var n=a("2b0e"),i=a("5c96"),r=a.n(i),l=(a("0fae"),function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",{attrs:{id:"app"}},[a("Header"),a("section",{staticClass:"container"},[a("aside",{staticClass:"side-menu"},[a("SideMenu",{attrs:{defaultActive:t.activeMenu},on:{change:t.handleChangeActiveTab}})],1),a("article",{staticClass:"content"},["total"===t.activeMenu?a("Statistics",{attrs:{originData:t.originData,originUserData:t.originUserData}}):[a("h2",[t._v("建设中")])]],2)])],1)}),o=[],s=a("bc3a"),c=a.n(s),u=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("el-page-header",{attrs:{content:""},on:{back:function(e){t.location=".."}}}),a("el-menu",{staticClass:"el-menu-demo",attrs:{"default-active":t.activeIndex,mode:"horizontal"},on:{select:t.handleTitleSelect}},[a("el-menu-item",{attrs:{index:"1"}},[t._v("面板")]),a("el-menu-item",{attrs:{index:"2"}},[t._v("预约")]),a("el-menu-item",{attrs:{index:"3"}},[t._v("查刀")]),a("el-menu-item",{attrs:{index:"4"}},[t._v("统计")]),a("el-menu-item",{attrs:{index:"5"}},[t._v("我的")])],1)],1)},d=[],f={data:function(){return{activeIndex:"4"}},methods:{handleTitleSelect:function(t){switch(t){case"1":window.location="../";break;case"2":window.location="../subscribers/";break;case"3":window.location="../progress/";break;case"4":window.location="../statistics/";break;case"5":window.location="../my/";break;default:break}}}},m=f,p=a("2877"),b=Object(p["a"])(m,u,d,!1,null,null,null),g=b.exports,v=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("el-menu",{attrs:{"default-active":t.defaultActive},on:{select:t.handleSelect}},[a("el-menu-item",{attrs:{index:"total"}},[t._v("总伤害")]),a("el-menu-item",{attrs:{index:"cycle"}},[t._v("按周目")]),a("el-menu-item",{attrs:{index:"boss"}},[t._v("按BOSS")]),a("el-menu-item",{attrs:{index:"player"}},[t._v("按玩家")])],1)},h=[],_={props:["defaultActive"],methods:{handleSelect:function(t){this.$emit("change",t)}}},w=_,y=Object(p["a"])(w,v,h,!1,null,null,null),D=y.exports,S=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("h1",{staticStyle:{"text-align":"center"}},[t._v("伤害统计")]),a("span",[t._v("伤害颜色：")]),a("a",{staticClass:"digit6"},[t._v("十万")]),t._v(" | "),a("a",{staticClass:"digit7"},[t._v("百万")]),t._v(" | "),a("a",{staticClass:"digit8"},[t._v("千万")]),t._v(" | "),a("a",{staticClass:"digit9"},[t._v("亿")]),a("el-table",{attrs:{data:t.statisticsData,"default-sort":{prop:"damage",order:"descending"}}},[t._v("> "),a("el-table-column",{attrs:{prop:"qqid",label:"QQ号",sortable:""}}),a("el-table-column",{attrs:{prop:"nickname",label:"昵称",sortable:""}}),a("el-table-column",{attrs:{prop:"damage",label:"总伤害",sortable:""},scopedSlots:t._u([{key:"default",fn:function(e){return e.row?[a("a",{class:"digit"+e.row.damage.toString().length},[t._v(t._s(e.row.damage))])]:void 0}}],null,!0)}),a("el-table-column",{attrs:{prop:"total",label:"总出刀数",sortable:""}}),a("el-table-column",{attrs:{prop:"totalNotRemain",label:"总出刀数（不包含剩余刀）",sortable:"",width:"220"}}),a("el-table-column",{attrs:{prop:"normal",label:"正常刀数",sortable:""}}),a("el-table-column",{attrs:{prop:"tail",label:"尾刀数",sortable:""}}),a("el-table-column",{attrs:{fixed:"right",label:"操作"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("el-button",{attrs:{type:"text",size:"small"},on:{click:function(a){return t.handleClick(e.row)}}},[t._v("查看")])]}}])})],1),a("el-dialog",{attrs:{title:"伤害详情",visible:t.dialogTableVisible},on:{"update:visible":function(e){t.dialogTableVisible=e}}},[a("el-table",{attrs:{data:t.gridData}},[a("el-table-column",{attrs:{prop:"cycle",label:"周目"}}),a("el-table-column",{attrs:{prop:"boss_num",label:"BOSS顺位"}}),a("el-table-column",{attrs:{label:"刀伤害"},scopedSlots:t._u([{key:"default",fn:function(e){return e.row?[a("span",{domProps:{innerHTML:t._s(t.csummary(e.row))}}),a("el-popover",{attrs:{placement:"top",effect:"light",trigger:"hover"}},[t._v(" "+t._s(t.cdetail(e.row))+" "),a("i",{staticClass:"el-icon-info",attrs:{slot:"reference"},slot:"reference"})])]:void 0}}],null,!0)})],1)],1)],1)},x=[],O=(a("99af"),a("4160"),a("d81d"),a("4fad"),a("d3b7"),a("07ac"),a("25f0"),a("159b"),a("5530")),k=a("3835"),j=a("cd3f"),T=a.n(j),C={props:["originData","originUserData"],data:function(){return{dialogTableVisible:!1,activeId:null}},computed:{userData:function(){var t=this;if(!this.originData||!this.originUserData)return{};var e={};return this.originUserData.forEach((function(t){e[t.qqid]={nickname:t.nickname,damage:0,damageDetail:[]}})),T()(this.originData).sort((function(t,e){return t.challenge_time>e.challenge_time?1:-1})).forEach((function(t){var a=t.qqid,n=t.damage;e[a].damage+=n,e[a].damageDetail.push(t)})),Object.values(e).forEach((function(e){var a=t.count(e.damageDetail);e.total=a.total,e.normal=a.normal,e.remain=a.remain,e.tail=a.tail,e.totalNotRemain=a.totalNotRemain})),e},statisticsData:function(){return Object.entries(this.userData).map((function(t){var e=Object(k["a"])(t,2),a=e[0],n=e[1];return Object(O["a"])(Object(O["a"])({},n),{},{qqid:a})}))},gridData:function(){return this.dialogTableVisible?this.userData[this.activeId].damageDetail:[]}},methods:{count:function(t){var e=0,a=0,n=0;return t.forEach((function(t){t.is_continue?a++:0===t.health_ramain?n++:e++})),{normal:e,ramain:a,tail:n,total:t.length,totalNotRemain:t.length-a}},csummary:function(t){if(void 0==t)return"";var e="";return t.is_continue&&(e="（剩余刀）"),0===t.health_ramain&&(e="（尾刀）"),"".concat(e,' <a class="digit').concat(t.damage.toString().length,'">').concat(t.damage,"</a>")},cdetail:function(t){if(void 0==t)return"";var e=new Date;e.setTime(1e3*t.challenge_time);var a=e.toLocaleString("chinese",{hour12:!1})+"\n";return a+=t.cycle+"周目"+t.boss_num+"号boss\n",a+=(t.health_ramain+t.damage).toLocaleString()+"→"+t.health_ramain.toLocaleString(),t.message&&(a+="\n留言："+t.message),a},handleClick:function(t){this.activeId=t.qqid,this.dialogTableVisible=!0}}},M=C,q=(a("b823"),Object(p["a"])(M,S,x,!1,null,null,null)),E=q.exports,P={name:"App",components:{Header:g,SideMenu:D,Statistics:E},data:function(){return{activeMenu:"total",originData:[],originUserData:[]}},mounted:function(){var t=this;c.a.all([c.a.get("./api/"),c.a.post("../api/",{action:"get_member_list",csrf_token:window.csrf_token})]).then(c.a.spread((function(e,a){0==e.data.code?0==a.data.code?(t.originData=e.data.challenges,t.originUserData=a.data.members):t.$alert(a.data.message,"获取成员失败"):t.$alert(e.data.message,"获取记录失败")})))},methods:{handleChangeActiveTab:function(t){this.activeMenu=t}}},$=P,U=(a("034f"),Object(p["a"])($,l,o,!1,null,null,null)),A=U.exports;n["default"].use(r.a),n["default"].config.productionTip=!1,new n["default"]({render:function(t){return t(A)}}).$mount("#app")},"85ec":function(t,e,a){},b823:function(t,e,a){"use strict";var n=a("f340"),i=a.n(n);i.a},f340:function(t,e,a){}});
//# sourceMappingURL=app.8c00ce4a.js.map