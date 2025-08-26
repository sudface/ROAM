# Vibe coded :thumbsup:
import os
import requests
from datetime import datetime, timedelta
from processROAM import LOAM, ROAM, FOAM
import argparse

import subprocess
import os
import shutil
import sys

def preprocess_roam(filename: str):
    # Check for Unix-like system
    if os.name != "posix":
        raise EnvironmentError("This function only works on Unix-like systems")

    # Build temp file name
    temp_filename = f"{filename}_temp"

    try:
        # Write first line to temp file
        with open(temp_filename, "w") as tmp_out:
            subprocess.run(
                ["head", "-n1", filename],
                stdout=tmp_out,
                check=True
            )

        # Append grep results
        with open(temp_filename, "a") as tmp_out:
            subprocess.run(
                ["grep", "All card types", filename],
                stdout=tmp_out,
                check=True
            )

        # Replace original file with temp file
        shutil.move(temp_filename, filename)
        print(f"Processed and replaced: {filename}")

    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


def download_and_process_data(data_type: str, start_date: str, end_date: str, save_dir: str = "processed"):
    """
    Download and process data files (LOAM or ROAM) from Transport NSW between start_date and end_date.

    Args:
        data_type (str): Type of data to process ("LOAM" or "ROAM").
        start_date (str): Start date in YYYYMMDD format.
        end_date (str): End date in YYYYMMDD format.
        save_dir (str): Directory to save processed JSON files.
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")

    headers = {
        "Referer": "https://opendata.transport.nsw.gov.au/"
    }

    current = start
    while current <= end:
        year_month = current.strftime("%Y-%m")
        yyyymmdd = current.strftime("%Y%m%d")
        yyyy_mm_dd = current.strftime("%Y-%m-%d")
        url = f"https://opendata-tpa.transport.nsw.gov.au/{data_type}/{year_month}/{data_type}_{yyyymmdd}.txt"
        
        infile = f"{data_type}_{yyyymmdd}.txt"
        outfile = os.path.join(save_dir, f"{data_type}_{yyyymmdd}.json")

        try:
            print(f"Downloading: {infile}")
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code == 200:
                # Save temp file
                with open(infile, "wb") as f:
                    f.write(response.content)

                # Run processing function
                if data_type == "LOAM":
                    LOAM(infile, outfile, yyyy_mm_dd)
                if data_type == "FOAM":
                    FOAM(infile, outfile, yyyy_mm_dd)
                elif data_type == "ROAM":
                    preprocess_roam(infile)
                    ROAM(infile, outfile)
                print(f"Processed -> {outfile}")

                # Delete infile
                os.remove(infile)
                print(f"Deleted: {infile}")
            else:
                print(f"File not found: {url} (status {response.status_code})")
        except requests.RequestException as e:
            print(f"Error downloading {url}: {e}")

        current += timedelta(days=1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and process LOAM or ROAM data files.")
    parser.add_argument("-l", "--loam", nargs=2, metavar=("start_date", "end_date"),
                        help="Specify the start and end dates in YYYYMMDD format for LOAM.")
    parser.add_argument("-r", "--roam", nargs=2, metavar=("start_date", "end_date"),
                        help="Specify the start and end dates in YYYYMMDD format for ROAM.")
    parser.add_argument("-f", "--foam", nargs=2, metavar=("start_date", "end_date"),
                        help="Specify the start and end dates in YYYYMMDD format for FOAM.")
    args = parser.parse_args()

    if args.loam:
        start_date, end_date = args.loam
        download_and_process_data("LOAM", start_date, end_date)
    if args.roam:
        start_date, end_date = args.roam
        download_and_process_data("ROAM", start_date, end_date)
    if args.foam:
        start_date, end_date = args.foam
        download_and_process_data("FOAM", start_date, end_date)
