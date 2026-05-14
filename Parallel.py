from multiprocessing import Process, Value, Lock, Event
import time
from PrimeFormula import is_prime

def worker(best_prime,next_start,block_size,lock,stop_event):

    while not stop_event.is_set():

        #pedir prox intervalo
        with lock:
            start = next_start.value
            next_start.value += block_size

        end = start + block_size

        # garantir numero impar
        if start %2 == 0:
            start += 1

        #explorar intervalo
        for n in range(start, end, 2):
            if stop_event.is_set():
                return

            if is_prime(n):
                with lock:
                    if n > best_prime.value:
                        best_prime.value = n


def find_max_prime_parallel(timeout, workers):

    start_number = 10**15
    block_size = 1000000
    best_prime = Value('Q', 2)
    next_start = Value('Q', start_number)
    lock = Lock()
    stop_event = Event()
    processes = []


    # criar processos
    for _ in range(workers):

        p = Process(
            target=worker,
            args=(
                best_prime,
                next_start,
                block_size,
                lock,
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