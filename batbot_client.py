#Batbot Echo Client protocol
#Created by Brandon Nguyen
# Modified by Kelly Mak
# The client (external computer) will run this progam for a certain number of iterations, waits for data to be sent 
#     from the server, after which is stores it into an array and plots for the user to see. When complete, 
#     ends process and makes a file on the client side 
# argv: batbot_client.py iterations 

#Standard libraries
import socket
import csv
import time
import sys
import os
import subprocess
import time
import datetime
import warnings 

#External libraries	
import paramiko #SSH protocol
import matplotlib.pyplot as plt #Matlab-esque plotting
import numpy as np #Matlab-esque syntax/functions
#from scipy.signal import butter, lfilter, freqz

warnings.filterwarnings("ignore",".*GUI is implemented.*")

#fs = 250000 #Hz - sampling rate 
#lowcut = 20000 #Hz
#lowcut = 50000 #Hz - lowest freq 
#highcut = 100000 #Hz - highest freq 

#filters 
#def butter_bandpass(lowcut, highcut, fs, order = 5):
#	nyq = 0.5*fs # nyquist freq, twice sampling frequency 
#	low = lowcut/nyq
#	high = highcut/nyq
#	b, a = butter(order, [low, high], btype = 'band') #num and denom polynomials of the IIR filter 
#	return b, a
	
#def butter_bandpass_filter(data, lowcut, highcut, fs, order = 5):
#	b, a = butter_bandpass(lowcut, highcut, fs, order = order)
#	y = lfilter(b, a, data) # output of the digital filter 
#	return y

tic = time.time()

#Check for command line arguments.
# argv: iterations host user pass. Defaults : 20 BatBotRPi.local pi 123
if len(sys.argv) >= 2: #if 2 or more command line arguments 
	iterations = int(sys.argv[1]) #sets the number of iterations for echo-pulse protocol
else:
	iterations = 20 #Set the number of echo-pulse iterations to 20 by default
	
host = "BatBotRPi.local"
username = "pi"
password = "123"	
	
#Find the IPV6 address of the Pi using the windows 'ping' command 
print("Finding IPV6 address...")
system_result = subprocess.run("ping -n 1 " + host, stdout = subprocess.PIPE) #Ping the RPi once
stdout = str(system_result.stdout) #Store the returned string from ping

print(stdout) # ** 


try: 
	ip_frontbound = stdout.index('[') 
	ip_backbound = stdout.index(']')
	ipv6_addr = stdout[ip_frontbound + 1 : ip_backbound] #The IPV6 is enclosed by brackets
	print(ipv6_addr)
except ValueError: #Substring not found, the pinna is not connected 
	print('Not connected to picostation or sonar')
	sys.exit(1)

cwd = os.getcwd() #Current working directory
port = 21435 #Arbitrarily determine the port # that matches with the server program



# #Socket client setup
#if pscan(port) << if port is open 
s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM) #create a new socket. AF_INET6 (host, port, flowinfo, scopeid).
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try: 
	s.connect((ipv6_addr, port)) #connect address and port to socket 
	#s.listen()
except ConnectionRefusedError:
	#s.send(b'quit')
	#s.shutdown(1)
	s.close()
	print("Socket in use")
	sys.exit(1)
except TimeoutError:
	try: 
		s.send(b'quit')
		s.close()
		print("Time out Error when trying to connect socket")
	except OSError:
		print("OS ERROR 2")
except OSError:
	print("OS ERROR 1")		
		

print("Running for " + str(iterations) + " iterations...")

maketimevec = True
t = [] #time
lp_total = [] #total data sets for left pinna 
rp_total = [] #total data sets for right pinna
plt.ion() #Initialize interactive plotting to display plots later

file_counter = 0
		
