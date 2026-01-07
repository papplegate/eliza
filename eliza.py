"""
ELIZA Chatbot Reimplementation.

This is a simplified version inspired by Joseph Weizenbaum's 1966 ELIZA program.
"""

import cmd
import json
import re
from typing import List, Tuple, Optional

with open("eliza_script.json", "r", encoding="utf-8") as f:
    SCRIPT = json.load(f)

# Global memory storage for recalled memories
MEMORY = []


def store_memory(keyword: str, normalized_input: str) -> None:
    """
    Check if keyword has memory rules and store matching inputs for later recall.

    Args:
        keyword: The keyword that matched
        normalized_input: The normalized user input
    """
    memory_rules = SCRIPT.get("memory_rules", {})
    if keyword not in memory_rules:
        return

    # Apply keyword substitution if it exists
    keyword_data = SCRIPT["keywords"].get(keyword, {})
    if "substitution" in keyword_data and keyword_data["substitution"]:
        substitute = keyword_data["substitution"]
        transformed_input = re.sub(
            r"\b" + re.escape(keyword) + r"\b",
            substitute,
            normalized_input,
            flags=re.IGNORECASE,
        )
    else:
        transformed_input = normalized_input

    # Apply pronoun reflection
    transformed_input = reflect_pronouns(transformed_input)

    # Try to match against memory patterns
    for memory_rule in memory_rules[keyword]:
        pattern = memory_rule["pattern"]

        # Expand word list references
        expanded_pattern = expand_word_lists(pattern)
        match = re.search(expanded_pattern, transformed_input, re.IGNORECASE)
        if match:
            # Store all templates for this match as a single memory entry
            templates = []
            for rule in memory_rules[keyword]:
                if re.search(
                    expand_word_lists(rule["pattern"]), transformed_input, re.IGNORECASE
                ):
                    memory_text = generate_response(rule["template"], match.groups())
                    templates.append(memory_text)

            # Store as a list of templates for this memory
            MEMORY.append(templates)
            break  # Only store one memory entry per input


def recall_memory() -> Optional[str]:
    """
    Recall a stored memory using rotation like keyword responses.

    Returns:
        A memory response, or None if no memories are stored
    """
    if not MEMORY:
        return None

    # Get the first memory entry
    memory_templates = MEMORY[0]

    # Use the last template and remove it
    response = memory_templates.pop()

    # If no templates left, remove this memory entry
    if not memory_templates:
        MEMORY.pop(0)

    return response


def eliza_response(
    user_input: str, _history: Optional[List[Tuple[str, str]]] = None
) -> str:
    """
    Generate an ELIZA-style response to user input.

    Args:
        user_input: The user's input text
        history: Optional list of (user_input, eliza_response) tuples representing
                conversation history. Used for context-aware responses.

    Returns:
        ELIZA's response as an uppercase string
    """
    # Normalize: trim, uppercase, split
    words = user_input.strip().upper().split()

    # Apply delimiter truncation (before stripping punctuation, so we can detect delimiters)
    words = truncate_on_delimiters(words)

    # Strip punctuation from each word
    clean_words = [word.strip(".,!?;:") for word in words]
    normalized_input = " ".join(clean_words)

    keyword_matches = find_keywords(clean_words)
    keyword_matches.sort(key=lambda x: x[1], reverse=True)

    for keyword, _ in keyword_matches:
        response = try_keyword(keyword, normalized_input)
        if response:
            # Check if this keyword has memory rules and store matches
            store_memory(keyword, normalized_input)
            return response

    # Before falling back to NONE, check if we have stored memories
    memory_response = recall_memory() if MEMORY else None
    if memory_response:
        return memory_response

    if "NONE" in SCRIPT["keywords"]:
        response = try_keyword("NONE", normalized_input)
        if response:
            return response

    return "PLEASE GO ON"


def apply_pre_substitutions(words: List[str]) -> List[str]:
    """Apply pre-substitutions to words."""
    substitutions = SCRIPT["pre_substitutions"]
    return [substitutions.get(word, word) for word in words]


def truncate_on_delimiters(words: List[str]) -> List[str]:
    """
    Apply ELIZA's delimiter rule from Weizenbaum 1966:
    - Before finding a keyword: delete text up to and including comma/period
    - After finding a keyword: delete text from comma/period onward

    Note: Words still have punctuation at this point for delimiter detection.
    """
    keywords = SCRIPT["keywords"]
    keyword_found = False
    result: List[str] = []

    for word in words:
        # Check if this word ends with a delimiter
        has_delimiter = word.endswith(",") or word.endswith(".")

        # Strip punctuation to check if it's a keyword
        clean_word = word.strip(".,!?;:")

        if not keyword_found:
            # Before finding keyword: skip everything up to delimiter
            if has_delimiter:
                # Delete this word and everything before it
                result = []
                continue
            result.append(word)
            # Check if this is a keyword
            if clean_word in keywords:
                keyword_found = True
        else:
            # After finding keyword: include this word, then stop at delimiter
            result.append(word)
            if has_delimiter:
                # Delimiter found - stop here, delete subsequent text
                break

    return result


def find_keywords(words: List[str]) -> List[Tuple[str, int]]:
    """Find all keywords present in the input words, return with their ranks."""
    keywords = SCRIPT["keywords"]
    found = []

    for word in words:
        # Words are already clean (punctuation stripped and substitutions applied)
        if word in keywords:
            rank = keywords[word].get("rank", 0)
            found.append((word, rank))

    return found


