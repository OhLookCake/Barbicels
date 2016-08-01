from __future__ import print_function
import ConfigParser
import string
import random
import re
from collections import Counter
import time
import json
import commands
import sys

#### INITIALIZE #####
random.seed(sys.argv[1])

#changes added by vivek

#-------------------------------------------------------
#Read config file
config = ConfigParser.RawConfigParser()
config.read('../config.cfg')

numrows = int(config.get('Board', 'numrows'))
numcols = int(config.get('Board', 'numcols'))
centresquare = (numrows // 2, numcols //2) #This is effectively rounded up in 0-index

lettermultiplierstring = config.get('Board', 'lettermultiplier').split(',')
lettermultiplier = [[int(k) for k in lettermultiplierstring[i:i+numcols]] for i in range(0, numrows*numcols,numcols)]

wordmultiplierstring = config.get('Board', 'wordmultiplier').split(',')
wordmultiplier = [[int(k) for k in wordmultiplierstring[i:i+numcols]] for i in range(0, numrows*numcols,numcols)]

initialboardstring = config.get('Board', 'initialboard').split(',')
initialboard = [initialboardstring[i:i+numcols] for i in range(0, numrows*numcols,numcols)]
letterboard = initialboard

tilepoints = {L:int(config.get('TilePoints', L)) for L in string.ascii_uppercase+'?'}
tilepoints.update({L:int(config.get('TilePoints', '?')) for L in string.ascii_lowercase}) # basically, also add equivalent of blank points for lower case letters

bagdict = {L:int(config.get('TileDistribution', L)) for L in string.ascii_uppercase+'?'}
bag = list(''.join([L*bagdict[L] for L in string.ascii_uppercase+'?']))

startplayer = int(config.get('Game', 'startplayer'))
if startplayer not in [1,2]:
    startplayer = int(round(random.random())) + 1
activeplayer = startplayer

#commands for agent call
cmdPlayer = [0,0,0]
cmdPlayer[1] = config.get('Agents','Agent1Command')
cmdPlayer[2] = config.get('Agents','Agent2Command')
playernames = ['', '', '']
playernames[1] = config.get('Agents','Agent1Name')
playernames[2] = config.get('Agents','Agent2Name')

score = [0, int(config.get('Game', 'initialscore1')) , int(config.get('Game', 'initialscore2'))]
secondsremaining =  [0, int(config.get('Game', 'totalseconds1')), int(config.get('Game', 'totalseconds2'))]
rack = [None, None, None]

#display flags 
#show messages passed to agents?
showMessages = ['','','']
showMessages[1] = config.get('Display','agent1ShowMessages')
showMessages[2] = config.get('Display','agent2ShowMessages')

#show Board after each move? If this is true, the previous value is ignored.
showBoardAtEveryMove = ['','','']
showBoardAtEveryMove[1] = config.get('Display','agent1ShowBoardAtEveryMove')
showBoardAtEveryMove[2] = config.get('Display','agent2ShowBoardAtEveryMove')
# print(showMessages,showBoardAtEnd,showBoardAtEveryMove)


dictfile = config.get('Meta', 'dictionaryfile')
gamefile = config.get('Meta', 'gamefile')

fh = open(dictfile, 'r')
wordlist = {w.replace("\n", "").upper():1 for w in fh.readlines()}

##### FUNCTIONS #######

def throwerror(errcode):
    if errcode == 12:
        print("Move cannot play on board.")
    elif errcode == 11:
        print("Unparseable move. Verify format.")
    elif errcode == 31:
        print("Internal error: Attempt to draw too many tiles")
    elif errcode == 41:
        print("The rack does not contain all the tiles to play that move")
    elif errcode == 42:
        print("Unplayable move")
    elif errcode == 43:
        print("Move goes outside the board")
    elif errcode == 44:
        print("The move forms an invalid word")
    elif errcode == 45:
        print("The first move must cover the centre square")
    elif errcode == 46:
        print("Preceding or trailing tiles on board")



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


def showall():

#    mixboard = copy.copy(letterboard)
#    for i in xrange(numrows):
#        for j in xrange(numcols):
#            if letterboard[i][j] == '.':
#                if lettermultiplier[i][j]>1:
#                    mixboard[i][j] = str(lettermultiplier[i][j]) + 'l'
#                elif wordmultiplier[i][j] > 1:
#                    mixboard[i][j] = str(wordmultiplier[i][j]) + 'w'
#                else:
#                    mixboard[i][j] = ' .'
#            else:
#                mixboard[i][j] = ' ' + letterboard[i][j]
#
    showboard(letterboard)
    for player in [1,2]:
        #print("Player" + str(player), end='')
        print(playernames[player], end='')

        if activeplayer == player:
            print('*: ', end='')
        else:
            print(': ', end='')
        print(''.join(rack[player]))
        print('Score ' + str(score [player]))
        print('')

def showallgameover():
    showboard(letterboard)
    print('\nGAME OVER')

    for player in [1,2]:
        #print("Player" + str(player)+ ': ', end='')
        print(playernames[player] + ': ', end='')
        if len(rack[player]) == 0:
            print('-')
        else:
            print(''.join(rack[player]))
        print('Score ' + str(score[player]), end = '')
        if score[player] > score[3 - player]:
            print(' WINS')
        elif score[player] < score[3 - player]:
            print(' LOSES')
        else:
            print('TIES')

        print('')


def checkword(word):
    return word.upper() in wordlist

def translateMoveToGcg(move):
    """Translates move to gcg format
    """
    cols = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']
    if move[2]=='H':
        move  = ''.join([str(move[0]+1),cols[move[1]]])
    else:
        move = ''.join([cols[move[1]],str(move[0]+1)])
    return move


def drawtiles(k):
    """
    Returns k tiles from the bag's current distribution, and updates the bag to remove those tiles
    In case of attempt to draw more tiles than in the bag, returns None
    """
    if len(bag) < k:
        errcode = 31
        throwerror(errcode)
        return None
    tiles = [bag.pop(random.randrange(len(bag))) for _ in xrange(k)]
    return tiles

def INVOKEprog(player, stringboard, thisrack, agentscore, opponentscore, secondstogo, errcode, moverequired, endofgameflag):

    """
    moverequired = True
        implies it is the agent's move to play and their clock is running. A response is expected.
    moverequired = False
        implies it is the opponent's turn to play. The message is sent to update the agent with the new drawn tiles.
    """

    #dictdatatosend=(stringboard, thisrack, agentscore, opponentscore, secondstogo, errcode, moverequired, endofgameflag)
    dictdatatosend={}
    dictdatatosend['board'] = stringboard
    dictdatatosend['rack'] = thisrack
    dictdatatosend['score'] = {}
    dictdatatosend['score']['me'] = agentscore
    dictdatatosend['score']['opponent'] = opponentscore
    dictdatatosend['secondstogo'] = secondstogo
    dictdatatosend['errcode'] = errcode
    dictdatatosend['status'] = {}
    dictdatatosend['status']['moverequired'] = moverequired
    dictdatatosend['status']['endofgame'] = endofgameflag
    #dictdatatosend = (stringboard, thisrack, agentscore, opponentscore, secondstogo, errcode, moverequired, endofgameflag)

    datatosend = json.dumps(dictdatatosend)

    # if moverequired:
    #     starttime = time.time()
    #     move = raw_input(str(datatosend)+'\n') #player  'player' 's setting
    #     endtime = time.time()
    #     timeconsumed = endtime - starttime
    #     return (move, timeconsumed)
    if moverequired:
        starttime = time.time()
        
        message = str(datatosend)

        if showBoardAtEveryMove[player]=='True':
            showboard(letterboard)
            print("Rack: " + ''.join(rack[player]))
            for p in [1,2]:
                #print("Player" + str(player), end='')
                print(playernames[p], end='')

                if activeplayer == p:
                    print('*: ', end='')
                else:
                    print(': ', end='')
                
                print('Score ' + str(score [p]))

        cmd = cmdPlayer[player]+" '"+ re.sub('\'', '\"', message) + "'"

        if showMessages[player]=='True':
            print("Message to ", playernames[player])
            print(str(datatosend))

        move = commands.getoutput(cmd)

        print(str(move))
        endtime = time.time()
        timeconsumed = endtime - starttime
        return (move, timeconsumed)
    else:
	# pass
        if showMessages[player]=='True':
            print("Message to ", playernames[player])
            print(str(datatosend))



def parsemove(move):
    """ Moveformat:
        Startingsquare in format like:  F3/10B/8,5,H/6,4,V
            F3: row3, column6, VERTICAL
            10B: row10, column2, HORIZONTAL
            8,5,H: row8, column5, HORIZONTAL (row is always first)
            6,4,V: row6, column4, VERTICAL (row is always first)
        <space>
        word to be played in CAPS. if a blank is introduced, use lowercase letter to indicate blank
        existing letters on the board that are played through NEED to be mentioned either enclosed in (), or as '#'
        Examples:
            MA(C)HIN(E)
            MA(C)HIN#
            MA#HIN#
            CREaT(I)ON
            DIReC(T)(O)R
            (SPEAK)ER
            (#####)ER

        For a pass move:
            Pass OR pass
        For an exchange move:
            exch<space>tiles to exchange.
            E.g.: exch AUUI

        Move examples:
            3B TRIA(N)GLE
            F4 SKID
            E1 T#BLE
            E1 T(A)BLE
            6G (M)yTHS
            B3 (WHISK)ED
            B3 (W)(H)(I)(S)(K)ED
            B3 #####ED
            exch VVUWP
            Exch Q
            Pass

    """
    parseerror = False

    move = move.strip()
    movesplit = move.split()
    loc= None
    word = None

    if len(movesplit) == 2:
        loc = movesplit[0]
        word = movesplit[1]
    elif len(movesplit) == 1:
        loc = movesplit[0]
    else:
        parseerror = True

    if parseerror:
        return (None, parseerror)

    # Play, Exch, or Pass
    if loc.lower() == 'pass':
        return (('pass',''), None)
    if loc.lower() == 'exch':
        if word is not None and word != '' and all([char in string.ascii_letters for char in word]):
            return (('exch', word.upper()), False)
        else:
            parseerror = True

    if parseerror:
        return (None, parseerror)

    #Reaches here only if regular (non-exchange, non-pass) move

    #Location
    row = -1
    col = -1
    dirc = '?'


    if len(loc.split(',')) == 3:
        locsplit = loc.split(',')
        row = int(locsplit[0])
        col = int(locsplit[1])
        dirc =  locsplit[2].upper()
    elif loc[0] in string.ascii_uppercase[0:15] + string.ascii_lowercase[0:15]:
        dirc = 'V'
        col = string.ascii_letters.find(loc[0]) % 26
        if str.isdigit(loc[1:]):
            row = int(loc[1:])
        else:
            row = None
        if row not in range(1,16): #user entered, so 1-indexed
            parseerror = True
    elif loc[-1] in string.ascii_uppercase[0:15] + string.ascii_lowercase[0:15]:
        dirc = 'H'
        col = string.ascii_letters.find(loc[-1]) % 26
        if str.isdigit(loc[:-1]):
            row = int(loc[:-1])
        else:
            row = None
        if row not in range(1,16): #user entered, so 1-indexed
            parseerror = True
    else:
        parseerror = True
    if parseerror:
        return (None, parseerror)

    #WORD
    parsedword = ''
    actualword = ''
    existing = False
    for char in word:
        if char in string.ascii_letters + '#':
            actualword = actualword + char
        if existing:
            if char in string.ascii_letters + '#':
                parsedword = parsedword + '#'
                continue
            elif char == ')':
                existing = False
                continue
            else:
                parseerror = True
        else:
            if char in string.ascii_letters + '#':
                parsedword = parsedword + char
                continue
            elif char == '(':
                existing = True
                continue
            else:
                parseerror = True

    if parseerror:
        return (None, parseerror)

    return ((row-1, col, dirc, parsedword, actualword), parseerror)  # This is 0-indexed!



def validatemove(parsedmove,rack):
    """
    Validates that:
        1. The move is made using the given rack only
        2. Move does not ignore any already placed tiles
        3. Move stays within the board
        4. All words formed are valid words
        5. No prefix and suffix letters occur on board
        6. If it is the first move, then the centre square must be covered
    """
    valid = True

    parsedword = parsedmove[3]
    actualword = parsedmove[4]
    centresquarecovered = False

    #1
    blankedmove = re.sub('#', '', re.sub('[a-z]', '?', parsedword))

    if Counter(blankedmove) - Counter(rack):
        errcode = 41
        throwerror(errcode)
        return (None, False, errcode)

    #2, 3
    r = parsedmove[0]
    c = parsedmove[1]
    dirc = parsedmove[2]
    i = 0
    for i in range(len(actualword)):
        if (r,c) == centresquare:
            centresquarecovered = True
        if r > numrows - 1 or c > numcols - 1:
            valid = False
            errcode = 43
            throwerror(errcode)
            return (None, False, errcode)

        if (actualword[i] != '#' and letterboard[r][c] == '.') or (actualword[i] == letterboard[r][c]) or (actualword[i]=='#' and letterboard[r][c]!='.'):
            if actualword[i]=='#':
                actualword = actualword[:i] + letterboard[r][c] + actualword[i+1:]
            if dirc == 'H':
                c+=1
            else:
                r+=1
        else:
            valid = False
            errcode = 42
            throwerror(errcode)
            return (None, False, errcode)


    #4
    if not checkword(actualword):
            valid = False
            errcode = 44
            throwerror(errcode)
            return (None, False, errcode)

    r = parsedmove[0]
    c = parsedmove[1]
    dirc = parsedmove[2]
    i = 0
    for i in range(len(actualword)):
        perpendicularword = actualword[i]

        if dirc == 'H':
            rtemp = r-1
            while rtemp >= 0 and letterboard[rtemp][c]!='.':
                perpendicularword = letterboard[rtemp][c] + perpendicularword
                rtemp-=1
            rtemp = r+1

            while rtemp < numrows and letterboard[rtemp][c]!='.':
                perpendicularword = perpendicularword + letterboard[rtemp][c]
                rtemp+=1
            c+=1
        else:
            ctemp = c-1
            while ctemp >= 0 and letterboard[r][ctemp]!='.':
                perpendicularword = letterboard[r][ctemp] + perpendicularword
                ctemp-=1
            ctemp = c+1
            while ctemp < numcols and letterboard[r][ctemp]!='.':
                perpendicularword = perpendicularword + letterboard[r][ctemp]
                ctemp+=1
            r+=1

        if len(perpendicularword) > 1 and not checkword(perpendicularword):
            valid = False
            errcode = 44
            throwerror(errcode)
            return (None, False, errcode)
    #5
    if not(r >= numrows or c >= numcols or letterboard[r][c]=='.') or \
    (dirc == 'H' and parsedmove[1]>0 and not letterboard[parsedmove[0]][parsedmove[1]-1]=='.') or \
    (dirc == 'V' and parsedmove[0]>0 and not letterboard[parsedmove[0]-1][parsedmove[1]]=='.') or \
    len(actualword)==1:
        valid = False
        errcode = 46
        throwerror(errcode)
        return (None, False, errcode)

    #6
    if not centresquarecovered and all([char == '.' for char in ''.join([''.join(row) for row in letterboard])]):
        valid = False
        errcode = 45
        throwerror(errcode)
        return (None, False, errcode)

    return(actualword, valid, None)



def scoremove(parsedmove):
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

def getmove(player):
    #1. Send board.
    """ The format is one long string of length 225

        .         - indicates empty spot
        UPPERCASE - indicates a placed letter
        lowercase - indicates a blank designated as the specified letter
    """
    stringboard = ''.join([''.join(row) for row in letterboard])
    errcode = 0

    while True:
        (move, timeconsumed) = INVOKEprog(player, stringboard, rack[player], score[player], score[3-player], secondsremaining[player], errcode, True, False) #wait for response # for how long?
        # See parsemove() for move format

        parsedmove, parseerror = parsemove(move)
        #print('$$ ' + str(parsedmove) + ' $$$ ' + str(parseerror) )
        if parseerror:
            errcode = 11
            throwerror(errcode)
            continue

        if parsedmove[0]=='pass' or parsedmove[0]=='exch':
            return (parsedmove[0], parsedmove[1], timeconsumed)
        actualword = parsedmove[4] # but will be fixed when validity is checked

        # validatemove (on board)
        actualword, valid, errcode = validatemove(parsedmove, rack[player])
        if not valid:
            throwerror(errcode)
            continue
        else:
            errcode = 0
            break
    return (parsedmove[0], parsedmove[1], parsedmove[2], parsedmove[3], actualword, timeconsumed)

def fullmove(player, showboard=False):
    global bag
    #send board, current scores, recieve move, validate move
    parsedmove = getmove(player)
    # (7, 7, 'H', 'NOT', 'NOT', 4.132262945175171)

    if parsedmove[0] == 'pass':
        movescore = 0
        tilesplayed = []
        timeconsumed = parsedmove[2]
        #Update gcg file here

    elif parsedmove[0] == 'exch':
        movescore = 0
        tilesplayed = parsedmove[1]
        timeconsumed = parsedmove[2]
        #Update gcg file here

    else:
        #Update Board, score move, update time
        movescore, tilesplayed = scoremove(parsedmove)
        
        score[player]+=movescore
        timeconsumed = parsedmove[5]

        #format move to shift to gcg
        wordPlayed = parsedmove[4]
        move  = translateMoveToGcg(parsedmove[:3])
        moveFormatGcg = ' '.join(['>' + playernames[player]+':', ''.join(rack[player]), move, wordPlayed, str(movescore),str(score[player])])
        #Update gcg file here
        outgcgfile =  open(gamefile, "a")
        outgcgfile.write(moveFormatGcg + '\n')
        outgcgfile.close()


    #tilesplayed = re.sub('[abcdefghijklmnopqrstuvwxyz]', '?', tilesplayed)
    tilesplayed = [x if not x in list('abcdefghijklmnopqrstuvwxyz') else '?' for x in tilesplayed]
    #print(tilesplayed)
    secondsremaining[player] -= timeconsumed

    #return updated board, score, new rack, new time
    stringboard = ''.join([''.join(row) for row in letterboard])
    dictleftonrack = dict(Counter(rack[player]) - Counter(tilesplayed))
    leftonrack = list(''.join(x*dictleftonrack[x] for x in dictleftonrack))
    ntilestodraw = min(len(tilesplayed), len(bag))
    #print(' >> '+ str(tilesplayed) + '>>' + str(leftonrack) + ' >> '+ str(ntilestodraw))

    if ntilestodraw == 0:
        rack[player] = leftonrack
        if len(rack[player]) == 0:
            # game over
            rackbonus = 2 * sum([tilepoints[x] for x in rack[3 - player]])
            score[player]+=rackbonus
            #timebonus
            if secondsremaining[3 - player] < 0:
                minutesovertime = -(floor(secondsremaining[3 - player] / 60))
                score[player] += (int(minutesovertime) * 10)

            if secondsremaining[player] < 0:
                minutesovertime = -(floor(secondsremaining[player] / 60))
                score[3 - player] += (int(minutesovertime) * 10)

            INVOKEprog(player, stringboard, rack[player], score[player], score[3 - player], secondsremaining[player], 0, False, True)
            INVOKEprog(3 - player, stringboard, rack[3 - player], score[3 - player], score[player], secondsremaining[3 - player], 0, False, True)

            return True
    else:
        rack[player] = leftonrack + drawtiles(ntilestodraw)
        INVOKEprog(player, stringboard, rack[player], score[player], score[3 - player], secondsremaining[player], 0, False, False)
        if parsedmove[0] == 'exch':
            bag = bag + tilesplayed 
        return False



##### PROCESS ######

rack[startplayer] = drawtiles(7)
rack[3 - startplayer] = drawtiles(7)

gameover = False
#prepare game file header

outgamefile = open(gamefile,"w")
outgamefile.write('#player1 ' + playernames[1] + ' ' + playernames[1] + '\n')
outgamefile.write('#player2 ' + playernames[2] + ' ' + playernames[2] + '\n')
outgamefile.close()


while not gameover:
    #showall()
    gameover = fullmove(activeplayer)

    activeplayer = 3 - activeplayer

print('')
showallgameover()


##### TESTING ######


