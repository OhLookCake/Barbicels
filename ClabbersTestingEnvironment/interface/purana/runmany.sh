

for i in `seq 1 $1`;
do
        echo $i
        echo $i >> $2
        python UniversalInterface.py $i >> $2
        echo "------------------" >> $2
done

