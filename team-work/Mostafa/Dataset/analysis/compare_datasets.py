#!/usr/bin/env python3
import argparse, pandas as pd
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); args=ap.parse_args(); root=Path(args.root)
 rows=[]
 for p in sorted(root.rglob("*.csv")):
  try:
   df=pd.read_csv(p,nrows=1000); rows.append({"file":str(p),"sample_rows":len(df),"columns":len(df.columns),"missing_cells":int(df.isna().sum().sum()),"duplicate_rows":int(df.duplicated().sum())})
  except Exception as e: rows.append({"file":str(p),"error":str(e)})
 out=root/"analysis"/"dataset_inventory.csv"; out.parent.mkdir(exist_ok=True); pd.DataFrame(rows).to_csv(out,index=False,encoding="utf-8-sig"); print(out)
if __name__=="__main__": main()
