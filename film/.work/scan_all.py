import json,subprocess,glob,os,sys
sys.path.insert(0,"film/kit")
from harvest import scan
from pathlib import Path
from common import probe_duration
rows=[]
for p in sorted(glob.glob("film/corpus/videos/*.mp4")):
    segs=scan(Path(p), Path("film/.work/scanall")/os.path.basename(p)[:-4])
    d=probe_duration(p)
    # collapse to the act order
    order=[s["kind"] for s in segs]
    rows.append({"slug":os.path.basename(p)[:-4],"dur":round(d,2),
                 "segments":[{"k":s["kind"],"s":s["start"],"e":s["end"]} for s in segs]})
    print(rows[-1]["slug"], round(d,1), " ".join(f'{s["kind"][:4]}:{s["start"]}-{s["end"]}' for s in segs), flush=True)
json.dump(rows,open("film/.work/corpus-scan.json","w"),indent=1)
print("SCAN DONE")
