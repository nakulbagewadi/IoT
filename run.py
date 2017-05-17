#!flask/bin/python

from app import app

app.run(debug = True,
        host = '0.0.0.0',
        port = 7777,
        ssl_context=('/home/pi/IoT/Final_Project/sensors-api/ssl/server.crt',
                     '/home/pi/IoT/Final_Project/sensors-api/ssl/server.key'))
