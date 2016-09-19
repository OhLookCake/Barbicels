# $1 is number of games
# $2 is seed
# $3 is add offset
# $4 is the config file
# $5 is generation id
# $6-12 are weights for clabbers


weightfile=output/weightfile.txt
outfile=`echo output/outfile${5}_${3}.txt`

#Write weights to file
echo   >> $weightfile
echo Generation $5 _ $3 >> $weightfile
echo $6 $7 $8 $9 $10 $11 $12 >> $weightfile
echo   >> $weightfile

# Our TestAgent
python ../agents/Clabbers2/clabbers2.py $4 1 $3 $6 $7 $8 $9 $10 $11 $12 > /dev/null &
sleep 5

# Opponent to test/learn (Quackle)
python ../agents/Quackle/QuackleWrapper.py $4 2 $3 > /dev/null & 
sleep 2

python interface.py $1 $2 $3 $4 > $outfile

#number of wins
wins=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS" | grep TestAgent | wc -l)

#score for
scorefor=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep TestAgent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)

#score against 
scoreagainst=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep Opponent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)

#Net score against (because we want to minimize this)
echo -1000000*$wins-$scorefor+$scoreagainst | bc 


