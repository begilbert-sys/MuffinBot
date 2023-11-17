<!DOCTYPE html>
<html>

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width">
  {% load static %}

  <title>Stats FAQ</title>

  <link rel="stylesheet" href="{% static 'style.css' %}" type="text/css" />
  <link rel="icon" href="{{ guild_icon }}">

</head>
<body>
    <div class="greybar" style="margin-bottom:15px;"></div>
    <div class="headerlinks">
        <a href="/stats/">1. Main page</a> | <a href="/stats/details/">2. Detailed info</a> | 3. FAQ
    </div>
    <div class="greybar"></div>
    <div class='questions'>
    <h3>
        How did you make this?
    </h3>
    <p>
        Back in the days when <a href="https://en.wikipedia.org/wiki/Internet_Relay_Chat">IRC</a> was widely used,
        stats could be generated for an IRC channel using a program called <a href="https://storage.googleapis.com/mircstats/index.html">mIRCStats</a>.
        MuffinBot is essentially a rendition of mIRCStats, tailored and expanded for use on Discord. 
        <br>
        The project's source code is available on my <a href="https://github.com/begilbert-sys/MuffinBot">GitHub</a>.
    </p>
    <br>
    <h3>
        How can I add this to my own server?
    </h3>
    <p>
        As of right now, the bot only works for this server,
        but I plan to allow additional servers very soon.
        If you are interested in having the bot on your server, you can ping or DM me on Discord (@muffinlicious) and I'll add yours when I'm done :-) 
    </p>
    <br>
    <h3>
        I don't want my info displayed! Can I get it removed?
    </h3>
    <p>
        All collected info is already publicly available on the server.
        However, if you want your info removed, you can type the command: 
        <span class="command"><code>$blacklist</code></span>
        and any mention of you will immediately be purged. If you want to undo this decision at any point, type the command:
        <span class="command"><code>$whitelist</code></span>
    </p>
</body>
</html>