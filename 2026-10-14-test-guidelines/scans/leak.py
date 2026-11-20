import json,re,os,glob,collections
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
d=json.load(open('audit/2026-10-14-test-guidelines/scans/inv.json'))
lit=re.compile(r'''(?<![\w$])(["'`])((?:(?!\1)[^\\\n]|\\.){3,80})\1''')
idish=re.compile(r'^(?=.*\d)(?=.*[A-Za-z])[A-Za-z0-9][\w.:/-]{2,}$|^0x[0-9a-fA-F]{6,}$|^\d{5,}$')
# production runtime sources
prod=[p for p in d['prod'] if (p.startswith('services/') or p.startswith('contracts/src') or p.startswith('reference/') or p.startswith('scripts/') or p.startswith('tooling/') or p.startswith('perf/tools')) and not p.endswith('.lean')]
prodtext={p:open(p,errors='ignore').read() for p in prod}
testlits=collections.defaultdict(set)
for t in d['tests']:
    if t.endswith('.lean'): continue
    for m in lit.finditer(open(t,errors='ignore').read()):
        s=m.group(2)
        if idish.match(s) and not re.match(r'^(node:|\.\.?/|https?:)',s) and not s.endswith(('.mjs','.js','.py','.json','.md','.lean','.sol','.tsv','.ts','.txt','.csv','.toml','.yaml','.yml')):
            testlits[s].add(t)
hits=collections.defaultdict(list)
for s,ts in testlits.items():
    q=[f'"{s}"',f"'{s}'",f'`{s}`']
    for p,txt in prodtext.items():
        if any(x in txt for x in q):
            hits[s].append(p)
print(len(testlits),'id-ish test literals;',len(hits),'also in production')
for s in sorted(hits):
    print(repr(s),'| tests:',len(testlits[s]),sorted(testlits[s])[:2],'| prod:',hits[s][:3])
