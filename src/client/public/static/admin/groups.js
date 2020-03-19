var vm = new Vue({
    el: '#app',
    data: {
        groupData: [],
    },
    mounted() {
        this.refresh();
    },
    methods: {
        refresh: function (event) {
            var thisvue = this;
            axios.post(api_path, {
                action: 'get_data',
                csrf_token: csrf_token,
            }).then(function (res) {
                if (res.data.code == 0) {
                    thisvue.groupData = res.data.data;
                } else {
                    thisvue.$alert(res.data.message, '加载数据错误');
                }
            }).catch(function (error) {
                thisvue.$alert(error, '加载数据错误');
            });
        },
    },
    delimiters: ['[[', ']]'],
})