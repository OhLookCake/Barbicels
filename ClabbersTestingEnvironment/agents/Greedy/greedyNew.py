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
import socket

### READ MESSAGE #####

random.seed(1)
start_time = time.time()

"""
expecting argv to be of length 3. 


sys.argv[2] is the player index, 1 or 2

The message is the json in the expected format - enclosed in quotes.
So that python interprets it as one long string

"""


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


def genRowWords2(rack, row, anchorpoints, anchorconstraints, alphasetdict):

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
#                   print(4,pos)
                    break
                
                
            if not(moveokay and atleastonerackletterused and touchesanchor):
#               print(5,pos)
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

def genAllWords(board, flipped,alphasetdict ):

    #flipped is a boolean indicating whether the board is transposed or not. This allows annotating the moves correctly
    numoccupied = sum(x!='.' for row in board for x in row)
    movelist = []

    if numoccupied > 0:
        calculateAnchors(board)
    
        for i in range(numrows):
            #print(i) #row/col number
            row = board[i]
            rowmoves = genRowWords2(rack, row, board_anchorpoints[i], board_anchorconstraints[i], alphasetdict)
    
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
##### Begin main func


configfilename = sys.argv[1]
#message = json.loads(sys.argv[2])
playerInd = int(sys.argv[2])


    

#### INITIALIZE #####

#Read config file
config = ConfigParser.RawConfigParser()
config.read(configfilename)

HOST = config.get('Agents', 'Agent'+str(playerInd)+'Host')
PORT = int(config.get('Agents', 'Agent'+str(playerInd)+'Port'))

numrows = int(config.get('Board', 'numrows'))
numcols = int(config.get('Board', 'numcols'))

lettermultiplierstring = config.get('Board', 'lettermultiplier').split(',')
lettermultiplier = [[int(k) for k in lettermultiplierstring[i:i+numcols]] for i in range(0, numrows*numcols,numcols)]

wordmultiplierstring = config.get('Board', 'wordmultiplier').split(',')
wordmultiplier = [[int(k) for k in wordmultiplierstring[i:i+numcols]] for i in range(0, numrows*numcols,numcols)]

tilepoints = {L:int(config.get('TilePoints', L)) for L in string.ascii_uppercase+'?'}
tilepoints.update({L:int(config.get('TilePoints', '?')) for L in string.ascii_lowercase}) # basically, also add equivalent of blank points for lower case letters

bagdict = {L:int(config.get('TileDistribution', L)) for L in string.ascii_uppercase+'?'}
bag = list(''.join([L*bagdict[L] for L in string.ascii_uppercase+'?']))

dictionarieslocation = config.get('Meta', 'dictionarieslocation')


###### Read optimized text files
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
#print('lwordlists', time.time() - start_time)   

alphasetdict = {}    
#if numblanks == 0:
fh = open(dictionarieslocation + "/alphasetdict.txt", "r")
lines = [w.replace("\n", "") for w in fh.readlines()]
alphasetdict0 ={}
for line in lines:
    l = line.split(" ")
    k = l[0]
    alphasetdict0[k] = l[1:]
#elif numblanks == 1:
fh = open(dictionarieslocation + "/alphasetdict1B.txt", "r")
lines = [w.replace("\n", "") for w in fh.readlines()]
alphasetdict1 ={}
for line in lines:
    l = line.split(" ")
    k = l[0]
    alphasetdict1[k] = l[1:]
#else:
#2 blanks
fh = open(dictionarieslocation + "/alphasetdict2B.txt", "r")
lines = [w.replace("\n", "") for w in fh.readlines()]
alphasetdict2 ={}
for line in lines:
    l = line.split(" ")
    k = l[0]
    alphasetdict2[k] = l[1:]
#########
## Initialize constants
AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
board_anchorpoints = [[False]*15]*15
board_anchorconstraints = [[AZ]*15]*15


##### Message Passing 
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect to server and send data
sock.bind((HOST, PORT))
print(HOST + " and " + str(PORT) + "\n")

sock.listen(100)
conn, addr = sock.accept()
print ('connected with' + addr[0] + ":" + str(addr[1]) )

message = json.loads('{"status":{"moverequired":"blah"}}')
while True:

    startime = 0
    endtime = 0

    # Connect to server and send data
    #sock.sendall(data + "\n")

    # Receive data from the server and begin compute
    received = conn.recv(1024)
    print(message['status']['moverequired'])
    print("Received: [" + received + "]")
    message = json.loads(received)   

    #print(HOST + " and " + str(PORT) + "\n" + str(message))


    #print('***********')


    ###########
    ## PARSE MESSAGE
    if message['status']['moverequired'] == False:
        print("MOVENOTREQUIRED")
        continue
    boardstring = message["board"]
    rack = ''.join(message["rack"])
    numblanks = sum(1 for x in rack if x=='?')
    board = [list(boardstring)[i:i+numcols] for i in range(0, numrows*numcols,numcols)]


    #showboard(board)

    ####New addition
    if numblanks == 0:
        alphasetdict = alphasetdict0
    elif numblanks == 1:
        alphasetdict = alphasetdict1
    else:
        alphasetdict = alphasetdict2
    starttime = time.time()

    hpossiblemoves = genAllWords(board, False, alphasetdict)
    #print(hpossiblemoves[0:9])
    #print('***********')

    numoccupied = sum(x!='.' for row in board for x in row)

    #If it is the first move of the game, the symmetry makes it necessary to consider only one direction
    if numoccupied > 0:
        flippedboard = map(list, zip(*board))
        vpossiblemoves = genAllWords(flippedboard, True, alphasetdict) #Warning: stuff will be overwritten here! We don't care, but beware!
    #    print(vpossiblemoves[0:9])
    #    print('***********')
    else:
        vpossiblemoves = []

    endtime = time.time()
    timeconsumed = endtime - starttime
    print ("\nTime consumed was " +str(timeconsumed))
    allmoveslist = hpossiblemoves + vpossiblemoves
    #print('Total number of possible moves: ', len(allmoveslist))


    for i,move in enumerate(allmoveslist):
        allmoveslist[i]+=(scoremove(move)[0],)
        
    allmoveslist.sort(key=lambda tup: tup[6], reverse=True)     
    #for move in allmoveslist[0:10]:
    #    print(move)

    #print('end', time.time() - start_time)    
    if len(allmoveslist) > 0:
    	fullmove = allmoveslist[0]
    	row = str(fullmove[0] + 1)
    	col = AZ[fullmove[1]]
    	
    	gcgmove = ""
    	if fullmove[2] == 'H':
    	    gcgmove = row + col + " " + fullmove[4]
    	else:
    	    gcgmove = col + row + " " + fullmove[4]
    else:
    	gcgmove = "pass"

    	
    print("Sent: " + gcgmove)# + ' ' + str(fullmove[6]))
    conn.sendall(gcgmove)
    #sock.close()

    

