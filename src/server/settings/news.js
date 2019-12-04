function Confirm() {
    var t = $("#setting").serializeArray();
    var formData = {};
    $.each(t, function () {
        formData[this.name] = this.value;
    });
    formData["news_jp_official"] = formData["news_jp_official"] == "on";
    formData["news_jp_twitter"] = formData["news_jp_twitter"] == "on";
    if (!/^\d+$/.test(formData["news_interval_minutes"])) {
        alert("请填写正确的间隔");
        return
    }
    formData["news_interval_minutes"] = parseInt(formData["news_interval_minutes"]);
    if (formData["news_interval_minutes"] < 10) {
        alert("时间间隔太小");
        return
    }
    if (formData["notify_groups"] == "") {
        formData["notify_groups"] = [];
    } else {
        if (!/^\d+(\r\n\d+)*$/.test(formData["notify_groups"])) {
            alert("请填写正确的群号");
            return
        }
        formData["notify_groups"] = formData["notify_groups"].split("\r\n").map(function (x) { return parseInt(x); });
    }
    if (formData["notify_privates"] == "") {
        formData["notify_privates"] = [];
    } else {
        if (!/^\d+(\r\n\d+)*$/.test(formData["notify_privates"])) {
            alert("请填写正确的QQ号");
            return
        }
        formData["notify_privates"] = formData["notify_privates"].split("\r\n").map(function (x) { return parseInt(x); });
    }
    var text = JSON.stringify({ version: 3100, settings: formData });
    $.post("1234567"/*this is coding-api address*/, { raw: text }, function (data) {
        $('#pc #setting_code').attr("value", "设置码" + data);
    });
}


function Copy_code() {
    let a = document.forms["pc"]["setting_code"];
    a.select();
    document.execCommand("Copy");
    alert("已复制，请在群里粘贴。");
}

