import pytest

from classify import classify, find_verb


@pytest.mark.parametrize("title, body, expected", [
    ("What is the best way to read a file?", "", "Evaluating"),
    ("What is the difference between a list and a tuple?", "", "Analyzing"),
    ("Why does my loop skip items?", "", "Analyzing"),
    ("What does the yield keyword do?", "", "Understanding"),
    ("How does the GIL work?", "", "Understanding"),
    ("How to create a dictionary from two lists", "", "Creating"),
    ("How can I iterate over rows in a DataFrame?", "", "Applying"),
    ("Python list of lists", "I want to convert it to a string.", "Understanding"),
    ("How do I get the last element of a list?", "", "Applying"),
    ("Remove a prefix from a string", "", "Unclassified"),
    ("pg_config executable not found", "", "Unclassified"),
])
def test_classify(title, body, expected):
    assert classify(title, body)[0] == expected


def test_table_word_used_as_a_noun_is_ignored():
    assert find_verb("Sort the list by key") is None
    assert find_verb("my code prints the wrong value") is None


def test_table_word_in_verb_position_is_matched():
    assert find_verb("I want to use map here") == ("Applying", "use")
    assert find_verb("Efficiently updating a dictionary") == ("Analyzing", "updating")
    assert find_verb("Write a function that reverses a string") == ("Applying", "write")


def test_title_takes_priority_over_body():
    assert classify("How to debug a crash", "I want to create a tool.") == ("Evaluating", "debug")
