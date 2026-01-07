import json
import re
from typing import Any


def parse_eliza_script():
    """Parse the original ELIZA script from the appendix into a structured JSON format."""

    with open("weizenbaum_1966_appendix.txt", "r", encoding="utf-8") as f:
        content = f.read()

    result = {
        "greeting": "HOW DO YOU DO. PLEASE TELL ME YOUR PROBLEM",
        "keywords": {},
        "word_lists": {},
        "pre_substitutions": {},
        "memory_rules": {},
    }

    # Split content into individual LISP expressions
    expressions = []
    depth = 0
    start = 0

    for i, char in enumerate(content):
        if char == "(":
            if depth == 0:
                start = i
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                expressions.append(content[start : i + 1])

    # Process each expression
    for expr in expressions:
        expr = expr.strip()
        if not expr:
            continue

        try:
            parsed = parse_lisp_expression(expr)
            if not parsed:
                continue

            # Extract greeting
            if (
                len(parsed) == 1
                and isinstance(parsed[0], str)
                and "HOW DO YOU DO" in parsed[0]
            ):
                result["greeting"] = parsed[0]
                continue

            # Skip START marker
            if parsed == ["START"]:
                continue

            # Handle simple substitutions like (DONT = DON'T)
            if len(parsed) == 3 and parsed[1] == "=":
                result["pre_substitutions"][parsed[0]] = parsed[2]
                continue

            # Handle MEMORY rules
            if len(parsed) >= 1 and parsed[0] == "MEMORY":
                memory_data = parse_memory_rule(parsed)
                if memory_data:
                    result["memory_rules"][memory_data["keyword"]] = memory_data[
                        "templates"
                    ]
                continue

            # Handle keyword definitions
            if len(parsed) >= 1:
                keyword = parsed[0]
                keyword_data = parse_keyword_definition(parsed)
                if keyword_data:
                    result["keywords"][keyword] = keyword_data

        except Exception:
            # Skip malformed expressions
            continue

    return result


def parse_lisp_expression(expr):
    """Parse a single LISP expression into a nested list structure."""
    expr = expr.strip()
    if not expr.startswith("(") or not expr.endswith(")"):
        return None

    # Remove outer parentheses
    content = expr[1:-1].strip()
    if not content:
        return []

    # Parse tokens
    tokens = []
    i = 0
    while i < len(content):
        if content[i] == " ":
            i += 1
            continue
        if content[i] == "(":
            # Find matching closing parenthesis
            depth = 1
            j = i + 1
            while j < len(content) and depth > 0:
                if content[j] == "(":
                    depth += 1
                elif content[j] == ")":
                    depth -= 1
                j += 1
            if depth == 0:
                # Recursively parse nested expression
                nested = parse_lisp_expression(content[i:j])
                if nested is not None:
                    tokens.append(nested)
                i = j
            else:
                i += 1
        else:
            # Find end of token
            j = i
            while j < len(content) and content[j] not in " ()":
                j += 1
            token = content[i:j]
            if token:
                tokens.append(token)
            i = j

    return tokens


def find_referenced_positions(responses):
    """Find which positions are referenced in response templates."""
    referenced = set()
    for resp in responses:
        if isinstance(resp, list):
            # Check if this is a PRE directive: (PRE (YOU ARE 3) (=I))
            if len(resp) >= 2 and resp[0] == "PRE":
                # resp[1] is the transformation list like ['YOU', 'ARE', '3']
                if len(resp) > 1 and isinstance(resp[1], list):
                    for item in resp[1]:
                        if isinstance(item, str) and item.isdigit():
                            referenced.add(int(item))
            else:
                # Regular response list, look for string digits
                for item in resp:
                    if isinstance(item, str) and item.isdigit():
                        referenced.add(int(item))
        elif isinstance(resp, str):
            # Response is a string, find numbers in it
            for match in re.finditer(r"\b(\d+)\b", resp):
                referenced.add(int(match.group(1)))
        elif isinstance(resp, dict):
            # Already formatted PRE directive (shouldn't happen at this stage)
            if resp.get("type") == "pre" and "transformation" in resp:
                for item in resp["transformation"]:
                    if isinstance(item, str) and item.isdigit():
                        referenced.add(int(item))
    return referenced


