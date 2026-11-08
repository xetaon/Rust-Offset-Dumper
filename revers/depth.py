import re, sys
p = r'C:\Users\SystemX\Desktop\Vlone Rust Internal\Interact.h'
lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
d = 0
start = 2322
for i in range(start - 1, 3300):
    s = lines[i]
    if i + 1 >= start and (i + 1) in (3143, 3163, 3193, 3246, 3249, 3280, 3281, 3282, 3283):
        print(i + 1, 'depth', d, '|', s.strip()[:110])
    t = re.sub(r'//.*', '', s)
    t = re.sub(r'"(?:\\.|[^"\\])*"', '', t)
    t = re.sub(r"'(?:\\.|[^'\\])*'", '', t)
    d += t.count('{') - t.count('}')
print('end depth', d)
