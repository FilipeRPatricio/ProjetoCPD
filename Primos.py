"""
Primos.py - Cálculo de números primos com suporte sequencial e paralelo.

Módulo que implementa a verificação de primalidade e a busca de números primos
máximos com execução sequencial e paralela dentro de um tempo limite (timeout).

Funções Expostas:
- is_prime(n): verifica se um número é primo
- find_max_prime_sequential(timeout): busca sequencial de maior primo
- find_max_prime_parallel(timeout, workers): busca paralela de maior primo

Algoritmos:
- Verificação: Teste de divisibilidade otimizado (wheel factorization base 6)
- Sequencial: Iteração simples sobre números ímpares
- Paralelo: Múltiplos processos com sincronização via Lock e Event
"""

import time
from multiprocessing import Process, Value, Lock, Event


# ---------------------------------------------------------------------------
# Verificação de Primalidade
# ---------------------------------------------------------------------------

def is_prime(n: int) -> bool:
    """
    Verifica se um número é primo usando testes de divisibilidade otimizados.
    
    Algoritmo:
    1. Casos especiais: n < 2 (não primo), n ∈ {2,3} (primo)
    2. Eliminar pares e múltiplos de 3
    3. Testar divisores da forma 6k±1 até √n (wheel factorization)
    
    Complexidade: O(√n)
    
    Args:
        n (int): Número a verificar.
    
    Returns:
        bool: True se n é primo, False caso contrário.
    
    Exemplo:
        >>> is_prime(7)
        True
        >>> is_prime(10)
        False
    """
    # Números menores que 2 não são primos
    if n < 2:
        return False
    
    # 2 e 3 são primos
    if n in (2, 3):
        return True
    
    # Eliminar pares e múltiplos de 3
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    # Testar divisores da forma 6k±1 até √n
    # Todos os primos > 3 são da forma 6k±1
    divisor = 5
    while divisor * divisor <= n:
        if n % divisor == 0 or n % (divisor + 2) == 0:
            return False
        divisor += 6
    
    return True


# ---------------------------------------------------------------------------
# Execução Sequencial
# ---------------------------------------------------------------------------

def find_max_prime_sequential(timeout: float) -> int:
    """
    Procura o maior número primo possível durante um tempo limite,
    usando um algoritmo sequencial.
    
    Algoritmo:
    1. Começar em n = 10^12 + 1 (número grande)
    2. Incrementar n de 2 em 2 (testar apenas números ímpares)
    3. Verificar cada n com is_prime()
    4. Manter o maior primo encontrado
    5. Parar quando timeout é excedido
    
    Complexidade: O(timeout * √n) onde n é o número testado
    
    Args:
        timeout (float): Tempo máximo de execução em segundos (> 0).
    
    Returns:
        int: O maior número primo encontrado no tempo disponível.
    
    Raises:
        ValueError: Se timeout <= 0.
    
    Exemplo:
        >>> primo = find_max_prime_sequential(5.0)
        >>> print(primo)  # Maior primo encontrado em 5 segundos
    """
    # Validar parâmetro
    if timeout <= 0:
        raise ValueError("O timeout deve ser positivo")
    
    # Registar tempo de início
    start_time = time.time()
    
    # Iniciar busca em número grande para encontrar primos maiores
    current_number = 10**12 + 1
    best_prime = 2
    
    # Executar busca até exceder timeout
    while time.time() - start_time < timeout:
        # Testar primalidade do número atual
        if is_prime(current_number):
            best_prime = current_number
        
        # Incrementar de 2 em 2 (testar apenas números ímpares)
        current_number += 2
    
    return best_prime


# ---------------------------------------------------------------------------
# Execução Paralela
# ---------------------------------------------------------------------------

