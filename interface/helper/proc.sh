cat outbest.txt | grep -A 1 Fitness | while read line;
do
echo $line | sed "s/Fitness=-//g"| tr '\r\n' ' '| cut -d" " -f2-
echo ">>>"
done
	
