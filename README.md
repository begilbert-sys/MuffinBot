# MuffinBot
A discord.py bot wrapped inside of a Django application.
This app has two main functionalities: 
* On the backend: all readable messages from a discord server are processed in batches, and relevant info is saved to a local SQLite3 database
* On the frontend: the database info is neatly displayed on a webpage with help from Django's HTML templating and some Javascript
