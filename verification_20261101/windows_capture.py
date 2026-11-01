import sys
from common import ROOT,AUDIT,run,runtime_env
script=sys.argv[1];arguments=sys.argv[2:]
name='windows-'+script.removesuffix('.py')+('-'+'-'.join(arguments) if arguments else '')
run(name,[str(ROOT/'.conda/acoustics/python.exe'),'-u',str(AUDIT/script),*arguments],env=runtime_env())
