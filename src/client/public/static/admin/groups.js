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
        delete_group: function (scope) {
            var thisvue = this;
            thisvue.$confirm('是否删除' + scope.row.group_name, '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'danger'
            }).then(() => {
                axios.post(api_path, {
                    action: 'drop_group',
                    csrf_token: csrf_token,
                    group_id: scope.row.group_id,
                }).then(function (res) {
                    if (res.data.code == 0) {
                        thisvue.$message({
                            message: '删除成功',
                            type: 'success',
                        });
                    } else {
                        thisvue.$message.error('删除失败' + res.data.message);
                    }
                }).catch(function (error) {
                    thisvue.$message.error(error);
                });
            }).catch(() => {
                thisvue.$message({
                    type: 'info',
                    message: '已取消删除'
                });
            });
        },
    },
    delimiters: ['[[', ']]'],
})