def _worker_find_max_prime(worker_id: int, num_workers: int, 
                           start_number: int, jump: int, 
                           best_prime: Value, lock: Lock, 
                           stop_event: Event) -> None:
    """
    Worker paralelo que procura números primos numa região do espaço de busca.
    
    Cada worker começa numa posição diferente e incrementa de num_workers*jump
    em num_workers*jump, explorando diferentes regiões do espaço em paralelo.
    
    Sincronização:
    - Lock: garante que actualizações de best_prime são atómicas
    - Event: sinaliza quando a busca deve parar (timeout excedido)
    
    Args:
        worker_id (int): ID único do worker (0 até num_workers-1).
        num_workers (int): Número total de workers.
        start_number (int): Número inicial de busca (base).
        jump (int): Tamanho do salto entre iterações.
        best_prime (Value): Variável partilhada (maior primo encontrado).
        lock (Lock): Lock para sincronização de acesso a best_prime.
        stop_event (Event): Evento para sinalizar paragem.
    """
    # Calcular posição inicial deste worker
    current_number = start_number + worker_id * jump
    
    # Garantir que começamos com número ímpar
    if current_number % 2 == 0:
        current_number += 1
    
    # Executar busca até receber sinal de paragem
    while not stop_event.is_set():
        # Testar primalidade do número atual
        if is_prime(current_number):
            # Actualizar melhor primo de forma atómica
            with lock:
                # Verificar novamente após adquirir lock
                if current_number > best_prime.value:
                    best_prime.value = current_number
        
        # Saltar para próximo número (distribuição entre workers)
        # Cada worker avança de num_workers*jump
        current_number += num_workers * jump


def find_max_prime_parallel(timeout: float, workers: int) -> int:
    """
    Procura o maior número primo possível durante um tempo limite,
    usando múltiplos processos em paralelo.
    
    Algoritmo:
    1. Criar N workers (processos)
    2. Cada worker começa em posição diferente (worker_id * jump)
    3. Cada worker incrementa de N*jump (não sobreposição)
    4. Workers actualizam valor partilhado (best_prime) com Lock
    5. Timer principal aguarda timeout
    6. Sinal Event para parar todos os workers
    7. Sincronizar e recolher resultado
    
    Distribuição de Trabalho:
    - Workers distribuem o espaço de busca equitativamente
    - Sem conflitos (cada worker explora região diferente)
    - Actualização sincronizada de melhor primo via Lock
    
    Sincronização:
    - Value('Q', 2): Inteiro de 64-bit partilhado
    - Lock: Protege actualizações de best_prime
    - Event: Sinaliza paragem coordenada
    - join(): Aguarda término de todos os processes
    
    Args:
        timeout (float): Tempo máximo de execução em segundos (> 0).
        workers (int): Número de processos paralelos (> 0).
    
    Returns:
        int: O maior número primo encontrado no tempo disponível.
    
    Raises:
        ValueError: Se timeout <= 0 ou workers <= 0.
    
    Exemplo:
        >>> primo = find_max_prime_parallel(5.0, workers=4)
        >>> print(primo)  # Maior primo encontrado em 5 segundos com 4 workers
    """
    # Validar parâmetros
    if timeout <= 0:
        raise ValueError("O timeout deve ser positivo")
    if workers <= 0:
        raise ValueError("Número de workers deve ser positivo")
    
    # Configuração de busca
    start_number = 10**15  # Começar em número muito grande
    jump = 100_000_000     # Salto grande entre números testados
    
    # Criar estruturas de sincronização partilhadas
    # Value('Q', 2): Inteiro 64-bit inicializado a 2 (menor primo)
    best_prime = Value('Q', 2)
    lock = Lock()
    stop_event = Event()
    processes = []
    
    # Criar e iniciar workers
    for worker_id in range(workers):
        # Criar processo para executar _worker_find_max_prime
        process = Process(
            target=_worker_find_max_prime,
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
        processes.append(process)
        process.start()
    
    # Aguardar timeout no processo principal
    time.sleep(timeout)
    
    # Sinalizar a todos os workers para parar
    stop_event.set()
    
    # Aguardar término de todos os workers
    for process in processes:
        process.join()
    
    # Retornar o melhor primo encontrado
    return best_prime.value