var vm = new Vue({
    el: '#app',
    data: {
        userData: [],
        authtype: [{
            value: 100,
            label: '成员',
        }, {
            value: 10,
            label: '公会战管理员',
        }, {
            value: 2,
            label: '机器人管理员',
        }, {
            value: 1,
            label: '主人',
        }],
    },
    mounted() {
        this.refresh();
    },
    methods: {
        datestr: function (ts) {
            if (ts == 0) {
                return '-';
            }
            var nd = new Date();
            nd.setTime(ts * 1000);
            return nd.toLocaleString('chinese', { hour12: false });
        },
        refresh: function (event) {
            var thisvue = this;
            axios.post(api_path, {
                action: 'get_data',
                csrf_token: csrf_token,
            }).then(function (res) {
                if (res.data.code == 0) {
                    thisvue.userData = res.data.data;
                } else {
                    thisvue.$alert(res.data.message, '加载数据错误');
                }
            }).catch(function (error) {
                thisvue.$alert(error, '加载数据错误');
            });
        },
        modify: function (scope) {
            var thisvue = this;
            axios.post(api_path, {
                action: 'modify_user',
                csrf_token: csrf_token,
                data: {
                    qqid: scope.row.qqid,
                    authority_group: scope.row.authority_group,
                },
            }).then(function (res) {
                if (res.data.code == 0) {
                    thisvue.$message({
                        message: '修改成功',
                        type: 'success',
                    });
                } else {
                    thisvue.$message.error('修改失败' + res.data.message);
                }
            }).catch(function (error) {
                thisvue.$message.error(error);
            });
        },
    },
    delimiters: ['[[', ']]'],
})