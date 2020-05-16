/*
* TODO:
*  公会伤害成长曲线
*  公会成员成长曲线合图
*  公会成员总伤害对比表
*  公会成员刀平均伤害对比表
*  公会成员各Boss刀数统计
*  各个玩家与BOSS均伤偏差值百分比统计
*/

if (!Object.defineProperty) {
    alert('浏览器版本过低');
}
// 这代码很乱，到时候重构一下
var vm = new Vue({
    el: '#app',
    data: {
        members: [],
        range: '',
        pickerOptions: {
          shortcuts: [{
            text: '最近一周',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近半个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 15);
              picker.$emit('pick', [start, end]);
            }
          },  {
            text: '最近一个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近三个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近一年',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 365);
              picker.$emit('pick', [start, end]);
            }
          }]
        },
        challenges: [],
        activeIndex: '4',
        challenge_map: {},
        player_damage_cache: {},
        total_damage: {},
        contain_tail_and_continue: true,
        global_table_data: [],
        player_data: {
            damage: [
                
            ],
        },
        color_list: ['#c23531','#2f4554', '#61a0a8', '#d48265', '#91c7ae','#749f83',  '#ca8622', '#bda29a','#6e7074', '#546570', '#c4ccd3'],                
        challenge_chart: null,
        boss_dmg_chart: null,
        miss_chart: null,
        last_chart: null,
        boss_blood_chart: null,
        total_time_chart: null,
        boss_hit_chart: null,
        personal_progress_chart: null,
        personal_time_chart: null,
        is_loading: true,
        selecting_tab: "table",
        selecting_qqid: parseInt(qqid)
    },
    mounted() {
        this.boss_dmg_chart = echarts.init(document.getElementById("boss_dmg_chart"));
        this.challenge_chart = echarts.init(document.getElementById("challenge_chart"));
        this.sum_dmg_chart = echarts.init(document.getElementById("sum_dmg_chart"));
        this.miss_chart = echarts.init(document.getElementById("miss_chart"));
        this.last_chart = echarts.init(document.getElementById("last_chart"));
        this.boss_blood_chart = echarts.init(document.getElementById("boss_blood_chart"));
        this.total_time_chart = echarts.init(document.getElementById("total_time_chart"));
        this.boss_hit_chart = echarts.init(document.getElementById("boss_hit_chart"));
        this.personal_progress_chart = echarts.init(document.getElementById("personal_progress_chart"));
        this.personal_time_chart = echarts.init(document.getElementById("personal_time_chart"));
        this.selecting_tab = "total";
        this.refresh_data();
    },
    watch: {
        contain_tail_and_continue: function() {
            this.init();
        },
        selecting_qqid: function() {
            this.init_chart(this.player_damage(this.selecting_qqid).boss_damage_list);
            this.init_player_data();
        },
        selecting_tab: function() {
            this.init();
            setTimeout("vm.resizeAll()", 100);
        },
        range: function(value) {
            this.init();
            console.log(value);
        },
    },
    methods: {
        // tools function
        sum: (iterable) => {
            let sum = 0;
            iterable.forEach(v => sum += v);
            return sum;
        },
        format_to2: (num) => { return (num >= 10) ?  num.toString() : '0' + num.toString() },

        refresh_data: function() {
            const that = this;
            axios.get('../api/').then(res=> {
                if (res.data.code != 0) {
                    that.$alert(res.data.message, '获取记录失败');
                    that.is_loading = false;
                    return;
                }
                that.challenges = res.data.challenges;
                that.members = res.data.members;
                for (let challenge of that.challenges) {
                    let arr = that.challenge_map[challenge.qqid];
                    if (arr == undefined) {
                        arr = [];
                        that.challenge_map[challenge.qqid] = arr;
                    }
                    arr.push(challenge);
                }
                for (let member of that.members) {
                    member.challenges = that.challenge_map[member.qqid];
                }
                that.sort_and_divide();
                that.init();
                that.is_loading = false;
            // }).catch(function (error) {
            //     thisvue.$alert(error, '获取数据失败');
            //     thisvue.is_loading = false;
            });
        },

        init: function() {
            this.__total_damage();
            this.__global_table_data();
            this.init_player_data();
            if (this.selecting_tab === 'total') {
                this.init_chart(this.total_damage.boss_damage_list);
            }
            else if (this.selecting_tab === 'channel') {
                this.init_chart(this.total_damage.boss_damage_list);
            }
            else {
                this.init_chart(this.player_damage(this.selecting_qqid).boss_damage_list);
            }
        },
        // function for init
        init_chart: function(boss_damage_list) {
            let temp = this.boss_average_damage_for_chart(boss_damage_list, this.contain_tail_and_continue);
            let option = {
                title: {
                    text: '不同 Boss 刀均伤害'
                },
                tooltip: {},
                legend: {
                    data: ['伤害']
                },
                xAxis: {
                    data: temp[0],
                },
                yAxis: {},
                series: [{
                    name: '伤害',
                    type: 'bar',
                    data: temp[1],
                    itemStyle: {
                        color: (params) => {
                            let boss_id = parseInt(temp[0][params.dataIndex][0]) - 1;
                            return this.color_list[boss_id];
                        },
                    }
                }]
            }

            let temp2 = this.boss_challenge_count_for_chart(boss_damage_list, true);
            let option2 = {
                title: {
                    text: '不同 Boss 出刀数'
                },
                tooltip: {},
                series: [{
                    type: 'pie',
                    center: ['50%', '50%'],
                    data: temp2,
                    itemStyle: {
                        color: (params) => {
                            let boss_id = parseInt(temp2[params.dataIndex].name[0]) - 1;
                            return this.color_list[boss_id];
                        }
                    }
                }]
            }
            let temp3 = this.boss_sum_damage_for_chart(boss_damage_list);
            let option3 = {
                title: {
                    text: 'Boss 总伤害'
                },
                tooltip: {},
                legend: {
                    data: ['伤害']
                },
                xAxis: {
                    data: temp3[0],
                },
                yAxis: {},
                series: [{
                    name: '伤害',
                    type: 'bar',
                    data: temp3[1],
                    itemStyle: {
                        color: (params) => {
                            let boss_id = parseInt(temp3[0][params.dataIndex][0]) - 1;
                            return this.color_list[boss_id];
                        },
                    }
                }]
            }
            let temp4 = this.boss_miss_for_chart(this.global_table_data);
            let option4 = {
                title: {
                    text: '成员出刀考勤'
                },
                tooltip: {},
                legend: {
                    data: ['次数']
                },
                // grid: {
                //     bottom: 60
                // },
                xAxis: {
                    type: 'category',
                    data: temp4[0],
                    axisLabel: {
                        interval: 0,
                        rotate: 45
                    }
                },
                yAxis: {
                    type: 'value',
                    max: Math.max.apply(temp4[1]),
                    min: 0
                },
                series: [{
                    name: '出刀次数',
                    data: temp4[1],
                    type: 'bar',
                    showBackground: true,
                    backgroundStyle: {
                        color: 'rgba(220, 220, 220, 0.8)'
                    }
                }]
            }
            let temp5 = this.boss_last_for_chart();
            let option5 = {
                title: {
                    text: '尾刀统计',
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b} : {c} ({d}%)'
                },
                series: [
                    {
                        name: '次数',
                        type: 'pie',
                        radius: '55%',
                        data: temp5,
                        emphasis: {
                            itemStyle: {
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                            }
                        }
                    }
                ]
            };
            let temp6 = this.boss_blood_for_chart();
            let option6 = {
                title: {
                    text: 'BOSS血量曲线',
                },
                grid: {
                    bottom: 80
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'cross',
                        animation: false,
                        label: {
                            formatter: params => {
                                if (params.axisDimension === "x") {
                                    return (new Date(params.value)).toLocaleString();
                                }
                                if (params.axisDimension === "y") {
                                    return params.value.toLocaleString();
                                }
                                return params.value;
                            }
                        }
                    },
                    formatter: (params) => {
                        const series = params[0];
                        const [ts, value] = series.data;
                        const matched = temp6[1].find(f => (!f.gte || f.gte  <= ts) && (!f.lt || f.lt > ts));
                        return `${(new Date(ts)).toLocaleString()}<br />${series.marker}${(matched && matched.label) + "<br />" || ""}血量：${value.toLocaleString()}`
                    }
                },
                toolbox: {
                    show: true,
                    feature: {
                        dataZoom: {
                            yAxisIndex: 'none'
                        },
                        restore: {},
                        saveAsImage: {}
                    }
                },
                xAxis: {
                    type: 'time',
                    boundaryGap: false,
                },
                yAxis: {
                    type: 'value',
                    axisLabel: {
                        formatter: v => `${v / 10000} W`
                    },
                    axisPointer: {
                        snap: true
                    }
                },
                dataZoom: [
                    {
                        type: 'inside'
                    },
                    {
                        show: true,
                        realtime: true,
                        handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
                        handleSize: '80%',
                        handleStyle: {
                            color: '#fff',
                            shadowBlur: 3,
                            shadowColor: 'rgba(0, 0, 0, 0.6)',
                            shadowOffsetX: 2,
                            shadowOffsetY: 2
                        },
                    }
                ],
                visualMap: {
                    type: "piecewise",
                    show: false,
                    dimension: 0,
                    seriesIndex: 0,
                    pieces: temp6[1]
                },
                series: [
                    {
                        name: '血量',
                        type: 'line',
                        // smooth: true,
                        data: temp6[0],
                        areaStyle: {},
                    }
                ]
            };
            let temp7 = this.time_for_chart(this.challenges);
            let option7 = {
                title: {
                    text: '出刀时间',
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        animation: true,
                        label: {
                            backgroundColor: '#505765'
                        }
                    }
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: true,
                    axisLine: {onZero: false},
                    data: [...Array(24).keys()].map(i => `${i}时`),
                },
                yAxis: {
                    name: '刀',
                    type: 'value'
                },
                visualMap: [{
                    type: "piecewise",
                    show: false,
                    dimension: 0,
                    seriesIndex: 0,
                    pieces: [
                        {lte: 5, label: '凌晨', color: 'grey'},
                        {gt: 5,lte: 12, label: '上午', color: '#9cc5b0'},
                        {gt: 12,lte: 18, label: '下午', color: '#c54730'},
                        {gt: 18, label: '晚上', color: '#384b5a'},
                    ]
                }],
                series: {
                    name: '刀数',
                    type: 'bar',

                    animation: true,
                    lineStyle: {
                        width: 2
                    },
                    data: temp7
                }
            }
            let temp8 = this.boss_player_hit_count_for_chart();
            let option8 = {
                title: {
                    text: '成员BOSS出刀数'
                },
                tooltip: {
                    position: 'top'
                },
                animation: true,
                xAxis: {
                    type: 'category',
                    data: temp8[1],
                    splitArea: {
                        show: true
                    },
                    axisLabel: {
                        interval: 0,
                        rotate: 45
                    }
                },
                yAxis: {
                    type: 'category',
                    data: temp8[0],
                    splitArea: {
                        show: true
                    }
                },
                visualMap: {
                    min: 0,
                    max: 10,
                    calculable: true,
                    orient: 'horizontal',
                    left: 'center',
                    top: 0
                },
                series: [{
                    name: 'Punch Card',
                    type: 'heatmap',
                    data: temp8[2],
                    label: {
                        show: true
                    },
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            };

            this.boss_dmg_chart.setOption(option);
            this.challenge_chart.setOption(option2);
            this.sum_dmg_chart.setOption(option3);
            this.miss_chart.setOption(option4);
            this.last_chart.setOption(option5);
            this.boss_blood_chart.setOption(option6);
            this.total_time_chart.setOption(option7);
            this.boss_hit_chart.setOption(option8);
        },

        resizeAll: function() {
            this.sum_dmg_chart.resize();
            this.miss_chart.resize();
            this.last_chart.resize();
            this.boss_blood_chart.resize();
            this.total_time_chart.resize();
            this.personal_progress_chart.resize();
            this.personal_time_chart.resize();
            this.boss_hit_chart.resize();
        },

        init_player_data: function() {
            let max = 0, min = 2147483647, s = [0, 0, 0], c = [0, 0, 0];
            let pchallenge = this.challenge_map[this.selecting_qqid];
            for (let date in pchallenge) {
                let clist = pchallenge[date];
                let dmglist = []
                for (let i = 0; i < clist.length; i++) {
                    let damage = 0;
                    if (clist[i].health_ramain != 0) {
                        damage = clist[i].damage;
                    } 
                    else if (clist[i+1].is_continue) {
                        damage = clist[i].damage + clist[i+1].damage
                        i++;
                    }
                    if (max < damage) max = damage;
                    if (min > damage) min = damage;
                    dmglist.push(damage);
                    dmglist.sort((a, b) => {return b - a});
                }
                for (let i = 0; i < dmglist.length; i++) {
                    s[i] += dmglist[i];
                    c[i]++;
                }
            }
            this.player_data.damage = [
                {label: '最高单次伤害', value: max},
                {label: '最低单次伤害', value: min},
                {label: '伤害最高刀均伤害', value: Math.floor(s[0] / c[0])},
                {label: '伤害次高刀均伤害', value: Math.floor(s[1] / c[1])},
                {label: '伤害最低刀均伤害', value: Math.floor(s[2] / c[2])}
            ]
            const player_challs = this.challenges.filter(c => c.qqid == this.selecting_qqid);
            const param1 = this.time_for_chart(player_challs);
            const option1 = {
                title: {
                    text: '出刀时间',
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        animation: true,
                        label: {
                            backgroundColor: '#505765'
                        }
                    }
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: true,
                    axisLine: {onZero: false},
                    data: [...Array(24).keys()].map(i => `${i}时`),
                },
                yAxis: {
                    name: '刀',
                    type: 'value'
                },
                visualMap: [{
                    type: "piecewise",
                    show: false,
                    dimension: 0,
                    seriesIndex: 0,
                    pieces: [
                        {lte: 5, label: '凌晨', color: 'grey'},
                        {gt: 5,lte: 12, label: '上午', color: '#9cc5b0'},
                        {gt: 12,lte: 18, label: '下午', color: '#c54730'},
                        {gt: 18, label: '晚上', color: '#384b5a'},
                    ]
                }],
                series: {
                    name: '刀数',
                    type: 'bar',

                    animation: true,
                    lineStyle: {
                        width: 2
                    },
                    data: param1
                }
            };
            const param2 = this.day_damage_for_chart(player_challs);
            const option2 = {
                title: {
                  text: "伤害成长曲线"
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false
                },
                yAxis: {
                    type: 'value',
                    scale: true,
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        animation: true,
                    }
                },
                series: [
                    {
                        type: 'line',
                        name: '三刀总伤害',
                        smooth: 0.6,
                        symbolSize: 10,
                        color: 'green',
                        lineStyle: {
                            width: 5
                        },
                        data: param2
                    }
                ]
            };

            this.personal_time_chart.setOption(option1)
            this.personal_progress_chart.setOption(option2)

        },

        __total_damage: function() {
            this.total_damage = [];
            let boss_damage_list = {};
            let result = {normal_damage: [], continue_damage: [], tail_damage: [], count: 0, count_continue: 0, count_tail: 0};
            for (let challenge of this.challenges) {
                let dict = boss_damage_list[challenge.boss_num];
                if (dict == undefined) {
                    dict = {normal_damage: [], continue_damage: [], tail_damage: [], count: 0, count_continue: 0, count_tail: 0}
                    boss_damage_list[challenge.boss_num] = dict;
                }
                let damage = challenge.damage;
                if (challenge.health_ramain == 0) {
                    result.tail_damage.push(damage);
                    result.count_tail++;
                    dict.tail_damage.push(damage);
                    dict.count_tail++;
                    continue;
                }
                if (challenge.is_continue) {
                    result.continue_damage.push(damage);
                    result.count_continue++;
                    dict.continue_damage.push(damage);
                    dict.count_continue++;
                    continue;
                }
                result.normal_damage.push(damage);
                result.count++;
                dict.normal_damage.push(damage);
                dict.count++;
            }
            result.boss_damage_list = boss_damage_list;
            this.total_damage = result;
        },

        __global_table_data: function () {
            this.global_table_data = [];
            for (let member of this.members) {
                let sum = this.total_sum_damage();
                let pdmg = this.player_damage(member.qqid);
                let player_sum = this.player_sum_damage(member.qqid);
                let dict = {
                    qqid: member.qqid,
                    nickname: member.nickname,
                    count: pdmg.count + pdmg.count_continue / 2 + pdmg.count_tail / 2,
                    count_continue: pdmg.count_continue,
                    count_tail: pdmg.count_tail,
                    avg_dmg: this.player_average_damage(member.qqid, this.contain_tail_and_continue),
                    sum_dmg: player_sum,
                    sum_dmg_rate: (100 * player_sum / sum).toFixed(2) + '%'
                }
                this.global_table_data.push(dict);
            }
        },

        ts_to_day: function (ts) {
            // 减去5点
            let date = new Date((ts - 18000) * 1000);
            return date.getFullYear() + '-' + this.format_to2(date.getMonth() + 1) + '-' + this.format_to2(date.getDate());
        },
        sort_challenge_by_time: function(c1, c2) {
            return c1.challenge_time - c2.challenge_time;
        },
        sort_and_divide: function() {
            for (let m of this.members) {
                let detail = {};
                let challenges = m.challenges;
                if (!challenges) {
                    continue;
                }
                for (let challenge of challenges) {
                    if (detail[this.ts_to_day(challenge.challenge_time)] == undefined) {
                        detail[this.ts_to_day(challenge.challenge_time)] = [];
                    }
                    detail[this.ts_to_day(challenge.challenge_time)].push(challenge);
                }
                for (let key in detail) {
                    detail[key].sort(this.sort_challenge_by_time);
                }
                m.challenges = detail;
                this.challenge_map[m.qqid] = detail;
            }
        },

        total_average_damage: function(contain_tail_and_continue = false) {
            return this.average_damage(this.total_damage, contain_tail_and_continue);
        },
        player_average_damage: function(player_qqid, contain_tail_and_continue = false) {
            return this.average_damage(this.player_damage(player_qqid), contain_tail_and_continue);
        },

        boss_average_damage_for_chart: function(boss_damage_list, contain_tail_and_continue = false) {
            let l1 = [], l2 = [];
            for (let index in boss_damage_list) {
                let damage = boss_damage_list[index];
                let ret = this.average_damage(damage, contain_tail_and_continue);
                if (!isNaN(ret)) {
                    l1.push(index + "号Boss");
                    l2.push(ret);
                }
            }
            return [l1, l2];
        },
        boss_miss_for_chart: function(global_table_data) {
            const counts = global_table_data.map(elem => elem.count);
            const names = global_table_data.map(elem => elem.nickname);
            return [names, counts];
        },
        boss_last_for_chart: function() {
            const map = {};
            for (const i in this.challenges) {
                if (this.challenges[i].is_continue) {
                    const name = this.get_player(this.challenges[i].qqid).nickname;
                    if (name in map)
                        map[name] += 1;
                    else
                        map[name] = 1;
                }
            }
            return Object.keys(map).map(name => ({name: name, value: map[name]}));
        },
        boss_blood_for_chart: function() {
            const challs = this.challenges.sort((a, b) => a.challenge_time - b.challenge_time);
            let bosses = [];
            let now_boss, last_position, last_circle;
            for (const i in challs) {
                if (now_boss === undefined)
                    now_boss = challs[i].boss_num;
                if (last_position === undefined)
                    last_position = challs[i].challenge_time * 1000;
                if (last_circle === undefined)
                    last_circle = challs[i].cycle;
                if (challs[i].boss_num !== now_boss) {
                    const time = challs[i].challenge_time * 1000;
                    bosses.push({
                        gte: last_position,
                        lt: time,
                        color: this.color_list[now_boss - 1],
                        label: `${last_circle}周目${now_boss}王`
                    });
                    now_boss = challs[i].boss_num;
                    last_position = time;
                    last_circle = challs[i].cycle;
                }
            }
            if (now_boss && last_position) {
                bosses.push({
                    gte: last_position,
                    color: this.color_list[now_boss - 1]
                });
            }
            return [challs.map(c => [c.challenge_time * 1000, c.health_ramain]), bosses];
        },
        boss_sum_damage_for_chart: function(boss_damage_list) {
            let l1 = [], l2 = [];
            for (let index in boss_damage_list) {
                let damage = boss_damage_list[index];
                let ret = this.sum_damage(damage);
                if (!isNaN(ret)) {
                    l1.push(index + "号Boss");
                    l2.push(ret);
                }
            }
            return [l1, l2];
        },
        boss_challenge_count_for_chart: function(boss_damage_list, contain_tail_and_continue = false) {
            let l1 = []
            for (let index in boss_damage_list) {
                let damage = boss_damage_list[index];
                let ret = damage.count + (contain_tail_and_continue ? (damage.count_continue + damage.count_tail) / 2 : 0);
                if (ret != 0) l1.push({name: index + "号Boss", value: ret});
            }
            return l1;
        },
        boss_player_hit_count_for_chart: function() {
            const names = [], counter = {};
            const hanzi = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
            const max_boss_num = Math.max.apply(Math, [0, ...this.challenges.map(c => c.boss_num)]);
            const bosses = [...Array(max_boss_num || 0).keys()].map(k => `${k in hanzi ? hanzi[k] : k}王`).reverse()

            this.challenges.forEach(c => {
                const boss = c.boss_num;
                const name = this.get_player(c.qqid).nickname;
                if (!(boss in counter)) {
                    counter[boss] = {}
                }
                const boss_count = counter[boss];
                if (!(name in boss_count)) {
                    boss_count[name] = 0
                }
                const is_full = c.health_ramain && !c.is_continue;
                boss_count[name] += is_full ? 1 : 0.5;
            })
            const result = [];
            const get_nickname_index = name => {
                if (!names.includes(name))
                    names.push(name)
                return names.findIndex(n => n === name);
            }
            const get_boss_index = num => max_boss_num - parseInt(num);
            Object.keys(counter).forEach(num => {
                Object.keys(counter[num]).forEach(name => {
                    result.push([
                        get_boss_index(num),
                        get_nickname_index(name),
                        counter[num][name]
                    ])
                })
            })
            return [
                bosses,
                names,
                result.map(function (item) {
                    return [item[1], item[0], item[2] || '-'];
                })
            ];
        },
        time_for_chart: function(challenges) {
            const time = {};
            [...Array(24).keys()].forEach(i => time[i] = 0);
            for (const i in challenges) {
                const t = new Date(challenges[i].challenge_time * 1000);
                time[t.getHours()] += 1;
            }
            return Object.values(time);
        },
        day_damage_for_chart: function(challenges) {
            const dates = {};
            challenges.forEach(c => {
                const date = this.ts_to_day(c.challenge_time);
                if (date in dates) {
                    dates[date] += c.damage;
                } else {
                    dates[date] = c.damage;
                }
            });
            return Object.entries(dates).sort(
                (a, b) =>
                    new Date(a[0]) - new Date(b[0])
            );
        },

        average_damage: function(damage, contain_tail_and_continue) {
            let sum = this.sum(damage.normal_damage);
            let count = damage.count;
            if (contain_tail_and_continue) {
                sum += this.sum(damage.continue_damage) + this.sum(damage.tail_damage);
                count += (damage.count_continue + damage.count_tail) / 2;
            }
            return Math.floor(sum / count);
        },

        total_sum_damage: function() {
            return this.sum_damage(this.total_damage);
        },
        player_sum_damage: function(player_qqid) {
            return this.sum_damage(this.player_damage(player_qqid));
        },
        sum_damage: function(damage) {
            return this.sum(damage.normal_damage) + this.sum(damage.continue_damage) + this.sum(damage.tail_damage);
        },

        challenge_count: function(damage, contain_tail_and_continue) {
            return damage.count + (contain_tail_and_continue ? (damage.count_tail + damage.count_continue) / 2 : 0);
        },

        get_player: function(qqid) {
            return this.members.find(o => o.qqid === qqid);
        },

        player_damage: function(player_qqid) {
            if (this.player_damage_cache[player_qqid] != undefined) return this.player_damage_cache[player_qqid];

            let challenges = this.challenge_map[player_qqid];
            let boss_damage_list = {};
            let result = {normal_damage: [], continue_damage: [], tail_damage: [], count: 0, count_continue: 0, count_tail: 0};
            for (let day in challenges) {
                for (let challenge of challenges[day]) {
                    let dict = boss_damage_list[challenge.boss_num];
                    if (dict == undefined) {
                        dict = {normal_damage: [], continue_damage: [], tail_damage: [], count: 0, count_continue: 0, count_tail: 0}
                        boss_damage_list[challenge.boss_num] = dict;
                    }
                    let damage = challenge.damage;
                    if (challenge.health_ramain == 0) {
                        result.tail_damage.push(damage);
                        result.count_tail++;
                        dict.tail_damage.push(damage);
                        dict.count_tail++;
                        continue;
                    }
                    if (challenge.is_continue) {
                        result.continue_damage.push(damage);
                        result.count_continue++;
                        dict.continue_damage.push(damage);
                        dict.count_continue++;
                        continue;
                    }
                    result.normal_damage.push(damage);
                    result.count++;
                    dict.normal_damage.push(damage);
                    dict.count++;
                }
            }
            result.boss_damage_list = boss_damage_list;
            this.player_damage_cache[player_qqid] = result;
            return result;
        },
        get_today: function () {
            let d = new Date();
            d -= 18000000;
            d = new Date(d).setHours(0, 0, 0, 0);
            return d;
        },
    },
    delimiters: ['[[', ']]'],
})