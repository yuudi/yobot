var vm = new Vue({
    el: '#sending',
    data: {
        message_type: 'group',
        user_id: 0,
        group_id: 0,
        message: '',
    },
    mounted() {
        if (localStorage.message_type) {
            this.message_type = localStorage.message_type;
            this.user_id = localStorage.user_id;
            this.group_id = localStorage.group_id;
            this.message = localStorage.message;
        }
    },
    watch: {
        message_type: function (newmessage_type) {
            localStorage.message_type = newmessage_type;
        },
        user_id: function (newuser_id) {
            localStorage.user_id = newuser_id;
        },
        group_id: function (newgroup_id) {
            localStorage.group_id = newgroup_id;
        },
        message: function (newmessage) {
            localStorage.message = newmessage;
        },
    },
    methods: {
        send_msg: function (event) {
            axios.post(
                api_path,
                this.$data,
            ).then(function (res) {
                if (res.data.code == 0) {
                    alert('已发送');
                } else {
                    alert('发送失败：' + res.data.message);
                }
            }).catch(function (error) {
                alert(error);
            });
        },
    },
    delimiters: ['[[', ']]'],
})