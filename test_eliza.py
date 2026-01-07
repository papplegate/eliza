"""
Test suite for ELIZA chatbot implementation.
"""

import pytest
from eliza import eliza_response, MEMORY


def test_exchange_1():
    """First exchange from the dialog."""
    response = eliza_response("Men are all alike.")
    assert response == "IN WHAT WAY"


def test_exchange_2():
    """Second exchange from the dialog."""
    response = eliza_response("They're always bugging us about something or other.")
    assert response == "CAN YOU THINK OF A SPECIFIC EXAMPLE"


def test_exchange_3():
    """Third exchange from the dialog."""
    response = eliza_response("Well, my boyfriend made me come here.")
    assert response == "YOUR BOYFRIEND MADE YOU COME HERE"


def test_exchange_4():
    """Fourth exchange - response to statement about being sad."""
    response = eliza_response("He says I'm depressed much of the time.")
    assert response == "I AM SORRY TO HEAR YOU ARE DEPRESSED"


def test_exchange_5():
    """Fifth exchange - response to being unhappy."""
    response = eliza_response("It's true.  I am unhappy.")
    assert response == "DO YOU THINK COMING HERE WILL HELP YOU NOT TO BE UNHAPPY"


def test_exchange_6():
    """Exchange about needing help."""
    response = eliza_response("I need some help, that much seems certain.")
    assert response == "WHAT WOULD IT MEAN TO YOU IF YOU GOT SOME HELP"


def test_exchange_7():
    """Exchange about learning to get along with parent."""
    response = eliza_response("Perhaps I could learn to get along with my mother.")
    assert response == "TELL ME MORE ABOUT YOUR FAMILY"


def test_exchange_8():
    """Exchange about parent taking care."""
    response = eliza_response("My mother takes care of me.")
    assert response == "WHO ELSE IN YOUR FAMILY TAKES CARE OF YOU"


def test_exchange_9():
    """Simple response about parent."""
    response = eliza_response("My father.")
    assert response == "YOUR FATHER"


def test_exchange_10():
    """Exchange about resemblance."""
    response = eliza_response("You are like my father in some ways.")
    assert response == "WHAT RESEMBLANCE DO YOU SEE"


def test_exchange_11():
    """Exchange about not being aggressive."""
    response = eliza_response(
        "You are not very aggressive but I think you don't want me to notice that."
    )
    assert response == "WHAT MAKES YOU THINK I AM NOT VERY AGGRESSIVE"


def test_exchange_12():
    """Exchange about not arguing."""
    response = eliza_response("You don't argue with me.")
    assert response == "WHY DO YOU THINK I DON'T ARGUE WITH YOU"


def test_exchange_13():
    """Exchange about being afraid."""
    response = eliza_response("You are afraid of me.")
    assert response == "DOES IT PLEASE YOU TO BELIEVE I AM AFRAID OF YOU"


def test_exchange_14():
    """Exchange about parent being afraid."""
    response = eliza_response("My father is afraid of everybody.")
    assert response == "WHAT ELSE COMES TO MIND WHEN YOU THINK OF YOUR FATHER"


def test_exchange_15():
    """Final exchange with context-aware response."""
    response = eliza_response("Bullies.")
    assert (
        response
        == "DOES THAT HAVE ANYTHING TO DO WITH THE FACT THAT YOUR BOYFRIEND MADE YOU COME HERE"
    )
