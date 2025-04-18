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

        keyword = parsed[0]
        result[keyword] = {}

        stack = list(parsed[1:])
        stack.reverse()
        while len(stack):
            element = stack.pop()
            if type(element) == str:
                if re.compile(r'\d+').search(element):
                    result[keyword]['score'] = int(element)
                elif element == '=':
                    result[keyword]['replace'] = stack.pop()
                else:
                    print(f"No match for {element} in {parsed}")
        # types = []
        # for element in parsed[1:]:
        #     types.append(str(type(element)))
        #     if type(element) == str and re.compile(r'\d+').search(element):
        #         result[parsed[0]]['score'] = int(element)
        # print(types)

print(result)
