import re
substitutions = {
    r'([^() \n]+)': r'"\1",',  # delineate "strings" 
    r'\)': r'),',  # add commas after "tuples"
}

with open('weizenbaum_1966_appendix.txt', 'r') as appendix:
    for line in appendix.readlines()[2:]:
        for pattern, replacement in substitutions.items():
            line = re.compile(pattern).sub(replacement, line)
        print(line, end='')
