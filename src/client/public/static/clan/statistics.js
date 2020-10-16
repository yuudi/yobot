if (!Object.defineProperty) {
    alert('浏览器版本过低');
}
var vm = new Vue({
    el: '#app',
    data: {
        progressData: [],
        members: [],
        tailsData: [],
        tailsDataVisible: false,
        group_name: null,
        reportDate: null,
        activeIndex: '4',
        multipleSelection: [],
        sendRemindVisible: false,
        send_via_private: false,
        dropMemberVisible: false,
        today: 0,
    },
    methods: {
        handleTitleSelect(key, keyPath) {
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
    }
})

