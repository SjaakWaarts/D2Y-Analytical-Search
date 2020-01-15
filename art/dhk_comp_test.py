def fib(n):
    old, new = 0, 1
    for _ in range(n):
        old, new = new, old + new
    return old

def test_fib():
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(10) == 55
