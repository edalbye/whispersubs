import argparse
from pathlib import Path

from subtitling import create_subtitles, SubbingParameters
from utils import find_model
from appui import appUI

if __name__ == "__main__":
    UI = appUI()
    