import re

SUBSTITUTIONS = {
    r'([^() \n]+)': r'"\1",',  # delineate "strings" 
    r'\)(?!\n)': r'),',  # add commas after "tuples"
}

result = {}
with open('weizenbaum_1966_appendix.txt', 'r') as appendix:
    for i, line in enumerate(appendix):

        if i < 2 or i > 69:
            continue

        for pattern, replacement in SUBSTITUTIONS.items():
            line = re.compile(pattern).sub(replacement, line)
        exec('parsed = ' + line)

        result[parsed[0]] = {}

        for element in parsed[1:]:
            if type(element) == str and re.compile(r'\d+').search(element):
                result[parsed[0]]['score'] = int(element)

print(result)
