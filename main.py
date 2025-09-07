from xractor import Xractor
import pandas as pd

INFILE = "sample_infile.csv"
OUT_DIR = "downloaded_xrays"

xray_collector = Xractor(workers=3, manual_signin=False)
xray_collector.run_workers(pd.read_csv(INFILE), OUT_DIR)