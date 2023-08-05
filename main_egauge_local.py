from modules import database
import json
import argparse
import datetime
import requests
import base64
import math

from subprocess import call
import xml.etree.ElementTree as ET
import time
import requests
import urllib2
import decimal
import sys
import urllib

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

import ntplib
from datetime import datetime as dt

config_path = "/home/pi/IKoF/eGauge/assets/"

class eGauge(object):

    def __init__(self):

        #Init mysql server (needed for reboot)
        call(['sudo','service','mysql','start'])

        self.DROP = 0
		self.eGaugeRetryTime = 10

        #Fail counters
        self.egauge_fail = 0
        self.database_fail = 0
        self.serial_fail = 0

        # initialize the config variables
		elf.eGaugeConfig = json.load(open(config_path + 'eGaugeConfig.json'))
        self.eGaugeDevices = json.load(open(config_path + 'eGaugeDevices.json'))
        self.eGaugeRegisters = json.load(open(config_path + 'eGaugeRegistersPro.json'))

		self.configModBus = self.eGaugeConfig["ModBus"]
       	self.configXML = self.eGaugeConfig["XML"]
		self.max_error = self.eGaugeConfig["max_error"]
        self.devices = self.eGaugeDevices["devices"]
        self.registers = self.eGaugeRegisters["registers"]
		self.configDatabase = self.eGaugeConfig['Database']

        # Database config
        self.max_error_database = self.configDatabase["max_error_database"]
        self.db_table = self.configDatabase["DB_TABLE"]

		#Open serial connection
		self.client = ModbusClient(method=self.configModBus['method'], port=self.configModBus['port'], timeout=self.configModBus['timeout'], baudrate=self.configModBus['baudrate'], stopbits=self.configModBus['stopbits'], parity=self.configModBus['parity'], bytesize=self.configModBus['bytesize'])
		self.connection = self.client.connect()
		self.interval = self.configModBus['interval']
	        
		# eGaugeIp for getting the XML data        
		self.eGaugeIP = self.configXML['eGaugeIP']
	
		#Records current time and starts the data reception from egauge monitor
		self.get_ntp_time()
        self.past_time = datetime.datetime.utcnow()
        self.eGaugeRoutine()

    #Records sensor values and stores them at local database every second
    def eGaugeRoutine(self):

        #Loop
        while(True):
	   		try:
            	#Check if a second has passed
            	self.current_time = datetime.datetime.utcnow()
                #print(self.current_time)
            	if ((self.current_time - self.past_time).total_seconds() >= self.interval):
                    try:
                        # Call the routine to store the egauge readings
                        self.readEGauge()
						#Reinit serial gmail counter
                        self.serial_fail = 0
                    except Exception as error:
                        print(str(error) + " at " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        self.serial_fail += 1
                        if (self.serial_fail == self.max_error):
                            print("Serial connection offline after %s attempts" % (self.max_error))
                    finally:
                        #Closes the socket connection
                        self.past_time = self.current_time
                        end_time = datetime.datetime.utcnow()
            except KeyboardInterrupt:
	        	sys.exit('\n\nExiting by CTRL+C!!!\n')
                raise

    def get_ntp_time(self):
        NTPClient = ntplib.NTPClient()
        while True:
            try:
                #Try to connect to the NTP pool...
                response = NTPClient.request('pool.ntp.org')
                print("Time updated from NTP Server!")

                #If we get a response, update the system time.
                t = dt.fromtimestamp(response.tx_time)

                # Update Raspberry local date and time
                NewDateTime = t.strftime('%Y-%m-%d %H:%M:%S %Z')
                set_string = "--set=" + NewDateTime
                call(["date", set_string])
                break
            except:
                print("Could not connect to pool.")

    def readEGauge(self):
	    try:
			dict = {}
            for k, v in self.registers.items():
                	reg = self.client.read_input_registers(v['register']-30000,2,unit=1)
			decoder = BinaryPayloadDecoder.fromRegisters(reg.registers, byteorder=Endian.Big)
			
			if v['type'] == "uint32":
				#print("$$$$$$",k)
				if k == "timestamp":
					timestamp = datetime.datetime.fromtimestamp(int(decoder.decode_32bit_uint())).strftime('%Y-%m-%dT%H:%M:%SZ')
                                        #timestamp = '2022-02-10T19:24:00Z'
					

			if v['type'] == "float32":
                        	value= decoder.decode_32bit_float()								
				dict[k] = value

			self.interval = self.configModBus['interval']


	    except Exception:
			print(Exception)

	
 	    self.egauge_fail = 0
            #print("saving...")
            self.storeData(timestamp,dict)
	    
        except Exception as error:
            print(str(error) + " at " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.DROP = self.DROP + 1
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            print('egauge unit unreachable, retrying in %ss' % (self.eGaugeRetryTime))         

	    self.egauge_fail += 1
            if (self.egauge_fail == self.max_error):
                print("Egauge unit is offline after %s attempts. Error %s" %(self.max_error, error))

	    #time.sleep(self.eGaugeRetryTime)

    def storeData(self, a_timestamp, a_data):
        for idx, e in enumerate(self.devices):
	    #print(e["id"],e["name"])	
            data = self.buildJSON(e['struct'], a_data, e['name'])
            resp = self.insertRecord(a_timestamp, e['id'], json.dumps(data))

	    #Check if database did not fail
            if (resp == True):
                self.database_fail = 0
            else:
                self.database_fail += 1
		print("There was an error writing to the database")
                if (self.database_fail == self.max_error_database):
                    print("Database server offline after %s attempts" %(self.max_error_database))

    def buildJSON(self, a_device_struct, a_data, device_name):
        data = {}
        sum_l = 0
        for k, v in enumerate(a_device_struct, 1):
            data_temp = {}
            data_temp["V"] = str(round(decimal.Decimal(a_data[v["V"]]), 3))
            data_temp["I"] = str(round(decimal.Decimal(a_data[v["I"]]), 3))
            data_temp["P"] = str(abs(round(decimal.Decimal(a_data[v["P"]]), 3)))
            data_temp["S"] = str(round(decimal.Decimal(a_data[v["V"]]) * decimal.Decimal(a_data[v["I"]]), 3))
            #data_temp["Q"] = str(round(math.sqrt(decimal.Decimal(a_data[v["P"]])**2 * decimal.Decimal(data_temp["S"])**2), 3))
	    data_temp["Q"] = "NaN"
            data_temp["PF"] = str(round(decimal.Decimal(data_temp["P"])/decimal.Decimal(data_temp["S"]), 3))
            
            data["L%d"%(k)] = data_temp
            sum_l = sum_l + decimal.Decimal(a_data[v["P"]])

        #print device_name, data 
        return data

    def insertRecord(self,  a_device_id, a_timestamp, a_data):
        resp = database.createEGaugeRecord(self.db_table, a_device_id, a_timestamp, a_data)
	return resp 

if __name__ == '__main__':
    eGauge = eGauge()

