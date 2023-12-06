# visualizes the size of all tables in my database using a pie chart
# for personal debugging purposes
import psycopg
import matplotlib.pyplot as plt

SCHEMA = 'public'

connection = psycopg.connect(dbname='discord_stats', user='muffin')
cursor = connection.cursor()
cursor.execute(
    f"""SELECT table_name FROM information_schema.tables WHERE table_schema = '{SCHEMA}';"""
)

table_sizes = dict()
for table, in cursor.fetchall():
    cursor.execute(
        f"""SELECT pg_total_relation_size('"{SCHEMA}"."{table}"');"""
    )
    [size] = cursor.fetchone()
    table_sizes[table] = size

total = sum(table_sizes.values())
labels = list()
sizes = list()
other = 0 
for table in sorted(table_sizes, key=lambda table: table_sizes[table], reverse=True):
    value = table_sizes[table]
    if (value/total) > 0.01:
        labels.append(table)
        sizes.append(value)
    else:
        other += value
if other:
    labels.append('Other')
    sizes.append(other)


def fmt(pct_value):
    mb_value = (total*pct_value/100) / (10 ** 6)
    return '{:.1f}%\n({:.2f}MB)'.format(pct_value, mb_value)
fig, ax = plt.subplots()
ax.pie(sizes, labels=labels, autopct=fmt, radius=1.5)
plt.show()