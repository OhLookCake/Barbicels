import commands
import re
import sys
import ConfigParser
import json
import socket

#This file acts as a wrapper around Quackle, and translates between the interface and Quackle,
# in both directions

#running: python QuackleWrapper.py [configfile] [jsonmessage]


def formatMove(move):
    """changes quackle move format move to interface move format"""
    #handle for exchanges
    move = move.replace('.', '#', len(move))
    return move

def quackle(gameFile,rack):
    #./test mode='positions' --position='temp.gcg' --report --rack="ABCDEFG"
    
    command  = 'cd '+quacklePath+';' + ' ./test mode="positions" --position="' + gameFile + '" --lexicon="csw12" ' + '--report --rack="' + rack + '" | tail -1 | cut -d, -f 1'
    #print (command)
    output = commands.getoutput(command)
    scoreoutput = re.sub('^.*\=\ ','',output)
    output = re.sub('\(.*','',output)
    #print ("output is "+ output)

    if(output[0]=='-' and output[1]==' '):
        return 'pass'
    elif(output[0]=='-' and output[1].isalpha()):
        return 'exch '+output[1:]
    else:
        return formatMove(output)

pName = []
pDict = []



# main 
if __name__ == '__main__':
    # out = gameFromGcg('logan.gcg')
    config = ConfigParser.RawConfigParser()
    config.read(sys.argv[1])
    playerInd = sys.argv[2]
    gamefile = config.get('Meta', 'gamefile')
    quacklePath = config.get('Agents', 'quacklepath')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HOST = config.get('Agents', 'Agent'+str(playerInd)+'Host')
    PORT = int(config.get('Agents', 'Agent'+str(playerInd)+'Port'))
    # Connect to server and send data
    sock.bind((HOST, PORT))
    print(HOST + " and " + str(PORT) + "\n")
    sock.listen(100)
    conn, addr = sock.accept()
    print ('connected with' + addr[0] + ":" + str(addr[1]) )

    while True:
        # Receive data from the server and begin compute
        received = conn.recv(1024)
        print("Received: <" + received + ">")
        if received == None or received == "":
            break
        message = json.loads(received)   
        ###########
        ## PARSE MESSAGE
        if message['status']['moverequired'] == False:
            continue
        rack = ''.join(message["rack"])
        gcgmove = quackle(gamefile, rack)
        conn.sendall(gcgmove)
    sock.close()

