var vm = new Vue({
    el: '#app',
    data: {
        setting: {},
        hide_jjckey: 0,
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
            axios.put(
                api_path,
                this.setting,
            ).then(function (res) {
                if (res.data.code == 0) {
                    alert('设置成功');
                } else {
                    alert('设置失败：' + res.data.message);
                }
            }).catch(function (error) {
                alert(error);
            });
        },
        comfirm_change_clan_mode: function (event) {
            this.$alert('修改模式后，公会战数据会重置。请不要在公会战期间修改！', '警告', {
                confirmButtonText: '知道了',
                type: 'warning',
            });
        },
    },
    watch: {
        'setting.public_basepath': function (newpath) {
            if (newpath.charAt(0) !== '/') {
                newpath = '/' + newpath;
            }
            if (newpath.charAt(newpath.length - 1) !== '/') {
                newpath = newpath + '/';
            }
        }
    },
    delimiters: ['[[', ']]'],
})