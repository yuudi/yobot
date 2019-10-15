<?php

function posturl($data)
{
    $authkey = "*****"; //按照pcrdfans作者要求保密

    $url = "https://api.pcrdfans.com/x/v1/search";
    $headerArray = [
        'Authorization:' . $authkey,
        "Content-type:application/json",
        "Accept:application/json",
        "Origin:https://pcrdfans.com",
        "Referer:https://pcrdfans.com/battle",
        "Sec-Fetch-Mode:cors",
        "User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
    ];
    $curl = curl_init();
    curl_setopt($curl, CURLOPT_URL, $url);
    curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, FALSE);
    curl_setopt($curl, CURLOPT_SSL_VERIFYHOST, FALSE);
    curl_setopt($curl, CURLOPT_POST, TRUE);
    curl_setopt($curl, CURLOPT_POSTFIELDS, $data);
    curl_setopt($curl, CURLOPT_HTTPHEADER, $headerArray);
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
    $output = curl_exec($curl);
    curl_close($curl);
    return $output;
}

$defs = explode(".", $_GET["def"]);
$def = [];
foreach ($defs as $key => $value) {
    $def[$key] = intval($value);
}

$parr = [
    "_sign" => "a",
    "def" => $def,
    "nonce" => "a",
    "page" => 1,
    "sort" => 1,
    "ts" => mktime()
];
$pdata = json_encode($parr);

$raw_response = posturl($pdata);
header("Content-type:application/json");
echo $raw_response;
