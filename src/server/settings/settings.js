function Confirm() {
    var t = $("#setting").serializeArray();
    var formData = {};
    $.each(t, function () {
        formData[this.name] = this.value;
    });
    if (formData["super-admin"].search(/^\d{5,10}(?: \d{5,10})*$/)) {
        alert("请填写正确QQ号");
        return
    }
    formData["super-admin"] = formData["super-admin"].split(" ").map(Number);
    if (formData["black-list"].search(/^(?:\d{5,10}(?: \d{5,10})*)?$/)) {
        alert("请填写正确QQ号");
        return
    }
    formData["black-list"] = formData["black-list"].split(" ").map(Number);
    if (formData["update-time"] == "") {
        alert("请填写自动更新时间");
        return
    }
    formData["setting-restrict"] = parseInt(formData["setting-restrict"]);
    formData["auto_update"] = formData["auto_update"] == "on";
    formData["gacha_on"] = formData["gacha_on"] == "on";
    formData["preffix_on"] = formData["preffix_on"] == "on";
    formData["gacha_private_on"] = formData["gacha_private_on"] == "on";
    formData["zht_in"] = formData["zht_in"] == "on";
    formData["zht_out"] = formData["zht_out"] == "on";
    var text = JSON.stringify({ version: 2999, settings: formData });
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
    $("#auto_update").change(function () {
        if ($("#auto_update").is(":checked")) {
            $("#update_input").prop("disabled", false);
        } else {
            $("#update_input").prop("disabled", true);
        }
        $("#restart").html("（重启后生效）")
    });
    $("#preffix_on").change(function () {
        if ($("#preffix_on").is(":checked")) {
            $("#preffix_input").prop("disabled", false);
        } else {
            $("#preffix_input").prop("disabled", true);
        }
    });
    $("#zht_out").change(function () {
        if ($("#zht_out").is(":checked")) {
            $("#zht_style_input").prop("disabled", false);
        } else {
            $("#zht_style_input").prop("disabled", true);
        }
    });
    var form_old = getQueryVariable("form");
    if (form_old) {
        $("#top").html("<p>已加载当前的设置</p>");
        let t = decodeURIComponent(form_old);
        let form = JSON.parse(t);
        $("[name=super-admin]").val(form["super-admin"].join(" "));
        $("[name=black-list]").val(form["black-list"].join(" "));
        $("[name=setting-restrict]").val(form["setting-restrict"]);
        $("[name=auto_update]").prop("checked", form["auto_update"]);
        $("[name=update-time]").val(form["update-time"]);
        $("[name=show_jjc_solution]").val(form["show_jjc_solution"]);
        $("[name=gacha_on]").prop("checked", form["gacha_on"]);
        $("[name=gacha_private_on]").prop("checked", form["gacha_private_on"]);
        $("[name=preffix_on]").prop("checked", form["preffix_on"]);
        $("[name=preffix_string]").val(form["preffix_string"]);
        $("[name=zht_in]").prop("checked", form["zht_in"]);
        $("[name=zht_out]").prop("checked", form["zht_out"]);
        $("[name=zht_out_style]").val(form["zht_out_style"]);

    }
});