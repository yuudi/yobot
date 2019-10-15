<?php

//用伪静态将/daily目录解析到此脚本
//代码中的保密部分已被替换为1234567
$page404 = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>yobot</title></head><body><p>404: file not found</p><p><a href='https://yobot.xyz/'>return to home</a></p></body></html>";
if (substr($_SERVER["REQUEST_URI"], 0, 6) == "/daily") {
    $url = $_SERVER["REQUEST_URI"];
    $url = rtrim($url, "?" . $_SERVER['QUERY_STRING']);
    $filepath = "uploads/1234567" . substr($url, 6) . ".csv";
    if (file_exists($filepath)) {
        $fp = fopen($filepath, 'r') or die("can't open file");
        fseek($fp, 3);
        echo "<!DOCTYPE html><html><head><meta charset='utf-8'><title>yobot</title><style>th{background-color:#A7C942;color:#ffffff;}tr.even td{color:#000000;background-color:#EAF2D3;}table,td,th{border: 1px solid black;}</style></head><body><table border='1'><tbody>";
        $row_type = "th";
        $even_row = false;
        while ($csv_line = fgetcsv($fp)) {
            if ($even_row) {
                echo "<tr>";
            } else {
                echo "<tr class='even'>";
            }
            for ($i = 0, $j = count($csv_line); $i < $j; $i++) {
                echo "<" . $row_type . ">" . $csv_line[$i] . "</" . $row_type . ">";
            }
            echo "</tr>";
            $row_type = "td";
            $even_row = !$even_row;
        }
        echo "</tbody></table></body></html>";
        fclose($fp) or die("can't close file");
    } else {
        http_response_code(404);
        echo $page404;
    }
} elseif ($_SERVER["REQUEST_URI"] == "/filelist/?auth=1234567") {
    $fs = scandir("uploads/1234567/");
    echo "<!DOCTYPE html><html><head><meta charset='utf-8'><title>yobot</title></head><body>";
    foreach (array_slice($fs, 2) as $f) {
        echo "<p><a href='/daily/" . substr($f, 0, -4) . "'>" . $f . "</a></p>";
    }
    echo "</body></html>";
} else {
    http_response_code(404);
    echo $page404;
}
