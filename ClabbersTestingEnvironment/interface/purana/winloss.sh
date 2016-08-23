echo 'Number of WINS:'
sh scorelines.sh $1 | grep WINS | cut -d\: -f1 | sort | uniq -c

