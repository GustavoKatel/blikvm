#!/usr/bin/env python
# encoding: utf-8

import RPi.GPIO
import time
from http.server import BaseHTTPRequestHandler
from socketserver import UnixStreamServer
import os
from pwd import getpwnam
import threading

#settings
fan_gpio=12 # Fan GPIO pin number (default: 12)
idle_speed = 0 # Fan speed when under min_temp(IDLE) (min: 0, max: 100)
min_temp = 60 # Fan starting temperature 
max_temp = 65 # Fan max speed temperature (max: 65)

VERSION = "0.1"
SOCKET_PATH = "/run/kvmd/fan.sock"

# Remove existing socket file if it exists
if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

#define GPIO
RPi.GPIO.setwarnings(False)
RPi.GPIO.setmode(RPi.GPIO.BCM)
RPi.GPIO.setup(fan_gpio, RPi.GPIO.OUT)
pwm = RPi.GPIO.PWM(fan_gpio,100)
running = False
cpu_temp = 0.0
fan_speed = 0.0

def running_status():
	return "true"
	# if running:
	# 	return "true"
	# return "false"

class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		content = "Stub"
		content_type = "text/plain"
		status = 200

		if self.path == '/':
			content_type = "application/json"
			content = f'{{"ok": true, "result": {{"version": "{VERSION}"}}}}\n'
		elif self.path == '/state':
			content_type = "application/json"
			content = ( '{"ok": true, "result": {'
					 f'"service": {{"now_ts": 0.01}},'
					f' "temp": {{"real": {cpu_temp:.2f}, "fixed": {cpu_temp:.2f}}},'
					f' "fan": {{"speed": {fan_speed:.2f}, "pwm": 0, "ok": {running_status()}, "last_fail_ts": -1}},'
					 ' "hall": {"available": false, "rpm": 0}'
					 '}}\n' )
		else:
			status = 404
			content = "Not Found\n"

		self.send_response_only(status)
		self.send_header('Content-type', content_type)
		self.end_headers()
		self.wfile.write(bytes(content, "utf-8"))

class UnixSocketHttpServer(UnixStreamServer):
    def get_request(self):
        request, client_address = super(UnixSocketHttpServer, self).get_request()
        return (request, ["local", 0])

def start_server():
	server = UnixSocketHttpServer(SOCKET_PATH, Handler)
	uid = getpwnam("kvmd").pw_uid
	gid = getpwnam("kvmd").pw_gid
	os.chown(SOCKET_PATH,uid,gid)
	os.chmod(SOCKET_PATH,0o666)
	server.serve_forever()

threading.Thread(target=start_server).start()

#running code
try:
	while True:
		tmpFile = open( '/sys/class/thermal/thermal_zone0/temp' )
		cpu_temp = int(tmpFile.read())/1000
		tmpFile.close()
		print("Temp:",cpu_temp)
		if (cpu_temp >= max_temp) or (cpu_temp > min_temp): 
			if(not running): #if fan not running, start fan
				print("PWM_Start")
				pwm.start(0)
				running = True
			if (cpu_temp >= max_temp): #For safety, temp exceeds 60 degrees, the fan speed is always set to 100%.
				set_speed = 100
			else:
				temp_speed = int((cpu_temp - min_temp) / (max_temp - min_temp) * 100) # set 0~100% for min and max temp ranges
				set_speed = min(max(idle_speed, temp_speed), 100) # make speed not over 100 
			print("set_speed:",set_speed,"%") 
			fan_speed = set_speed
			pwm.ChangeDutyCycle(set_speed)
		else :
			if(running):
				running = False
				pwm.stop()
				print("PWM_Stop")

		time.sleep(5)
				
except KeyboardInterrupt:
		pass
pwm.stop()
os.remove(SOCKET_PATH)
