while read -u 10 num;
do
	v="array.*"$num
	cat output_completerun/evolout.txt | grep $v
done 10< bestfitness.txt
