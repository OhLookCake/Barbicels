# $1 is number of games
# $2 is seed
# $3 is add offset


#python ../agents/Quackle/QuackleWrapper.py /home/eeshan/Projects/ScrabbleAgent/Barbicels/ClabbersTestingEnvironment/config.cfg 1 > /dev/null & 
python ../agents/Clabbers2/clabbers2.py /home/eeshan/Projects/ScrabbleAgent/Barbicels/ClabbersTestingEnvironment/config.cfg 1 0.9517013325515 1.394450095657 -1.43441229167 0.23536850482 35.3783286556 1.30668904834 -28.0010544458 > /dev/null & 

sleep 5

python ../agents/Quackle/QuackleWrapper.py /home/eeshan/Projects/ScrabbleAgent/Barbicels/ClabbersTestingEnvironment/config.cfg 2 > /dev/null & 
sleep 5

outfile=`echo outfile${3}.txt`
python interface.py $1 $2 > $outfile

#number of wins
wins=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS" | grep TestAgent | wc -l)

#score for
scorefor=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep TestAgent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)

#score against
scoreagainst=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep Opponent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)


echo 1000000*$wins+$scorefor-$scoreagainst | bc > value${3}


