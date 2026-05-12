import sys
import os

#add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.rag.ingestion import build_index

build_index()