import pytest

from myia import myia
from myia.compile.backends import load_backend
from myia.lib import Empty, HandleInstance, core
from myia.operations import handle, handle_get, handle_set

try:
    load_backend('relay')
except Exception:
    pytestmark = pytest.mark.skip('Requires relay')


def add_one(x):
    # Not universal, but should work from universal function
    return x + 1


@core(use_universe=True)
def increment(h):
    return handle_set(h, add_one(handle_get(h)))


def test_increment():

    @myia(use_universe=True, backend='relay')
    def plus4(x):
        h = handle(x)
        increment(h)
        increment(h)
        increment(h)
        increment(h)
        return handle_get(h)

    assert plus4(3) == 7
    assert plus4(10) == 14


def test_increment_interleave():

    @myia(use_universe=True, backend='relay')
    def plus2(x, y):
        h1 = handle(x)
        h2 = handle(y)
        increment(h1)
        increment(h2)
        increment(h1)
        increment(h2)
        return handle_get(h1), handle_get(h2)

    assert plus2(3, 6) == (5, 8)
    assert plus2(10, -21) == (12, -19)


def test_increment_loop():

    @myia(use_universe=True, backend='relay')
    def plus(x, y):
        h = handle(x)
        i = y
        while i > 0:
            increment(h)
            i = i - 1
        return handle_get(h)

    assert plus(3, 4) == 7
    assert plus(10, 13) == 23


def test_increment_recursion():

    @myia(use_universe=True, backend='relay')
    def length(h, xs):
        if not isinstance(xs, Empty):
            increment(h)
            length(h, xs.tail)
        return handle_get(h)

    h = HandleInstance(0)
    hb = length.to_device(h)
    assert length(hb, [1, 2, 3, 4]) == 4


def test_give_handle():

    @myia(use_universe=True, backend='relay')
    def plus(h, y):
        i = y
        while i > 0:
            increment(h)
            i = i - 1
        return handle_get(h)

    h1 = HandleInstance(0)
    h2 = HandleInstance(0)

    hb1 = plus.to_device(h1)
    hb2 = plus.to_device(h2)

    # handle is updated automatically
    assert plus(hb1, 4) == 4
    assert plus(hb2, 9) == 9
    assert plus(hb1, 30) == 34


def test_return_handle():

    @myia(use_universe=True, backend='relay')
    def plus2(h):
        increment(h)
        increment(h)
        return h

    h = HandleInstance(0)
    hb = plus2.to_device(h)
    # This might return a BackendValue later but it seems
    # to return the handle for now.
    h2 = plus2(hb)
    assert h2.state == 2
