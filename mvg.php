<?php
if (!isset($_GET['urlToOpen'])) {
    http_response_code(400);
    echo json_encode(["error" => "Missing URL"]);
    exit;
}

$url = filter_var($_GET['urlToOpen'], FILTER_SANITIZE_URL);

if (!filter_var($url, FILTER_VALIDATE_URL)) {
    http_response_code(400);
    echo json_encode(["error" => "Invalid URL"]);
    exit;
}

// API-Call
// You can replace `MyCustomPHPProxy` with your own name for the User Agent
$options = [
    "http" => [
        "header" => "User-Agent: MyCustomPHPProxy\r\n",
        "timeout" => 10
    ]
];

$context = stream_context_create($options);
$response = @file_get_contents($url, false, $context);

if ($response === FALSE) {
    http_response_code(500);
    echo json_encode(["error" => "Failed to fetch data"]);
} else {
    header("Content-Type: application/json");
    echo $response;
}
?>
