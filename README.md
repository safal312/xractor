# Xractor

Xractor is a module that allows scraping of [X-Ray data](https://www.amazon.com/salp/xray) from the Amazon Prime Video Platform. X-Ray data has been deemed quite useful in academia for network analysis of character interactions however the current method to gather it is [manual](https://weltliteratur.net/extracting-network-data-from-amazon-prime-videos/). This tool allows a user to pass in a set of links for automatic scraping for large scale analysis.

## Installation Guide

Please install with the following instruction:(TBD)

If running locally, please install the module locally with the following instructions:
```
# create and activate virtual environment then run the following command
pip install -e .
```

## Usage

```python
from xractor import Xractor
import pandas as pd

INFILE = "sample_infile.csv"
OUT_DIR = "downloaded_xrays"

xscraper = Xractor()
xscraper.run_workers(pd.read_csv(INFILE), OUT_DIR)
```

The code snippet above showcases basic usage of the module. You first instantiate the module and call `run_workers` with the input data in a pandas dataframe format and the output directory to download the xray files to.

When run initially, the cookies of the logged in session won't be available. Hence, the user will be prompted to log in and notify in the terminal once done. This will save the cookies file locally and the driver will use that to continue execution of the program. Please follow the recommendations mentioned in this README file for efficient execution.

The `Xractor` class accepts the following parameters for some customization:

### Parameters:

- **workers (int, optional, default: 1):**
  - Number of parallel workers for concurrent scraping, improving performance.

- **headless (bool, optional, default: False):**
  - If True, the browser runs in headless mode (without a visible GUI).

- **manual_signin (bool, optional, default: False):**
  - If True, enables manual sign-in, allowing the user to interactively sign in if required. Else, a `.env` file is required with `USER` and `PASS` variables for the username and password to their Amazon account.

- **base_url (str, optional, default: "https://www.amazon.com"):**
  - The base URL to start scraping from. An example url in the input file needs to something like `/gp/video/detail/B0B683GB78/ref=atv_dp_atf_prime_sd_mv_resume_t1ADAAAAAA0wr0?autoplay=1&t=0`. The base_url is concatenated afterwards.

- **sign_in_url (str, optional, default: "https://www.amazon.com/gp/sign-in.html"):**
  - URL for signing in.

- **cookies_file (str, optional, default: "cookies.pkl"):**
  - File to store cookies for persistent sessions across multiple scrapes. If the file is not present at the start of the program, the user will be prompted to sign-in first.

- **fname_in_file (str, optional, default: "file"):**
  - Column name for in the input file for unique file names.

- **link_in_file (str, optional, default: "link"):**
  - Column name for the link information in the input file.

- **meta_file (str, optional, default: "log.csv"):**
  - CSV file to store metadata and logging information.

- **overwrite_old_movie_dirs (bool, optional, default: True):**
  - If True, overwrites old movie directories; if False, appends to existing directories.

- **retries (int, optional, default: 3):**
  - Number of retries in case of a failed request or other issues.

### Directory Structure:

```
xractor_package/
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements.txt
├── src/
│   └── xractor/
│       ├── __init__.py
│       ├── xractor.py
│       └── scraper/
│           ├── __init__.py
│           └── scraper.py
├── main.py
└── sample_infile.csv
```

The repository contains all the necessary code for the module. Along with it, a `sample_infile.csv` is provided for reference to what the input file should looks like. The `main.py` file gives example code to run the module.

### Input File & Output
The input file must have two columns. By default, they can be named `file` for the unique name for each link and `link` for the actual link to the Prime Video profile of a particular movie.
On successful downloads, a new directory with the name in `file` will be created under the `downloaded_xrays` folder according to the sample usage above. Inside each directory, two files will be available `Xray.json` and `PlaybackResources.json`. 
- The `Xray.json` file has the necessary partitioned scene list and characters appearing in those scenes. 
- The `PlaybackResources.json` file includes additional metadata for each movie like the title, subtitles, etc.

The directory structure will look as follows:

```
downloaded_xrays/
├── <file_1>/
│   ├── Xray.json
│   └── PlaybackResources.json
├── <file_2>/
│   ├── Xray.json
│   └── PlaybackResources.json
└── log.csv
```

The `log.csv` file includes essential information on the download process. The following are the columns available in the table:

- **fname (int):**
  - Unique name of content provided in input file.

- **link (str):**
  - Link provided in input file.

- **xray_present (bool):**
  - If True, the "X-RAY"tag is present on the content's profile page. If False, the content doesn't have X-Ray data.

- **playable (bool):**
  - If True, play button is available. If False, there could be couple of reasons: movie is not available on Prime memebership or movie is not available in the region. In both these cases, the play button won't be available.

- **playback (bool):**
  - If True, PlayBack Resources was successfully downloaded.

- **xray (bool):**
  - If True, Xray file was successfully downloaded.

- **all_resource (bool):**
  - If True, both xray and playbackresources files were successfully downloaded.

### Scraping Data for Input File
TBD

### Recommendations
Xractor uses multiple heuristics to scrape the data while navigating through the complex nature of the Amazon Prime Video platform and network issues. Therefore, it is recommended to run the browser in visual mode (headless=False) to inspect the situation at certain times.

##### Captcha
The browser will come to a halt when a captcha is encountered. At that case, the user will have to enter the captcha in the terminal. The new cookies file will be downloaded and you can run the program again smoothly without interventions for a long period.

##### Caveats of Playback Resources and X-Ray files
The playback resources file at times becomes immediately available when the movie's profile loads. However, you have to click on the "Play" button to get the x-ray file. Hence, in many cases, only the playback resources file is downloaded when an unexpected network error occurs or when the x-ray file is not present.

Additionally, the x-ray file at times may not have the scene-wise character information. Some X-ray files only have the cast list of the movie but don't have scene-wise information. While parsing, a user should be aware of and handle that scenario accordingly.

*An example parsing script will be uploaded soon.*

##### Retries
It is recommended to do a couple of runs of the movies that have both xrays and are playable but the files weren't downloaded. These could be a result of network issues. 

In some rare scenarios, we even found some movies with "x-ray" tag that didn't have any x-ray data. Hence, a couple of retries (approximately 2) should be enough to gather the maximum amount of data.

##### Duplicates
We found in some rare scenarios that the X-Ray data was duplicated for some movies (The same X-Ray file was downloaded twice under different directories). We recommend doing some robust checks after the files are downloaded to handle these issues. One heuristic we recommend is to look at the cast list of movies and see how they match.

### Raise Issues
If you encounter a problem, please raise an [issue](https://github.com/safal312/xractor/issues) with the particular problem, any error messages, code snippets, and steps for reproduction.

***Thank you for sticking to the end!***