def format_pattern(pattern_list, referenced_positions):
    """
    Convert a pattern list to a modern Python regex pattern.
    Returns (regex_pattern, position_map) where position_map maps
    original ELIZA positions to capture group numbers.
    Only creates capture groups for positions referenced in responses.
    Generates patterns for use with re.search():
    - Skips leading '0' wildcard (search finds pattern anywhere)
    - Makes trailing '0' wildcard greedy (.*) to capture to end
    """
    regex_parts = []
    position_map = {}
    capture_count = 0
    position = 0

    # Determine if first/last items are wildcards for special handling
    is_first = True
    last_wildcard_index = None
    for i, item in enumerate(pattern_list):
        if item == "0":
            last_wildcard_index = i

    for i, item in enumerate(pattern_list):
        position += 1
        should_capture = position in referenced_positions
        is_last_wildcard = item == "0" and i == last_wildcard_index
        is_first_wildcard = is_first and item == "0"

        if isinstance(item, list):
            is_first = False
            # Handle alternations like (* WANT NEED) or word list refs like (/BELIEF)
            if len(item) > 0:
                # Check if it's a word list reference
                if isinstance(item[0], str) and item[0].startswith("/"):
                    # Word list reference - will be expanded later
                    if should_capture:
                        capture_count += 1
                        position_map[position] = capture_count
                        # Wrap in parens so expand_wordlist_refs creates a capturing group
                        regex_parts.append("(" + item[0] + ")")
                    else:
                        regex_parts.append(item[0])  # Will expand to non-capturing
                elif isinstance(item[0], str) and item[0] == "*":
                    # Alternation: (* WANT NEED ...)
                    words = [str(x) for x in item[1:]]
                    if should_capture:
                        capture_count += 1
                        position_map[position] = capture_count
                        regex_parts.append(
                            "("
                            + "(?:"
                            + "|".join(re.escape(w) for w in words)
                            + ")"
                            + ")"
                        )
                    else:
                        regex_parts.append(
                            "(?:" + "|".join(re.escape(w) for w in words) + ")"
                        )
                else:
                    # Regular alternation - clean up tokens with leading *
                    cleaned_items = []
                    for x in item:
                        if isinstance(x, str) and x.startswith("*") and len(x) > 1:
                            cleaned_items.append(x[1:])
                        else:
                            cleaned_items.append(str(x))
                    if should_capture:
                        capture_count += 1
                        position_map[position] = capture_count
                        regex_parts.append(
                            "("
                            + "(?:"
                            + "|".join(re.escape(w) for w in cleaned_items)
                            + ")"
                            + ")"
                        )
                    else:
                        regex_parts.append(
                            "(?:" + "|".join(re.escape(w) for w in cleaned_items) + ")"
                        )
        else:
            # Replace numeric wildcards with regex wildcards
            if item == "0":
                # Skip leading wildcard - re.search() will find pattern anywhere
                if is_first_wildcard:
                    is_first = False
                    continue

                # Trailing wildcard should be greedy to capture to end
                if should_capture:
                    capture_count += 1
                    position_map[position] = capture_count
                    if is_last_wildcard:
                        regex_parts.append("(.*)")  # Greedy capture to end
                    else:
                        regex_parts.append("(.*?)")  # Non-greedy for middle wildcards
                else:
                    if is_last_wildcard:
                        regex_parts.append(".*")  # Greedy non-capture to end
                    else:
                        regex_parts.append(".*?")  # Non-greedy non-capture
                is_first = False
            else:
                # Literal word - NOT captured, no word boundaries
                regex_parts.append(re.escape(str(item)))
                is_first = False

    # Join parts with spaces, but wildcards match spaces themselves
    # ELIZA's "0" wildcard matches zero or more words, so regex wildcards
    # shouldn't have explicit spaces around them
    regex = ""
    for i, part in enumerate(regex_parts):
        if i > 0:
            # Don't add space around bare wildcards or captured wildcards
            # They need to match spaces themselves to allow zero-word matches
            prev_part = regex_parts[i - 1]
            curr_part = part

            # Check if previous or current part is a wildcard (bare or captured)
            prev_is_wildcard = prev_part in (".*?", ".*") or prev_part.startswith("(.*")
            curr_is_wildcard = curr_part in (".*?", ".*") or curr_part.startswith("(.*")

            if not prev_is_wildcard and not curr_is_wildcard:
                regex += " "
        regex += part

    return regex, position_map


def renumber_response(response, position_map):
    """
    Renumber position references in a response template.
    Converts old ELIZA position numbers to new capture group numbers.
    """
    if isinstance(response, dict):
        # Special handling for PRE directives - renumber transformation array
        if response.get("type") == "pre" and "transformation" in response:
            new_transformation = []
            for item in response["transformation"]:
                if isinstance(item, str) and item.isdigit():
                    old_pos = int(item)
                    if old_pos in position_map:
                        new_transformation.append(str(position_map[old_pos]))
                    else:
                        new_transformation.append(item)
                else:
                    new_transformation.append(item)
            response["transformation"] = new_transformation
        return response

    if not isinstance(response, str):
        return response

    # Use placeholders to avoid cascading replacements
    # First pass: replace old positions with placeholders
    result = response
    for old_pos in sorted(position_map.keys(), reverse=True):
        placeholder = f"__PH{old_pos}__"
        result = re.sub(r"\b" + str(old_pos) + r"\b", placeholder, result)

    # Second pass: replace placeholders with new positions
    for old_pos in position_map.keys():
        new_pos = position_map[old_pos]
        placeholder = f"__PH{old_pos}__"
        result = result.replace(placeholder, str(new_pos))

    return result


