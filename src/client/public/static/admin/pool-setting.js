var vm = new Vue({
    el: '#app',
    data: {
        settings: null,
    },
    mounted() {
        var thisvue = this;
        axios.get(api_path).then(function (res) {
            if (res.data.code == 0) {
                thisvue.settings = res.data.settings;
            } else {
                alert(res.data.message, '加载数据错误');
            }
        }).catch(function (error) {
            alert(error, '加载数据错误');
        });
    },
    methods: {
        addpool: function () {
            let newname = "奖池" + (Object.keys(this.settings.pool).length+1);
            this.$set(this.settings.pool, newname, {
                prop: 0,
                prop_last: 0,
                prefix: "★★★",
                pool: ["请输入内容"],
            });
        },
        update: function () {
            var thisvue = this;
            axios.put(api_path, {
                setting: thisvue.settings,
                csrf_token: csrf_token,
            }).then(function (res) {
                if (res.data.code == 0) {
                    alert('设置成功，重启后生效');
                } else {
                    alert('设置失败：' + res.data.message);
                }
            }).catch(function (error) {
                alert(error);
            });
        },
    },
    delimiters: ['[[', ']]'],
})