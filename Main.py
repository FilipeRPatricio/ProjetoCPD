import time

from PrimeFormula import is_prime


def find_max_prime_sequential(timeout):
    start = time.time()

    n = 10**12 + 1

    best = 2

    while time.time() - start < timeout:

        if is_prime(n):
            best = n

        n += 2

    return best