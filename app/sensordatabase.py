#!flask/bin/python

import sqlite3, json

# Create database in RAM
def create_database():
    print '\n\n >>>>>> Creating database in RAM...'
	
    conn = sqlite3.connect(":memory:", check_same_thread = False)
    conn.row_factory = sqlite3.Row	    # Enables column access by name
    c = conn.cursor()
    # Create table
    c.execute('''CREATE TABLE sensors_data
                 (temp real, pressure real, altitude real, mytime text)''')

    conn.commit()			    # Save and commit changes

def get_database_sensor_data():
    print '''\n  >>>>>> get_database_sensor_data(): 
	  Accessing the database to display data in JSON format'''
    
    sensor_rows = c.execute('SELECT * from sensors_data').fetchall()

    rows = [dict(row) for row in sensor_rows]
    json_database = json.dumps(rows)        # JSONify

    return json_database
