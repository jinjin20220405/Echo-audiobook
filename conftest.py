import sys
from pathlib import Path

# 把项目根目录加入 sys.path，让 pytest 能正确 import src.*
sys.path.insert(0, str(Path(__file__).parent))