def expand_wordlist_refs(pattern: str, word_lists: dict) -> str:
    """Expand word list references like /BELIEF in regex patterns."""
    result = pattern

    # Find all /WORDLIST tokens in the pattern
    for wordlist_name, words in word_lists.items():
        ref = "/" + wordlist_name
        if ref in result:
            # Check if this is a captured or non-captured group
            # Look for (/ or just /
            captured_ref = "(" + ref
            if captured_ref in result:
                # Already has capturing parens, expand as non-capturing inside
                expanded = (
                    "(" + "(?:" + "|".join(re.escape(w) for w in words) + ")" + ")"
                )
                result = result.replace(captured_ref, expanded)
            else:
                # No capturing parens, expand as non-capturing group
                expanded = "(?:" + "|".join(re.escape(w) for w in words) + ")"
                result = result.replace(ref, expanded)

    return result


def format_response(resp):
    """Convert a response to proper format, handling special directives."""
    if isinstance(resp, list):
        # Check for PRE directive
        if len(resp) >= 2 and resp[0] == "PRE":
            return {
                "type": "pre",
                "transformation": resp[1] if len(resp) > 1 else [],
                "target": resp[2] if len(resp) > 2 else [],
            }
        # Check for NEWKEY
        if len(resp) == 1 and resp[0] == "NEWKEY":
            return {"type": "newkey"}
        # Check for keyword reference like (=WORD)
        if len(resp) == 1 and isinstance(resp[0], str) and resp[0].startswith("="):
            return {"type": "goto", "keyword": resp[0][1:]}
        # Regular response - join into string
        return " ".join(str(r) for r in resp)
    if isinstance(resp, str):
        # Check for inline keyword reference
        if resp == "NEWKEY":
            return {"type": "newkey"}
        if resp.startswith("="):
            return {"type": "goto", "keyword": resp[1:]}
        return resp
    else:
        return str(resp)


def parse_memory_rule(parsed_expr):
    """Parse a MEMORY rule like (MEMORY MY (0 YOUR 0 = template) ...)."""
    if len(parsed_expr) < 3:
        return None

    # Format: (MEMORY keyword (pattern = template) ...)
    keyword = parsed_expr[1]
    templates = []

    for item in parsed_expr[2:]:
        if isinstance(item, list) and "=" in item:
            # Find the = separator
            eq_index = item.index("=")
            pattern = item[:eq_index]
            template_parts = item[eq_index + 1 :]

            # Find which positions are referenced in the template
            referenced_positions = set()
            for part in template_parts:
                if isinstance(part, str) and part.isdigit():
                    referenced_positions.add(int(part))

            # Format the pattern and get position mapping
            formatted_pattern_result = format_pattern(pattern, referenced_positions)
            if isinstance(formatted_pattern_result, tuple):
                pattern_str = formatted_pattern_result[0]
                position_map = (
                    formatted_pattern_result[1]
                    if len(formatted_pattern_result) > 1
                    else {}
                )
            else:
                pattern_str = formatted_pattern_result
                position_map = {}

            # Renumber template positions using position_map
            renumbered_template_parts = []
            for part in template_parts:
                if isinstance(part, str) and part.isdigit():
                    old_pos = int(part)
                    new_pos = position_map.get(old_pos, old_pos)
                    renumbered_template_parts.append(str(new_pos))
                else:
                    renumbered_template_parts.append(part)

            templates.append(
                {
                    "pattern": pattern_str,
                    "template": " ".join(str(t) for t in renumbered_template_parts),
                }
            )

    return {"keyword": keyword, "templates": templates}


