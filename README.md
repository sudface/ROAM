# ROAM
Analysis of the Rail Opal Assignment Model

The data used is derived from Transport for NSW datasets, <a href="https://opendata.transport.nsw.gov.au/data/dataset/roam-rail-opal-assignment-model">ROAM</a> and <a href="https://opendata.transport.nsw.gov.au/data/dataset/loam-light-rail-opal-assignment-model">LOAM</a> and FOAM. Transport uses Opal tap data to estimate what services passengers are taking. 

The ROAM is provided in a single 300MB PSV file per day, with all sorts of extraneous information about specific opal card demographics. This is unnecessary for patronage, so `prefilter.sh` removes this and converts it down to a [~19MB file](./samples/ROAM_20250822_all.txt). Further removing unnecesssary columns and repetition can bring this down to a [useful 5MB psv file](./samples/ROAM_20250822_usefulcols.psv).

The PSV file as a format is hard to visualise, so a python [script](./processROAM.py) `processROAM.py` converts this into a JSON file with information about each trip, the stops it makes, and the change of passenger load over time, providing more valuable insights.

To automate the collection of data, `loamDownloader.py` [here](./loamDownloader.py) downloads datasets in a time range for either the LOAM or ROAM and automatically processes them into the JSON file. Data samples available in [./samples](./samples/)

To make this data easy to view, [index.html](./index.html) displays each trip on a graph and allows sorting and filtering of stations and services. A sample is deployed at https://sudface.github.io/ROAM/.

Example trip from [output JSON](./samples/ROAM_20250822.json) file:
```json
{
    "TRIP_NAME": "0136-001-101-002:1000",
    "LINE": "M1",
    "ORIG_STN": "Tallawong",
    "DEST_STN": "Sydenham",
    "TIME": "2025-08-22 04:08:02",
    "SEAT_CAPACITY": 378,
    "SEGMENT_DIRECTION": "Up",
    "STOPS": [
        [1, "Tallawong", "2025-08-22 04:08:02", 0],
        [2, "Rouse Hill", "2025-08-22 04:10:37", 0],
        [3, "Kellyville", "2025-08-22 04:13:25", 0],
        [4, "Bella Vista", "2025-08-22 04:16:07", 20],
        [5, "Norwest", "2025-08-22 04:18:51", 20],
        [6, "Hills Showground", "2025-08-22 04:21:29", 20],
        [7, "Castle Hill", "2025-08-22 04:24:02", 20],
        [8, "Cherrybrook", "2025-08-22 04:26:46", 20],
        [9, "Epping", "2025-08-22 04:32:15", 40],
        [10, "Macquarie University", "2025-08-22 04:35:58", 40],
        [11, "Macquarie Park", "2025-08-22 04:37:57", 40],
        [12, "North Ryde", "2025-08-22 04:40:05", 40],
        [13, "Chatswood", "2025-08-22 04:46:01", 40],
        [14, "Crows Nest", "2025-08-22 04:49:48", 60],
        [15, "Victoria Cross", "2025-08-22 04:51:59", 60],
        [16, "Barangaroo", "2025-08-22 04:54:58", 60],
        [17, "Martin Place", "2025-08-22 04:57:09", 60],
        [18, "Gadigal", "2025-08-22 04:58:47", 40],
        [19, "Central", "2025-08-22 05:00:42", 40],
        [20, "Waterloo", "2025-08-22 05:02:50", 20],
        [21, "Sydenham", "2025-08-22 05:06:51", 20]
    ]
}
```

## Downloader
Only works on UNIX-like machines due to use of `grep`.
Downloads data within a date range, and automatically processes them to JSON.

```
usage: loamDownloader.py [-h] [-l start_date end_date] [-r start_date end_date]

options:
  -h, --help            Show this help message and exit
  start_date end_date   A date range in the YYYYMMDD format to download
  -l                    Download the LOAM dataset (Trains)
  -r                    Download the ROAM dataset (Light Rail)
  -f                    Download the FOAM dataset (Ferries)
```

## Processor
Can be used from the command line, or imported in a python script

Has two main module functions: 
 * `ROAM(in_roam, out_roam)` 
 * `LOAM(in_loam, out_loam, datestring)`
 * `FOAM(in_loam, out_loam, datestring)`
 * * Where `datestring` is of the hyphenated form `2025-08-22`

Or via the command line:
```
usage: processROAM.py [-h] [-r] [-l] [-f] date

positional arguments:
  date        Date of file in YYYYMMDD format. 
              For example, 20250822 will search for "LOAM_20250822.txt"

options:
  -h, --help  Show this help message and exit
  -r, --roam  Process ROAM (Trains)
  -l, --loam  Process LOAM (Light Rail)
  -f, --foam  Process FOAM (Ferries)
```
