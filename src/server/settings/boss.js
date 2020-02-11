
function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) { return pair[1]; }
    }
    return (false);
}

var clipboard = new ClipboardJS('.btn');
clipboard.on('success', function (e) {
    alert("已复制，请在群里粘贴。");
});

clipboard.on('error', function (e) {
    alert("复制失败，请手动复制！");
});
var boss_health = {
    jp: [
        [6000000, 8000000, 10000000, 12000000, 15000000],
        [6000000, 8000000, 10000000, 12000000, 15000000],
        [7000000, 9000000, 13000000, 14000000, 17000000],
    ],
    tw: [
        [6000000, 8000000, 10000000, 12000000, 15000000],
        [6000000, 8000000, 10000000, 12000000, 15000000],
        [6000000, 8000000, 10000000, 12000000, 15000000],
    ],
    cn: [
        [6000000, 8000000, 10000000, 12000000, 20000000],
        [6000000, 8000000, 10000000, 12000000, 20000000],
        [6000000, 8000000, 10000000, 12000000, 20000000],
    ],
    eff: [
        [1.2, 1.2, 1.3, 1.4, 1.5],
        [1.6, 1.6, 1.8, 1.9, 2.0],
        [2.0, 2.0, 2.4, 2.4, 2.6],
    ],
};
let q = getQueryVariable("form");
if (q) {
    boss_health = JSON.parse(decodeURIComponent(q));
}
var vm = new Vue({
    el: '#boss',
    data: {
        key_name: {
            jp: "日服",
            tw: "台服",
            cn: "国服",
            eff: "得分系数"
        },
        boss_health: boss_health,
        setting_code: { code: "设置码" },
    },
    methods: {
        confirm: function (enevt) {
            let thisvue = this;
            let text = JSON.stringify({ version: 3115, settings: this.boss_health });
            let bodyFormData = new FormData();
            bodyFormData.set('raw', text);
            axios.post(
                "http://io.yobot.monster/3.0.0/settings/coding.php",
                data = bodyFormData,
                headers = { 'Content-Type': 'multipart/form-data' },
                responseType = "text",
            ).then(function (res) {
                thisvue.setting_code.code = "设置码" + res.data;
            })
        }
    },
});