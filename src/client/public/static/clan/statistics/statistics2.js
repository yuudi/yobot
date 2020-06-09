/*
* TODO:
*  公会伤害成长曲线
*  公会成员成长曲线合图
*  各个玩家与BOSS均伤偏差值百分比统计
*/

const numberFormatter = num => {
    if (num < 10000)
        return `${num.toLocaleString()}`
    if (num < 100000000)
        return `${(num / 10000).toLocaleString()} W`
    return `${(num / 100000000).toLocaleString()} E`
}

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
              start.setHours(0, 0, 0, 0);
              end.setHours(0, 0, 0, 0);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近半个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 15);
              start.setHours(0, 0, 0, 0);
              end.setHours(0, 0, 0, 0);
              picker.$emit('pick', [start, end]);
            }
          },  {
            text: '最近一个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
              start.setHours(0, 0, 0, 0);
              end.setHours(0, 0, 0, 0);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近三个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
              start.setHours(0, 0, 0, 0);
              end.setHours(0, 0, 0, 0);
              picker.$emit('pick', [start, end]);
            }
          }, {
            text: '最近一年',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 365);
              start.setHours(0, 0, 0, 0);
              end.setHours(0, 0, 0, 0);
              picker.$emit('pick', [start, end]);
            }
          }]
        },
        allChallenges: [],
        activeIndex: '4',
        challengeMap: {},
        challenges: [],
        playerDamages: {},
        totalDamage: {},
        containTailAndContinue: true,
        globalTableData: [],
        playerData: {
            damage: [
                
            ],
        },
        colorList: ['#c23531','#2f4554', '#61a0a8', '#d48265', '#91c7ae','#749f83',  '#ca8622', '#bda29a','#6e7074', '#546570', '#c4ccd3'],                
        challengeChart: null,
        bossDmgChart: null,
        missChart: null,
        lastChart: null,
        bossBloodChart: null,
        totalTimeChart: null,
        bossHitChart: null,
        personalProgressChart: null,
        personalTimeChart: null,
        totalDamageChart: null,
        isLoading: true,
        selectingTab: "table",
        selectingQQid: parseInt(qqid)
    },
    mounted() {
        this.bossDmgChart = echarts.init(document.getElementById("bossDmgChart"));
        this.challengeChart = echarts.init(document.getElementById("challengeChart"));
        this.sumDmgChart = echarts.init(document.getElementById("sumDmgChart"));
        this.missChart = echarts.init(document.getElementById("missChart"));
        this.lastChart = echarts.init(document.getElementById("lastChart"));
        this.bossBloodChart = echarts.init(document.getElementById("bossBloodChart"));
        this.totalTimeChart = echarts.init(document.getElementById("totalTimeChart"));
        this.bossHitChart = echarts.init(document.getElementById("bossHitChart"));
        this.personalProgressChart = echarts.init(document.getElementById("personalProgressChart"));
        this.personalTimeChart = echarts.init(document.getElementById("personalTimeChart"));
        this.totalDamageChart = echarts.init(document.getElementById("totalDamageChart"));
        this.selectingTab = "total";
        this.fetchData();
    },
    watch: {
        containTailAndContinue: function() {
            this.init();
        },
        selectingQQid: function() {
            this.initChart(this.playerDamage(this.selectingQQid).bossDamageList);
            this.initPlayerData();
        },
        selectingTab: function() {
            this.init();
            setTimeout("vm.resizeAll()", 100);
        },
        range: function() {
            this.refreshData();
            this.init();
        },
    },

    methods: {
        // tools function
        sum: (iterable) => {
            let sum = 0;
            iterable.forEach(v => sum += v);
            return sum;
        },
        formatTo2: (num) => { return (num >= 10) ?  num.toString() : '0' + num.toString() },

        fetchData: function() {
            const that = this;
            axios.get('../api/').then(res=> {
                if (res.data.code != 0) {
                    that.$alert(res.data.message, '获取记录失败');
                    that.isLoading = false;
                    return;
                }
                that.allChallenges = res.data.challenges;
                that.members = res.data.members;
                if (that.members.filter((elem) => {return elem.qqid == that.selectingQQid}).length == 0) {
                    that.selectingQQid = that.members[0].qqid;
                }
                that.refreshData();
            }).catch(function (error) {
                that.$alert(error, '获取数据失败，请联系维护人员');
                that.isLoading = false;
                console.error(error);
                console.error(error.stack);
            });
        },

        filtedChallenge: function() {
            if (!this.range) return this.allChallenges;
            const leftRange = this.range[0].getTime() / 1000 + 18000;
            const rightRange = this.range[1].getTime() / 1000 + 18000 + 86400;
            return this.allChallenges.filter((elem) => {return elem.challenge_time <= rightRange && elem.challenge_time >= leftRange});
        },

        refreshData: function() {
            this.challenges = this.filtedChallenge();
            this.challengeMap = {};
            for (let challenge of this.challenges) {
                let arr = this.challengeMap[challenge.qqid];
                if (arr == undefined) {
                    arr = [];
                    this.challengeMap[challenge.qqid] = arr;
                }
                arr.push(challenge);
            }
            for (let member of this.members) {
                member.challenges = this.challengeMap[member.qqid];
            }
            this.sortAndDivide();
            this.init();
            this.isLoading = false;
        },

        init: function() {
            this.initTotalDamage();
            this.initPlayerDamage();
            this.initGlobalTableData();
            this.initPlayerData();
            if (this.selectingTab === 'total') {
                this.initChart(this.totalDamage.bossDamageList);
            }
            else if (this.selectingTab === 'channel') {
                this.initChart(this.totalDamage.bossDamageList);
            }
            else {
                this.initChart(this.playerDamage(this.selectingQQid).bossDamageList);
            }
        },
        // function for init
        initChart: function(bossDamageList) {
            let temp = this.bossAverageDamageForChart(bossDamageList, this.containTailAndContinue);
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
                yAxis: {
                    axisLabel: {
                        formatter: numberFormatter
                    }
                },
                series: [{
                    name: '伤害',
                    type: 'bar',
                    data: temp[1],
                    itemStyle: {
                        color: (params) => {
                            let bossId = parseInt(temp[0][params.dataIndex][0]) - 1;
                            return this.colorList[bossId];
                        },
                    }
                }]
            }

            let temp2 = this.bossChallengeCountForChart(bossDamageList, true);
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
                            let bossId = parseInt(temp2[params.dataIndex].name[0]) - 1;
                            return this.colorList[bossId];
                        }
                    }
                }]
            }
            let temp3 = this.bossSumDamageForChart(bossDamageList);
            let option3 = {
                title: {
                    text: 'Boss 总伤害'
                },
                tooltip: {},
                legend: {
                    data: ['伤害']
                },
                xAxis: {
                    data: temp3[0]
                },
                yAxis: {
                    axisLabel: {
                        formatter: numberFormatter
                    }
                },
                series: [{
                    name: '伤害',
                    type: 'bar',
                    data: temp3[1],
                    itemStyle: {
                        color: (params) => {
                            let bossId = parseInt(temp3[0][params.dataIndex][0]) - 1;
                            return this.colorList[bossId];
                        },
                    }
                }]
            }
            let temp4 = this.bossMissForChart(this.globalTableData);
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
            let temp5 = this.bossLastForChart();
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
            let temp6 = this.bossBloodForChart();
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
                                    return (new Date(params.value)).toLocaleString(options = { timeZone: 'asia/shanghai' });
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
                        return `${(new Date(ts)).toLocaleString(options = { timeZone: 'asia/shanghai' })}<br />${series.marker}${(matched && matched.label) + "<br />" || ""}血量：${value.toLocaleString()}`
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
                        formatter: numberFormatter
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
            let temp7 = this.timeForChart(this.challenges);
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
            let temp8 = this.bossPlayerHitCountForChart();
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
            let temp9 = this.membersDamageForChart(this.globalTableData);
            let option9 = {
                title: {
                    text: '成员伤害统计'
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'cross',
                        crossStyle: {
                            color: '#999'
                        }
                    }
                },
                toolbox: {
                    feature: {
                        dataView: {show: true, readOnly: false},
                        magicType: {show: true, type: ['line', 'bar']},
                        restore: {show: true},
                        saveAsImage: {show: true}
                    }
                },
                legend: {
                    data: ['总伤害', '刀均伤害']
                },
                xAxis: [
                    {
                        type: 'category',
                        data: temp9[0],
                        axisPointer: {
                            type: 'shadow'
                        },
                        axisLabel: {
                            interval: 0,
                            rotate: 45
                        },
                        boundaryGap: true,
                    }
                ],
                yAxis: [
                    {
                        type: 'value',
                        name: '总伤害',
                        axisLabel: {
                            formatter: numberFormatter
                        }
                    },
                    {
                        type: 'value',
                        name: '刀均伤害',
                        axisLabel: {
                            formatter: numberFormatter
                        }
                    }
                ],
                series: [
                    {
                        name: '总伤害',
                        type: 'bar',
                        data: temp9[1]
                    },
                    {
                        name: '刀均伤害',
                        type: 'bar',
                        yAxisIndex: 1,
                        data: temp9[2]
                    }
                ]
            };


            this.bossDmgChart.setOption(option);
            this.challengeChart.setOption(option2);
            this.sumDmgChart.setOption(option3);
            this.missChart.setOption(option4);
            this.lastChart.setOption(option5);
            try{
                // 这里有时会出现一个错误，原因未知
                this.bossBloodChart.setOption(option6);
            }catch(e){console.error(e)}
            this.totalTimeChart.setOption(option7);
            this.bossHitChart.setOption(option8);
            this.totalDamageChart.setOption(option9);
        },

        resizeAll: function() {
            this.sumDmgChart.resize();
            this.missChart.resize();
            this.lastChart.resize();
            this.bossBloodChart.resize();
            this.totalTimeChart.resize();
            this.personalProgressChart.resize();
            this.personalTimeChart.resize();
            this.bossHitChart.resize();
            this.totalDamageChart.resize();
        },

        initPlayerData: function() {
            let max = 0, min = 2147483647, s = [0, 0, 0], c = [0, 0, 0];
            let pchallenge = this.challengeMap[this.selectingQQid];
            if (pchallenge != undefined) {
                for (let date in pchallenge) {
                    let clist = pchallenge[date];
                    let dmglist = []
                    for (let i = 0; i < clist.length; i++) {
                        let damage = 0;
                        if (clist[i].health_ramain != 0) {
                            damage = clist[i].damage;
                        } 
                        else if (clist[i+1] && clist[i+1].is_continue) {
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
                this.playerData.damage = [
                    {label: '最高单次伤害', value: max},
                    {label: '最低单次伤害', value: min},
                    {label: '伤害最高刀均伤害', value: Math.floor(s[0] / c[0])},
                    {label: '伤害次高刀均伤害', value: Math.floor(s[1] / c[1])},
                    {label: '伤害最低刀均伤害', value: Math.floor(s[2] / c[2])}
                ]
            } else {
                this.playerData.damage = [
                    {label: '最高单次伤害', value: 0},
                    {label: '最低单次伤害', value: 0},
                    {label: '伤害最高刀均伤害', value: 0},
                    {label: '伤害次高刀均伤害', value: 0},
                    {label: '伤害最低刀均伤害', value: 0}
                ]
            }
            const playerChalls = this.challenges.filter(c => c.qqid == this.selectingQQid);
            const param1 = this.timeForChart(playerChalls);
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
            const param2 = this.dayDamageForChart(playerChalls);
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
                    axisLabel: {
                        formatter: numberFormatter
                    }
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

            this.personalTimeChart.setOption(option1)
            this.personalProgressChart.setOption(option2)

        },

        initTotalDamage: function() {
            this.totalDamage = [];
            let bossDamageList = {};
            let result = {normalDamage: [], continueDamage: [], tailDamage: [], count: 0, countContinue: 0, countTail: 0};
            for (let challenge of this.challenges) {
                let dict = bossDamageList[challenge.boss_num];
                if (dict == undefined) {
                    dict = {normalDamage: [], continueDamage: [], tailDamage: [], count: 0, countContinue: 0, countTail: 0}
                    bossDamageList[challenge.boss_num] = dict;
                }
                let damage = challenge.damage;
                if (challenge.health_ramain == 0) {
                    result.tailDamage.push(damage);
                    result.countTail++;
                    dict.tailDamage.push(damage);
                    dict.countTail++;
                    continue;
                }
                if (challenge.is_continue) {
                    result.continueDamage.push(damage);
                    result.countContinue++;
                    dict.continueDamage.push(damage);
                    dict.countContinue++;
                    continue;
                }
                result.normalDamage.push(damage);
                result.count++;
                dict.normalDamage.push(damage);
                dict.count++;
            }
            result.bossDamageList = bossDamageList;
            this.totalDamage = result;
        },

        initPlayerDamage: function () {
            for (const elem of this.members) {
                const playerQQid = elem.qqid;
                let challenges = this.challengeMap[playerQQid];
                let bossDamageList = {};
                let result = {normalDamage: [], continueDamage: [], tailDamage: [], count: 0, countContinue: 0, countTail: 0};
                for (let day in challenges) {
                    for (let challenge of challenges[day]) {
                        let dict = bossDamageList[challenge.boss_num];
                        if (dict == undefined) {
                            dict = {normalDamage: [], continueDamage: [], tailDamage: [], count: 0, countContinue: 0, countTail: 0}
                            bossDamageList[challenge.boss_num] = dict;
                        }
                        let damage = challenge.damage;
                        if (challenge.health_ramain == 0) {
                            result.tailDamage.push(damage);
                            result.countTail++;
                            dict.tailDamage.push(damage);
                            dict.countTail++;
                            continue;
                        }
                        if (challenge.is_continue) {
                            result.continueDamage.push(damage);
                            result.countContinue++;
                            dict.continueDamage.push(damage);
                            dict.countContinue++;
                            continue;
                        }
                        result.normalDamage.push(damage);
                        result.count++;
                        dict.normalDamage.push(damage);
                        dict.count++;
                    }
                }
                result.bossDamageList = bossDamageList;
                this.playerDamages[playerQQid] = result;
            }
        },

        initGlobalTableData: function () {
            this.globalTableData = [];
            for (const member of this.members) {
                const sum = this.totalSumDamage();
                const pdmg = this.playerDamage(member.qqid);
                const playerSum = this.playerSumDamage(member.qqid);
                const tempAvgDmg = this.playerAverageDamage(member.qqid, this.containTailAndContinue);
                const tempSumDmgRate = (100 * playerSum / sum);
                let dict = {
                    qqid: member.qqid,
                    nickname: member.nickname,
                    count: pdmg.count + pdmg.countContinue / 2 + pdmg.countTail / 2,
                    countContinue: pdmg.countContinue,
                    countTail: pdmg.countTail,
                    avgDmg: isNaN(tempAvgDmg) ? 0 : tempAvgDmg,
                    sumDmg: playerSum,
                    sumDmgRate: isNaN(tempSumDmgRate) ? '--' : tempSumDmgRate.toFixed(2) + '%'
                }
                this.globalTableData.push(dict);
            }
        },

        tsToDay: function (ts) {
            // 减去5点
            let date = new Date((ts - 18000) * 1000);
            return date.getFullYear() + '-' + this.formatTo2(date.getMonth() + 1) + '-' + this.formatTo2(date.getDate());
        },
        sortChallengeByTime: function(c1, c2) {
            return c1.challenge_time - c2.challenge_time;
        },
        sortAndDivide: function() {
            for (let m of this.members) {
                let detail = {};
                let challenges = m.challenges;
                if (!challenges) {
                    continue;
                }
                for (let challenge of challenges) {
                    if (detail[this.tsToDay(challenge.challenge_time)] == undefined) {
                        detail[this.tsToDay(challenge.challenge_time)] = [];
                    }
                    detail[this.tsToDay(challenge.challenge_time)].push(challenge);
                }
                for (let key in detail) {
                    detail[key].sort(this.sortChallengeByTime);
                }
                m.challenges = detail;
                this.challengeMap[m.qqid] = detail;
            }
        },

        totalAverageDamage: function(containTailAndContinue = false) {
            return this.averageDamage(this.totalDamage, containTailAndContinue);
        },
        playerAverageDamage: function(playerQQid, containTailAndContinue = false) {
            return this.averageDamage(this.playerDamage(playerQQid), containTailAndContinue);
        },

        bossAverageDamageForChart: function(bossDamageList, containTailAndContinue = false) {
            let l1 = [], l2 = [];
            for (let index in bossDamageList) {
                let damage = bossDamageList[index];
                let ret = this.averageDamage(damage, containTailAndContinue);
                if (!isNaN(ret)) {
                    l1.push(index + "号Boss");
                    l2.push(ret);
                }
            }
            return [l1, l2];
        },
        bossMissForChart: function(globalTableData) {
            const counts = globalTableData.map(elem => elem.count);
            const names = globalTableData.map(elem => elem.nickname);
            return [names, counts];
        },
        bossLastForChart: function() {
            const map = {};
            for (const i in this.challenges) {
                if (this.challenges[i].is_continue) {
                    const name = this.getPlayer(this.challenges[i].qqid).nickname;
                    if (name in map)
                        map[name] += 1;
                    else
                        map[name] = 1;
                }
            }
            return Object.keys(map).map(name => ({name: name, value: map[name]}));
        },
        bossBloodForChart: function() {
            const challs = this.challenges.sort((a, b) => a.challenge_time - b.challenge_time);
            let bosses = [];
            let nowBoss, lastPosition, lastCircle;
            for (const i in challs) {
                if (nowBoss === undefined)
                    nowBoss = challs[i].boss_num;
                if (lastPosition === undefined)
                    lastPosition = challs[i].challenge_time * 1000;
                if (lastCircle === undefined)
                    lastCircle = challs[i].cycle;
                if (challs[i].boss_num !== nowBoss) {
                    const time = challs[i].challenge_time * 1000;
                    bosses.push({
                        gte: lastPosition,
                        lt: time,
                        color: this.colorList[nowBoss - 1],
                        label: `${lastCircle}周目${nowBoss}王`
                    });
                    nowBoss = challs[i].boss_num;
                    lastPosition = time;
                    lastCircle = challs[i].cycle;
                }
            }
            if (nowBoss && lastPosition) {
                bosses.push({
                    gte: lastPosition,
                    color: this.colorList[nowBoss - 1],
                    label: `${lastCircle}周目${nowBoss}王`
                });
            }
            return [challs.map(c => [c.challenge_time * 1000, c.health_ramain]), bosses];
        },
        bossSumDamageForChart: function(bossDamageList) {
            let l1 = [], l2 = [];
            for (let index in bossDamageList) {
                let damage = bossDamageList[index];
                let ret = this.sumDamage(damage);
                if (!isNaN(ret)) {
                    l1.push(index + "号Boss");
                    l2.push(ret);
                }
            }
            return [l1, l2];
        },
        bossChallengeCountForChart: function(bossDamageList, containTailAndContinue = false) {
            let l1 = []
            for (let index in bossDamageList) {
                let damage = bossDamageList[index];
                let ret = damage.count + (containTailAndContinue ? (damage.countContinue + damage.countTail) / 2 : 0);
                if (ret != 0) l1.push({name: index + "号Boss", value: ret});
            }
            return l1;
        },
        bossPlayerHitCountForChart: function() {
            const names = [], counter = {};
            const hanzi = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
            const maxBossNum = Math.max.apply(Math, [0, ...this.challenges.map(c => c.boss_num)]);
            const bosses = [...Array(maxBossNum || 0).keys()].map(k => `${k in hanzi ? hanzi[k] : k}王`).reverse()

            this.challenges.forEach(c => {
                const boss = c.boss_num;
                const name = this.getPlayer(c.qqid).nickname;
                if (!(boss in counter)) {
                    counter[boss] = {}
                }
                const bossCount = counter[boss];
                if (!(name in bossCount)) {
                    bossCount[name] = 0
                }
                const isFull = c.health_ramain && !c.is_continue;
                bossCount[name] += isFull ? 1 : 0.5;
            })
            const result = [];
            const getNicknameIndex = name => {
                if (!names.includes(name))
                    names.push(name)
                return names.findIndex(n => n === name);
            }
            const getBossIndex = num => maxBossNum - parseInt(num);
            Object.keys(counter).forEach(num => {
                Object.keys(counter[num]).forEach(name => {
                    result.push([
                        getBossIndex(num),
                        getNicknameIndex(name),
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
        timeForChart: function(challenges) {
            const time = {};
            [...Array(24).keys()].forEach(i => time[i] = 0);
            for (const i in challenges) {
                const t = new Date(challenges[i].challenge_time * 1000);
                time[t.getHours()] += 1;
            }
            return Object.values(time);
        },
        dayDamageForChart: function(challenges) {
            const dates = {};
            challenges.forEach(c => {
                const date = this.tsToDay(c.challenge_time);
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

        membersDamageForChart: function(globalTableData) {
            const data = globalTableData.sort((a, b) => b.sumDmg - a.sumDmg);
            const full = data.map(elem => elem.sumDmg);
            const average = data.map(elem => elem.avgDmg);
            const names = data.map(elem => elem.nickname);
            return [names, full, average];
        },

        averageDamage: function(damage, containTailAndContinue) {
            let sum = this.sum(damage.normalDamage);
            let count = damage.count;
            if (containTailAndContinue) {
                sum += this.sum(damage.continueDamage) + this.sum(damage.tailDamage);
                count += (damage.countContinue + damage.countTail) / 2;
            }
            return Math.floor(sum / count);
        },

        totalSumDamage: function() {
            return this.sumDamage(this.totalDamage);
        },
        playerSumDamage: function(playerQQid) {
            return this.sumDamage(this.playerDamage(playerQQid));
        },
        sumDamage: function(damage) {
            return this.sum(damage.normalDamage) + this.sum(damage.continueDamage) + this.sum(damage.tailDamage);
        },

        challengeCount: function(damage, containTailAndContinue) {
            return damage.count + (containTailAndContinue ? (damage.countTail + damage.countContinue) / 2 : 0);
        },

        getPlayer: function(qqid) {
            return this.members.find(o => o.qqid === qqid) || {nickname:'未加入',qqid:qqid,sl:null};
        },

        playerDamage: function(playerQQid) {
            return this.playerDamages[playerQQid];
        },
        getToday: function () {
            let d = new Date();
            d -= 18000000;
            d = new Date(d).setHours(0, 0, 0, 0);
            return d;
        },
    },
    delimiters: ['[[', ']]'],
})