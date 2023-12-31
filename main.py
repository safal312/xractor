from xractor import Xractor
import pandas as pd

INFILE = "sample_infile.csv"
OUT_DIR = "downloaded_xrays"

xscraper = Xractor(workers=3, manual_signin=False)
xscraper.run_workers(pd.read_csv(INFILE), OUT_DIR)