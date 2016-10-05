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



class Move:
    def __init__(self, category, startrow, startcol, direction, word, tileword):
        #category is 'P'/'E'/'R'  (Pass/Exchange/Regular)
        #startrow, starcol are integers 0 indexed
        #direction is uppercase V or H
        # word has blank lowercased already
        #Eg. 5,0,'V','TaBLE', 'TaB#E'

        self.category = category
        self.startrow = startrow - 1
        self.startcol = startcol - 1
        self.direction = direction
        self.word = word
        self.tileword = tileword
        self.score = 0
        self.features = []

    def translateMoveToGcg(move):
        """Translates move to gcg format
        """
        cols = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']
        if self.direction=='H':
            gcgmove  = ''.join([str(self.startrow+1), cols[self.startcol]])
        else:
            gcgmove  = ''.join([cols[self.startcol], str(self.startrow+1)])

        return gcgmove

class Node:
    def __init__(self, move, board, mytiles, opptiles, scorediff, onturn):
        self.move = move
        self.board = board
        self.mytiles = mytiles #list
        self.opptiles = opptiles #list
        self.scorediff = scorediff
        self.onturn = onturn
        self.passcount = 0
        self.value = 0



def updateboard(board, move):
    r = move.startrow
    c = move.startcol
    dirc = move.direction
    parsedword = move.tileword
    actualword = move.word
    i = 0
    for i in range(len(actualword)):
        if parsedword[i]!='#':
            board[r][c] = parsedword[i]

        if dirc == 'H':
            c+=1
        elif dirc =='V':
            r+=1

    


def evaluateMove(startnode, currentdepth):
    print("\n DEPTH " + str(currentdepth))

    if startnode.onturn == 0:    #OUR AGENT
        if len(startnode.opptiles) == 0: # the game has actually ended, a move shouldn't be played
            print("HERE1")
            rackbonus = 2 * sum([tilepoints[x] for x in startnode.mytiles])
            return (startnode.scorediff - rackbonus)

        moves = genAllWords(startnode.board, False, ''.join(startnode.mytiles))
        moves+=genAllWords(startnode.board, True, ''.join(startnode.mytiles))
    else:                       #OPPONENT
        if len(startnode.mytiles) == 0: # the game has actually ended, a move shouldn't be played
            print("HERE2")
            rackbonus = 2 * sum([tilepoints[x] for x in startnode.opptiles])
            return (startnode.scorediff + rackbonus)
        moves = genAllWords(startnode.board, False, ''.join(startnode.opptiles))
        moves+=genAllWords(startnode.board, True, ''.join(startnode.opptiles))

    print("#MOVES"+str(len(moves)))

    #TODO: add pass ka mechanic
    # moves.append(passing move)
    ctr = 1
    nodelist = []
    for move in moves:
        print("counter="+str(ctr))
        ctr+=1
        movenode = copy.deepcopy(startnode)
        print("Move " +str(move.startrow)+" "+str(move.startcol)+" "+str(move.tileword))
        updateboard(movenode.board, move)

        movenode.move = move
        if startnode.onturn == 0:
            movenode.mytiles = list(Counter(startnode.mytiles) - Counter(re.sub('#', '', move.tileword)))
            movescore, blah = scoremove(move, board)
            movenode.scorediff += movescore
            movenode.onturn = 1
        else:
            movenode.opptiles = list(Counter(startnode.opptiles) - Counter(re.sub('#', '', move.tileword)))
            movescore, blah = scoremove(move, board)
            movenode.scorediff -= movescore
            movenode.onturn = 0
        #if move is pass update passcount

        movevalue = evaluateMove(movenode, currentdepth+1)
        movenode.value = movevalue
        nodelist.append(movenode)

    if startnode.onturn==0:
        return max(nodelist, key=lambda n: n.value)
    else:
        return min(nodelist, key=lambda n: n.value)


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
            #vpattern = re.compile(upstring + '([A-Z])' + downstring)
            
            if len(leftstring + rightstring) > 0:
                hcandidates = ''.join([m.group(1) for m in [hpattern.match(w) for w in lwordlists[len(leftstring + rightstring) + 1]] if m])
            else:
                hcandidates = AZ
            
            board_anchorconstraints[i][j] = hcandidates            
            if len(board_anchorconstraints[i][j])>0:
                board_anchorpoints[i][j] = True
                
    #return (board_anchorpoints, board_anchorconstraints)    


def genRowWords2(rack, row, anchorpoints, anchorconstraints):
    """
    eg:
    rack = "RECDNAV"
    row = ['.','.','.','.','.','.','.','.','.','.','E','.','.','.','.']
    anchorconstraints = [AZ,AZ,AZ,AZ,AZ,AZ,AZ,'PQS',AZ,'RST',AZ,'P',AZ,AZ,AZ]
    anchorpoints = [False,False,True,False,False,False,False,False,False,False,False,True,False,False,False]
    """
    
    if sum(anchorpoints) == 0:
        return []
     

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
            #    print(1,pos)
                continue
            #print(pos, fw)
            if pos + len(fw) < numcols and row[pos + len(fw)]!='.':
            #    print(2,pos)                
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
                #    print(3,pos)                    
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
                #    print(4,pos)
                    break
                
                
            if not(moveokay and atleastonerackletterused and touchesanchor):
            #    print(5,pos)
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

                            
    #print(movelist)
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

