from __future__ import print_function
import ConfigParser
import string
import random
import re
from collections import Counter
#import pickle
import json
import copy
import itertools
import time
import sys
import os
import csv
import socket
### READ MESSAGE #####

start_time = time.time()

"""
expecting argv to be of length 3.
argv[1] is the config file
argv[2] is player number
argv[3] is offset
argv[4:10] is the weight set
"""

configfilename = sys.argv[1]
#message = json.loads(sys.argv[2])
offset = int(sys.argv[3])
#multipliers = [1,1.4,-1.4,0.2,35,1.3,-28]
#multipliers = , 2.5, 2.5, 14, 27.5, 13.5] # gen 1
multipliers = [0.380178567047442, 0.6120864644845542, 2.149980971221099, 2.474715020475558, 12.965240890748841, 25.768325231286795, 14.766862823640619] # updated by multiplying with stddev from gen 4

def showboard(board):
    #board is a numrows*numcols list    
    
    print('   |  A |  B |  C |  D |  E |  F |  G |  H |  I |  J |  K |  L |  M |  N |  O |')
    print('   ============================================================================')
    
    rownum = 1
    for row in board:
        if rownum < 10:
            print(' ', end = '')
        print(str(rownum) + ' |  ', end = '')
        rownum +=1
        
        for col in row:
            print(col, end=' |  ')
        print('')
        print('   ----------------------------------------------------------------------------')
    
    #print('----------------------------------------------------------------------------')
    
###### MOVE GENERATION #########

def strIntersection(str1, str2):
    for i in str1:
        str3 = ''
        str3 = str3.join(i for i in str1 if i in str2 not in str3)
    return str3
    
def calculateAnchors(board):

    global board_anchorpoints# = [[False]*15]*15
    global board_anchorconstraints# = [[AZ]*15]*15
    
    for i in range(15):
        board_anchorpoints[i] = [False]*15
        board_anchorconstraints[i] = [AZ]*15
        
        for j in range(15):
            board_anchorpoints[i][j] = False
            if ( (i-1)<0 or board[i-1][j]=='.' ) and \
            ( (i+1)>=15 or board[i+1][j]=='.'  ) and \
            ( (j-1)<0 or board[i][j-1]=='.'    ) and \
            ( (j+1)>=15 or board[i][j+1]=='.'  ):
                continue
            if board[i][j]!='.':
                board_anchorpoints[i][j] = False
                board_anchorconstraints[i][j] =  board[i][j]
                continue
    
            
            leftstring = ""
            rightstring = ""
            upstring = ""
            downstring =""
            
            ci = i - 1
            while ci >= 0 and board[ci][j]!='.':
                leftstring = board[ci][j] + leftstring
                ci-=1
                
            ci = i + 1
            while ci < 15 and board[ci][j]!='.':
                rightstring = rightstring + board[ci][j]
                ci+=1
                
            cj = j - 1
            while cj >= 0 and board[i][cj]!='.':
                upstring = board[i][cj] + upstring
                cj-=1
                
            cj = j + 1
            while cj < 15 and board[i][cj]!='.':
                downstring = downstring + board[i][cj]
                cj+=1
            
            
            hpattern = re.compile(leftstring + '([A-Z])' + rightstring)
#            vpattern = re.compile(upstring + '([A-Z])' + downstring)
            
            if len(leftstring + rightstring) > 0:
                hcandidates = ''.join([m.group(1) for m in [hpattern.match(w) for w in lwordlists[len(leftstring + rightstring) + 1]] if m])
            else:
                hcandidates = AZ
                
#            if len(upstring + downstring) > 0:
#                vcandidates = ''.join([m.group(1) for m in [vpattern.match(w) for w in lwordlists[len(upstring + downstring) + 1]] if m])
#            else:
#                vcandidates = AZ
            
#            board_anchorconstraints[i][j] = strIntersection(hcandidates, vcandidates)
            board_anchorconstraints[i][j] = hcandidates            
            #print(i,j,hcandidates,vcandidates)
            if len(board_anchorconstraints[i][j])>0:
                board_anchorpoints[i][j] = True
                
    #return (board_anchorpoints, board_anchorconstraints)    


