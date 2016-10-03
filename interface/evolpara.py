from __future__ import print_function
import numpy as np
from joblib import Parallel, delayed
import sys
import cma
import commands
import pickle

"""
argv[1]: config file
"""
def fitnessfunc(itercounter, weights, counter, gamesperagent):
	print(str(counter))
	sys.stdout.flush()	
	cmd = "sh runall.sh " + str(gamesperagent) + " 999 " + str(counter) + " " + sys.argv[1] + " " + str(itercounter) + " " + " ".join([str(w) for w in weights])
	print("CMD: " +cmd)
	sys.stdout.flush()	
	output = commands.getoutput(cmd)
	print(output)
	sys.stdout.flush()
	fitness = int(output)
	print("Generation " + str(itercounter) + "_" + str(counter) + " Fitness="+str(fitness))
	sys.stdout.flush()
	return (weights, fitness)
if __name__=="__main__":

	#PARAMS
	popsize = 50
	maxiter = 10
	gamesperagent = 100
	itercounter = 9

	#initweights = [5.6, -2, 2, 7, 2 ]
	#initweights = [3.33, 2, 0, -2, 2, 1.63, 1.66]

	#es = cma.CMAEvolutionStrategy(initweights, 1, {'popsize':popsize, 'maxiter':maxiter})
	#ALTERNATIVELY, load
	es = pickle.load(open('saved-cma-object_' + str(itercounter) + '.pkl', 'rb'))
	with Parallel (n_jobs=4) as parallel:
		while not es.stop():
			print("Generation " + str(itercounter))
			sys.stdout.flush()	
			solutions = es.ask()
			fitness_for_weights = parallel( delayed (fitnessfunc)
					(itercounter, weights, counter, gamesperagent)
					for (weights, counter) in 
					zip (solutions, range(1, popsize+1)) )
			sys.stdout.flush()	
			for i in fitness_for_weights:
				print(i)
				sys.stdout.flush()	
			fitnessvector= [ i[1] for i in fitness_for_weights]
			print(fitnessvector)
			sys.stdout.flush()
			es.tell(solutions, fitnessvector )
			es.disp()  # uses option verb_disp with default 100
			sys.stdout.flush()	

			es.result_pretty()
			sys.stdout.flush()	
			esfile = 'saved-cma-object_' + str(itercounter+1) + '.pkl'
			pickle.dump(es, open(esfile, 'wb'))
			print('Saved weights at end of generation ' + str(itercounter) + " in file " + esfile)

			itercounter+=1

		cma.pprint(es.best.__dict__)
		sys.stdout.flush()	

		#es.logger.add()  # write data to disc to be plotted
		#es.disp()