while file_counter < iterations:
	try:
	
		file_counter = file_counter + 1
		lp_current = [] #Current data set for left pinna
		rp_current = [] #Current data set for right pinna
		tic1 = time.time()
		
		print("Sending run command to Pi.")
		try: 
			s.send(b'run') #Tells Pi to run the sbRIO loop!
		except ConnectionAbortedError:
			print("Connection aborted Error (117)")
			s.shutdown(1)
			s.close()
			sys.exit(1)
		except OSError:
			print("OS Error run")
			sys.exit(1)
		print("run")
		try:
			data = s.recv(1024).decode().strip() #Read data from Pi   **# There is some slowness here 
			# print("try recv")
			# data = s.recv(1024) # stuck here 
			# print("recv: ", str(data))
			# data = data.decode()
			# print("decode: ", str(data))
			# data = data.strip()
			# print ("strip: ", str(data))
			#s.settimeout(35) 		*edit to function correctly -> if need be
				#print(Set timeout reached) 
		except TimeoutError:
			print("Timeout Error when trying to recieve data from Pi")
			s.shutdown(1)
			s.close()
			sys.exit(1)
		#print("data: " + str(data)) # ** check this when run 
		
		tic2 = time.time()

		if data == "fileready":
			#Can definitely be faster if we bypass writing the datafile.dat here
			tic_obtain = time.time()
			print("Obtaining file #" + str(file_counter))
			with open('datafile.dat', 'wb') as fid: 
				line = 1
				while (line):
					line = s.recv(1024) #Receive 1024 bytes of data from server
					#print("line: " + line) # ** Look out for this. What keeps changing 
					if b'done' in line: #If 'done' command is received from RPi
						fid.write(line) #Write the line to the file
						print("done!")
						break #End file writing
					fid.write(line) #Write line to file
			print("Obtained! Time: " + str(time.time() - tic_obtain))	
			
			print("Editing file...")
			#File: [0] = time, [1] = left, [2] = right
			with open('datafile.dat', 'rb+') as f: #Since 'done' will be written to the file, we need to remove it
				f.seek(0, 2) #End of file
				size = f.tell() #Tells position of pointer, so entire 'size' of file
				f.truncate(size - 4) #Truncates the file to 4 from the end, deleting the last 4 chars

			tic_edit = time.time()
			
			for line in csv.reader(open('datafile.dat'), delimiter = '\t', skipinitialspace = True):
				lp_current.append(line[1]) #Append respective data to the left lists
				rp_current.append(line[2]) #Append respective data to the right lists
			
			print("Time to edit data: " + str(time.time() - tic_edit))
			
			tic_plotting = time.time()
			#pdb.set_trace() #debugger ** 
			if maketimevec == True: #Runs once
				print("maketimevec == True")
				for line in csv.reader(open('datafile.dat'), delimiter = '\t', skipinitialspace = True): #open up datafile
					t.append(line[0]) #create a time vector
						
				lp_total.append(t) #Append time vector to the first column of left data
				rp_total.append(t) #Append time vector to the first column of right data
				
				lp_current_array = np.float64(lp_current) #Re-assign left and right data as float64 so we can plot it
				rp_current_array = np.float64(rp_current)

				
			
					
				#Filter here
				#lp_current_filtered = butter_bandpass_filter(lp_current_array, lowcut, highcut, fs, order = 2)
				#rp_current_filtered = butter_bandpass_filter(rp_current_array, lowcut, highcut, fs, order = 2)
				
				#y1 = lp_current_filtered
				#y2 = rp_current_filtered
				
				#Initialize figure
				fig = plt.figure()
				fig.subplots_adjust(hspace = 0.5) #Space between subplots
				plt.subplots_adjust(top = 0.85) #Space from top
				plt.suptitle('Live Data', fontsize = 20) #Overall title
				
			
				
				#Top subplot
				ax = fig.add_subplot(211)
				plt.title('Left Pinnae Live Data')
				plt.xlabel('Time [ms]')
				plt.ylabel('Amplitude [V]')
				axes1 = plt.gca() #Setting axis limits and tick size
				axes1.set_ylim([-3,3])
				plt.yticks(np.arange(-3, 4, 1.0))
				
				
				#Bottom subplot
				ax1 = fig.add_subplot(212)
				plt.title('Right Pinnae Live Data')
				plt.xlabel('Time [ms]')
				plt.ylabel('Amplitude [V]')
				axes2 = plt.gca()
				axes2.set_ylim([-3,3])
				#plt.yticks(np.arange(-3, 4, 1.0))
				plt.yticks(np.arange(-3, 4, 1))
				
				#Set & Initialize left and right pinnae plots
				lp_plot, = ax.plot(t, lp_current_array, label = "L", color = 'r', linestyle = '-')
				rp_plot, = ax1.plot(t, rp_current_array, label = "R", color = 'b', linestyle = '-')
				
				maketimevec = False
			
			lp_current_array = np.float64(lp_current)
			rp_current_array = np.float64(rp_current)
				
			#Filter here
			#lp_current_filtered = butter_bandpass_filter(lp_current_array, lowcut, highcut, fs, order = 2)
			#rp_current_filtered = butter_bandpass_filter(rp_current_array, lowcut, highcut, fs, order = 2)
			
			lp_plot.set_ydata(lp_current_array)
			rp_plot.set_ydata(rp_current_array)
			
			#lp_total.append(lp_current_filtered)
			#rp_total.append(rp_current_filtered)
			#lp_raw.append(lp_current)
			lp_total.append(lp_current)
			rp_total.append(rp_current)
			
			#fig.canvas.draw()
			plt.pause(0.00001)
			
			os.remove(cwd + "\datafile.dat")
			print("Time to plot: " + str(time.time() - tic_plotting))
			print("Loop time: " + str(time.time() - tic1))	
			
		
	except TimeoutError:
		print("Time out Error in loop") 
		s.send(b'quit') #quit command 
		s.shutdown(1) #close socket
		s.close()
		sys.exit(1) #exit program 

	except ConnectionAbortedError:
		print("Connection Aborted Error")
		s.send(b'quit')
		s.shutdown(1)
		s.close()
		sys.exit(1)
	except KeyboardInterrupt:
		print("Keyboard Interrupt")
		s.send(b'quit')
		s.shutdown(1)
		s.close()
		sys.exit(1)
	#except file fail:
	#	s.close()	

			#except KeyboardInterrupt:
	#	print("Force Stopped.")
		#Stop program on the Pi: \x003
	