def genRowWords2(rack, row, anchorpoints, anchorconstraints):

    """
    eg:
        rack = "RECDNAV"
        row = ['.','.','.','.','.','.','.','.','.','.','E','.','.','.','.']
        anchorconstraints = [AZ,AZ,AZ,AZ,AZ,AZ,AZ,'PQS',AZ,'RST',AZ,'P',AZ,AZ,AZ]
        anchorpoints = [False,False,False,False,False,False,False,False,False,False,False,True,False,False,False]
    """
    
    if sum(anchorpoints) == 0:
        return []
#    print(anchorconstraints)  

    blankspresent = len(rack) - len(re.sub('\?', '', rack))
    letters = re.sub('\?', '', rack) + ''.join([x for x in row if x!='.' ]) 
    foundwordlist = []
    movelist = []
    
        
    powerset = itertools.chain.from_iterable(itertools.combinations(letters, r) for r in range(2,len(letters)+1))
    
    for subset in powerset:
        key = ''.join(sorted(subset))
        if key in alphasetdict:
            words = alphasetdict[key]
            for fw in words:
                foundwordlist.append(fw)
                
    foundwordlist = list(set(foundwordlist))
    for fw in foundwordlist:
        for pos in xrange(numcols - len(fw) + 1):
            """ To check:
                1. nothing to the left of start. nothing to the right of end
                2. all the letters in the row letters position are in the right position
                3. at least one letter from the rack is used
                4. at least one anchor point is touching
                5. all anchor constraints are obeyed
                Do all this in one iteration over the wordstring
            """
            racklettersused =""
            
            #1.
            if pos > 0 and row[pos-1]!='.':
#                print(1,pos)
                continue
#            print(pos, fw)
            if pos + len(fw) < numcols and row[pos + len(fw)]!='.':
#                print(2,pos)                
                continue
            
            moveokay = True            
            atleastonerackletterused = False
            touchesanchor = False
            hashword = fw
            
            
            for i,l in enumerate(fw):
                boardpos = pos + i
                
                #2. 
                if row[boardpos]!='.' and row[boardpos]!=l:
                    moveokay = False
#                    print(3,pos)                    
                    break
                
                #3.
                if row[boardpos]=='.':
                    atleastonerackletterused = True
                else:
                    hashword = hashword[:i] + '#' + hashword[i+1:]
                
                #4.
                if anchorpoints[boardpos]:
                    touchesanchor = True
                
                #5.
                if row[boardpos] == '.' and l not in anchorconstraints[boardpos]:
                    moveokay = False
#                    print(4,pos)
                    break
                
                
            if not(moveokay and atleastonerackletterused and touchesanchor):
#                print(5,pos)
                continue
            
            blankedcounterdict = dict(Counter(re.sub('#','',hashword)) - Counter(re.sub('\?', '', rack)))
            blankedletter = ''.join(x*blankedcounterdict[x] for x in blankedcounterdict)  # assumes at most 1 blank
            
            if blankspresent < len(blankedletter):
                continue
            
            if len(blankedletter) > 0:
                #blank included
                for i,l in enumerate(hashword):
                    if l == blankedletter:
                        temphashword = hashword[:i] + l.lower() + hashword[i+1:]
                        movelist.append((pos, temphashword, fw[:i] + l.lower() + fw[i+1:], re.sub('#','', temphashword)))
            else:
                movelist.append((pos, hashword, fw, re.sub('#','',hashword)))
                            
#    print(movelist)
    return movelist
    
                

def genRowWords(rack, row, anchorpoints, anchorconstraints):
    """
    eg:
        rack = "RECDNAV"
        row = ['.','.','.','.','.','.','.','.','.','.','E','.','.','.','.']
        anchorconstraints = [AZ,AZ,AZ,AZ,AZ,AZ,AZ,'PQS',AZ,'RST',AZ,'P',AZ,AZ,AZ]
        anchorpoints = [False,False,False,False,False,False,False,False,False,False,False,True,False,False,False]
    """
    if sum(anchorpoints) ==0:
        return []

    actualrack = rack
    if '?' in rack:
        rack = AZ
    
    regstring = ""
    
    for i in range(15):
        if row[i]!='.':
            regstring+='[' + row[i] + '#]'
        else:
            regstring+='[' + strIntersection(anchorconstraints[i],rack) + '#]'
    
    regstring = '#' + regstring + '#'
    
    
    rejectioncounter = [0,0,0]
    results = []


    checker = re.compile(r'(?=(' + regstring + '))')
