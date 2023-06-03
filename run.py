import argparse
from src import SBFScraper
import logging

# set up logging
logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a file handler and set its level to ERROR
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.ERROR)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

if __name__ == "__main__":
    # get file naem from args
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", help="Name of file to save to")
    args = parser.parse_args()
    SBFScraper(filename=args.f).run()
