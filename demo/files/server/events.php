<?php

$event = file_get_contents('php://input');

$file = 'data.txt';

$current = file_get_contents($file);
$current .= $event  ."\n";
file_put_contents($file, $current);

?>