#    print(regstring)

    found = checker.finditer(readhashedwordstring)
        
    for match in found:
        w = match.group(1)
        w= w[1:-1]
        start = len(re.search('^#*',w).group(0))
        end = 14 - len(re.search('#*$',w).group(0))
        
        leftbit =""
        x = start - 1
        while x >= 0 and row[x] != '.':
            leftbit = row[x] + leftbit
            x-=1
            
        rightbit = ""
        x = end + 1
        while x < 15 and row[x] != '.':
            rightbit = rightbit + row[x]
            x+=1
            
        actualword = leftbit + w[start:end+1] + rightbit

        
        if not actualword in lwordlists[len(actualword)]: # the effective word is not a word
            rejectioncounter[0]+=1
            continue
        
        if not max([a!='#' and b for a,b in zip(w,anchorpoints)]): # does not touch any anchor point
            rejectioncounter[1]+=1
            continue
        
        lettersadded = [w[i] for i in range(len(w)) if w[i]!='#' and row[i]=='.']
        diffneededtoavailable =  Counter(lettersadded) - Counter(actualrack)       
        numblanks = sum([i=='?' for i in actualrack])
        if len(diffneededtoavailable) > numblanks:
            rejectioncounter[2]+=1
            continue
        
        anno_col = start - len(leftbit)
        anno_word = ""
        ctr = 0
        for letter in actualword:
            pos = start - len(leftbit) + ctr
            if row[pos]=='.':
                anno_word = anno_word + actualword[ctr]
            else:
                anno_word = anno_word + '(' + actualword[ctr] + ')'
            ctr+=1
        
        hashword = re.sub('\(.\)', '#', anno_word)
        letterword = actualword

        results+=[(anno_col,hashword,letterword,''.join(lettersadded))]

#    print(rejectioncounter)       
#    return list(set(results))
    return results

def genAllWords(board, flipped):

    #flipped is a boolean indicating whether the board is transposed or not. This allows annotating the moves correctly
    numoccupied = sum(x!='.' for row in board for x in row)
    movelist = []

    if numoccupied > 0:
        calculateAnchors(board)
    
        for i in range(numrows):
            #print(i) #row/col number
            row = board[i]
            rowmoves = genRowWords2(rack, row, board_anchorpoints[i], board_anchorconstraints[i])
    
            if not flipped:
                for rawmove in rowmoves:
                    #Got:    col, hashword, letterword, newletters
                    #Needed: row, col, 'H'/'V', hashword, letterword, time(useless))
                    formattedmove = (i, rawmove[0], 'H', rawmove[1], rawmove[2], rawmove[3])
                    movelist= movelist + [formattedmove]
            else:
                for rawmove in rowmoves:
                    #Got:    row, hashword, letterword, newletters
                    #Needed: row, col, 'H'/'V', hashword, letterword, time(useless))
                    formattedmove = (rawmove[0], i, 'V', rawmove[1], rawmove[2], rawmove[3])
                    movelist= movelist + [formattedmove]
    else:
        #First Move of the game. No anchors, etc.
        letters = rack
        foundwordlist = []
        powerset = itertools.chain.from_iterable(itertools.combinations(letters, r) for r in range(2,len(letters)+1))
    
        for subset in powerset:
            key = ''.join(sorted(subset))
            if key in alphasetdict:
                words = alphasetdict[key]
                for fw in words:
                    foundwordlist.append(fw)
                    
        foundwordlist = list(set(foundwordlist))
        ccol = numcols //2
        crow = numrows //2
        for w in foundwordlist:
            blankedletter = ''.join(list(Counter(w) - Counter(letters))) # assumes at most 1 blank. Also. if word can be made without blank. we'll ALWAYS prefer to make it that way.

            if len(blankedletter) > 0:
                #blank included
                for i,l in enumerate(w):
                    if l == blankedletter:
                        tempw = w[:i] + l.lower() + w[i+1:]
                        for i in range((ccol - len(w) + 1), ccol + 1):
                            movelist.append((crow, i, 'H', tempw, tempw, tempw))
            else:
                for i in range((ccol - len(w) + 1), ccol + 1):
                    movelist.append((crow, i, 'H', w, w, w))
        
    return movelist
    
    
