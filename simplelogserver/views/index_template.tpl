<!DOCTYPE html>
<html lang="en">

<head>
    <title>Simple Log Server</title>
    <link type="text/css" href="main.css" rel="stylesheet">
</head>

<body>
<div id="root-container">
    <header role="banner">
        <h1>Simple Log Server</h1>
        <p>Last update: <time datetime="{{ update_timestamp.isoformat() }}">{{ update_timestamp.strftime("%c") }}</time></p>
    </header>

    <section id="main" role="main">
    </section>
</div>
<script src="main.js"></script>
</body>

</html>
