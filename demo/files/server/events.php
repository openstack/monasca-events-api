<?php

$event = $_POST["event"];

$file = 'data.txt';

$current = file_get_contents($file);
$current .= $event  ."<br> \n";
file_put_contents($file, $current);

?>