#File making; starts post while loop
lp_total_zipped = list(zip(*lp_total)) #Transposes the left data so that each column is a set of data 
rp_total_zipped = list(zip(*rp_total)) #Transposes the right data so that each column is a set of data 

# try:
	# for i in lp_current:
		# print("currrent "+i+": " + lp_current[i])
# except TypeError:
	# print ("Type error in loop")
	# s.send(b'quit')
	# s.shutdown(1)
	# s.close()
	# sys.exit(1)



print("Creating files for " + str(file_counter) + " iterations...")
try:
	date_time = time.strftime("%d_%m_%Y_%H%M%S")
except:
	date_time = 'hi'
	print("Hi used")
with open('data\\'+'lp_' + date_time + '.dat', 'w', newline = '') as csvfile: #Open left data file for writing
	datawriter = csv.writer(csvfile, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL) #Set csv writer for left data
	for item in lp_total_zipped: #Iterate through the list
		for j in range(len(item)):
			csvfile.write("%.6f\t" % float(item[j])) #Write each line of the final data file
		csvfile.write("\n") #New line
		
with open('data\\'+'rp_' + date_time + '.dat', 'w', newline = '') as csvfile:
	datawriter = csv.writer(csvfile, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for item in rp_total_zipped:
		for k in range(len(item)):
			csvfile.write("%.6f\t" % float(item[k]))
		csvfile.write("\n")
		

		
s.send(b'quit') #Send a quit command to the server

print("Files created!")

print("Overall program time: " + str(time.time() - tic))

#s.shutdown(1)
s.close()
