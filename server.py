
import smbus
import time
from flask import Flask, request
import flask
import datetime
import thread
import threading
import os
import RPi.GPIO as GPIO
import json

DEVICE_BUS = 1
DEVICE_ADDR = 0x48
CMD_STANDBY = 0
CMD_OPEN = 1
CMD_CLOSE = 2

engine1_s0 = 0
engine1_s1 = 5
engine1_s2 = 6
engine1_s3 = 13
engine1_s4 = 19
engine1_open = 1
engine1_close = 7

bus = smbus.SMBus(DEVICE_BUS)
threshold = 24
delta = 2
engine1_pos = 5
engine1_expectedPos = 0
timeInterval = 600 # => 10min



mainLock = threading.Lock()

app = Flask(__name__)

def sensorsCallback(channel):
    global engine1_pos
    if channel == engine1_s0:
        engine1_pos = 0
    if channel == engine1_s1:
        engine1_pos = 1
    if channel == engine1_s2:
        engine1_pos = 2
    if channel == engine1_s3:
        engine1_pos = 3
    if channel == engine1_s4:
        engine1_pos = 4

    checkPosition()

def getCurrentPosition():
	if GPIO.input(engine1_s0) == 1:
		return 0
	if GPIO.input(engine1_s1) == 1:
                return 1
	if GPIO.input(engine1_s2) == 1:
                return 2
	if GPIO.input(engine1_s3) == 1:
                return 3
	if GPIO.input(engine1_s4) == 1:
                return 4
	return 5
def checkPosition():
    global engine1_pos
    global engine1_expectedPos
    if engine1_pos > engine1_expectedPos:
        setEngineOpenClose(1, CMD_CLOSE)
    if engine1_pos < engine1_expectedPos:
        setEngineOpenClose(1, CMD_OPEN)
    if engine1_pos == engine1_expectedPos:
        setEngineOpenClose(1, CMD_STANDBY)

def setEngineOpenClose(engine, cmd):
    if engine == 1:
        if cmd == CMD_STANDBY:
            GPIO.output(engine1_open, 0)
            GPIO.output(engine1_close, 0)
        if cmd == CMD_OPEN:
            GPIO.output(engine1_open, 1)
            GPIO.output(engine1_close, 0)
        if cmd == CMD_CLOSE:
            GPIO.output(engine1_open, 0)
            GPIO.output(engine1_close, 1)

def GPIO_Init():
    # GPIO INIT
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(engine1_s0, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(engine1_s1, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(engine1_s2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(engine1_s3, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(engine1_s4, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(engine1_open, GPIO.OUT)
    GPIO.setup(engine1_close, GPIO.OUT)

    GPIO.add_event_detect(engine1_s0, GPIO.RISING, callback=sensorsCallback, bouncetime=300)
    GPIO.add_event_detect(engine1_s1, GPIO.RISING, callback=sensorsCallback, bouncetime=300)
    GPIO.add_event_detect(engine1_s2, GPIO.RISING, callback=sensorsCallback, bouncetime=300)
    GPIO.add_event_detect(engine1_s3, GPIO.RISING, callback=sensorsCallback, bouncetime=300)
    GPIO.add_event_detect(engine1_s4, GPIO.RISING, callback=sensorsCallback, bouncetime=300)

@app.route('/')
def index():
	mainLock.acquire(True)
	tmp = readTemp()
	ret = {"temperature":tmp}
	mainLock.release()
	return flask.jsonify(**ret)

@app.route('/status')
def status():
        mainLock.acquire(True)
        tmp = readTemp()
	jsonStr = ""
	with open("config.json", "r") as jsonIn:
                jsonStr = jsonIn.read()
	jsonDict = json.loads(jsonStr)
	ret = {"temperature":tmp, "engine1_pos":engine1_pos,"config":jsonDict }
        mainLock.release()
        return flask.jsonify(**ret)

@app.route('/history')
def history():
	mainLock.acquire(True)
	retStr = ""
	with open("tempHistory.csv", "r") as csvIn:
		retStr = csvIn.read()
	mainLock.release()
	return retStr

@app.route('/config', methods=['POST'])
def config():
	mainLock.acquire(True)
	thresholdStr = request.form.get('threshold')
	deltaStr = request.form.get('delta')
	timeIntervalStr = request.form.get('timeInterval')
	with open("config.json", "r") as jsonIn:
                jsonStr = jsonIn.read()
        jsonDict = json.loads(jsonStr)
	print thresholdStr
	if thresholdStr != None:
                jsonDict['threshold'] = int(thresholdStr)
	if deltaStr != None:
		jsonDict['delta'] = int(deltaStr)
	if timeIntervalStr != None:
                jsonDict['timeInterval'] = int(timeIntervalStr)
	with open("config.json", "w") as jsonIn:
                jsonStr = jsonIn.write(json.dumps(jsonDict))
	mainLock.release()
	updateConfig()
	return "OK"

def updateConfig():
	global delta
	global threshold
	global timeInterval
	mainLock.acquire(True)
	with open("config.json", "r") as jsonIn:
                jsonStr = jsonIn.read()
        jsonDict = json.loads(jsonStr)
	delta = jsonDict["delta"]
	threshold = jsonDict["threshold"]
	timeInterval = jsonDict["timeInterval"]
	mainLock.release()

def readTemp():
        bus.write_byte(DEVICE_ADDR, 0)
        return bus.read_byte(DEVICE_ADDR)

def threadFn():
	global timeInterval
	global threshold
	global delta
	global engine1_pos
	global engine1_expectedPos
	while True:
		time.sleep(timeInterval)
		mainLock.acquire(True)
        	tmp = readTemp()
        	s = str(tmp) + "," + datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "\n"
        	with open("tempHistory.csv", "a") as csvOut:
                	csvOut.write(s)
		os.system("tail -n 10080 tempHistory.csv > .tmpHistory ; cat .tmpHistory > tempHistory.csv ; rm .tmpHistory")

		if tmp > threshold + delta and engine1_expectedPos < 4:
			engine1_expectedPos = engine1_expectedPos + 1
		if tmp < threshold - delta and engine1_expectedPos > 0:
			engine1_expectedPos = engine1_expectedPos - 1
		checkPosition()
		mainLock.release()

if __name__ == '__main__':
	updateConfig()
	GPIO_Init()
	engine1_pos = getCurrentPosition()
	checkPosition()

	try:
	        thread.start_new_thread(threadFn,())
	except:
	        print "Error while trying to start a new thread, please send an email to contact@nicolasanjoran.com"

	app.run(debug=True, host='0.0.0.0', use_reloader=False)
