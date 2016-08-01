"""
This file pre-processes the dictionary, and stores it in an appropriate data structure for use in the agents

"""

dictfile = '../dictionaries/csw12.txt'

fh = open(dictfile, 'r')
wordlist = [w.replace("\n", "").upper() for w in fh.readlines()]
fh.close()

alphasetdict ={}
for w in wordlist:
    
    ## alphasetdict
    s = ''.join(sorted(list(w)))
    if s in alphasetdict:
        alphasetdict[s].append(w)
    else:
        alphasetdict[s]=[w]

fo = open("alphasetdict.txt", "w")
for k in alphasetdict:
    line = k
    for w in alphasetdict[k]:
        line+=" " + w
    fo.write(line+"\n")
fo.close()

lwordlists = {x:{} for x in range(2,16)}

f2 = open("lwordlists.txt", "w")
for k in alphasetdict:
    for w in alphasetdict[k]:
        lwordlists[len(k)][w]=1
    

for k in lwordlists:
    line = str(k)
    for w in lwordlists[k]:
        line+=" " + w
    f2.write(line+"\n")
f2.close()







        

