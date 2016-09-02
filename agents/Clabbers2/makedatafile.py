import csv
import sys

featurefile = sys.argv[1]
gcgfile = sys.argv[2]
outfilenumber = sys.argv[3]

clabbers = '>Clabbers2:'
quackle = '>Quackle:'

with open(gcgfile, 'r') as gcg:
    gcglines = gcg.readlines()

ctr = -1

clabbersscore=0
quacklescore=0

scorediffs = []
for gline in gcglines:
    ctr+=1
    if ctr <2:
        #header rows
        continue
    g = gline.split(' ')
    if g[0] == clabbers:
        clabbersscore = int(g[-1])
    else:
        quacklescore = int(g[-1])
    scorediffs.append(clabbersscore - quacklescore)

#print scorediffs
offset=0
if gcglines[2].split(' ')[0] == quackle:
    offset = 1

ctr = 0

fh = open('traindata' + outfilenumber + '.csv', 'w')

with open(featurefile) as csvfile:
    featurereader = csv.reader(csvfile, delimiter=',')
    for row in featurereader:

        n = ctr*2 + 5 + offset
        if n >= len(scorediffs):
            n = len(scorediffs)-1

        target = scorediffs[n]
        row.append(str(target))
        fh.write(','.join(row)+'\n')

        ctr+=1

fh.close()





