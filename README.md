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

Requirements:

- XRay module where you pass a list of links and the tool will get if for you
- The input file should have a list of links from that Amazon Prime Video platform.
- Before starting the script, the module will check for a pickle dump which it will use for logging in. If not available in the current directory, it will prompt the user to login.
- The user will need to provide the link for logging in as well.

- The tool uses multiple heuristics to be able to ease the data collection process but they are not perfect. Manual intervention in few cases might be required when data collection comes to a halt. Moreover, additional checks might need to be performed to ensure the validity of the downloaded files.
