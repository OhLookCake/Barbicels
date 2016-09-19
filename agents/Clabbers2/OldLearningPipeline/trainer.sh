
#config has been set appropriately

for i in `seq 1 $1`;
do
	echo $i

	#Run one iteration
	cd ../../interface/
	python UniversalInterface.py $i

	#make one training file
	cd ../agents/Clabbers2
	python makedatafile.py datafile ../../interface/gamefile.gcg $i

	# make large training data
	rm -f fulltrainingdataset.csv
	#low=$(($i-4))
	#for j in `seq $low $i`;
	#do
	#	cat "traindata$j.csv" >> fulltrainingdataset.csv
	#done
	cat "traindata$i.csv" > fulltrainingdataset.csv

	#make model
	Rscript model.R


	#update weights
	python updateweights.py

	cp weights.txt "weights$i.txt"
done














