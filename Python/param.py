#Parameter Adjustments for the RPi/sbRIO
#Created by Brandon Nguyen & Cody Earles
# Modified by: Kelly Mak
# This file changes the parameters of the seial port if necessary 
# argv : param.py [amplitude, chirpLength, initFreq, finalFreq, interPulseTime, numSamples](1-6) valueToChangeto 

from ftplib import FTP
import time
import os
import thread
import threading
import serial
import sys

# "a" - adjust the parameters 
# "e" - exit paramter adjustment mode, while waiting for a seial character to change parameters 
# "o" - start sonar sequence (chirp)
# "s" - stops the program, require restart 


#Initialize serial, Baud rate 9600
ser = serial.Serial('/dev/ttyUSB0',9600)
        
#check for command line arguments
if len(sys.argv) == 3: 
	param_to_change = str(sys.argv[1]) #First argument is the parameter value to change
	new_value = float(sys.argv[2]) #Second argument is the new value
else:
	print("Please enter valid arguments: 'param.py [parameter #] [value]'")
	ser.write("a") #adjust param 
	time.sleep(2)
	ser.write("e") #exit param change 
	while ser.inWaiting():
		print(ser.readline().strip()) #Reads instructions from sbRIO
	sys.exit()
	
#Create data folder (if it doesnt exist) and navigate to its path
data_path = '/home/pi/DATA/'

ser.write("a") #adjust param 
time.sleep(2)
print("Current values: ")
while ser.inWaiting():
        print(ser.readline().strip())  #Displays serial data from sbRIO that contains the current values
if 0 < float(param_to_change) < 7:
        ser.write(param_to_change) #Write parameter # to sbRIO
        time.sleep(2)
        while ser.inWaiting(): #number of bytes in input buffer
                print(ser.readline().strip()) #Read parameter value from sbRIO
        ser.write(str(new_value)) #write new_value (argv[2]) to serial 
        print("New parameters: ")
        time.sleep(2)
        ser.write("e") #e's are exit commands on the sbRIO program
		time.sleep(2) #Include delays so that sbRIO can process the commands
        ser.write("e") #exit param change 
        time.sleep(2)
        while ser.inWaiting():
                print(ser.readline().strip())  #print the newest values. Removes whitespace characters 
else:
        print("Please enter a valid number.")





