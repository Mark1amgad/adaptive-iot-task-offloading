#!/usr/bin/env python3
import argparse, pandas as pd, json, sys
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output",default=""); args=ap.parse_args()
 try: df=pd.read_csv(args.input, nrows=100000)
 except Exception as e: print(f"تعذر قراءة CSV: {e}",file=sys.stderr); return 2
 try: summary=df.describe(include="all",datetime_is_numeric=True).to_dict()
 except TypeError: summary=df.describe(include="all").to_dict()
 report={"file":args.input,"rows_sampled":len(df),"columns":list(df.columns),"dtypes":{k:str(v) for k,v in df.dtypes.items()},"missing":df.isna().sum().to_dict(),"duplicates_in_sample":int(df.duplicated().sum()),"numeric_summary":summary}
 text=json.dumps(report,ensure_ascii=False,indent=2,default=str)
 print(text)
 if args.output: Path(args.output).write_text(text,encoding="utf-8")
 return 0
if __name__=="__main__": raise SystemExit(main())
