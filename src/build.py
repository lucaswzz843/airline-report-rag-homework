import argparse
from rag import build_bm25,build_vectors
p=argparse.ArgumentParser();p.add_argument('--vectors',action='store_true');a=p.parse_args()
build_bm25()
if a.vectors:build_vectors()
