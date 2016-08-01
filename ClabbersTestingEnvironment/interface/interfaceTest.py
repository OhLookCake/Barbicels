import socket
import time
HOST = "localhost"
PORT = 9000
def playFunc(ind, sock):
	HOST = "localhost"
	PORT = 9000

	# Create a socket (SOCK_STREAM means a TCP socket)
	
	starttime = 0
	endtime = 0
	message = str(ind)
	# Connect to server and send data
	print(HOST + " and " + str(PORT) + "\n" + message)
	

	sock.sendall(message + "\n")
	starttime = time.time()

	# Receive data from the server and shut down
	received = sock.recv(1024)
	endtime = time.time()


	print("Received: " + received)

	timeconsumed = endtime - starttime
	return (received, timeconsumed)
if __name__ == '__main__':
	i = 0
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#sock.setblocking(1)
	sock.connect((HOST, int(PORT)) )
	for i in range (200):
		playFunc(i, sock)
	sock.close()