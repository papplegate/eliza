import re
line = "(SORRY ((0) (PLEASE DON'T APOLIGIZE) (APOLOGIES ARE NOT NECESSARY) (WHAT FEELINGS DO YOU HAVE WHEN YOU APOLOGIZE) (I'VE TOLD YOU THAT APOLOGIES ARE NOT REQUIRED)))"
add_quotes = re.sub(r'([^\(^\)^ ]+)', r'"\1",', line)
add_commas = re.sub(r'(\)+)', r'\1,', add_quotes)
print(add_commas)
