"""
This file pre-processes the dictionary, and stores it in an appropriate data structure for use in the agents

"""

dictfile = '../dictionaries/csw12.txt'

fh = open(dictfile, 'r')
wordlist = [w.replace("\n", "").upper() for w in fh.readlines()]
fh.close()

alphasetdict ={}

#One blank:

for w in wordlist:
    ## alphasetdict
    alphaw = ''.join(sorted(list(w)))
    for i,letter in enumerate(alphaw):
        if i> 0 and w[i-1] == letter:
            continue
        s = ''.join(sorted(list(w[:i]+w[i+1:])))
        if s in alphasetdict:
            alphasetdict[s].append(w)
        else:
            alphasetdict[s]=[w]


fo = open("alphasetdict1B.txt", "w")
for k in alphasetdict:
    line = k
    for w in alphasetdict[k]:
        line+=" " + w
    fo.write(line+"\n")
fo.close()



