from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

from app import sensors

sensors.GPIO_Setup()
sensors.create_database()


