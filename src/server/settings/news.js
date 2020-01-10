function Confirm() {
    var t = $("#setting").serializeArray();
    var formData = {};
    $.each(t, function () {
        formData[this.name] = this.value;
    });
    formData["news_jp_official"] = formData["news_jp_official"] == "on";
    formData["news_jp_twitter"] = formData["news_jp_twitter"] == "on";
    formData["news_tw_official"] = formData["news_tw_official"] == "on";
    formData["news_tw_facebook"] = formData["news_tw_facebook"] == "on";
    formData["news_cn_official"] = formData["news_cn_official"] == "on";
    formData["news_cn_bilibili"] = formData["news_cn_bilibili"] == "on";
    formData["calender_on"] = formData["calender_on"] == "on";
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
    var text = JSON.stringify({ version: 3108, settings: formData });
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

function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) { return pair[1]; }
    }
    return (false);
}

$(document).ready(function () {
    var form_old = getQueryVariable("form");
    if (form_old) {
        $("#top").html("<p>已加载当前的设置</p>");
        let t = decodeURIComponent(form_old);
        let form = JSON.parse(t);
        $("[name=news_jp_official]").prop("checked", form["news_jp_official"]);
        $("[name=news_jp_twitter]").prop("checked", form["news_jp_twitter"]);
        $("[name=news_tw_official]").prop("checked", form["news_tw_official"]);
        $("[name=news_tw_facebook]").prop("checked", form["news_tw_facebook"]);
        $("[name=news_cn_official]").prop("checked", form["news_cn_official"]);
        $("[name=news_cn_bilibili]").prop("checked", form["news_cn_bilibili"]);
        $("[name=news_interval_minutes]").val(form["news_interval_minutes"]);
        $("[name=calender_on]").prop("checked", form["calender_on"]);
        $("[name=calender_region]").val(form["calender_region"]);
        $("[name=calender_time]").val(form["calender_time"]);
        $("[name=notify_groups]").val(form["notify_groups"].join("\n"));
        $("[name=notify_privates]").val(form["notify_privates"].join("\n"));
        if ($("[name=calender_on]").is(":checked")) {
            $("[name=calender_region]").prop("disabled", false);
            $("[name=calender_time]").prop("disabled", false);
        } else {
            $("[name=calender_region]").prop("disabled", true);
            $("[name=calender_time]").prop("disabled", true);
        }
    }
    $("[name=calender_on]").change(function () {
        if ($("[name=calender_on]").is(":checked")) {
            $("[name=calender_region]").prop("disabled", false);
            $("[name=calender_time]").prop("disabled", false);
        } else {
            $("[name=calender_region]").prop("disabled", true);
            $("[name=calender_time]").prop("disabled", true);
        }
    });
});
