var vm = new Vue({
    el: '#app',
    data: {
        setting: {},
        activeNames: [],
        bossSetting: false,
        domain: '',
        domainApply: false,
        applyName: '',
        loading: false,
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
                {
                    setting: this.setting,
                    csrf_token: csrf_token,
                },
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
        sendApply: function (api) {
            if (this.domain === '') {
                alert('请选择后缀');
                return;
            }
            if (/^[0-9a-z]{1,16}$/.test(this.applyName)) {
                ;
            } else {
                alert('只能包含字母、数字');
                return;
            }
            var thisvue = this;
            this.loading = true;
            axios.get(
                api + '?name=' + thisvue.applyName + thisvue.domain
            ).then(function (res) {
                thisvue.domainApply = false;
                if (res.data.code == 0) {
                    alert('申请成功，请等待1分钟左右解析生效');
                    thisvue.setting.public_address = thisvue.setting.public_address.replace(/\/\/([^:\/]+)/, '//' + thisvue.applyName + thisvue.domain);
                    thisvue.update(null);
                } else if (res.data.code == 1) {
                    alert('申请失败，此域已被占用');
                } else {
                    alert('申请失败，' + res.data.message);
                }
                thisvue.loading = false;
            }).catch(function (error) {
                thisvue.loading = false;
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