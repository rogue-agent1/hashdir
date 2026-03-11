#!/usr/bin/env python3
"""hashdir - Hash entire directory contents. Zero deps."""
import sys,os,hashlib
def main():
    path=sys.argv[1] if len(sys.argv)>1 else '.'
    algo=sys.argv[2] if len(sys.argv)>2 else 'sha256'
    h=hashlib.new(algo);count=0
    for r,ds,fs in sorted(os.walk(path)):
        ds.sort();fs.sort()
        for f in fs:
            fp=os.path.join(r,f)
            try:
                data=open(fp,'rb').read()
                h.update(fp.encode());h.update(data);count+=1
            except:pass
    print(f'{algo}:{h.hexdigest()}')
    print(f'{count} files hashed')
if __name__=='__main__':main()
