function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) { return pair[1]; }
    }
    return (false);
}

var pool_num = 0;

function pool_content(id, name, prop, prop_last, pref, pool) {
    return '<span class="content" id="'
        + id.toString()
        + '"><h3>奖池'
        + id.toString()
        + '</h3><input type="button" value="删除" class="drop" id="'
        + id.toString()
        + '"><br>名称:<input type="text" id="name" value="'
        + name
        + '" /><br>基本抽概率:<input type="number" id="prop" value="'
        + prop.toString()
        + '" /><br>保底抽概率:<input type="number" id="prop_last" value="'
        + prop_last.toString()
        + '" /><br>前缀:<input type="text" id="pref" value="'
        + pref
        + '" /><br>内容:<br>(每行一个)<br><textarea id="pool" cols="25">'
        + pool
        + '</textarea><br><br></span>';
}

$(document).ready(function () {
    if (pool_old == "") {
        alert("卡池丢失");
    } else {
        let old = JSON.parse(decodeURIComponent(pool_old));
        for (p in old["pool"]) {
            pool_num += 1;
            $("#pools").append(pool_content(pool_num, p, old["pool"][p]["prop"], old["pool"][p]["prop_last"], old["pool"][p]["prefix"], old["pool"][p]["pool"].join("\n")));
        }
        $("#combo").val(old["settings"]["combo"]);
        $("#day_limit").val(old["settings"]["day_limit"]);
        $("#auto_update").prop("checked", old["settings"]["auto_update"]);
        $("#fix_last").prop("checked", !old["settings"]["shuffle"]);
    }
    autosize($('textarea'));

    $("#add").click(function () {
        pool_num += 1;
        $("#pools").append(pool_content(pool_num, "pool" + pool_num.toString(), 0, 0, "", ""));
        autosize($('textarea'));

        $(".drop").click(function () {
            let pool_id = $(this).attr("id");
            $(`.content#${pool_id}`).remove();
        });
    });
    $(".drop").click(function () {
        let pool_id = $(this).attr("id");
        $(`.content#${pool_id}`).remove();
    });
    $("#confirm").click(function () {
        let pool_setting = {};
        pool_setting["info"] = { name: "自定义卡池" };
        pool_setting["settings"] = {
            combo: parseInt($("#combo").val()),
            day_limit: parseInt($("#day_limit").val()),
            auto_update: $("#auto_update").prop("checked"),
            shuffle: !$("#fix_last").prop("checked")
        };
        pool_setting["pool"] = {};
        for (c of $(".content")) {
            pool_setting["pool"][$(c).find("#name").val()] = {
                prop: parseInt($(c).find("#prop").val()),
                prop_last: parseInt($(c).find("#prop_last").val()),
                prefix: $(c).find("#pref").val(),
                pool: $(c).find("#pool").val().split("\n")
            }
        }
        let text = JSON.stringify({ version: 3104, settings: pool_setting });
        $.post("1234567"/*this is coding-api address*/, { raw: text }, function (data) {
            $('#pc #setting_code').attr("value", "设置码" + data);
        });
    });
    $("#copy").click(function () {
        let a = document.forms["pc"]["setting_code"];
        a.select();
        document.execCommand("Copy");
        alert("已复制，请在群里粘贴。");
    });
});