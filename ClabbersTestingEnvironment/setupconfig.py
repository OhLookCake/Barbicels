import ConfigParser

config = ConfigParser.ConfigParser()
config.optionxform = str
config.read('./default.cfg') #default configuration file used as baseline


print('This modifies the default.cfg config and writes out config.cfg substituting the values supplied by the user. Not all options are accessed using this file, but for first time usage, this is the recommended way of setting up config.cfg. Any further changes can be made directly in the cfg file.\n\n')

#setting up Meta
mainDir = raw_input("Enter absolute path of directory containing ClabbersTestingEnvironment: ").rstrip()
mainDir = mainDir.rstrip('/')
mainDir = mainDir + "/ClabbersTestingEnvironment"
config.set('Meta','gamefile',mainDir+"/interface/gamefile.gcg")
config.set('Meta','dictionarieslocation',mainDir+"/dictionaries")

#setting up agents
agents = ['Human', 'Greedy', 'Quackle','Clabbers1','Clabbers2']
agentsLoc = ['/Human/human.py', '/Greedy/greedy.py', '/Quackle/QuackleWrapper.py', '/Clabbers1/clabbers1.py', '/Clabbers2/clabbers2.py']


print('\nChoose the two agents')
for i in range(len(agents)):
	print(str(i)+": "+agents[i])

a1 = int(raw_input("Choose first agent: "))
a1Name = raw_input("Name of first agent: ")
a2 = int(raw_input("choose second agent: "))
a2Name = raw_input("Name of second agent: ")
agent1 = "../agents"+ agentsLoc[a1]
agent2 = "../agents"+ agentsLoc[a2]

agent1Cmd = "python " + agent1 +" " +mainDir+"/config.cfg"
agent2Cmd = "python " + agent2 +" " +mainDir+"/config.cfg"

qpath = ''
if agents[a1]=='Quackle' or agents[a2]=='Quackle':
    qpath = raw_input("\nEnter absolute path of directory containing Quackle test executable (E.g.: /home/eeshan/Projects/quackle/test/): ").rstrip()
    qpath = qpath.rstrip('/')
    qpath = qpath+'/'


config.set('Agents','Agent1Command',agent1Cmd)
config.set('Agents','Agent1Name',a1Name)
config.set('Agents','Agent2Command',agent2Cmd)
config.set('Agents','Agent2Name',a2Name)
config.set('Agents','quacklepath',qpath)

#setting up Display
dispList = ['Both agents','Agent1 only','Agent2 only', 'None']
print("\nDisplay passed json messages on screen for")
for i in range(len(dispList)):
	print(str(i)+": "+dispList[i])

msgDisp = int(raw_input())

print("\nDraw board and racks on screen after each move for")
for i in range(len(dispList)):
	print(str(i)+": "+dispList[i])

boardDisp = int(raw_input())

if msgDisp== 0:
	config.set('Display','agent1ShowMessages','True')
	config.set('Display','agent2ShowMessages','True')
elif msgDisp== 1:
	config.set('Display','agent1ShowMessages','True')
	config.set('Display','agent2ShowMessages','False')
elif msgDisp== 2:
	config.set('Display','agent1ShowMessages','False')
	config.set('Display','agent2ShowMessages','True')
elif msgDisp== 3:
	config.set('Display','agent1ShowMessages','False')
	config.set('Display','agent2ShowMessages','False')

if boardDisp== 0:
	config.set('Display','agent1ShowBoardAtEveryMove','True')
	config.set('Display','agent2ShowBoardAtEveryMove','True')
elif boardDisp== 1:
	config.set('Display','agent1ShowBoardAtEveryMove','True')
	config.set('Display','agent2ShowBoardAtEveryMove','False')
elif boardDisp== 2:
	config.set('Display','agent1ShowBoardAtEveryMove','False')
	config.set('Display','agent2ShowBoardAtEveryMove','True')
elif boardDisp== 3:
	config.set('Display','agent1ShowBoardAtEveryMove','False')
	config.set('Display','agent2ShowBoardAtEveryMove','False')

config.write(open('config.cfg','w'))

print('config.cfg has been correctly set.')

