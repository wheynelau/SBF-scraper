import argparse
from src import SBFScraper

if __name__ == "__main__":
    # get file naem from args
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", help="Name of file to save to")
    args = parser.parse_args()
    SBFScraper(filename=args.f).run()
