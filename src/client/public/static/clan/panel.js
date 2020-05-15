if (!Object.defineProperty) {
    alert('浏览器版本过低');
}
var vm = new Vue({
    el: '#app',
    data: {
        activeIndex: "1",
        groupData: {},
        bossData: { cycle: 0, full_health: 0, health: 0, num: 0 },
        is_admin: false,
        self_id: 0,
        today_sl: false,
        members: [],
        damage: 0,
        defeat: null,
        behalf: null,
        boss_num: null,
        recordFormVisible: false,
        recordDefeatVisible: false,
        recordBehalfVisible: false,
        lockBossVisible: false,
        subscribe: null,
        message: '',
        subscribeFormVisible: false,
        subscribeCancelVisible: false,
        suspendVisible: false,
        statusFormVisible: false,
        leavePage: false,
    },
    mounted() {
        var thisvue = this;
        axios.post("./api/", {
            action: 'get_data',
            csrf_token: csrf_token,
        }).then(function (res) {
            if (res.data.code == 0) {
                thisvue.groupData = res.data.groupData;
                thisvue.bossData = res.data.bossData;
                thisvue.is_admin = res.data.selfData.is_admin;
                thisvue.self_id = res.data.selfData.user_id;
                thisvue.today_sl = res.data.selfData.today_sl;
                document.title = res.data.groupData.group_name + ' - 公会战';
            } else {
                thisvue.$alert(res.data.message, '加载数据错误');
            }
        }).catch(function (error) {
            thisvue.$alert(error, '加载数据错误');
        });
        axios.post("./api/", {
            action: 'get_member_list',
            csrf_token: csrf_token,
        }).then(function (res) {
            if (res.data.code == 0) {
                thisvue.members = res.data.members;
            } else {
                thisvue.$alert(res.data.message, '获取成员失败');
            }
        }).catch(function (error) {
            thisvue.$alert(error, '获取成员失败');
        });
        this.status_long_polling();
    },
    destroyed: function () {
        this.leavePage = true;
    },
    computed: {
        damageHint: function () {
            if (this.damage < 10000) {
                return '';
            } else if (this.damage < 100000) {
                return '万';
            } else if (this.damage < 1000000) {
                return '十万';
            } else if (this.damage < 10000000) {
                return '百万';
            } else if (this.damage < 100000000) {
                return '千万';
            } else {
                return '`(*>﹏<*)′';
            }
        },
    },
    methods: {
        find_name: function (qqid) {
            for (m of this.members) {
                if (m.qqid == qqid) {
                    return m.nickname;
                }
            };
            return qqid;
        },
        status_long_polling: function () {
            var thisvue = this;
            axios.post("./api/", {
                action: 'update_boss',
                timeout: 30,
                csrf_token: csrf_token,
            }, {
                timeout: 40000,
            }).then(function (res) {
                if (res.data.code == 0) {
                    thisvue.bossData = res.data.bossData;
                    thisvue.status_long_polling();
                    if (res.data.notice) {
                        thisvue.$notify({
                            title: '通知',
                            message: '(' + (new Date()).toLocaleTimeString('chinese', { hour12: false }) + ') ' + res.data.notice,
                            duration: 60000,
                        });
                    }
                } else if (res.data.code == 1) {
                    thisvue.status_long_polling();
                } else {
                    thisvue.$confirm(res.data.message, '刷新boss数据错误', {
                        confirmButtonText: '重试',
                        cancelButtonText: '取消',
                        type: 'warning'
                    }).then(() => {
                        thisvue.status_long_polling();
                    });
                }
            }).catch(function (error) {
                if (thisvue.leavePage) {
                    return;
                }
                thisvue.$confirm(error, '刷新boss错误', {
                    confirmButtonText: '重试',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(() => {
                    thisvue.status_long_polling();
                });
            });
        },
        callapi: function (payload) {
            var thisvue = this;
            payload.csrf_token = csrf_token;
            axios.post("./api/", payload).then(function (res) {
                if (res.data.code == 0) {
                    if (res.data.bossData) {
                        thisvue.bossData = res.data.bossData;
                    }
                    if (res.data.notice) {
                        thisvue.$notify({
                            title: '通知',
                            message: res.data.notice,
                            duration: 60000,
                        });
                    }
                } else {
                    thisvue.$alert(res.data.message, '数据错误');
                }
            }).catch(function (error) {
                thisvue.$alert(error, '数据错误');
            });
        },
        recordselfdamage: function (event) {
            this.callapi({
                action: 'addrecord',
                defeat: false,
                damage: this.damage,
                behalf: null,
                message:this.message,
            });
            this.recordFormVisible = false;
        },
        recordselfdefeat: function (event) {
            this.callapi({
                action: 'addrecord',
                defeat: true,
                behalf: null,
                message:this.message,
            });
            this.recordDefeatVisible = false;
        },
        recorddamage: function (event) {
            this.callapi({
                action: 'addrecord',
                defeat: this.defeat,
                behalf: this.behalf,
                damage: this.damage,
                message:this.message,
            });
            this.recordBehalfVisible = false;
        },
        recordundo: function (event) {
            this.callapi({
                action: 'undo',
            });
        },
        challengeapply: function (appli_type) {
            this.callapi({
                action: 'apply',
                extra_msg:this.message,
                appli_type:appli_type,
            });
            this.lockBossVisible=false;
        },
        cancelapply: function (event) {
            this.callapi({
                action: 'cancelapply',
            });
        },
        addsuspend: function (event) {
            this.callapi({
                action: 'addsubscribe',
                boss_num: 0,
                message: this.message,
            });
            this.suspendVisible=false;
        },
        cancelsuspend: function (event) {
            this.callapi({
                action: 'cancelsubscribe',
                boss_num: 0,
            });
        },
        save_slot: function (event) {
            this.today_sl = !this.today_sl;
            this.callapi({
                action: 'save_slot',
                today: this.today_sl,
            });
        },
        addsubscribe: function (event) {
            this.callapi({
                action: 'addsubscribe',
                boss_num: parseInt(this.subscribe),
                message: this.message,
            });
            this.subscribeFormVisible = false;
        },
        cancelsubscribe: function (event) {
            this.callapi({
                action: 'cancelsubscribe',
                boss_num: parseInt(this.subscribe),
            });
            this.subscribeCancelVisible = false
        },
        startmodify: function (event) {
            if (this.is_admin) {
                this.statusFormVisible = true;
            } else {
                this.$alert('此功能仅公会战管理员可用');
            }
        },
        modify: function (event) {
            this.callapi({
                action: 'modify',
                cycle: this.bossData.cycle,
                boss_num: this.bossData.num,
                health: this.bossData.health,
            });
            this.statusFormVisible = false;
        },
        handleSelect(key, keyPath) {
            this.leavePage = true;
            switch (key) {
                case '2':
                    window.location = './subscribers/';
                    break;
                case '3':
                    window.location = './progress/';
                    break;
                case '4':
                    window.location = './statistics/';
                    break;
                case '5':
                    window.location = `./${this.self_id}/`;
                    break;
            }
        },
    },
    delimiters: ['[[', ']]'],
})