def scoremove(parsedmove): 
    letterboard = copy.deepcopy(board)
    
    r = parsedmove[0]
    c = parsedmove[1]
    dirc = parsedmove[2]
    parsedword = parsedmove[3]
    actualword = parsedmove[4]
    
    i = 0 
    totalscore = 0
    mainwordscore = 0
    mainwordmultiplier = 1

    for i in range(len(actualword)):
        if parsedword[i] == '#':
            mainwordscore+=tilepoints[actualword[i]]
        else:
            mainwordscore+=(tilepoints[actualword[i]] * lettermultiplier[r][c])
            mainwordmultiplier *= wordmultiplier[r][c]
            
            hasperpendicularplay = False #if there is one, we'll set this to true later.
            perpendicularwordscore = (tilepoints[actualword[i]] * lettermultiplier[r][c])
            perpendicularwordmultiplier = wordmultiplier[r][c]

            #calculate perpendicular word score
            if dirc == 'H':
                rtemp = r-1
                while rtemp >= 0 and letterboard[rtemp][c]!='.':
                    hasperpendicularplay = True
                    perpendicularwordscore += tilepoints[letterboard[rtemp][c]]
                    rtemp-=1
                rtemp = r+1                
                
                while rtemp < numrows and letterboard[rtemp][c]!='.':
                    hasperpendicularplay = True
                    perpendicularwordscore += tilepoints[letterboard[rtemp][c]]
                    rtemp+=1
                
            else:
                ctemp = c-1
                while ctemp >= 0 and letterboard[r][ctemp]!='.':
                    hasperpendicularplay = True
                    perpendicularwordscore += tilepoints[letterboard[r][ctemp]]
                    ctemp-=1
                ctemp = c+1                
                while ctemp < numcols and letterboard[r][ctemp]!='.':
                    hasperpendicularplay = True
                    perpendicularwordscore += tilepoints[letterboard[r][ctemp]]
                    ctemp+=1
            
            perpendicularwordscore *= perpendicularwordmultiplier
            if hasperpendicularplay:
                totalscore += perpendicularwordscore
        
        letterboard[r][c] = actualword[i] #BOARD UPDATED HERE                    
        if dirc == 'H':
            c+=1
        elif dirc =='V':
            r+=1

    
    totalscore+=(mainwordscore*mainwordmultiplier)
    
    
    tilesplayed = [p for p in parsedword if not p=='#']
    ntilesplayed = len(tilesplayed)
    if ntilesplayed == 7:
        totalscore+=50

    return (totalscore, tilesplayed)
def makefeatures_state(board, rack, scorediff):
    """
    STATE FEATURES:
        currentscorediff(+/-)
        
        numtilesleftinbag
        
        numunseenvowels
        numunseenconsonants
        numunseenblanks
        
        numblanksonmyrack
    """
    currentscorediff = scorediff
    
    boardstring = ''.join(''.join(x) for x in board)
    
    tilesonboard = re.sub('\.','',boardstring)
    numtilesonboard = len(tilesonboard)
    
    numvowelsonboard = sum(x in 'AEIOU' for x in tilesonboard)
    numvowelsonrack =  sum(x in 'AEIOU' for x in rack)
    numunseenvowels = 42 - numvowelsonboard - numvowelsonrack 
    
    numconsonantsonboard = sum(x in 'BCDFGHJKLMNPQRSTVWXYZ' for x in tilesonboard)
    numconsonantsonrack =  sum(x in 'BCDFGHJKLMNPQRSTVWXYZ' for x in rack)
    numunseenconsonants = 58 - numconsonantsonboard - numconsonantsonrack
    
    numtilesleftinbag = 0
    if numtilesonboard >= 86:
        numtilesleftinbag = 0
    else:
        numtilesleftinbag = 100 - 14 - (numtilesonboard)
    
    numblanksonmyrack = sum(x=='?' for x in rack)
    numblanksonboard = sum(x.islower() for x in tilesonboard)
    numunseenblanks = 2 - numblanksonmyrack - numblanksonboard
    
    
    featurevec1 = (currentscorediff, numtilesleftinbag, numunseenvowels, numunseenconsonants, (numunseenconsonants-numunseenvowels), numunseenblanks, numblanksonmyrack)
    
    return featurevec1