def genAllWords(board, flipped, rack):

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


    MOVELIST = []
    for move in movelist:
        m = Move('R', move[0]+1, move[1]+1, move[2], move[4], move[3])
        MOVELIST.append(m)
        
    return MOVELIST
    
    
def scoremove(parsedmove, xboard): 
    copyofboard = copy.deepcopy(xboard)
    
    r = parsedmove.startrow
    c = parsedmove.startcol
    dirc = parsedmove.direction
    parsedword = parsedmove.tileword
    actualword = parsedmove.word
    
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
                while rtemp >= 0 and copyofboard[rtemp][c]!='.':
                    hasperpendicularplay = True
                    perpendicularwordscore += tilepoints[copyofboard[rtemp][c]]
                    rtemp-=1
                rtemp = r+1                
                
                while rtemp < numrows and copyofboard[rtemp][c]!='.':
                    hasperpendicularplay = True
                    perpendicularwordscore += tilepoints[copyofboard[rtemp][c]]
                    rtemp+=1
                
            else:
                ctemp = c-1
                while ctemp >= 0 and copyofboard[r][ctemp]!='.':
                    hasperpendicularplay = True
                    perpendicularwordscore += tilepoints[copyofboard[r][ctemp]]
                    ctemp-=1
                ctemp = c+1                
                while ctemp < numcols and copyofboard[r][ctemp]!='.':
                    hasperpendicularplay = True
                    perpendicularwordscore += tilepoints[copyofboard[r][ctemp]]
                    ctemp+=1
            
            perpendicularwordscore *= perpendicularwordmultiplier
            if hasperpendicularplay:
                totalscore += perpendicularwordscore
        
        copyofboard[r][c] = actualword[i] #COPY OF BOARD UPDATED HERE                    
        if dirc == 'H':
            c+=1
        elif dirc =='V':
            r+=1

    
    totalscore+=(mainwordscore*mainwordmultiplier)
    
    
    tilesplayed = [p for p in parsedword if not p=='#']
    ntilesplayed = len(tilesplayed)
    if ntilesplayed == 7:
        totalscore+=50

    return (totalscore, copyofboard)

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
    

    MCtrials = 100
    numtilestodraw = min(featurevec1[1], 7-len(leave))
    tilesonboard = re.sub('[a-z]', '?', re.sub('\.','',boardstring))
    unseentilesdict = dict(Counter(fullbag) - Counter(tilesonboard + tilestoplay))
    unseentiles = ''.join(x*unseentilesdict[x] for x in unseentilesdict)
    
    l_bingoprobnext, l_enumbingos = sampleFromBag(leave, numtilestodraw, unseentiles, MCtrials)


    featurevec2 = (movescore, proposedscorediff, len(leave), l_consminusvowels, l_blanks, l_bingoprobnext, l_enumbingos)
    #if l_bingoprobnext > 0:
    #    print(featurevec2)
    
    return featurevec2






########## GLOBAL / MAIN ###########
def sampleFromBag(leave, numtilestodraw, unseentiles, MCtrials):
    l_bingoprobnext = 0
    l_enumbingos = 0
    
    for i in range(MCtrials):
        hypotheticaldraw = ''.join(random.sample(unseentiles,numtilestodraw))
        #if hashmove == 'DOT':
        #    hypotheticaldraw = 'VSR'

        hrack = leave + hypotheticaldraw
        hrack = ''.join(sorted(list(hrack)))
        
        # if hashmove == 'DOT':
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

    return (l_bingoprobnext, l_enumbingos)




"""
expecting argv to be of length 3.
argv[1] is the config file
argv[2] is player number
argv[3] is offset
argv[4:8] is the weight set
"""
start_time = time.time()
configfilename = sys.argv[1]
#message = json.loads(sys.argv[2])
offset = int(sys.argv[3])
#multipliers = [1,1.4,-1.4,0.2,35,1.3,-28]
multipliers = [0.25, 1.5, 2.5, 5, 2]
playerInd= sys.argv[2]

#### INITIALIZE #####

#Read config file
config = ConfigParser.RawConfigParser()
config.read(configfilename)

numrows = int(config.get('Board', 'numrows'))
numcols = int(config.get('Board', 'numcols'))


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

weightstring = sys.argv[4:9] #up till 8th value
featureweights = [multipliers[i]*float(w) for (i,w) in enumerate(weightstring)]

## Initialize constants
AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
fullbag = 'AAAAAAAAABBCCDDDDEEEEEEEEEEEEFFGGGHHIIIIIIIIIJKLLLLMMNNNNNNOOOOOOOOPPQRRRRRRSSSSTTTTTTUUUUVVWWXYYZ'
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

