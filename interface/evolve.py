from __future__ import print_function

import sys
import cma
import commands

"""
argv[1]: config file
"""

#nitweights = [3.33, 2, 0, -2, 2, 1.63, 1.66]
#initweights = [3.6538984417038294, 2.1966382193174403, -0.22834153792447448, -1.9052604350884734, 2.0066830154832771, 0.50854203199765302, 1.8704899993770783]
#previous weights in backup file
#initweights = [3.893786623207748, 3.1604925401920547, -0.17075724311551416, -1.6503502356193231, 2.0694882686437124, -0.58694612682381375, 1.4049071458396685]
initweights = [3.608356154221005, 3.2294334839688794, 0.045944869557630219, -1.5351679383514576, 2.0742365631681241, -0.80033035111664907, 1.0381345634824373]# starting from Gen 6

es = cma.CMAEvolutionStrategy(initweights, 1, {'popsize':50, 'maxiter':50})
#es = cma.CMAEvolutionStrategy(initweights, 1, {'popsize':2, 'maxiter':1})
itercounter = 6
while not es.stop():
    print("Generation " + str(itercounter))
    solutions = es.ask()
    fitnessvector = []

    counter = 1
    sys.stdout.flush()	
    for weights in solutions:
	print(str(counter))
	cmd = "sh runall.sh 20 999 " + str(counter) + " " + sys.argv[1] + " " + str(itercounter) + " " + " ".join([str(w) for w in weights])
	print("CMD: " +cmd)
        sys.stdout.flush()	
	fitness = int(commands.getoutput(cmd))
	print("Fitness="+str(fitness))

	fitnessvector+=[fitness]
	counter+=1

	print(fitnessvector)
        sys.stdout.flush()	

    itercounter+=1
    es.tell(solutions, fitnessvector)

    #es.logger.add()  # write data to disc to be plotted
    #es.disp()

    es.result_pretty()
    sys.stdout.flush()	
