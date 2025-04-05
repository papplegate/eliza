import re
line = "(SORRY ((0) (PLEASE DON'T APOLIGIZE) (APOLOGIES ARE NOT NECESSARY) (WHAT FEELINGS DO YOU HAVE WHEN YOU APOLOGIZE) (I'VE TOLD YOU THAT APOLOGIES ARE NOT REQUIRED)))"
substitutions = {
    r'([^\(^\)^ ]+)': r'"\1",',
    r'(\)+)': r'\1,',
}
for pattern, replacement in substitutions.items():
    line = re.compile(pattern).sub(replacement, line)
exec('line = ' + line)
print(line)
