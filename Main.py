import time

from Parallel import find_max_prime_parallel


if __name__ == "__main__":

    timeout = int(input("Tempo de execução (segundos): "))

    workers = int(input("Número de workers: "))

    start_total = time.perf_counter()

    result = find_max_prime_parallel(timeout, workers)

    end_total = time.perf_counter()

    print("\nMaior primo encontrado:", result)
    print("Notação científica:", f"{result:.15e}")
    print("Número de dígitos:", len(str(result)))
    print("Tempo total:",
          round(end_total - start_total, 2),
          "segundos")