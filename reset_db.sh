# completely resets the Django database
# this purely exists for personal debugging purposes
read -p "Are you sure you want to erase the database? (Y/N): " confirm
if [ "$confirm" == "Y" ]; then
    find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf;
    rm db.sqlite3;
    rm -rf stats/migrations;
    python3 manage.py makemigrations stats;
    python3 manage.py migrate stats;
    python3 manage.py migrate;
    echo "Database Erased and Reset";
else
    echo "Operation Cancelled";
fi