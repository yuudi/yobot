var vm = new Vue({
    el: '#app',
    data: {
        activeIndex: null,
        groupData: {},
        form: {
            game_server: null,
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
            }
        },
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
                thisvue.form.game_server = res.data.groupData.game_server;
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
        delete_data: function (event) {
            var thisvue = this;
            axios.post('./api/', {
                action: 'restart',
                csrf_token: csrf_token,
            }).then(function (res) {
                if (res.data.code == 0) {
                    thisvue.$notify({
                        title: '通知',
                        message: '删除成功',
                    });
                } else {
                    thisvue.$alert(res.data.message, '删除失败');
                }
            }).catch(function (error) {
                thisvue.$alert(error, '删除失败');
            });
            this.confirmVisible = false;
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