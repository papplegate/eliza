import re
substitutions = {
    r'([^() \n]+)': r'"\1",',  # delineate "strings" 
    r'\)(?!\n)': r'),',  # add commas after "tuples"
}

with open('weizenbaum_1966_appendix.txt', 'r') as appendix:
    for i, line in enumerate(appendix):
        if i < 2:
            continue
        for pattern, replacement in substitutions.items():
            line = re.compile(pattern).sub(replacement, line)
        exec('line = ' + line)
        print(line)
