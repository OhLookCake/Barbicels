import commands
import re
import sys
import ConfigParser
import json

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

    output = commands.getoutput(command)
    scoreoutput = re.sub('^.*\=\ ','',output)
    output = re.sub('\(.*','',output)

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
    gamefile = config.get('Meta', 'gamefile')
    quacklePath = config.get('Agents', 'quacklepath')
    msg = json.loads(sys.argv[2])
    rack = ''.join(msg["rack"])
    out = quackle(gamefile, rack)
    print(out)
