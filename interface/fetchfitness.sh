# $1 is generation number
# $2 is agent number

outfile=`echo outfile${1}_${2}.txt`

#number of wins
wins=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS" | grep TestAgent | wc -l)

#score for
scorefor=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep TestAgent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)

#score against because we want to minimize this
scoreagainst=$(cat $outfile | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES" | grep Opponent | cut -d\  -f5 | tr \\n \+ | sed 's/$/0\n/g' | bc)

echo -1000000*$wins-$scorefor+$scoreagainst | bc 


