<!doctype html>
<html>

<head>
    <meta name='viewport' content='width=device-width, initial-scale=1' charset="utf-8" />
    <title>自定义卡池</title>
    <script src="https://cdn.staticfile.org/jquery/3.4.1/jquery.min.js"></script>
    <script src="https://cdn.staticfile.org/autosize.js/4.0.2/autosize.min.js"></script>
    <script>var pool_old = `<?php
        if (isset($_GET["code"])) {
            $code = strtolower($_GET["code"]);
            $con = mysqli_connect("localhost", "1234567", "1234567");
            mysqli_select_db($con, "1234567");
            $result = mysqli_query($con, "SELECT Raws FROM Coding WHERE Code='$code'");
    
            $setting = "";
            while ($row = mysqli_fetch_array($result)) {
                $setting = $row[0];
            }
            echo $setting;
        } ?>`;</script>
    <script src="pool.js"></script>
</head>

<body>
    <h1>自定义卡池</h1>
    <div id="pools"></div>
    <p>
        <input type="button" value="增加奖池" id="add">
    </p>
    <form id="cfg">
        每次抽卡数：<input id="combo" value="10" type="number" /><br>
        每日抽卡次数：<input id="day_limit" value="2" type="number" /><br>
        <input type="checkbox" id="auto_update">自动更新卡池<br>
        <input type="checkbox" id="fix_last" checked>保底抽固定为最后一抽
    </form>
    <p><input type="button" value="确认" id="confirm"></p>
    <form id="pc">
        <input type="text" id="setting_code">
        <input type="button" value="复制" id="copy">
    </form>
</body>

</html>