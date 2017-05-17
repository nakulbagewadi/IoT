#!flask/bin/python

from app import app
#import Adafruit_BMP.BMP085 as BMP085
import Adafruit_DHT as DHT
import RPi.GPIO as GPIO
import datetime, time, sys, string, sqlite3, json
import matplotlib.pyplot as graph
import LCD1602

from flask import Flask, jsonify, abort, request, render_template, redirect, url_for, flash
from apscheduler.scheduler import Scheduler
from .forms import LoginForm, IndexForm, GraphForm, LogoutForm

# GPIO pin assignments BCM format
HumitureSensor = 11
HumiturePIN = 23
GasSensorPIN = 24
FlameSensorPIN = 22
RainSensorPIN = 5
TouchPIN = 25
IRPIN = 12
LaserPIN = 16
Dual_Color_R = 6
Dual_Color_G = 13
red_pin = 17
green_pin = 18
blue_pin = 27

GPIO.setmode(GPIO.BCM)
freq = 1000                             # setup PWM frequency

GPIO.setup(red_pin,GPIO.OUT)
GPIO.setup(green_pin,GPIO.OUT)
GPIO.setup(blue_pin,GPIO.OUT)
RED = GPIO.PWM(red_pin, freq)           # init PWMs
GREEN = GPIO.PWM(green_pin, freq)
BLUE = GPIO.PWM(blue_pin, freq)

# Global variables	
conn = sqlite3.connect(":memory:", check_same_thread = False)
conn.row_factory = sqlite3.Row	        # Enables column access by name
c = conn.cursor()

last_emergency = 0
last_motion = 0
blank_line = '                '         # 16 spaces to clear a LCD line

# sensor dictionary to store indexing options chosen by user
sensor_indexing = { 'temperature': 0,
                    'humidity': 0,
                    'gas': 0,
                    'flame': 0,
                    'raindrop': 0,
                    'emergency': 1,
                    'motion': 0
                  }

