import time

from Parallel import find_max_prime_parallel


if __name__ == "__main__":

    timeout = int(input("Tempo de execução (segundos): "))

    start_total = time.perf_counter()

    result = find_max_prime_parallel(timeout, 4)

    end_total = time.perf_counter()

    print("\nMaior primo encontrado:", result)
    print("Tempo total:", round(end_total - start_total, 2), "segundos")