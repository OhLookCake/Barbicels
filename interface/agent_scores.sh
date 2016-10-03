for i in {0..30}
do
file=1_$i;wins=$(cat output/outfile$file.txt | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \|/g' | grep "WINS" | grep TestAgent | wc -l); total=$(cat output/outfile$file.txt | grep "GAME OVER" | wc -l);frac=$(echo $wins/$total | bc -l); echo $wins/$total = $frac
done
