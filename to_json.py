import json, re

SUBSTITUTIONS = {
    r'([^() \n]+)': r'"\1",',  # delineate "strings" 
    r'\)(?!\n)': r'),',  # add commas after "tuples"
}

result = {}
with open('weizenbaum_1966_appendix.txt', 'r') as appendix:
    total = 0
    unparsed = 0
    for i, line in enumerate(appendix):

        if i < 2 or i > 69:
            continue

        for pattern, replacement in SUBSTITUTIONS.items():
            line = re.compile(pattern).sub(replacement, line)
        exec('parsed = ' + line)

        if "DLIST" in parsed:
            term_list_name = parsed[-1][-1].replace('/', '')
            result.get(term_list_name, []).append(parsed[0])
            if len(parsed) == 3:
                total += 3
                continue
            parsed = parsed[:-2]

        keyword = parsed[0]
        result[keyword] = {}

        stack = list(parsed[1:])
        stack.reverse()
        while len(stack):
            element = stack.pop()
            total += 1
            if type(element) == str:
                if re.compile(r'\d+').search(element):
                    result[keyword]['score'] = int(element)
                elif element == '=':
                    result[keyword]['replace'] = stack.pop()
                else:
                    print(f"No match for {element} in {parsed}")
                    unparsed += 1
            if type(element) == tuple:
                if type(element[0]) is str and element[0][0] == '=':
                    result[keyword]["go_to"] = element[0][1:] 
                    continue
                try:
                    pattern = ' '.join(element[0]) if type(element[0]) is tuple else element[0][0]
                    result[keyword]["replacements"] = result[keyword].get('replacements', {}) | {pattern: [' '.join(replacement) for replacement in element[1:]]}
                except:
                    # print(f"No match for {element} in {parsed}")
                    unparsed += 1

print(json.dumps(result, indent=4))
print(total, unparsed, unparsed/total)
