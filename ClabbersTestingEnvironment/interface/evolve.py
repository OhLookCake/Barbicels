from __future__ import print_function

import cma
import commands


es = cma.CMAEvolutionStrategy(7 * [1], 1, {'popsize':2, 'maxiter':2})
itercounter = 1
while not es.stop():
    print("Iteration " + str(itercounter))
    solutions = es.ask()
    fitnessvector = []

    counter = 1
    for weights in solutions:
        print(str(counter), end=" ")
        cmd = "sh runall.sh 5 999 " + str(counter) + " " + " ".join([str(w) for w in weights])
        print("CMD: " +cmd)
        fitness = int(commands.getoutput(cmd))
        print("Fitness="+str(fitness))

        fitnessvector+=[fitness]

        counter+=1

        print(fitnessvector)

    itercounter+=1
    es.tell(solutions, fitnessvector)

    #es.logger.add()  # write data to disc to be plotted
    #es.disp()

    es.result_pretty()