##############################################
##############################################
##############################################

print('party')
##### TESTING ####
rack = "ACE"
row = ['.','.','.','.','.','.','.','.','.','.','E','.','S','.','.']
anchorconstraints = [AZ] * 15
anchorpoints = [False,False,True,False,False,False,False,False,False,True,False,True,False,False,False]

numblanks = sum(1 for x in rack if x=='?')

if numblanks == 0:
    alphasetdict = alphasetdict_0B
elif numblanks == 1:
    alphasetdict = alphasetdict_1B 
else:
    alphasetdict = alphasetdict_1B     

#print(genRowWords2(rack, row, anchorpoints, anchorconstraints))

##############################################
##############################################
##############################################

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
    scorediff = message["score"]["me"] - message["score"]["opponent"]

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
    hpossiblemoves = genAllWords(board, False, rack)
    #print(hpossiblemoves[0:9])
    #print('***********')

    numoccupied = sum(x!='.' for row in board for x in row)

    #If it is the first move of the game, the symmetry makes it necessary to consider only one direction
    if numoccupied > 0:
        flippedboard = map(list, zip(*board))
        vpossiblemoves = genAllWords(flippedboard, True, rack) #Warning: Stuff will be overwritten here! We don't care, but beware!
    else:
        vpossiblemoves = []

    allmoveslist = hpossiblemoves + vpossiblemoves
    #print('Total number of possible moves: ', len(allmoveslist))

    MOVES = allmoveslist

    if False: #86 - numoccupied <= 0:
        print('ENDGAME HAS BEGUN')

        mytiles = list(rack)
        boardtiles = [x for x in boardstring if x!='.']
        boardtiles = [x if x in AZ else '?' for x in boardtiles]

        dictopponent = dict(Counter(fullbag) - Counter(boardtiles) - Counter(mytiles))
        opptiles = ''.join(x*dictopponent[x] for x in dictopponent)
        print(opptiles)


        
        for move in allmoveslist[0:5]:
            movenode = Node(move, copy.deepcopy(board), mytiles, opptiles, scorediff, 1)
            print(move)
            print(evaluateMove(movenode, 1))
            
    else:
        # score according to our model, select best from the approximation

        featurevec1 = makefeatures_state(board, rack, message["score"]["me"] - message["score"]["opponent"])

        movefeatures = {}

        for i,move in enumerate(allmoveslist):
            move.score = scoremove(move, board)[0]
            #print(move)
            
            
        allmoveslist.sort(key=lambda m : m.score, reverse=True)     

        for i,move in enumerate(allmoveslist):

        # <modeling>
            movefeatures[i] = featurevec1 + makefeatures_stateaction(board, rack, move.tileword, allmoveslist[i].score,featurevec1)
            featurelist = ["currentScoreDifference", "numTilesLeftInBag", "numUnseenVowels", "numUnseenConsonants",  "numUnseenConsonantsMinusNumUnseenVowels", "numUnseenBlanks","numBlanksOnMyRack"] + ["moveScore", "proposedScoreDiff", "leave_length", "leave_numConsonantsMinusVowels", "leave_numBlanks", "leave_bingoProbOnNextDraw", "leave_expectedNumberOfBingosOnNextDraw"]

            reducedfeaturevector =  [movefeatures[i][7], abs(movefeatures[i][10]), movefeatures[i][11], movefeatures[i][12], movefeatures[i][13]]

            featurelist = ["moveScore", "leave_NumConsonantsMinusVowels", "leave_numBlanks", "leave_bingoProbOnNextDraw", "leave_expectedNumberOfBingosOnNextDraw"]


            # w dot phi
            effectivemovescore = sum([featureweights[j] * reducedfeaturevector[j] for j in range(len(reducedfeaturevector))])
            
            allmoveslist[i].features = ((effectivemovescore,) + tuple(reducedfeaturevector)) # Features and predicted score

        # </modeling>

            
        allmoveslist.sort(key=lambda m: m.features[0], reverse=True) #0th item is the predicted Q value


        if len(allmoveslist) > 0:
            fullmove = allmoveslist[0]
        #    print(fullmove)
            featurevector = fullmove.features
            featurelist = ["moveScore", "leave_NumConsonantsMinusVowels", "leave_numBlanks", "leave_bingoProbOnNextDraw", "leave_expectedNumberOfBingosOnNextDraw"]

            row = str(fullmove.startrow + 1)
            col = AZ[fullmove.startcol]
            
            gcgmove = ""
            if fullmove.direction == 'H':
                gcgmove = row + col + " " + fullmove.word
            else:
                gcgmove = col + row + " " + fullmove.word
        else:
            gcgmove = "pass"

        movescore = fullmove.score #also = fullmove.features[1]
        print("Sent: "+gcgmove+" ("+str(movescore)+")")
        conn.sendall(gcgmove)
        endtime = time.time()
        print("time consumed is " + str(endtime - startime))





