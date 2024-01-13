# create a production-ready copy of the projet
rsync -r --exclude-from=prodignore.txt ~/Documents/MuffinBot ~/Documents/MuffinBot-prod