def makefeatures_stateaction(board, rack, hashmove, movescore, featurevec1):
    
    """
    STATE_ACTION features:
        movescore
        proposedscorediff
        leave:
            length
            consminusvowels
            blanks
            bingoprobonnextdraw(leave+bag):montecarlo
        
        numnewTWSaccessible
        numnew9xaccessible
        numnewDWSaccessible
        numnewLSaccessiblenexttovowely
        "volatility"
        "openingness"
        "closingness"
    """
    fullbag = 'AAAAAAAAABBCCDDDDEEEEEEEEEEEEFFGGGHHIIIIIIIIIJKLLLLMMNNNNNNOOOOOOOOPPQRRRRRRSSSSTTTTTTUUUUVVWWXYYZ'
    
    proposedscorediff = featurevec1[0] + movescore
    
    #leave
    tilestoplay = re.sub('[a-z]', '?', hashmove)
    dictleave = dict(Counter(rack) - Counter(tilestoplay))
    leave = ''.join(x*dictleave[x] for x in dictleave)
        
    l_consminusvowels = sum(x in 'BCDFGHJKLMNPQRSTVWXYZ' for x in leave) - sum(x in 'AEIOU' for x in leave) 
    l_blanks = sum(x=='?' for x in leave)
    
    l_bingoprobnext = 0
    l_enumbingos = 0
    MCtrials = 100
    numtilestodraw = min(featurevec1[1], 7-len(leave))
    tilesonboard = re.sub('[a-z]', '?', re.sub('\.','',boardstring))
    unseentilesdict = dict(Counter(fullbag) - Counter(tilesonboard + tilestoplay))
    unseentiles = ''.join(x*unseentilesdict[x] for x in unseentilesdict)
    

    for i in range(MCtrials):
        hypotheticaldraw = ''.join(random.sample(unseentiles,numtilestodraw))
#        if hashmove == 'DOT':
#            hypotheticaldraw = 'VSR'

        hrack = leave + hypotheticaldraw
        hrack = ''.join(sorted(list(hrack)))
        
#        if hashmove == 'DOT':
            #print(">",numtilestodraw,hypotheticaldraw, hrack)
            #hrack = 'HASTIER'
            #hrack = ''.join(sorted(list(hrack)))

        hnumblanks = sum(x=='?' for x in hrack)
        bingos = []
        
        if hnumblanks == 0:
            if hrack in alphasetdict_0B:
                bingos = alphasetdict_0B[hrack]
        elif hnumblanks ==1:
            bingokey = re.sub('\?', '', hrack)
            if bingokey in alphasetdict_1B:
                bingos = alphasetdict_1B[bingokey]
        else:
            bingokey = re.sub('\?', '', hrack)
            if bingokey in alphasetdict_1B:
                bingos = alphasetdict_1B[bingokey]

            
        l_enumbingos +=len(bingos)
        l_bingoprobnext += (len(bingos) > 0)
    l_bingoprobnext = l_bingoprobnext*1.0 / MCtrials
    l_enumbingos = l_enumbingos*1.0 / MCtrials

    featurevec2 = (movescore, proposedscorediff, len(leave), abs(l_consminusvowels), l_blanks, l_bingoprobnext, l_enumbingos)
#    if l_bingoprobnext > 0:
#        print(featurevec2)
    
    return featurevec2

    


#showboard(board)

#### INITIALIZE #####

