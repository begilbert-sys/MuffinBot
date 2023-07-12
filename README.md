# MuffinBot
A discord.py bot wrapped inside of a Django application.
This app has two main functionalities: 
* On the backend: all readable messages from a discord server are processed in batches, and relevant info is uploaded to a local SQLite3 database
* On the frontend: the database info is neatly displayed on a webpage with Django's HTML templating, plus a little help from Javascript
