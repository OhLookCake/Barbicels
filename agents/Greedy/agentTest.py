import socket
import time

HOST = "localhost"
PORT = 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.setblocking(1)
# Connect to server and send data
sock.bind((HOST, PORT))
print(HOST + " and " + str(PORT) + "\n")

sock.listen(100)
conn, addr = sock.accept()
print ('connected with' + addr[0] + ":" + str(addr[1]) )
ind = 0
while True:
    ind  = ind+1
    startime = 0
    endtime = 0
    gcgmove = str((ind+1)**2 )
    # Connect to server and send data
    #sock.sendall(data + "\n")

    # Receive data from the server and begin compute
    received = conn.recv(1024)

    print("Received: " + received)
    #message = json.loads(received)   
    starttime = time.time()

    print(HOST + " and " + str(PORT) + "\n" + gcgmove)

    print("Move is " + gcgmove)# + ' ' + str(fullmove[6]))
    #time.sleep(2)
    #sock.connect((HOST, PORT))
    conn.send(gcgmove)
    endtime = time.time()