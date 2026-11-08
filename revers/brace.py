import re, sys
p = sys.argv[1]
s = open(p, encoding='utf-8', errors='replace').read()
s = re.sub(r'//[^\n]*', '', s)
s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
s = re.sub(r"'(?:\\.|[^'\\])*'", "''", s)
print('braces', s.count('{') - s.count('}'))
print('parens', s.count('(') - s.count(')'))
