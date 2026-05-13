from multiprocessing import Process, Value, Lock, Event
import time
from PrimeFormula import is_prime

def worker(worker_id, start, workers, best_prime, stop_event):
    n = start + worker_id * 2

    while not stop_event.is_set():
        if is_prime(n):

            if n > best_prime.value:
                best_prime.value = n

        n += workers * 2

def find_max_prime_parallel(timeout, workers):

    start_number = 10**12 + 1
    best_prime = Value('Q', 2)
    stop_event = Event()

    processes = []

    # criar processos
    for i in range(workers):

        p = Process(
            target=worker,
            args=(
                i,
                start_number,
                workers,
                best_prime,
                stop_event
            )
        )

        processes.append(p)

    # arrancar processos
    for p in processes:
        p.start()

    # esperar timeout
    time.sleep(timeout)

    # mandar parar
    stop_event.set()

    # esperar que terminem
    for p in processes:
        p.join()

    return best_prime.value