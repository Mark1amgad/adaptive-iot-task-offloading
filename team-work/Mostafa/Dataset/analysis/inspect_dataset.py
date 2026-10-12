#!/usr/bin/env python3
import argparse, pandas as pd, json, sys
from pathlib import Path
def find_csv(p):
 p=Path(p); return [p] if p.is_file() else sorted(p.rglob("*.csv"))
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); args=ap.parse_args()
 files=find_csv(args.input)
 if not files: print("لم يُعثر على CSV", file=sys.stderr); return 2
 for f in files:
  try:
   df=pd.read_csv(f, nrows=100000)
   print(json.dumps({"file":str(f),"sample_rows":len(df),"columns":list(df.columns),"dtypes":{k:str(v) for k,v in df.dtypes.items()},"missing":df.isna().sum().to_dict()},ensure_ascii=False,indent=2))
  except Exception as e: print(f"فشل فحص {f}: {e}",file=sys.stderr)
 return 0
if __name__=="__main__": raise SystemExit(main())