with open('clabbersweightfile.txt', 'a') as fw:
    fw.write(str(sys.argv[4:11])+'\n')



#Read config file
config = ConfigParser.RawConfigParser()
config.read(configfilename)

numrows = int(config.get('Board', 'numrows'))
numcols = int(config.get('Board', 'numcols'))

playerInd= sys.argv[2]

HOST = config.get('Agents', 'Agent'+str(playerInd)+'Host')
PORT = int(config.get('Agents', 'Agent'+str(playerInd)+'Port')) + offset

lettermultiplierstring = config.get('Board', 'lettermultiplier').split(',')
lettermultiplier = [[int(k) for k in lettermultiplierstring[i:i+numcols]] for i in range(0, numrows*numcols,numcols)]

wordmultiplierstring = config.get('Board', 'wordmultiplier').split(',')
wordmultiplier = [[int(k) for k in wordmultiplierstring[i:i+numcols]] for i in range(0, numrows*numcols,numcols)]

tilepoints = {L:int(config.get('TilePoints', L)) for L in string.ascii_uppercase+'?'}
tilepoints.update({L:int(config.get('TilePoints', '?')) for L in string.ascii_lowercase}) # basically, also add equivalent of blank points for lower case letters

bagdict = {L:int(config.get('TileDistribution', L)) for L in string.ascii_uppercase+'?'}
bag = list(''.join([L*bagdict[L] for L in string.ascii_uppercase+'?']))

dictionarieslocation = config.get('Meta', 'dictionarieslocation')

#Read weight file
currentdir = os.path.dirname(os.path.abspath(__file__))
"""
fh = open(currentdir + '/weights.txt', "r")
weightstring = fh.readlines()[0].replace("\n", "")
featureweights = [float(w) for w in weightstring.split(',')]
fh.close()
"""
weightstring = sys.argv[4:11] #up till 9th value
featureweights = [multipliers[i]*float(w) for (i,w) in enumerate(weightstring)]


## Initialize constants
AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
board_anchorpoints = [[False]*15]*15
board_anchorconstraints = [[AZ]*15]*15

## Read optimized text files for dictionaries
#This is faster than reading a pickled object (!)


##lwordlists    
fh = open(dictionarieslocation + "/lwordlists.txt", "r")
lines = [w.replace("\n", "") for w in fh.readlines()]
lwordlists = {}
for line in lines:
    linelist = line.split(" ")
    k = int(linelist[0])
    d = {}
    for w in linelist[1:]:
        d[w] = 1
    lwordlists[k] = d
fh.close()
#print('lwordlists', time.time() - start_time)   

###alphasetdict
alphasetdict_0B = {}
fh = open(dictionarieslocation + "/alphasetdict.txt", "r")
lines = [w.replace("\n", "") for w in fh.readlines()]
for line in lines:
    l = line.split(" ")
    k = l[0]
    alphasetdict_0B[k] = l[1:]
fh.close()

alphasetdict_1B = {}        
fh = open(dictionarieslocation + "/alphasetdict1B.txt", "r")
lines = [w.replace("\n", "") for w in fh.readlines()]
alphasetdict_1B = {}
for line in lines:
    l = line.split(" ")
    k = l[0]
    alphasetdict_1B[k] = l[1:]
fh.close()

##### Message Passing 
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect to server and send data
sock.bind((HOST, PORT))
print(HOST + " and " + str(PORT) + "\n")

sock.listen(100)
conn, addr = sock.accept()
print ('connected with' + addr[0] + ":" + str(addr[1]) )

#if message['status']['moverequired'] == False:
#   sys.exit() #In the future, this may be used for some pre-processing
    

while True:

