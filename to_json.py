import re
line = "(REMEMBER 5 ((0 YOU REMEMBER 0) (DO YOU OFTEN THINK OF 4) (DOES THINKING OF 4 BRING ANYTHING ELSE TO MIND) (WHAT ELSE DO YOU REMEMBER) (WHY DO YOU REMEMBER 4 JUST NOW) (WHAT IN THE PRESENT SITUATION REMINDS YOU OF 4) (WHAT IS THE CONNECTION BETWEEN ME AND 4)) ((0 DO I REMEMBER 0) (DID YOU THINK I WOULD FORGET 5) (WHY DO YOU THINK I SHOULD RECALL 5 NOW) (WHAT ABOUT 5) (=WHAT) (YOU MENTIONED 5)) ((0) (NEWKEY)))"
substitutions = {
    r'\(([\w\d ]+?) \(': r'("\1", (',
    r'\(([^\(]+?)\)': r'"\1",',  # replace parenthesized words/groups with strings
    r'\) \(': r'), (',  # add commas between "tuples"
}
for pattern, replacement in substitutions.items():
    line = re.compile(pattern).sub(replacement, line)
print(line)
