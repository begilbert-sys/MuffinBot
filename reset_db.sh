# completely resets the Django database
# this purely exists for personal debugging purposes
read -p "Are you sure you want to erase the database? (Y/N): " confirm
if [ "$confirm" == "Y" ]; then
    # delete pycache files
    find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf;

    # reset postgres db
    psql service=djangodb -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION muffin;'
    
    rm -rf stats/migrations;
    python3 manage.py makemigrations stats;
    python3 manage.py migrate stats;
    python3 manage.py migrate;
    python3 manage.py createcachetable;
    echo "Database Erased and Reset";
else
    echo "Operation Cancelled";
fi