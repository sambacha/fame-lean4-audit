import os,re,json,sys
root=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
CODE=('.mjs','.js','.py','.sol','.lean','.ts')
skip=('.lake','.git','node_modules','docs/archive','__pycache__')
def is_test(p):
    b=os.path.basename(p)
    return bool(re.search(r'(^|/)(test|tests|Testing|PaperTests|Tests)(/|$)',p) or b.startswith('test_') or re.search(r'\.test\.(mjs|js)$|\.t\.sol$|_test\.py$|Test[s]?\.lean$|Tests?[A-Z]\w*\.lean$',b) or 'test-support' in p or p.startswith('test_reporting') or p.startswith('test-fixtures'))
tests=[];prod=[]
for d,ds,fs in os.walk(root):
    rel=os.path.relpath(d,root)
    if any(rel==s or rel.startswith(s+'/') for s in skip): ds[:]=[];continue
    for f in fs:
        if f.endswith(CODE):
            p=os.path.normpath(os.path.join(rel,f))
            (tests if is_test(p) else prod).append(p)
json.dump({'tests':sorted(tests),'prod':sorted(prod)},open('audit/2026-10-14-test-guidelines/scans/inv.json','w'),indent=0)
print(len(tests),len(prod))
from collections import Counter
c=Counter('/'.join(p.split('/')[:2])+' '+os.path.splitext(p)[1] for p in tests)
for k,v in sorted(c.items()): print(v,k)
