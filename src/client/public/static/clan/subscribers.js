var vm = new Vue({
    el: '#app',
    data: {
        bosstag: ['挂树', '预约1', '预约2', '预约3', '预约4', '预约5'],
        subscribers: [
            [], [], [], [], [], [],
        ],
        members: [],
        group_name: null,
        activeIndex: '2',
    },
    mounted() {
        var thisvue = this;
        axios.post('../api/', {
            action: 'get_subscribers',
            csrf_token: csrf_token,
        }).then(function (res) {
            if (res.data.code == 0) {
                for (sub of res.data.subscribers) {
                    thisvue.subscribers[sub.boss].push(sub);
                }
                thisvue.group_name = res.data.group_name;
                document.title = res.data.group_name + ' - 公会战设置';
            } else {
                thisvue.$alert(res.data.message, '获取数据失败');
            }
        }).catch(function (error) {
            thisvue.$alert(error, '获取数据失败');
        });
        axios.post('../api/', {
            action: 'get_member_list',
            csrf_token: csrf_token,
        }).then(function (res) {
            if (res.data.code == 0) {
                thisvue.members = res.data.members;
            } else {
                thisvue.$alert(res.data.message, '获取成员失败');
            }
        }).catch(function (error) {
            thisvue.$alert(error, '获取成员失败');
        });
    },
    methods: {
        find_name: function (qqid) {
            for (m of this.members) {
                if (m.qqid == qqid) {
                    return m.nickname;
                }
            };
            return qqid;
        },
        get_time_delta: function (time) {
            var dateBegin = new Date(time);
            var dateEnd = new Date();
            var dateDiff = dateEnd.getTime() - dateBegin.getTime();
            if (dateDiff >= 86400000) {
                return '24小时+'
            }
            var leave1 = dateDiff % (24 * 3600 * 1000);
            var hours = Math.floor(leave1 / (3600 * 1000));
            var leave2 = leave1 % (3600 * 1000);
            var minutes = Math.floor(leave2 / (60 * 1000));
            return (hours + "小时" + minutes + "分钟");
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