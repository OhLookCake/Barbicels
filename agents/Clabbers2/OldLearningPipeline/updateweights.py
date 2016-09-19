
alpha = 0.1

fh = open('weights.txt', 'r')
oldweights = fh.readlines()[0].split(',')
fh.close()

print oldweights

fh = open('newweights.csv', 'r')
learntweights = fh.readlines()
fh.close()

print learntweights

newweights = []

for i in range(len(oldweights)):
    wold = float(oldweights[i])
    j = i+1
    if i == (len(oldweights)-1):
        j = 0
    wlearntstr = learntweights[j]
    if wlearntstr == 'NA\n':
        wlearnt = 0
    else:
        wlearnt = float(wlearntstr)

    wnew = ((1-alpha)*wold) + (alpha*wlearnt)

    newweights.append(wnew)


print newweights

fh = open('weights.txt', 'w')
fh.write(','.join([str(x) for x in newweights]) + '\n')
fh.close()


