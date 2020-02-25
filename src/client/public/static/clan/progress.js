var vm = new Vue({
    el: '#app',
    data: {
        progressData: [],
        members: [],
        group_name: null,
        reportDate: null,
        activeIndex: '3',
    },
    mounted() {
        var thisvue = this;
        axios.all([
            axios.post('../api/', {
                action: 'get_challenge',
                ts: null,
            }),
            axios.post('../api/', {
                action: 'get_member_list'
            }),
        ]).then(axios.spread(function (res, memres) {
            if (res.data.code != 0) {
                thisvue.$alert(res.data.message, '获取记录失败');
                return;
            }
            if (memres.data.code != 0) {
                thisvue.$alert(memres.data.message, '获取成员失败');
                return;
            }
            thisvue.members = memres.data.members;
            thisvue.refresh(res.data.challenges);
        })).catch(function (error) {
            thisvue.$alert(error, '获取数据失败');
        });
    },
    methods: {
        cinfo: function (cha) {
            if (cha == undefined) {
                return '';
            }
            var info = '(' + cha.cycle + '-' + cha.boss_num + ')' + cha.damage.toLocaleString();
            return info;
        },
        arraySpanMethod: function ({ row, column, rowIndex, columnIndex }) {
            if (columnIndex >= 3) {
                if (columnIndex % 2 == 1) {
                    var detail = row.detail[columnIndex - 3];
                    if (detail != undefined && detail.health_ramain != 0) {
                        return [1, 2];
                    }
                } else {
                    var detail = row.detail[columnIndex - 4];
                    if (detail != undefined && detail.health_ramain != 0) {
                        return [0, 0];
                    }
                }
            }
        },
        report_day: function (event) {
            var thisvue = this;
            axios.post('../api/', {
                action: 'get_challenge',
                ts: (thisvue.reportDate.getTime() / 1000) + 43200,
            }).then(function (res) {
                if (res.data.code != 0) {
                    thisvue.$alert(res.data.message, '获取记录失败');
                } else {
                    thisvue.refresh(res.data.challenges);
                }
            }).catch(function (error) {
                thisvue.$alert(error, '获取记录失败');
            })
        },
        refresh: function (challenges) {
            this.progressData = [];
            var thisvue = this;
            var m = { qqid: -1 };
            for (c of challenges) {
                if (m.qqid != c.qqid) {
                    if (m.qqid != -1) {
                        thisvue.progressData.push(m);
                    }
                    m = {
                        qqid: c.qqid,
                        nickname: thisvue.find_name(c.qqid),
                        finished: 0,
                        detail: [],
                    }
                }
                if (c.is_continue) {
                    m.detail[2 * m.finished + 1] = c;
                    m.finished += 1;
                } else {
                    m.detail[2 * m.finished] = c;
                    if (c.health_ramain != 0) {
                        m.finished += 1;
                    }
                }
            }
            if (m.qqid != -1) {
                thisvue.progressData.push(m);
            }
        },
        find_name: function (qqid) {
            for (m of this.members) {
                if (m.qqid == qqid) {
                    return m.nickname;
                }
            };
            return qqid;
        },
        handleSelect(key, keyPath) {
            switch (key) {
                case '1':
                    window.location = '../';
                    break;
                case '2':
                    window.location = '../subscribers/';
                    break;
                case '3':
                    window.location = '../progress/';
                    break;
                case '4':
                    window.location = '../statistics/';
                    break;
                case '5':
                    window.location = `../my/`;
                    break;
            }
        },
    },
    delimiters: ['[[', ']]'],
})