cat $1 | tr \\n , | sed 's/,Score/XXXXScore/g' | tr , \\n | sed 's/XXXX/\ \| /g' | grep "WINS\|LOSES\|GAME OVER"  | sed 's/GAME OVER/\-\-\-\-\-\-\-/g'
