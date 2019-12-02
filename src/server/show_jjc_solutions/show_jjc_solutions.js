function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) { return pair[1]; }
    }
    return (false);
}

function stars(num) {
    var star_yellow = '☆';
    var star_pink = '★';
    var output = "";
    for (let i = 0; i < num; i++) {
        if (i == 5) {
            output += star_pink;
        } else {
            output += star_yellow;
        }
    }
    return output;
}

function load_solution() {
    var output = "";
    var equipment = '\u2694'
    var solutions = getQueryVariable("s");
    if (solutions == false) {
        document.getElementById("solutions").innerHTML = '<font size="15" color="red">参数错误</font>';
        return;
    }
    var solutions_items = solutions.split("-")
    output += "<p>查找到" + solutions_items.length + "条解法</p>";
    output += '<table border="0">'
    solutions_items.forEach(solution => {
        var teams = solution.split("_");
        var commet = teams[0].split(".");
        output += "<tr>";
        teams.slice(1).forEach(atk => {
            var chars = atk.split(".");
            output += '<td>';
            output += '<img src="https://redive.estertion.win/icon/unit/' + chars[0] + '.webp"><br>';
            output += stars(parseInt(chars[1]));
            if (chars[2] == "1") {
                output += equipment;
            }
            output += "</td>"
        })
        output += "<td>👍" + commet[0] + "<br>👎" + commet[1] + "<br>"
            + commet[2] + "年" + commet[3] + "月" + commet[4] + "日" + "</td></tr>";
    });
    output += '</table>'
    document.getElementById("solutions").innerHTML = output;
}