def expand_word_lists(pattern: str) -> str:
    """Expand word list references like (/FAMILY) in regex patterns."""
    word_lists = SCRIPT.get("word_lists", {})
    result = pattern

    for wordlist_name, words in word_lists.items():
        ref = "/" + wordlist_name
        # Look for captured (/WORDLIST) or uncaptured /WORDLIST
        captured_ref = "(" + ref + ")"
        if captured_ref in result:
            # Captured word list - create capturing group with alternation
            expanded = "((?:" + "|".join(re.escape(w) for w in words) + "))"
            result = result.replace(captured_ref, expanded)
        elif ref in result:
            # Uncaptured word list - create non-capturing group
            expanded = "(?:" + "|".join(re.escape(w) for w in words) + ")"
            result = result.replace(ref, expanded)

    return result


def try_keyword(keyword: str, normalized_input: str) -> Optional[str]:
    """Try to match patterns for a keyword and generate a response."""
    keyword_data = SCRIPT["keywords"].get(keyword)
    if not keyword_data:
        return None

    # If keyword has a substitution but no responses, try the substituted keyword
    if "substitution" in keyword_data and keyword_data["substitution"]:
        substitute = keyword_data["substitution"]
        if not keyword_data.get("responses"):
            # This is a simple redirect, try the substituted keyword
            return try_keyword(substitute, normalized_input)
        # Otherwise, transform the input for pattern matching with this keyword's patterns
        # For example, "I = YOU" means when user types "I", transform it to "YOU" to match patterns
        transformed_input = re.sub(
            r"\b" + re.escape(keyword) + r"\b",
            substitute,
            normalized_input,
            flags=re.IGNORECASE,
        )
    else:
        transformed_input = normalized_input

    # Apply pronoun reflection to transformed input before pattern matching
    # This allows patterns like "I(.*)YOU" to match when user says "you...me"
    # After YOU->I transformation: "I...ME", then ME->YOU gives "I...YOU"
    transformed_input = reflect_pronouns(transformed_input)

    responses = keyword_data.get("responses", {})
    if not responses:
        return None

    for pattern, response_list in responses.items():
        # Expand word list references in the pattern
        expanded_pattern = expand_word_lists(pattern)
        match = re.search(expanded_pattern, transformed_input, re.IGNORECASE)
        if match:
            # Use first response from the list
            response_template = response_list[0]

            # Handle special directives
            if isinstance(response_template, dict):
                if response_template.get("type") == "goto":
                    target_keyword = response_template["keyword"]
                    # Don't rotate for goto directives
                    return try_keyword(target_keyword, normalized_input)
                if response_template.get("type") == "newkey":
                    # Don't rotate for newkey directives
                    return None
                if response_template.get("type") == "pre":
                    # PRE directive: transform input, then goto target keyword
                    transformation = response_template.get("transformation", [])
                    target = response_template.get("target", [])

                    # Build new input from transformation
                    # transformation like ['YOU', 'ARE', '3'] means "YOU ARE <capture_group_3>"
                    new_words = []
                    for item in transformation:
                        if item.isdigit():
                            # Position reference - use captured group
                            pos = int(item)
                            if pos <= len(match.groups()):
                                new_words.append(match.group(pos))
                        else:
                            # Literal word
                            new_words.append(item)

                    new_input = " ".join(new_words)

                    # Extract target keyword (format: ['=KEYWORD'])
                    if target and len(target) > 0:
                        target_kw = target[0]
                        if target_kw.startswith("="):
                            target_kw = target_kw[1:]
                        # Don't rotate for PRE directives
                        return try_keyword(target_kw, new_input)

                    return None

            # Generate the response
            response = generate_response(response_template, match.groups())

            # Rotate: move used response to end of list (only if more than one response)
            if len(response_list) > 1:
                response_list.append(response_list.pop(0))

            return response

    return None


def reflect_pronouns(text: str) -> str:
    """
    Apply pronoun reflection and safe keyword substitutions to text.
    This handles pre_substitutions (ME -> YOU) and safe keyword substitutions like AM -> ARE.
    We avoid recursive pronoun substitutions (I/YOU/MY/YOUR).
    """
    words = text.split()
    # First apply pre_substitutions
    reflected_words = apply_pre_substitutions(words)

    # Then apply safe keyword substitutions (avoid pronoun recursion)
    # Safe substitutions are those that don't involve pronouns
    safe_substitutions = {
        "AM": "ARE",
    }

    final_words = []
    for word in reflected_words:
        if word in safe_substitutions:
            final_words.append(safe_substitutions[word])
        else:
            final_words.append(word)
    return " ".join(final_words)


def generate_response(template: str, captures: tuple) -> str:
    """Generate response from template by substituting numbered references with captures."""
    if not isinstance(template, str):
        return str(template)

    response = template

    for i, capture in enumerate(captures, 1):
        # Apply pronoun reflection to the captured text
        reflected_capture = reflect_pronouns(capture.strip())
        response = re.sub(r"\b" + str(i) + r"\b", reflected_capture, response)

    return response.strip()


class ElizaCmd(cmd.Cmd):
    """Interactive command-line interface for ELIZA chatbot."""

    intro = SCRIPT.get("greeting", "HOW DO YOU DO. PLEASE TELL ME YOUR PROBLEM")
    prompt = "> "

    def default(self, line: str) -> None:
        """Handle user input by generating ELIZA response."""
        if line.strip():
            response = eliza_response(line)
            print(response)

    def do_quit(self, _arg: str) -> bool:
        """Exit the ELIZA session."""
        print("GOODBYE")
        return True

    def do_exit(self, arg: str) -> bool:
        """Exit the ELIZA session."""
        return self.do_quit(arg)

    def do_EOF(self, arg: str) -> bool:  # pylint: disable=invalid-name
        """Handle EOF (Ctrl+D) to exit."""
        print()  # Print newline for clean exit
        return self.do_quit(arg)


if __name__ == "__main__":
    ElizaCmd().cmdloop()
