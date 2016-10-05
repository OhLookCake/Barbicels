import commands
import sys
"""argv[1] = evolout file
argv[2]: top x agent scores file"""
with open(sys.argv[2],"r") as f:
	cmd = "echo"+"\""+sys.argv[1]+"\""+" >> outbest.txt"
        out = commands.getstatusoutput(cmd)
	for l in  f:
		l = l.strip()
		cmd = "cat "+sys.argv[1]+"| grep \"Gen.*"+l+"\" >> outbest.txt"
		out = commands.getstatusoutput(cmd)
		cmd = "cat "+ sys.argv[1]+" | grep -A 2 \"Fitness.*"+l+"\" | tail -1 | cut -d\" \" -f9- >> outbest.txt"
		out = commands.getstatusoutput(cmd)
		#cmd = "cat "+sys.argv[1]+"| grep \"array.*"+l+"\" >> outbest.txt"
		#out = commands.getstatusoutput(cmd)
		#print (cmd)
		#print out
		#print "\n"
