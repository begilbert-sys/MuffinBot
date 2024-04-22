# MuffinBot
A WIP Discord Statistics Servivce. The website can be found here:
http://muffinstats.net/


Some samples from development:
<img src="https://i.imgur.com/9GlxI0q.png">

A discord.py bot wrapped inside of a Django application.
This app has two main functionalities: 
* On the backend: all readable messages from a discord server are processed in batches, and relevant info is saved to a PostgreSQL database
* On the frontend: the data is neatly displayed on a webpage with help from Django's HTML templating and some Javascript
