<?php
header("content-type: text/plain");
$file = "cache-" . date('Y-m-d') . ".ics";
if (file_exists($file)) {
    include($file);
} else {
    $new = file_get_contents("https://calendar.google.com/calendar/ical/obeb9cdv0osjuau8e7dbgmnhts%40group.calendar.google.com/public/basic.ics");
    echo ($new);
    file_put_contents($file, $new);
}
