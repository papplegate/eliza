import re
substitutions = {
    r'\(([^\(]+?)\)': r'"\1",',  # replace parenthesized words/groups with strings
    r'([\w\d]++)(?<!\")(?!\")': r'"\1",', # get any words/numbers we missed
    r'\) \(': r'), (',  # add commas between "tuples"
}

with open('weizenbaum_1966_appendix.txt', 'r') as appendix:
    for line in appendix:
        for pattern, replacement in substitutions.items():
            line = re.compile(pattern).sub(replacement, line)
        print(line)
