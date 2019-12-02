<?php

//代码中的保密部分已被替换为1234567

if ($_SERVER["REQUEST_METHOD"] == "GET") {
    $code = strtolower($_GET["code"]);
    $con = mysqli_connect("localhost", "1234567", "1234567");
    mysqli_select_db($con, "1234567");
    $result = mysqli_query($con, "SELECT Raws FROM Coding WHERE Code='$code'");
    header("Content-type:text/plain");
    $setting = "{}";
    while ($row = mysqli_fetch_array($result)) {
        $setting = $row[0];
    }
    echo $setting;
} else {
    $con = mysqli_connect("localhost", "1234567", "1234567");
    $characters = '3456789abcdefghijkmnpqrstuvwxy';
    $randomString = '';
    for ($i = 0; $i < 4; $i++) {
        $index = rand(0, strlen($characters) - 1);
        $randomString .= $characters[$index];
    }
    mysqli_select_db($con, "1234567");
    mysqli_query($con, "REPLACE INTO Coding (Code, Raws) VALUES ('$randomString', '$_POST[raw]')");
    header("Content-type:text/plain");
    echo $randomString;
}
