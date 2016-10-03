# $1 is number of games
# $2 is seed
# $3 is add offset
# $4 is the config file
# $5 is generation id
# $6-12 are weights for clabbers


#p1=$(echo $3%2 + 1| bc)         #player number for our agent    (Starts when offset is even)
#p2=$(echo \($3+1\)%2 + 1 | bc)  #player number for competing agent

echo Generation $5 _ $3 >> output/weightfile.txt
echo $6 $7 $8 $9 $10 $11 $12 >> output/weightfile.txt
echo   >> output/weightfile.txt

gamefile=`echo output/gamefile${5}_${3}.gcg`
touch $gamefile
sudo chmod +wrx $gamefile

clabbfile=`echo output/clabbfile${5}_${3}.txt`
quackfile=`echo output/quackfile${5}_${3}.txt`
python ../agents/Clabbers2/clabbers2.py $4 1 $3 $6 $7 $8 $9 $10 $11 $12 > $clabbfile &

sleep 5
python ../agents/Quackle/QuackleWrapper.py $4 2 $3 $5> $quackfile & 
sleep 2

outfile=`echo output/outfile${5}_${3}.txt`
python interface.py $1 $2 $3 $4 $5> $outfile

#number of wins
wins=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS" | grep TestAgent | wc -l)

#score for
scorefor=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep TestAgent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)

#score against because we want to minimize this
scoreagainst=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep Opponent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)


echo -1000000*$wins-$scorefor+$scoreagainst | bc 


