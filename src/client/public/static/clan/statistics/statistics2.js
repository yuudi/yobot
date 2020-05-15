if (!Object.defineProperty) {
    alert('浏览器版本过低');
}
// 这代码很乱，到时候重构一下
var vm = new Vue({
    el: '#app',
    data: {
        members: [],
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
        is_loading: true,
        selecting_tab: "table",
        selecting_qqid: parseInt(qqid)
    },
    mounted() {
        this.boss_dmg_chart = echarts.init(document.getElementById("boss_dmg_chart"));
        this.challenge_chart = echarts.init(document.getElementById("challenge_chart"));
        this.sum_dmg_chart = echarts.init(document.getElementById("sum_dmg_chart"));
        var thisvue = this;
        thisvue.selecting_tab = "total";
        axios.get('../api/').then(res=> {
            if (res.data.code != 0) {
                thisvue.$alert(res.data.message, '获取记录失败');
                thisvue.is_loading = false;
                return;
            }
            thisvue.challenges = res.data.challenges;
            thisvue.members = res.data.members;
            for (let challenge of thisvue.challenges) {
                let arr = thisvue.challenge_map[challenge.qqid];
                if (arr == undefined) {
                    arr = [];
                    thisvue.challenge_map[challenge.qqid] = arr;
                }
                arr.push(challenge);
            }
            for (let member of thisvue.members) {
                member.challenges = thisvue.challenge_map[member.qqid];
            }
            thisvue.sort_and_divide();
            thisvue.init();
            thisvue.is_loading = false;
        // }).catch(function (error) {
        //     thisvue.$alert(error, '获取数据失败');
        //     thisvue.is_loading = false;
        });
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
            setTimeout("vm.sum_dmg_chart.resize()", 100);
        }
    },
    methods: {
        // tools function
        sum: (iterable) => {
            let sum = 0;
            iterable.forEach(v => sum += v);
            return sum;
        },
        format_to2: (num) => { return (num >= 10) ?  num.toString() : '0' + num.toString() },

        init: function() {
            this.__total_damage();
            this.__global_table_data();
            this.init_player_data();
            if (this.selecting_tab == 'total') this.init_chart(this.total_damage.boss_damage_list);
            else this.init_chart(this.player_damage(this.selecting_qqid).boss_damage_list);
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
            this.boss_dmg_chart.setOption(option);
            this.challenge_chart.setOption(option2);
            this.sum_dmg_chart.setOption(option3);
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