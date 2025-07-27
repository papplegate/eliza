import json, re

SUBSTITUTIONS = {
    r'([^() \n]+)': r'"\1",',  # delineate "strings" 
    r'\)(?!\n)': r'),',  # add commas after "tuples"
}

result = {}
unmatched = []
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
            if isinstance(element, str):
                if re.compile(r'\d+').search(element):
                    result[keyword]['score'] = int(element)
                elif element == '=':
                    result[keyword]['replacement'] = stack.pop()
                else:
                    result[keyword]['replace_before_transforming'] = element
                continue

            if isinstance(element, tuple):
                if isinstance(element[0], str) and element[0][0] == '=':
                    result[keyword]["go_to"] = element[0][1:] 
                    continue

                if '=' in element:
                    equals_index = element.index('=')
                    pattern = ' '.join(element[:equals_index])
                    transformation = ' '.join(element[equals_index + 1:])
                    result[keyword]["transformations"] = result[keyword].get('transformations', {pattern: []})
                    result[keyword]["transformations"][pattern].append(transformation)
                    continue

                try:
                    pattern = ' '.join(element[0]) if isinstance(element[0], tuple) else element[0][0]
                    result[keyword]["transformations"] = result[keyword].get("transformations", {}) | {pattern: [' '.join(transformation) for transformation in element[1:]]} 
                except:
                    unmatched.append(str(element))

result['unmatched'] = unmatched
print(json.dumps(result, indent=4))
