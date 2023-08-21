import contextlib
import pytest
import re

@contextlib.contextmanager
def forgive(predicate):
    try:
        yield
    except BaseException as error:
        if not predicate(error):
            raise error

class BooleanPredicate:
    def __or__(self, rhs):
        return ShortCircuitPredicate(True, [self, rhs])
    def __and__(self, rhs):
        return ShortCircuitPredicate(False, [self, rhs])

class ShortCircuitPredicate(BooleanPredicate):
    """
    Return the first breaker in a sequence of predicates.
    If none return the breaker, then return its inverse.

    For `and`, the breaker is `False`.
    For `or`, the breaker is `True`.
    """
    def __init__(self, breaker, predicates):
        self.breaker = breaker
        self.predicates = predicates
    def __call__(self, *args, **kwargs):
        for predicate in self.predicates:
            if predicate(*args, **kwargs) == self.breaker:
                return self.breaker
        return not self.breaker

class FunctionPredicate(BooleanPredicate):
    def __init__(self, function):
        # We cannot just assign to `__call__` because
        # Python looks up special methods on the type, not the instance.
        self.function = function
    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)
    def matches(self, pattern):
        def function(*args, **kwargs):
            return re.search(pattern, self.function(*args, **kwargs))
        return FunctionPredicate(function)

class CapturePredicate:
    def __init__(self, cap):
        self.cap = cap
    def __getattr__(self, attr):
        def function(*args, **kwargs):
            return getattr(self.cap.readouterr(), attr)
        return FunctionPredicate(function)

@pytest.fixture
def cap(capfd):
    return CapturePredicate(capfd)
