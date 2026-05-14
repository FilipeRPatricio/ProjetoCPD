from multiprocessing import Process, Value, Lock, Event
import time
from PrimeFormula import is_prime

def worker(worker_id,workers,start_number,jump,best_prime,lock,stop_event):

    # posição inicial do worker
    n = start_number + worker_id * jump

    # garantir ímpar
    if n % 2 == 0:
        n += 1

    while not stop_event.is_set():

        if is_prime(n):

            with lock:

                if n > best_prime.value:
                    best_prime.value = n

        # saltar para a próxima posição
        n += workers * jump

def find_max_prime_parallel(timeout, workers):

    start_number = 10**15
    jump = 100_000_000

    best_prime = Value('Q', 2)
    lock = Lock()
    stop_event = Event()
    processes = []

    # criar workers
    for worker_id in range(workers):

        p = Process(
            target=worker,
            args=(
                worker_id,
                workers,
                start_number,
                jump,
                best_prime,
                lock,
                stop_event
            )
        )

        processes.append(p)

    # iniciar workers
    for p in processes:
        p.start()

    # esperar timeout
    time.sleep(timeout)

    # mandar parar
    stop_event.set()

    # esperar workers
    for p in processes:
        p.join()

    return best_prime.value