# Setup GPIOs
def GPIO_Setup():
    GPIO.setup(GasSensorPIN, GPIO.IN)
    GPIO.setup(FlameSensorPIN, GPIO.IN)
    GPIO.setup(RainSensorPIN, GPIO.IN)
    GPIO.setup(TouchPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)     # Set touch pin pull up to high level
    GPIO.setup(IRPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    GPIO.setup(Dual_Color_R, GPIO.OUT)
    GPIO.setup(Dual_Color_G, GPIO.OUT)
    GPIO.output(Dual_Color_R, GPIO.HIGH)    # RED led off
    GPIO.output(Dual_Color_G, GPIO.HIGH)    # GREEN led off
    
    GPIO.setup(LaserPIN, GPIO.OUT)          # Set LaserPIN's mode as output
    GPIO.output(LaserPIN, GPIO.HIGH)        # Set LaserPIN high(+3.3V) to turn off laser


    RED.start(0)                            # init PWM duty cycle to 0 (off)
    GREEN.start(0)
    BLUE.start(0)
    
    LCD1602.init(0x27, 1)	            # init(slave address, background light)
    LCD1602.clear()
    LCD1602.write(0, 0, 'Homeautomation &') # X, Y, String
    LCD1602.write(0, 1, 'Weather station')


# function to change the RGB LED color
def change_color_to(hex_color):
    # convert into decimal whole number
    rgb_color[0] = int(hex_color[0:2],16)   # red
    rgb_color[1] = int(hex_color[2:4],16)   # green
    rgb_color[2] = int(hex_color[4:6],16)   # blue

    # colors are determined by percentage of time for PWM
    percent_red = 100-(rgb_color[0]/255*100)
    percent_green = 100-(rgb_color[1]/255*100)
    percent_blue = 100-(rgb_color[2]/255*100)

    RED.ChangeDutyCycle(percent_red)
    GREEN.ChangeDutyCycle(percent_green)
    BLUE.ChangeDutyCycle(percent_blue)

    
# Create database in RAM
def create_database():
    print '\n\n >>> Creating database in RAM'

    # Create table
    c.execute('''CREATE TABLE sensors_data
                 (
                 temperature real,
                 humidity real,
                 gas str,
                 flame str,
                 raindrop str,
                 mytime text
                 )''')

    conn.commit()


# Gather sensor data periodically using apscheduler
def sensor_data():
    with app.app_context():
        print '\n  >>> sensor_data()'

            
        #mysensor = BMP085.BMP085()
        #temperature = mysensor.read_temperature() 	        # Read temperature
        #pressure = mysensor.read_pressure()                    # Read pressure
        #altitude = mysensor.read_altitude()	                # Read altitude
        humidity,temperature = DHT.read_retry(HumitureSensor, HumiturePIN)  # Read humidity

        gas = "No" if GPIO.input(GasSensorPIN) else "Yes"       # Get input from gas sensor
        flame = "No" if GPIO.input(FlameSensorPIN) else "Yes"   # Get input from flame sensor
        rain = "No" if GPIO.input(RainSensorPIN)  else "Yes"    # Get input from raindrop sensor
        
        now = time.strftime("%X")	                        # Get current time

        # Insert into database
        c.execute('INSERT INTO sensors_data VALUES (?,?,?,?,?,?)',
                  (temperature,humidity,gas,flame,rain,now))
        
        conn.commit()

        LCD1602.clear()
        tmpstring = 'T={0} H={1}'
        TandH_string = tmpstring.format(temperature, humidity)
        LCD1602.write(0, 0, TandH_string)                       # X, Y, String

        #sensors_data = {
        #    'time': now,
        #    'temperature': temperature,
        #    'humidity': humidity,
        #    'gas': gas,
        #    'flame': flame,
        #    'rain': rain
        #}
        #jsonify({'sensors_data': sensors_data})
        #print sensors_data


# Gather sensor data 2 periodically using apscheduler
def sensor_data_2():
    with app.app_context():
        print '\n  >>> sensor_data_2()'

        global last_emergency
        global last_motion

        if sensor_indexing['emergency'] == 1:                   # check if this option has been enabled
            current_emergency = GPIO.input(TouchPIN)            # read touch switch input      
            if current_emergency != last_emergency: 
                if current_emergency == 0:                      # touch action detected 
                    GPIO.output(LaserPIN, GPIO.LOW)             # laser on
                if current_emergency == 1:
                    GPIO.output(LaserPIN, GPIO.HIGH)            # laser off
            last_emergency = current_emergency
            #print '\n touch sensor =  '
            #print current_emergency
            
        if sensor_indexing['motion'] == 1:                      # check if this option has been enabled
            current_motion = GPIO.input(IRPIN)                  # read motion sensor input
            if current_motion != last_motion:
                if current_motion == 0:                         # motion detected
                    GPIO.output(Dual_Color_G, GPIO.LOW)         # GREEN led on
                if current_motion == 1:
                    GPIO.output(Dual_Color_G, GPIO.HIGH)        # GREEN led off
            last_motion = current_motion
            #print '\n motion sensor =  '
            #print current_motion


# turn off all GPIO functions
def turn_off_GPIO():
    LCD1602.clear()                         # turn off the LCD
    RED.stop()                              # stop PWMs
    GREEN.stop()
    BLUE.stop()
    GPIO.output(red_pin, GPIO.HIGH)         # Turn off all LEDs
    GPIO.output(green_pin, GPIO.HIGH)
    GPIO.output(blue_pin, GPIO.HIGH)
    GPIO.output(Dual_Color_R, GPIO.HIGH)
    GPIO.output(Dual_Color_G, GPIO.HIGH)
    GPIO.output(LaserPIN, GPIO.HIGH)        # turn off laser
    GPIO.cleanup()
    

# LOGIN PAGE
@app.route('/login', methods = ["GET", "POST"])
def login():
    form1 = LoginForm()
    if form1.validate_on_submit():
        return redirect('/index')
    # display initially or incorrect login credentials!
    return render_template('login.html', title='Sign In', form=form1)


# LOGOUT PAGE
@app.route('/logout', methods = ["GET", "POST"])
def logout():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    turn_off_GPIO()
    func()
    return render_template('login.html', title='Sign In', form=LoginForm())


# INDEX PAGE: Select which sensor data to display
@app.route('/index', methods = ["GET", "POST"])
def index():
    form2 = IndexForm()
    if form2.validate_on_submit():
        if form2.temperature.data:
            sensor_indexing['temperature'] = 1
        else:
            sensor_indexing['temperature'] = 0
            
        if form2.humidity.data:
            sensor_indexing['humidity'] = 1
        else:
            sensor_indexing['humidity'] = 0
            
        if form2.gas.data:
            sensor_indexing['gas'] = 1
        else:
            sensor_indexing['gas'] = 0
            
        if form2.flame.data:
            sensor_indexing['flame'] = 1
        else:
            sensor_indexing['flame'] = 0
            
        if form2.raindrop.data:
            sensor_indexing['raindrop'] = 1
        else:
            sensor_indexing['raindrop'] = 0

        if form2.emergency.data:
            sensor_indexing['emergency'] = 1
        else:
            sensor_indexing['emergency'] = 0

        if form2.motion.data:
            sensor_indexing['motion'] = 1
        else:
            sensor_indexing['motion'] = 0

        apsched = Scheduler()
        apsched.start()
        apsched.add_interval_job(sensor_data, seconds=5)
        apsched.add_interval_job(sensor_data_2, seconds=1)
    
    return render_template('index.html', title='Sensors', form=form2)


# GET sensor data from database
@app.route('/sensor-database', methods=['GET'])
@app.route('/sensors/api/v1.0/sensor-data/sensor-database', methods=['GET'])
def database_sensor_data():
    print '\n  >>> database_sensor_data()'

    column1 = " "
    column2 = " "
    column3 = " "
    column4 = " "
    column5 = " "
    column6 = "mytime"

    if sensor_indexing['temperature'] == 1:
        column1 = "temperature,"
    if sensor_indexing['humidity'] == 1:
        column2 = "humidity,"
    if sensor_indexing['gas'] == 1:
        column3 = "gas,"
    if sensor_indexing['flame'] == 1:
        column4 = "flame,"
    if sensor_indexing['raindrop'] == 1:
        column5 = "raindrop,"

    mystring = ''' SELECT {0} {1} {2} {3} {4} {5} from sensors_data '''
    query_string = mystring.format(column1, column2, column3, column4, column5, column6)
    
    sensor_rows = c.execute(query_string).fetchall()

    rows = [dict(row) for row in sensor_rows]

    return render_template('json.html', title='SENSORS-DB', json=rows)


# Plot sensor data from database
@app.route('/graphs',  methods = ["GET", "POST"])
@app.route('/sensors/api/v1.0/sensor-data/sensor-graphs', methods = ["GET", "POST"])
def graphs():
    form3 = GraphForm()
    if form3.validate_on_submit():
        if form3.temperature.data:
            sensor_indexing['temperature'] = 1
        else:
            sensor_indexing['temperature'] = 0
            
        if form3.humidity.data:
            sensor_indexing['humidity'] = 1
        else:
            sensor_indexing['humidity'] = 0

        print '\n  >>> graphs()'

        sensor_rows = c.execute("SELECT temperature, humidity, mytime from sensors_data").fetchall()
        
        temp = []
        humi = []
        times = []
        for row in sensor_rows:
            te, hu, ti = row
            temp.append(te)
            humi.append(hu)
            times.append(ti)

        x1 = range(len(times))
                
        if sensor_indexing['temperature'] == 1 and sensor_indexing['humidity'] == 1:
            graph.plot(x1,temp, 'r', marker='o', label='Temp')
            graph.plot(x1,humi, 'b', marker='x', label='Humidity')
        elif sensor_indexing['temperature'] == 1:
            graph.plot(x1,temp, 'r', marker='o', label='Temp')
        elif sensor_indexing['humidity'] == 1:
            graph.plot(x1,humi, 'b', marker='x', label='Humidity')
        else:
            return render_template('graphs.html', title='Graphs', form=form3)

        graph.xticks(x1, times)
        graph.legend(loc='upper left')
        graph.gcf().autofmt_xdate(ha='center')
        graph.show()
        
    return render_template('graphs.html', title='Graphs', form=form3)





















