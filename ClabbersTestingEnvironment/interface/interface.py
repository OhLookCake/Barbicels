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
import socket


#### INITIALIZE #####
random.seed(8)


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


class Playerinfo:
	def __init__(self, host, port, sock, name, score, rack, timeleft):
		self.host = host
		self.port = port
		self.sock = sock
		self.name = name
		self.score = score
		self.rack = rack
		self.timeleft = timeleft


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

	def translateMoveToGcg(move):
		"""Translates move to gcg format
		"""
		cols = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']
		if self.direction=='H':
			gcgmove  = ''.join([str(self.startrow+1), cols[self.startcol]])
		else:
			gcgmove  = ''.join([cols[self.startcol], str(self.startrow+1)])

		return gcgmove

class Board:
	def __init__(self, numrows, numcols, lettermultiplier, wordmultiplier, squares):
		self.numrows = numrows 
		self.numcols = numcols
		self.lettermultiplier = lettermultiplier  #bonuses
		self.wordmultiplier = wordmultiplier  #bonuses
		self.squares = squares #tiles. caps if letter, lower case if blank.
		self.centresquare = (numrows // 2, numcols //2) #This is effectively rounded up in 0-index
	
	def showboard(self):
	#board is a numrows*numcols list
		print('   |  A |  B |  C |  D |  E |  F |  G |  H |  I |  J |  K |  L |  M |  N |  O |')
		print('   ============================================================================')
		rownum = 1
		for row in self.squares:
			if rownum < 10:
				print(' ', end = '')
			print(str(rownum) + ' |  ', end = '')
			rownum +=1

			for col in row:
				print(col, end=' |  ')
			print('')
			print('   ----------------------------------------------------------------------------')

		#print('----------------------------------------------------------------------------')

	def playmove(move):
		#this is sanitized, valid, legal, ...
		#startrow, starcol are integers 0 indexed
		#direction is uppercase V or H
		# word has blank lowercased already

		row = move.startrow
		col = move.startcol

		for tile in move.word:
			self.squares[row][col] = tile
			if move.direction == 'V':
				row+=1
			else:
				col+=1



class Bag:
	def __init__(self, tiles):
		self.tiles = tiles

	def drawtiles(self, k):
		"""
		Returns k tiles from the bag's current distribution, and updates the bag to remove those tiles
		In case of attempt to draw more tiles than in the bag, returns None
		"""
		if len(self.tiles) < k:
			errcode = 31
			throwerror(errcode)
			return None
		drawntiles = [self.tiles.pop(random.randrange(len(self.tiles))) for _ in xrange(k)]
		return drawntiles


	def puttiles(self, tiles):
		"""
		Put back the tiles (half of hte exchange process)
		"""
		self.tiles += tiles 


class Game:
	
	def __init__(self, sock1, sock2):


		#### INITIALIZE #####
		
		#Read config file
		config = ConfigParser.RawConfigParser()
		config.read('../config.cfg')

		######## Board Params ###########

		numrows = int(config.get('Board', 'numrows'))
		numcols = int(config.get('Board', 'numcols'))

		lettermultiplierstring = config.get('Board', 'lettermultiplier').split(',')
		lettermultiplier = [[int(k) for k in lettermultiplierstring[i:i+numcols]] for i in range(0, numrows*numcols,numcols)]

		wordmultiplierstring = config.get('Board', 'wordmultiplier').split(',')
		wordmultiplier = [[int(k) for k in wordmultiplierstring[i:i+numcols]] for i in range(0, numrows*numcols,numcols)]

		initialboardstring = config.get('Board', 'initialboard').split(',')
		initialboard = [initialboardstring[i:i+numcols] for i in range(0, numrows*numcols,numcols)]
		squares = initialboard

		
		board = Board(numrows, numcols, lettermultiplier, wordmultiplier, squares)
		self.board = board
		
		######## Bag Params #############

		bagdict = {L:int(config.get('TileDistribution', L)) for L in string.ascii_uppercase+'?'}
		tilelist = list(''.join([L*bagdict[L] for L in string.ascii_uppercase+'?']))
		bag = Bag(tilelist)
		self.bag = bag

		######## Game Params #######

		tilepoints = {L:int(config.get('TilePoints', L)) for L in string.ascii_uppercase+'?'}
		tilepoints.update({L:int(config.get('TilePoints', '?')) for L in string.ascii_lowercase}) # basically, also add equivalent of blank points for lower case letters
		self.tilepoints = tilepoints

		startplayer = int(config.get('Game', 'startplayer'))
		if startplayer not in [1,2]:
			startplayer = int(round(random.random())) + 1

		hostPlayer = [0,0,0]
		hostPlayer[1] = config.get('Agents','Agent1Host')
		hostPlayer[2] = config.get('Agents','Agent2Host')

		portPlayer = [0,0,0]
		portPlayer[1] = int(config.get('Agents','Agent1Port'))
		portPlayer[2] = int(config.get('Agents','Agent2Port'))

		playernames = ['', '', '']
		playernames[1] = config.get('Agents','Agent1Name')
		playernames[2] = config.get('Agents','Agent2Name')

		score = [0, int(config.get('Game', 'initialscore1')) , int(config.get('Game', 'initialscore2'))]
		secondsremaining =  [0, int(config.get('Game', 'totalseconds1')), int(config.get('Game', 'totalseconds2'))]
		rack = [None, None, None]

		self.players = [None, None, None]
		self.players[1] = Playerinfo(hostPlayer[1], portPlayer[1], sock1, playernames[1], score[1], rack[1], secondsremaining[1])
		self.players[2] = Playerinfo(hostPlayer[2], portPlayer[2], sock2, playernames[2], score[2], rack[2], secondsremaining[2])


		#TODO: parse and use these.
		# #display flags 
		# #show messages passed to agents?
		# showMessages = ['','','']
		# showMessages[1] = config.get('Display','agent1ShowMessages')
		# showMessages[2] = config.get('Display','agent2ShowMessages')

		# #show Board after each move? If this is true, the previous value is ignored.
		# showBoardAtEveryMove = ['','','']
		# showBoardAtEveryMove[1] = config.get('Display','agent1ShowBoardAtEveryMove')
		# showBoardAtEveryMove[2] = config.get('Display','agent2ShowBoardAtEveryMove')
		# # print(showMessages,showBoardAtEnd,showBoardAtEveryMove)


		dictfile = config.get('Meta', 'dictionaryfile')	
		gamefile = config.get('Meta', 'gamefile')

		self.gamefile = gamefile
		
		fh = open(dictfile, 'r')
		wordlist = {w.replace("\n", "").upper():1 for w in fh.readlines()}
		self.wordlist = wordlist

		self.activeplayer = 1 #startplayer
		self.gameover = False


		# Actual init. Draw tiles.
		self.players[self.activeplayer].rack = self.bag.drawtiles(7)
		self.players[3 - self.activeplayer].rack = self.bag.drawtiles(7)

		outgamefile = open(self.gamefile,"w")
		outgamefile.write('#player1 ' + self.players[1].name + ' ' + self.players[1].name + '\n')
		outgamefile.write('#player2 ' + self.players[2].name + ' ' + self.players[2].name + '\n')
		
		outgamefile.close()

	
	def showall(self):
		# DONE

		self.board.showboard()
		for player in [1,2]:
			#print("Player" + str(player), end='')
			print(self.players[player].name, end='')

			if self.activeplayer == player:
				print('*: ', end='')
			else:
				print(': ', end='')
			print(''.join(self.players[player].rack))
			print('Score ' + str(self.players[player].score))
			print('')

	def showallgameover(self):
		self.board.showboard()
		print('\nGAME OVER')
		otherplayer = 2
		for player in [1,2]:
			#print("Player" + str(player)+ ': ', end='')
			print(self.players[player].name + ': ', end='')
			if len(self.players[player].rack) == 0:
				print('-')
			else:
				print(''.join(self.players[player].rack))
			print('Score ' + str(self.players[player].score), end = '')
			if self.players[player].score > self.players[otherplayer].score:
				print(' WINS')
			elif self.players[player].score < self.players[otherplayer].score:
				print(' LOSES')
			else:
				print('TIES')
			otherplayer = 1
			print('')
	
	def checkword(self, word):
		return word.upper() in self.wordlist

	def parsemove(self, textmove):
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
		move = Move('X', -1, -1, 'X', '', '')

		textmove = textmove.strip()
		movesplit = textmove.split()

		loc = None
		word = None



		if len(movesplit) == 1:
			#pass
			if movesplit[0].lower() == 'pass':
				move.category = 'P'
				return (move, parseerror)
			else:
				parseerror = True
				throwerror(11)
				return (None, parseerror)
		elif len(movesplit) == 2:
			#not pass
			if movesplit[0].lower() == 'exch':
				move.category = 'E'
				move.word = movesplit[1].upper()
				move.tileword = movesplit[1].upper()
				return (move, parseerror)
			else:
				#regular
				move.category = 'R'
		else:
			throwerror(11)
			return (None, parseerror)


		#Reaches here only if regular (non-exchange, non-pass) move
			
		loc = movesplit[0]
		word = movesplit[1]

		#Location
		if len(loc.split(',')) == 3:
			locsplit = loc.split(',')
			move.startrow = int(locsplit[0]) - 1
			move.startcol = int(locsplit[1]) - 1
			move.direction =  locsplit[2].upper()
		elif loc[0] in string.ascii_uppercase[0:15] + string.ascii_lowercase[0:15]:
			move.direction = 'V'
			move.startcol = string.ascii_letters.find(loc[0]) % 26
			if str.isdigit(loc[1:]):
				move.startrow = int(loc[1:]) - 1
			else:
				move.startrow = None
			if move.startrow not in range(0,15): #converted to 0-index
				parseerror = True
		elif loc[-1] in string.ascii_uppercase[0:15] + string.ascii_lowercase[0:15]:
			move.direction = 'H'
			move.startcol = string.ascii_letters.find(loc[-1]) % 26
			if str.isdigit(loc[:-1]):
				move.startrow = int(loc[:-1]) - 1
			else:
				move.startrow = None
			if move.startrow not in range(0,15): #converted to 0-index
				parseerror = True
		else:
			parseerror = True
		if parseerror:
			return (None, parseerror)


		#WORD
		parsedword = ''
		actualword = ''
		existing = False

		move.word = word
		move.tileword = ''

		r = move.startrow
		c = move.startcol

		for char in word:
			if not char in string.ascii_letters: #upper + lower
				parseerror = True
			if self.board.squares[r][c] == '.':
				move.tileword += char
			else:
				move.tileword += '#'
			if move.direction == 'H':
				c+=1
			elif move.direction == 'V':
				r+=1





			# if existing:
			# 	if char in string.ascii_letters + '#':
			# 		move.word = move.word + char # <
			# 		move.tileword = move.tileword + '#'
			# 		continue
			# 	elif char == ')':
			# 		existing = False
			# 		continue
			# 	else:
			# 		parseerror = True
			# else:
			# 	if char in string.ascii_letters + '#':
			# 		move.word = move.word + char  # <
			# 		move.tileword = move.tileword + char
			# 		continue
			# 	elif char == '(':
			# 		existing = True
			# 		continue
			# 	else:
			# 		parseerror = True

		#if there are #s, word will have a hashed version of word. But we are not supporting #s for now.
		# To allow hashes, some code needs to be changed.

		if parseerror:
			return (None, parseerror)

		return (move, parseerror)

	def validatemove(self, move, rack):
		"""
		Validates that:
			1. The move is made using the given rack only
			2. Move does not ignore any already placed tiles
			3. Move stays within the board
			4. All words formed are valid words
			5. No prefix and suffix letters occur on board
			6. If it is the first move, then the centre square must be covered
			7. if it is an exchange move, check if the tiles are actually available
		"""
		#NOTE: move is passed by reference. changes here will automatically get reflected.


		valid = True

		if move.category == 'R':

			parsedword = move.tileword
			actualword = move.word
			centresquarecovered = False

			#1        
			blankedmove = re.sub('#', '', re.sub('[a-z]', '?', move.tileword))

			if Counter(blankedmove) - Counter(rack):
				errcode = 41
				throwerror(errcode)
				return (False, errcode)

			#2, 3
			#centresquare = (7,7)
			i = 0
			r = move.startrow
			c = move.startcol
			
			for i in range(len(move.word)):
				
				if (r, c) == self.board.centresquare:
					centresquarecovered = True

				if r > self.board.numrows - 1 or c > self.board.numcols - 1:
					valid = False
					errcode = 43
					throwerror(errcode)
					return (False, errcode)

				if self.board.squares[r][c] != '.':
					#move.tileword[i] = '#'
					if move.word[i] != self.board.squares[r][c]:
						valid = False
						errcode = 42
						throwerror(errcode)
						return (False, errcode)

				if move.direction == 'H':
					c+=1
				else:
					r+=1

			
			#4
			if not self.checkword(move.word.upper()):
				valid = False
				errcode = 44
				throwerror(errcode)
				return (False, errcode)

			r = move.startrow
			c = move.startcol
			i = 0

			for i in range(len(actualword)):
				perpendicularword = move.word[i]

				if move.direction == 'H':
					rtemp = r-1
					while rtemp >= 0 and self.board.squares[rtemp][c]!='.':
						perpendicularword = self.board.squares[rtemp][c] + perpendicularword
						rtemp-=1
					rtemp = r+1

					while rtemp < self.board.numrows and self.board.squares[rtemp][c]!='.':
						perpendicularword = perpendicularword + self.board.squares[rtemp][c]
						rtemp+=1
					c+=1
				else:
					ctemp = c-1
					while ctemp >= 0 and self.board.squares[r][ctemp]!='.':
						perpendicularword = self.board.squares[r][ctemp] + perpendicularword
						ctemp-=1
					ctemp = c+1
					while ctemp < self.board.numcols and self.board.squares[r][ctemp]!='.':
						perpendicularword = perpendicularword + self.board.squares[r][ctemp]
						ctemp+=1
					r+=1

				if len(perpendicularword) > 1 and not self.checkword(perpendicularword):
					valid = False
					errcode = 44
					throwerror(errcode)
					return (False, errcode)

			#5

			if move.direction == 'H':
				if move.startcol != 0 and self.board.squares[move.startrow][move.startcol - 1] != '.':
					valid = False
					errcode = 46
					throwerror(errcode)
					return(False, errcode)
				if move.startcol + len(move.word) != self.board.numcols and self.board.squares[move.startrow][move.startcol + len(move.word)] != '.':
					valid = False
					errcode = 46
					throwerror(errcode)
					return(False, errcode)

			else:
				if move.startrow != 0 and self.board.squares[move.startrow - 1][move.startcol] != '.':
					valid = False
					errcode = 46
					throwerror(errcode)
					return(False, errcode)
				if move.startrow + len(move.word) != self.board.numrows and self.board.squares[move.startrow + len(move.word)][move.startcol] != '.':
					valid = False
					errcode = 46
					throwerror(errcode)
					return(False, errcode)

			#This feels surely correct, but if it doesn't work, refer to old code.

			#6
			if not centresquarecovered and all([char == '.' for char in ''.join([''.join(row) for row in self.board.squares])]):
				valid = False
				errcode = 45
				throwerror(errcode)
				return (False, errcode)
		elif move.category == 'E':
			blankedmove = re.sub('[a-z]', '?', move.tileword)
			if Counter(blankedmove) - Counter(rack):
				errcode = 41
				throwerror(errcode)
				return (False, errcode)

		return(valid, None)

	def scoremove(self, move):
		'''
		r = parsedmove[0]
		c = parsedmove[1]
		dirc = parsedmove[2]
		parsedword = parsedmove[3]
		actualword = parsedmove[4]
		'''

		i = 0
		r = move.startrow
		c = move.startcol
		totalscore = 0
		mainwordscore = 0
		mainwordmultiplier = 1

		for i in range(len(move.word)):
			if move.tileword[i] == '#':
				mainwordscore+=self.tilepoints[move.word[i]]
			else:
				mainwordscore+=(self.tilepoints[move.word[i]] * self.board.lettermultiplier[r][c])
				mainwordmultiplier *= self.board.wordmultiplier[r][c]

				hasperpendicularplay = False #if there is one, we'll set this to true later.
				perpendicularwordscore = (self.tilepoints[move.word[i]] * self.board.lettermultiplier[r][c])
				perpendicularwordmultiplier = self.board.wordmultiplier[r][c]

				#calculate perpendicular word score
				if move.direction == 'H':
					rtemp = r-1
					while rtemp >= 0 and self.board.squares[rtemp][c]!='.':
						hasperpendicularplay = True
						perpendicularwordscore += self.tilepoints[self.board.squares[rtemp][c]]
						rtemp-=1
					rtemp = r+1

					while rtemp < self.board.numrows and self.board.squares[rtemp][c]!='.':
						hasperpendicularplay = True
						perpendicularwordscore += self.tilepoints[self.board.squares[rtemp][c]]
						rtemp+=1

				else:
					ctemp = c-1
					while ctemp >= 0 and self.board.squares[r][ctemp]!='.':
						hasperpendicularplay = True
						perpendicularwordscore += self.tilepoints[self.board.squares[r][ctemp]]
						ctemp-=1
					ctemp = c+1
					while ctemp < self.board.numcols and self.board.squares[r][ctemp]!='.':
						hasperpendicularplay = True
						perpendicularwordscore += self.tilepoints[self.board.squares[r][ctemp]]
						ctemp+=1

				perpendicularwordscore *= perpendicularwordmultiplier
				if hasperpendicularplay:
					totalscore += perpendicularwordscore

			
			
			if move.direction == 'H':
				c+=1
			elif move.direction =='V':
				r+=1


		totalscore+=(mainwordscore*mainwordmultiplier)


		tilesplayed = [p for p in move.tileword if not p=='#']
		ntilesplayed = len(tilesplayed)
		if ntilesplayed == 7:
			totalscore+=50

		return (totalscore)

	def fullmove(self, showboard=False):
		
		#send board, current scores, recieve move, validate move
		okmove = False
		errorcode = 0 # Should this be errcode?
		timeconsumed = 0
		while not okmove:
			textmove, timethisiter = self.getmove(self.activeplayer, errorcode, True)
			timeconsumed+=timethisiter

			# gets a text move: 1B BOt | exch BBR | pass
			# NOT this: (7, 7, 'H', 'BOT', 'BOT', 4.19)
			move, parseerror = self.parsemove(textmove)

			if parseerror:
				errcode = 11
				throwerror(errcode)
				continue

			valid, errcode = self.validatemove(move, self.players[self.activeplayer].rack)
			if not valid:
				throwerror(errcode)
				continue
			else:
				errcode = 0

			okmove = True



		#server side processing of move
		self.players[self.activeplayer].timeleft-=timeconsumed
		gcgmove = ">" + self.players[self.activeplayer].name + ": " + ''.join(self.players[self.activeplayer].rack) + " " #incomplete right now!

		movescore = 0

		if move.category == 'P':
			movescore = 0
			tilesplayed = []
			gcgmove+= "- +0 " + str(self.players[self.activeplayer].score)

		elif move.category == 'E':
			movescore = 0
			tilesplayed = list(re.sub('#', '', move.tileword))
			gcgmove+= "-" + str(len(move.tileword)) + " +0 " + str(self.players[self.activeplayer].score)

		else:
			#Regular move
			#update time, racks
			movescore = self.scoremove(move)
			self.players[self.activeplayer].score+=movescore
			tilesplayed = list(re.sub('#', '', re.sub('[a-z]', '?', move.tileword)))
			
			#format move to shift to gcg
			#>Maven: ACNTVYZ 8F CAVY +24 132
			#>p2: INETTOD 8H NOT +3 123


			if move.direction == 'H':
				gcgmove+= str(move.startrow) + string.ascii_uppercase[move.startcol]
			else:
				gcgmove+= string.ascii_uppercase[move.startcol] + str(move.startrow)

			gcgmove+=" " + move.word + " " + str(movescore) + " " + str(self.players[self.activeplayer].score)


			#UPDATE BOARD

			i = 0
			r = move.startrow
			c = move.startcol
			
			for i in range(len(move.word)):
				self.board.squares[r][c] = move.word[i] #BOARD UPDATED HERE 

				if move.direction == 'H':
					c+=1
				elif move.direction =='V':
					r+=1

			#the move is correct, it has been put on the board
			#score, timeleft has been changed.

		#Draw new tiles:
		ntilestodraw = min(len(tilesplayed), len(self.bag.tiles))
		newtiles = self.bag.drawtiles(ntilestodraw)

		dictleftonrack = dict(Counter(self.players[self.activeplayer].rack) - Counter(tilesplayed))
		leftonrack = list(''.join(x*dictleftonrack[x] for x in dictleftonrack))                

		newrack = leftonrack+newtiles
		newrack.sort()

		self.players[self.activeplayer].rack = newrack



		#Update gcg file here
		outgcgfile =  open(self.gamefile, "a")
		outgcgfile.write(gcgmove + '\n')
		outgcgfile.close()


		if move.category=='E':
			self.bag.puttiles(tilesplayed) #put back the tiles in the bag


		if ntilestodraw == 0 and len(self.players[self.activeplayer].rack)==0:
			# game over
			self.gameover = True
			rackbonus = 2 * sum([self.tilepoints[x] for x in self.players[3 - self.activeplayer].rack])
			self.players[self.activeplayer].score+=rackbonus

			#timebonus
			if self.players[3- self.activeplayer].timeleft < 0:
				minutesovertime = -(floor(self.players[3- self.activeplayer].timeleft / 60))
				self.players[self.activeplayer].score+=(int(minutesovertime) * 10)

			if self.players[self.activeplayer].timeleft < 0:
				minutesovertime = -(floor(self.players[self.activeplayer].timeleft / 60))
				self.players[3 - self.activeplayer].score+=(int(minutesovertime) * 10)
			

			self.getmove(self.activeplayer, 0, False)
			self.getmove(3-self.activeplayer, 0, False)
			
			return True #gameoverflag

		return False #gameoverflag


	def play(self):
		##### PROCESS ######
		# Perform connections
		while not self.gameover:
			self.showall()
			self.gameover = self.fullmove()

			if not self.gameover:
				self.activeplayer = 3 - self.activeplayer

		self.showallgameover()
		#for player in [1,2]:
		#	self.players[player].sock.close()


	def getmove(self, player, errcode, moverequired):
		"""
		moverequired = True
			implies it is the agent's move to play and their clock is running. A response is expected.
		moverequired = False
			implies it is the opponent's turn to play. The message is sent to update the agent with the new drawn tiles.
		"""
		#player is a number

		dictdatatosend={}
		dictdatatosend['board'] = ''.join([''.join(x) for x in self.board.squares])
		dictdatatosend['rack'] = self.players[player].rack
		dictdatatosend['score'] = {}
		dictdatatosend['score']['me'] = self.players[player].score
		dictdatatosend['score']['opponent'] = self.players[3 - player].score
		dictdatatosend['secondstogo'] = self.players[player].timeleft
		dictdatatosend['errcode'] = errcode
		dictdatatosend['status'] = {}
		dictdatatosend['status']['moverequired'] = moverequired
		dictdatatosend['status']['endofgame'] = self.gameover
		
		datatosend = json.dumps(dictdatatosend)
		# if moverequired:
		#     starttime = time.time()
		#     move = raw_input(str(datatosend)+'\n') #player  'player' 's setting
		#     endtime = time.time()
		#     timeconsumed = endtime - starttime
		#     return (move, timeconsumed)

		message = str(datatosend)
		cmd = re.sub('\'', '\"', message) + "'"

		if moverequired:
				  
			#if showBoardAtEveryMove[player.playerid]=='True':
			self.board.showboard()
			print("Rack: " + ''.join(self.players[player].rack))
			for p in [1,2]:
				print(self.players[p].name, end='')

				if self.activeplayer == p:
					print('*: ', end='')
				else:
					print(': ', end='')
				
				print('Score ' + str(self.players[p].score))

			#if showMessages[player.id]=='True':
			print("Message to ", self.players[player].name)
			print(message)


			startime = 0
			endtime = 0
	
			self.players[player].sock.sendall(message + "\n")
			starttime = time.time()

			# Receive data from the server and shut down
			received = self.players[player].sock.recv(1024)
			endtime = time.time()

			print("Received: " + received)

			timeconsumed = endtime - starttime
			return (received, timeconsumed)
		else:

			print("Game over wala else")

			#if showMessages[player.id]=='True':
			print("Message to ", self.players[player].name)
			print(message)


			self.players[player].sock.sendall(message + "\n")

			return 0



if __name__ == "__main__":


	numiters = int(sys.argv[1])
	#Read config file
	config = ConfigParser.RawConfigParser()
	config.read('../config.cfg')

	p1host = config.get('Agents','Agent1Host')
	p1port = int(config.get('Agents','Agent1Port'))

	sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock1.connect((p1host, p1port))
	print("Socket1: " + p1host + ":" + str(p1port) + "\n" )

	p2host = config.get('Agents','Agent2Host')
	p2port = int(config.get('Agents','Agent2Port'))
	sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock2.connect((p2host, p2port))
	print("Socket2: " + p2host + ":" + str(p2port) + "\n")

	for i in range(numiters):
		mygame = Game(sock1, sock2)
		mygame.play()
		print("*" * 50)

	sock1.close()
	sock2.close()


	





	
