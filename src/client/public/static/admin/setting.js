var vm = new Vue({
    el: '#app',
    data: {
        setting: {},
        hide_jjckey: 0,
        activeNames: [],
        bossSetting: false,
    },
    mounted() {
        var thisvue = this;
        axios.get(api_path).then(function (res) {
            if (res.data.code == 0) {
                thisvue.setting = res.data.settings;
            } else {
                alert(res.data.message);
            }
        }).catch(function (error) {
            alert(error);
        });
    },
    methods: {
        update: function (event) {
            this.setting.web_mode_hint = false;
            axios.put(
                api_path,
                this.setting,
            ).then(function (res) {
                if (res.data.code == 0) {
                    alert('设置成功，重启机器人后生效');
                } else {
                    alert('设置失败：' + res.data.message);
                }
            }).catch(function (error) {
                alert(error);
            });
        },
        switch_levels: function (area) {
            if (this.setting.boss[area].length <= 3) {
                this.setting.boss[area].push([0, 0, 0, 0, 0]);
            } else {
                this.setting.boss[area].pop();
            }
        },
        comfirm_change_clan_mode: function (event) {
            this.$alert('修改模式后，公会战数据会重置。请不要在公会战期间修改！', '警告', {
                confirmButtonText: '知道了',
                type: 'warning',
            });
        },
    },
    delimiters: ['[[', ']]'],
})