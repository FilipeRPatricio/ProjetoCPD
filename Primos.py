"""
primos.py - Procura do maior número primo em tempo limitado.

Funções implementadas:
    - is_prime(n): verificação de primalidade (fornecida pelo enunciado)
    - find_max_prime_sequential(timeout): versão sequencial
    - find_max_prime_parallel(timeout, workers): versão paralela com multiprocessing
"""

import time
from multiprocessing import Process, Value, Lock, Event


# ---------------------------------------------------------------------------
# Função de primalidade (fornecida pelo enunciado — NÃO ALTERAR)
# ---------------------------------------------------------------------------

def is_prime(n: int) -> bool:
    """
    Verifica se n é um número primo.

    Returns:
        bool: True se n é primo, False caso contrário.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    divisor = 5
    while divisor * divisor <= n:
        if n % divisor == 0 or n % (divisor + 2) == 0:
            return False
        divisor += 6
    return True


# ---------------------------------------------------------------------------
# Versão Sequencial
# ---------------------------------------------------------------------------

def find_max_prime_sequential(timeout: float) -> int:
    """
    Procura o maior número primo possível durante timeout segundos,
    usando uma abordagem sequencial.

    Começa em 2 e percorre os números de forma crescente, mantendo
    o maior primo encontrado até ao limite temporal.

    Args:
        timeout (float): tempo máximo de execução em segundos.

    Returns:
        int: o maior número primo encontrado.
    """
    best = 2
    n = 2
    deadline = time.perf_counter() + timeout

    while time.perf_counter() < deadline:
        if is_prime(n):
            best = n
        n += 1

    return best


# ---------------------------------------------------------------------------
# Execução Paralela
# ---------------------------------------------------------------------------

INTERVAL_SIZE = 10 ** 12  # tamanho de cada intervalo de procura

def _worker(worker_id: int, num_workers: int, best_prime: Value, lock: Lock, stop_event: Event) -> None:
    """
    Processo worker que procura o maior primo em intervalos do espaço de busca.

    Estratégia:
    - Cada worker começa no seu intervalo inicial (definido pelo worker_id).
    - Dentro de cada intervalo, começa pelo fim e desce até encontrar um primo.
      O primeiro primo encontrado a descer é garantidamente o maior do intervalo.
    - Após encontrar esse primo (ou esgotar o intervalo), salta para o próximo
      intervalo não explorado (avança num_workers intervalos).
    - Nunca há sobreposição entre workers — cada um trata intervalos com
      índice worker_id + k * num_workers.

    Args:
        worker_id (int): identificador do worker (0 a num_workers-1).
        num_workers (int): número total de workers.
        best_prime (Value): memória partilhada com o maior primo encontrado.
        lock (Lock): lock para acesso exclusivo a best_prime.
        stop_event (Event): evento que sinaliza paragem coordenada.
    """

    interval_index = worker_id

    while not stop_event.is_set():

        # calcular limites do intervalo atual
        interval_end = (interval_index + 1) * INTERVAL_SIZE
        interval_start = interval_index * INTERVAL_SIZE

        # percorrer do fim para o início do intervalo
        n = interval_end
        while n >= interval_start and not stop_event.is_set():
            if is_prime(n):
                with lock:
                    if n > best_prime.value:
                        best_prime.value = n
                break
            n -= 1

        # saltar para o próximo intervalo deste worker
        interval_index += num_workers


def find_max_prime_parallel(timeout: float, workers: int) -> int:
    """
    Procura o maior número primo possível durante timeout segundos,
    usando múltiplos processos em paralelo.

    Estratégia de divisão do espaço de procura:
    - O espaço é dividido em intervalos de INTERVAL_SIZE números.
    - Cada worker fica responsável pelos intervalos com índice
      worker_id + k * num_workers (sem sobreposição).
    - Dentro de cada intervalo, o worker começa pelo fim e desce,
      encontrando assim o maior primo do intervalo imediatamente.
    - O resultado partilhado é atualizado sempre que um primo maior
      é encontrado, com sincronização via Lock.

    Utiliza processos (multiprocessing) em vez de threads para contornar
    o GIL do Python e obter paralelismo real em tarefas CPU-intensivas.

    Args:
        timeout (float): tempo máximo de execução em segundos.
        workers (int): número de processos paralelos.

    Returns:
        int: o maior número primo encontrado.
    """
    # memória partilhada entre processos
    best_prime = Value('Q', 2)  # 'Q' = unsigned long long (64 bits)
    lock = Lock()
    stop_event = Event()
    processes = []

    # criar e iniciar workers
    for worker_id in range(workers):
        p = Process(
            target=_worker,
            args=(worker_id, workers, best_prime, lock, stop_event)
        )
        processes.append(p)
        p.start()

    # aguardar o timeout
    time.sleep(timeout)

    # sinalizar paragem a todos os workers ao msm tempo
    stop_event.set()

    # esperar que todos os workers acabem
    for p in processes:
        p.join()

    return best_prime.value


if __name__ == "__main__":
    timeout = int(input("Tempo de execução (segundos): "))
    workers = int(input("Número de workers: "))

    t0 = time.perf_counter()
    result = find_max_prime_parallel(timeout, workers)
    elapsed = time.perf_counter() - t0

    print("\nMaior primo encontrado:", result)
    print("Notação científica:    ", f"{result:.6e}")
    print("Número de dígitos:     ", len(str(result)))
    print("Tempo total:           ", round(elapsed, 2), "segundos")

    """
    import os

    print(os.cpu_count())
    """