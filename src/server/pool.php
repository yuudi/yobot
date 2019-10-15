<?php

if ($_GET['type'] == 'json') {
    $json = file_get_contents("data.json");
    header("Content-type:application/json;charset=utf-8");
    echo $json;
} elseif ($_GET['type'] == 'json5') {
    $json = file_get_contents("data.json5");
    header("Content-type:text/plain;charset=utf-8");
    echo $json;
} else {
    http_response_code(400);
    echo "400: bad request";
}
