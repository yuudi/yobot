if (!Object.defineProperty) {
    alert('浏览器版本过低');
}
var vm = new Vue({
    el: '#app',
    data: {
        activeIndex: null,
        groupData: {},
        battle_id: null,
        data_slot_record_count: [],
        form: {
            game_server: null,
            privacy: {
                allow_guest: false,
                allow_statistics_api: false,
            },
            notify: {
                challenge: false,
                undo: false,
                apply: false,
                cancelapply: false,
                subscribe: false,
                cancelsubscribe: false,
                suspend: false,
                cancelsuspend: false,
                modify: false,
                sl: false,
            },
        },
        switchVisible: false,
        confirmVisible: false,
    },
    mounted() {
        var thisvue = this;
        axios.post('./api/', {
            action: 'get_setting',
            csrf_token: csrf_token,
        }).then(function (res) {
            if (res.data.code == 0) {
                thisvue.groupData = res.data.groupData;
                thisvue.battle_id = res.data.groupData.battle_id;
                thisvue.form.game_server = res.data.groupData.game_server;
                thisvue.form.privacy.allow_guest = Boolean(res.data.privacy & 0x1);
                thisvue.form.privacy.allow_statistics_api = Boolean(res.data.privacy & 0x2);
                document.title = res.data.groupData.group_name + ' - 公会战设置';
                var notify_code = res.data.notification;
                for (key in thisvue.form.notify) {
                    thisvue.form.notify[key] = Boolean(notify_code & 1);
                    notify_code >>= 1;
                }
            } else {
                thisvue.$alert(res.data.message, '加载数据失败');
            }
        }).catch(function (error) {
            thisvue.$alert(error, '加载数据失败');
        });
    },
    methods: {
        submit: function (event) {
            var thisvue = this;
            var privacy = (thisvue.form.privacy.allow_guest * 0x1) + (thisvue.form.privacy.allow_statistics_api * 0x2);
            var notify_code = 0;
            var magnitude = 1;
            for (key in thisvue.form.notify) {
                notify_code += thisvue.form.notify[key] * magnitude;
                magnitude <<= 1;
            }
            axios.post('./api/', {
                action: 'put_setting',
                csrf_token: csrf_token,
                game_server: thisvue.form.game_server,
                privacy: privacy,
                notification: notify_code,
            }).then(function (res) {
                if (res.data.code == 0) {
                    thisvue.$notify({
                        title: '通知',
                        message: '设置成功',
                    });
                } else {
                    thisvue.$alert(res.data.message, '保存设置失败');
                }
            }).catch(function (error) {
                thisvue.$alert(error, '保存设置失败');
            });
        },
        export_data: function (event) {
            window.location = '../statistics/api/';
        },
        call_api: function (payload) {
            var thisvue = this;
            payload.csrf_token = csrf_token;
            axios.post('./api/', payload).then(function (res) {
                if (res.data.code == 0) {
                    thisvue.$notify({
                        title: '通知',
                        message: '成功',
                    });
                } else {
                    thisvue.$alert(res.data.message, '失败');
                }
            }).catch(function (error) {
                thisvue.$alert(error, '失败');
            });
        },
        clear_data_slot: function (event) {
            this.call_api({
                action: 'clear_data_slot',
            });
            this.confirmVisible = false;
        },
        // new_data_slot: function (event) {
        //     this.call_api({
        //         action: 'new_data_slot',
        //     });
        // },
        switch_data_slot: function (event) {
            this.call_api({
                action: 'switch_data_slot',
                battle_id: this.battle_id,
            });
            this.switchVisible = false;
        },
        get_data_slot_record_count: function () {
            if (this.data_slot_record_count.length !== 0) {
                return
            }
            var thisvue = this;
            axios.post('./api/', {
                action: 'get_data_slot_record_count',
                csrf_token: csrf_token,
            }).then(function (res) {
                if (res.data.code == 0) {
                    thisvue.data_slot_record_count = res.data.counts;
                } else {
                    thisvue.$alert(res.data.message, '失败');
                }
            }).catch(function (error) {
                thisvue.$alert(error, '失败');
            });
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