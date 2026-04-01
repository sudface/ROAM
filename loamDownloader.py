# Vibe coded :thumbsup:
import os
import requests
from datetime import datetime, timedelta
from processROAM import LOAM, ROAM, FOAM
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed


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


def download(url, outfile, headers=None, timeout=20, chunk_size=8192):
    print(f"Downloading: {outfile}")

    with requests.get(url, headers=headers, stream=True, timeout=timeout) as response:
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        last_printed_bucket = -1  # tracks 0,10,20,...100

        with open(outfile, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue

                f.write(chunk)
                downloaded += len(chunk)

                if total_size:
                    percent = (downloaded / total_size) * 100
                    bucket = int(percent // 10) * 10  # 0,10,20,...

                    if bucket > last_printed_bucket:
                        last_printed_bucket = bucket
                        print(f"{outfile}: {bucket}% complete")

        # Ensure 100% is printed (in case of rounding issues)
        if total_size and last_printed_bucket < 100:
            print(f"{outfile}: 100% complete")


def process_single_day(current, data_type, save_dir, headers):
    year_month = current.strftime("%Y-%m")
    yyyymmdd = current.strftime("%Y%m%d")
    yyyy_mm_dd = current.strftime("%Y-%m-%d")

    url = f"https://opendata-tpa.transport.nsw.gov.au/{data_type}/{year_month}/{data_type}_{yyyymmdd}.txt"
    
    infile = f"{data_type}_{yyyymmdd}.txt"
    outfile = os.path.join(save_dir, f"{data_type}_{yyyymmdd}.json")

    try:
        download(url, infile, headers)

        if data_type == "LOAM":
            LOAM(infile, outfile, yyyy_mm_dd)
        elif data_type == "FOAM":
            FOAM(infile, outfile, yyyy_mm_dd)
        elif data_type == "ROAM":
            preprocess_roam(infile)
            ROAM(infile, outfile)

        print(f"Processed -> {outfile}")

        os.remove(infile)
        print(f"Deleted: {infile}")

    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")


def download_and_process_data(data_type: str, start_date: str, end_date: str, save_dir: str = "processed", max_workers: int = 4):

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")

    headers = {
        "Referer": "https://opendata.transport.nsw.gov.au/"
    }

    # Generate all dates first
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)

    # Parallel execution
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_day, d, data_type, save_dir, headers)
            for d in dates
        ]

        for future in as_completed(futures):
            # This ensures exceptions are raised
            future.result()


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
