<?php

//用post将文件发到此脚本
//代码中的保密部分已被替换为1234567
header("Content-type:text/plain");
if (isset($_FILES["file"])) {
    $filename_extension = substr($_FILES["file"]["name"], -4);
    if ($filename_extension == ".zip") {
        if ($_FILES["file"]["size"] < 2000000) {
            if ($_FILES["file"]["error"] > 0) {
                echo "Return Code: " . $_FILES["file"]["error"] . "<br />";
            } else {
                if (file_exists("uploads/" . $_FILES["file"]["name"])) {
                    echo $_FILES["file"]["name"] . " already exists. ";
                } else {
                    move_uploaded_file(
                        $_FILES["file"]["tmp_name"],
                        "uploads/" . $_FILES["file"]["name"]
                    );
                    $dirurl = dirname('http://' . $_SERVER['SERVER_NAME'] . $_SERVER["REQUEST_URI"]) . '/uploads/';
                    echo $dirurl . $_FILES["file"]["name"];
                }
            }
        } else {
            http_response_code(413);
            echo "error 413: file oversize";
        }
    } elseif ($filename_extension == ".csv") {
        if ($_FILES["file"]["size"] < 2000000) {
            if ($_FILES["file"]["error"] > 0) {
                echo "Return Code: " . $_FILES["file"]["error"] . "<br />";
            } else {
                if (file_exists("uploads/1234567/" . $_FILES["file"]["name"])) {
                    echo $_FILES["file"]["name"] . " already exists. ";
                } else {
                    move_uploaded_file(
                        $_FILES["file"]["tmp_name"],
                        "uploads/1234567/" . $_FILES["file"]["name"]
                    );
                    $dirurl = dirname('http://' . $_SERVER['SERVER_NAME'] . $_SERVER["REQUEST_URI"]) . '/uploads/daily/';
                    echo $dirurl . substr($_FILES["file"]["name"], 0, -4);
                }
            }
        } else {
            http_response_code(413);
            echo "error 413: file oversize";
        }
    } else {
        http_response_code(403);
        echo "error 403: file type not allowed";
    }
} else {
    http_response_code(400);
    echo "error 400: bad request";
}