def parse_keyword_definition(parsed_expr):
    """Parse a keyword definition into structured data."""
    if len(parsed_expr) < 1:
        return None

    keyword_data = {"rank": 0, "responses": {}, "substitution": None, "word_list": None}

    # Handle DLIST entries for word categories
    # DLIST(/CATEGORY) gets parsed as two tokens: "DLIST" and ["/CATEGORY"]
    # Track indices to skip in main parsing loop
    skip_indices = set()
    if len(parsed_expr) >= 3:
        for i, item in enumerate(parsed_expr[1:], start=1):
            if isinstance(item, str) and item == "DLIST":
                # Check if next item is the category list
                if i + 1 < len(parsed_expr) and isinstance(parsed_expr[i + 1], list):
                    category_list = parsed_expr[i + 1]
                    if len(category_list) > 0:
                        # Extract category - could be like ["/BELIEF"] or ["/NOUN", "FAMILY"]
                        category_parts = []
                        for part in category_list:
                            part_str = str(part)
                            # Remove leading /
                            if part_str.startswith("/"):
                                part_str = part_str[1:]
                            category_parts.append(part_str)
                        category = "_".join(category_parts)
                        keyword_data["word_list"] = category
                        # Mark both DLIST and its argument for skipping
                        skip_indices.add(i)
                        skip_indices.add(i + 1)
                        break

    # Parse remaining tokens
    i = 1
    while i < len(parsed_expr):
        # Skip indices that were processed as DLIST
        if i in skip_indices:
            i += 1
            continue

        item = parsed_expr[i]

        # Handle rank (numeric value)
        if isinstance(item, str) and item.isdigit():
            keyword_data["rank"] = int(item)
            i += 1
            continue

        # Handle substitution (= WORD)
        if isinstance(item, str) and item.startswith("="):
            if len(item) > 1:
                keyword_data["substitution"] = item[1:]
            elif i + 1 < len(parsed_expr):
                keyword_data["substitution"] = parsed_expr[i + 1]
                i += 1
            i += 1
            continue

        # Handle standalone substitution tokens like (=DIT)
        if (
            isinstance(item, list)
            and len(item) == 1
            and isinstance(item[0], str)
            and item[0].startswith("=")
        ):
            keyword_data["substitution"] = item[0][1:]
            i += 1
            continue

        # Handle response patterns (nested lists)
        if isinstance(item, list) and len(item) >= 2:
            pattern_list = item[0] if isinstance(item[0], list) else [item[0]]
            responses = item[1:]

            # Find which positions are referenced in responses
            referenced_positions = find_referenced_positions(responses)

            # Convert pattern to structured format
            pattern, position_map = format_pattern(pattern_list, referenced_positions)

            # Convert responses to structured format and renumber references
            response_strings = []
            for resp in responses:
                formatted_resp = format_response(resp)
                # Renumber position references in response
                renumbered_resp = renumber_response(formatted_resp, position_map)
                response_strings.append(renumbered_resp)

            keyword_data["responses"][pattern] = response_strings

        i += 1

    return keyword_data


# Generate the JSON
try:
    result = parse_eliza_script()

    # Post-process to organize word lists
    word_lists: dict[str, list[str]] = {}
    keywords_to_remove = []

    for keyword, data in result["keywords"].items():
        if data.get("word_list"):
            category = data["word_list"]
            if category not in word_lists:
                word_lists[category] = []
            word_lists[category].append(keyword)
            keywords_to_remove.append(keyword)

    # Clean up keywords that are just word list entries
    for keyword in keywords_to_remove:
        if (
            not result["keywords"][keyword]["responses"]
            and not result["keywords"][keyword]["substitution"]
        ):
            del result["keywords"][keyword]

    result["word_lists"] = word_lists

    # Special handling: NOUN_FAMILY words should also be included in FAMILY patterns
    if "NOUN_FAMILY" in word_lists and "FAMILY" in word_lists:
        # Add NOUN_FAMILY words (MOTHER, FATHER) to FAMILY word list
        # This allows patterns referencing /FAMILY to match both "mom" and "mother"
        for word in word_lists["NOUN_FAMILY"]:
            if word not in word_lists["FAMILY"]:
                word_lists["FAMILY"].append(word)

    # Remove empty word_list fields from remaining keywords
    for keyword, data in list(result["keywords"].items()):
        if "word_list" in data:
            del data["word_list"]
        # Remove null fields for cleaner output
        if data.get("substitution") is None:
            del data["substitution"]
        if not data.get("responses"):
            data.pop("responses", None)

    # Don't expand word lists here - let eliza.py handle it at runtime
    # This keeps the JSON readable and separates data from implementation

    print(json.dumps(result, indent=2))

except Exception as e:
    print(f"Error: {e}")
    # Fallback to simpler parsing if complex parsing fails
    with open("weizenbaum_1966_appendix.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    simple_result: dict[str, Any] = {
        "greeting": "HOW DO YOU DO. PLEASE TELL ME YOUR PROBLEM",
        "keywords": {},
        "word_lists": {},
        "pre_substitutions": {},
    }

    for line in lines:
        line = line.strip()
        if line and line.startswith("(") and line.endswith(")"):
            content = line[1:-1]
            if " = " in content and content.count("(") == 0:
                parts = content.split(" = ")
                if len(parts) == 2:
                    simple_result["pre_substitutions"][parts[0]] = parts[1]

    print(json.dumps(simple_result, indent=2))
