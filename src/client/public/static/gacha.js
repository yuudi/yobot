var pool = [
    [1071, 1061, 1070, 1804, 1012, 1043, 1057, 1028, 1029, 1011, 1030, 1018, 1032, 1053, 1049, 1009, 1047, 1010, 1063, 1036, 1044, 1037, 1056, 1014, 1092, 1094, 1095, 1096, 1107, 1108, 1113, 1114, 1065, 1117, 1122, 1109, 1110, 1075, 1077, 1078, 1079, 1081, 1083, 1084, 1086, 1087, 1088, 1091, 1097, 1099, 1100, 1103, 1104, 1106, 1111, 1115, 1119, 1120, 1124, 1125, 1127, 1128],
    [1045, 1048, 1008, 1006, 1046, 1020, 1033, 1031, 1017, 1042, 1051, 1027, 1007, 1038, 1016, 1026, 1023, 1015, 1054, 1005, 1013],
    [1003, 1034, 1040, 1022, 1004, 1052, 1025, 1050, 1001, 1021, 1055],
];
var experience = {
    "star3": 0,
    "star2": 0,
    "star1": 0,
    "diamond": 0,
};
var progress = false;
(function () {
    var h = localStorage['gacha_experience'];
    if (h) {
        [experience.star3, experience.star2, experience.star1, experience.diamond] = h.split(',').map(x => +x);
    }
})();
function randarr(arr) {
    return String(arr[Math.floor(Math.random() * arr.length)]);
}
function pick(i) {
    var x = Math.random();
    if (x < 0.025) {
        experience.star3 += 1;
        return randarr(pool[0]) + '31';
    } else if (x < 0.205) {
        experience.star2 += 1;
        return randarr(pool[1]) + '11';
    } else if (i == 9) {
        experience.star2 += 1;
        return randarr(pool[1]) + '11';
    }
    experience.star1 += 1;
    return randarr(pool[2]) + '11';
}
function sleep(time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}
async function reload() {
    var container = document.getElementById('container');
    container.innerHTML = '';
    for (i of Array(10).keys()) {
        await sleep(200);
        let chara = String(pick(i));
        let result = document.createElement('img');
        result.src = sourcebase + chara + '.jpg';
        container.appendChild(result);
        if (i === 4) {
            container.appendChild(document.createElement('br'));
        }
    }
    experience.diamond += 1500;
}
async function gacha() {
    if (progress) {
        return;
    }
    progress = true;
    await reload();
    document.getElementById('result').innerHTML = `★3: ${experience.star3}<br>★2: ${experience.star2}<br>★1: ${experience.star1}<br>总耗钻: ${experience.diamond}`;
    localStorage['gacha_experience'] = [experience.star3, experience.star2, experience.star1, experience.diamond].join(',');
    progress = false;
}