## PARSE MESSAGE

    startime = 0
    endtime = 0

    # Connect to server and send data
    #sock.sendall(data + "\n")

    # Receive data from the server and begin compute
    received = conn.recv(1024)

    print("Received: <" + received + ">")
    if received == None or received == "":
        break

    message = json.loads(received)   

    if message['status']['moverequired'] == False:
        continue

    startime = time.time()

    boardstring = message["board"]
    rack = ''.join(message["rack"])
    numblanks = sum(1 for x in rack if x=='?')

    if numblanks == 0:
        alphasetdict = alphasetdict_0B
    elif numblanks == 1:
        alphasetdict = alphasetdict_1B 
    else:
        alphasetdict = alphasetdict_1B 

    #print('dict objects', time.time() - start_time)   

    board = [list(boardstring)[i:i+numcols] for i in range(0, numrows*numcols,numcols)]

    #print('***********')
    hpossiblemoves = genAllWords(board, False)
    #print(hpossiblemoves[0:9])
    #print('***********')

    numoccupied = sum(x!='.' for row in board for x in row)

    #If it is the first move of the game, the symmetry makes it necessary to consider only one direction
    if numoccupied > 0:
        flippedboard = map(list, zip(*board))
        vpossiblemoves = genAllWords(flippedboard, True) #Warning: Stuff will be overwritten here! We don't care, but beware!
    #    print(vpossiblemoves[0:9])
    #    print('***********')
    else:
        vpossiblemoves = []

    allmoveslist = hpossiblemoves + vpossiblemoves
    #print('Total number of possible moves: ', len(allmoveslist))

    featurevec1 = makefeatures_state(board, rack, message["score"]["me"] - message["score"]["opponent"])

    movefeatures = {}

    for i,move in enumerate(allmoveslist):
        movescore = scoremove(move)[0]
        allmoveslist[i]+=(movescore,)
        #print(move)
        
        
    allmoveslist.sort(key=lambda tup: tup[6], reverse=True)     

    for i,move in enumerate(allmoveslist):

    # <modeling>
        movefeatures[i] = featurevec1 + makefeatures_stateaction(board, rack, move[3], allmoveslist[i][6],featurevec1)
        featurelist = ["currentScoreDifference", "numTilesLeftInBag", "numUnseenVowels", "numUnseenConsonants",  "numUnseenConsonantsMinusNumUnseenVowels", "numUnseenBlanks","numBlanksOnMyRack"] + ["moveScore", "proposedScoreDiff", "leave_length", "leave_numConsonantsMinusVowels", "leave_numBlanks", "leave_bingoProbOnNextDraw", "leave_expectedNumberOfBingosOnNextDraw"]

        reducedfeaturevector = [movefeatures[i][0], movefeatures[i][7], abs(movefeatures[i][10]), movefeatures[i][11], movefeatures[i][12], movefeatures[i][13],1]

        featurelist = ["currentScoreDifference", "moveScore", "leave_AbsnumConsonantsMinusVowels", "leave_numBlanks", "leave_bingoProbOnNextDraw", "leave_expectedNumberOfBingosOnNextDraw", "bias"]


        # w dot phi
        effectivemovescore = sum([featureweights[j] * reducedfeaturevector[j] for j in range(len(reducedfeaturevector))])
        
        allmoveslist[i]+=((effectivemovescore,) + tuple(reducedfeaturevector)) # Appending features and predicted score

    # </modeling>

        
    allmoveslist.sort(key=lambda tup: tup[7], reverse=True) #7th item is the predicted Q value

    if len(allmoveslist) > 0:
        fullmove = allmoveslist[0]
    #    print(fullmove)
        featurevector = fullmove[8:]
        featurelist = ["currentScoreDifference", "moveScore", "leave_AbsnumConsonantsMinusVowels", "leave_numBlanks", "leave_bingoProbOnNextDraw", "leave_expectedNumberOfBingosOnNextDraw", "bias"]

        with open(currentdir + '/datafile', 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=featurelist)
            writer.writerow({featurelist[f]:featurevector[f] for f in range(len(featurelist))})

        row = str(fullmove[0] + 1)
        col = AZ[fullmove[1]]
        
        gcgmove = ""
        if fullmove[2] == 'H':
            gcgmove = row + col + " " + fullmove[4]
        else:
            gcgmove = col + row + " " + fullmove[4]
    else:
        gcgmove = "pass"
    	
    print("Sent: "+gcgmove)
    conn.sendall(gcgmove)
    endtime = time.time()
    print("time consumed is " + str(endtime - startime))
#print(time.time()-start_time)
