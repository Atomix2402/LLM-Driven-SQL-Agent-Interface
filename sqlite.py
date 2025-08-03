import sqlite3

## code to connect to sqlite
conn = sqlite3.connect("student.db")

## creating a cursor object to insert records and create tables
cursor = conn.cursor()

# Creating the table
table_info="""
create table STUDENT(NAME VARCHAR(25),CLASS VARCHAR(25),
SECTION VARCHAR(25),MARKS INT)
"""

cursor.execute(table_info)

## Inserting records

cursor.execute('''insert into STUDENT values('Max','Data Science','B',90)''')
cursor.execute('''insert into STUDENT values('Daniel','Data Science','B',100)''')
cursor.execute('''insert into STUDENT values('Charles','DEVOPS','A',78)''')
cursor.execute('''insert into STUDENT values('Carlos','DEVOPS','A',55)''')
cursor.execute('''insert into STUDENT values('Lewis','DEVOPS','A',93)''')

# Display all the records

print("The records in the table STUDENT are: ")
op = cursor.execute('''select * from STUDENT''')
for row in op:
    print(row)

# Committing your database
conn.commit()
conn.close()
