import argparse
from src import SBFScraper
import logging

# set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output logs to the console
        logging.FileHandler('logfile.log')  # Save logs to a log file
    ]
)

if __name__ == "__main__":
    # get file naem from args
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", help="Name of file to save to")
    args = parser.parse_args()
    SBFScraper(filename=args.f).run()
