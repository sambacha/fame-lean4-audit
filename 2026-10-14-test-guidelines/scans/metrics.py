import json,re,os,csv
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
d=json.load(open('audit/2026-10-14-test-guidelines/scans/inv.json'))
R={
 'cases':r'^\s*(?:test|it)\s*\(|^\s*def test_\w+|function\s+test\w*\s*\(|function\s+invariant_\w*\s*\(',
 'asserts':r'\bassert\w*\b|\bexpect\w*\(|self\.assert\w+|\brequire\(',
 'lit_eq':r'assert\.(?:strictEqual|equal|deepStrictEqual|deepEqual)\([^;]*,\s*(?:-?\d[\d_n.]*|"[^"]*"|\'[^\']*\'|true|false|null)\s*[,)]|self\.assert(?:Equal|Equals)\([^\n]*,\s*(?:-?\d[\d_.]*|"[^"]*"|\'[^\']*\'|True|False|None)\s*[,)]|assertEq\([^;]*,\s*-?\d[\d_]*\s*[,)]',
 'neg':r'assert\.(?:throws|rejects|notEqual|notStrictEqual|notDeepStrictEqual|doesNotMatch|ok\(\s*!)|assertRaises|assertFalse|assertNotEqual|assertNotIn|expectRevert|vm\.expectRevert|\bassertFalse\b|refus|reject',
 'gen':r'Math\.random|mulberry|xorshift|splitmix|\bprng\b|\brng\b|PRNG|random\.Random|hypothesis|fast-check|forAll|requireHits|dkwCases|for\s*\(\s*let\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*[A-Z\d_]{2,}|function\s+testFuzz|uint\d*\s+\w+\)\s*public|bound\(|vm\.assume|invariant_|\bseed\b',
 'mutant':r'mutant|mutation|plant|kill',
}
rows=[]
for t in d['tests']:
    if t.endswith('.lean'): continue
    s=open(t,errors='ignore').read()
    r={'file':t,'lines':s.count('\n')}
    for k,p in R.items(): r[k]=len(re.findall(p,s,re.M))
    rows.append(r)
w=csv.DictWriter(open('audit/2026-10-14-test-guidelines/scans/test_file_metrics.csv','w'),fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('files',len(rows))
fl=[r for r in rows if r['cases']>0 and r['gen']==0 and r['neg']==0]
print('example-only & no negatives:',len(fl))
for r in fl: print(r)
fl2=[r for r in rows if r['cases']>0 and r['gen']==0 and r['neg']>0 and r['lit_eq']>=0.5*max(1,r['asserts'])]
print('literal-heavy, no generation:',len(fl2))
for r in fl2: print(r)
