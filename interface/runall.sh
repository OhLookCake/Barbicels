# $1 is number of games
# $2 is seed
# $3 is add offset


#python ../agents/Quackle/QuackleWrapper.py /home/eeshan/Projects/ScrabbleAgent/Barbicels/ClabbersTestingEnvironment/config.cfg 1 > /dev/null & 
python ../agents/Clabbers2/clabbers2.py /home/eeshan/Projects/ScrabbleAgent/Barbicels/ClabbersTestingEnvironment/config.cfg 1 $3 $4 $5 $6 $7 $8 $9 $10 > /dev/null & 

sleep 5

python ../agents/Quackle/QuackleWrapper.py /home/eeshan/Projects/ScrabbleAgent/Barbicels/ClabbersTestingEnvironment/config.cfg 2 $3 > /dev/null & 
sleep 2

outfile=`echo outfile${3}.txt`
python interface.py $1 $2 $3 > $outfile

#number of wins
wins=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS" | grep TestAgent | wc -l)

#score for
scorefor=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep TestAgent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)

#score against
scoreagainst=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep Opponent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)


echo 1000000*$wins+$scorefor-$scoreagainst | bc #  > value${3}


