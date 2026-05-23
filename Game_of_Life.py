"""
Game of Life - Implementação de Conway's Game of Life

Módulo que implementa o autómato celular de John Conway com suporte
para execução sequencial e paralela.

Regras de evolução:
- Uma célula viva com < 2 vizinhos morre (subpopulação)
- Uma célula viva com 2-3 vizinhos mantém-se viva
- Uma célula viva com > 3 vizinhos morre (sobrepopulação)
- Uma célula morta com exatamente 3 vizinhos torna-se viva (reprodução)

Vizinhança: 8 células adjacentes (Moore neighborhood)
Grelha: não cíclica (células nas fronteiras têm menos vizinhos)
"""

import multiprocessing as mp
from copy import deepcopy
import time


# ---------------------------------------------------------------------------
# Funções Auxiliares
# ---------------------------------------------------------------------------

def count_neighbors(grid, row, col):
    """
    Conta o número de vizinhos vivos de uma célula.
    
    Examina as 8 células adjacentes (vizinhança de Moore) e conta
    quantas estão vivas (valor 1). A grelha não é cíclica, logo células
    nas fronteiras têm menos vizinhos.
    
    Args:
        grid (list[list[int]]): Grelha de células (2D).
        row (int): Linha da célula.
        col (int): Coluna da célula.
    
    Returns:
        int: Número de vizinhos vivos (0-8).
    """
    num_neighbors = 0
    total_rows = len(grid)
    total_cols = len(grid[0])
    
    # Examinar 8 vizinhos (todos os offsets de -1 a +1, excluindo (0,0))
    for delta_row in [-1, 0, 1]:
        for delta_col in [-1, 0, 1]:
            # Ignorar a própria célula
            if delta_row == 0 and delta_col == 0:
                continue
            
            neighbor_row = row + delta_row
            neighbor_col = col + delta_col
            
            # Validar limites (grelha não cíclica)
            if 0 <= neighbor_row < total_rows and 0 <= neighbor_col < total_cols:
                num_neighbors += grid[neighbor_row][neighbor_col]
    
    return num_neighbors


def apply_rules(grid, row, col, num_neighbors):
    """
    Aplica as regras de Conway para determinar o próximo estado de uma célula.
    
    Regras aplicadas:
    1. Célula viva com < 2 vizinhos → morre (subpopulação)
    2. Célula viva com 2-3 vizinhos → permanece viva
    3. Célula viva com > 3 vizinhos → morre (sobrepopulação)
    4. Célula morta com exatamente 3 vizinhos → torna-se viva (reprodução)
    
    Args:
        grid (list[list[int]]): Grelha atual (usada apenas para consulta).
        row (int): Linha da célula.
        col (int): Coluna da célula.
        num_neighbors (int): Número de vizinhos vivos.
    
    Returns:
        int: Novo estado da célula (0 = morta, 1 = viva).
    """
    current_state = grid[row][col]
    
    # Célula viva
    if current_state == 1:
        # Morre se tem menos de 2 ou mais de 3 vizinhos
        if num_neighbors < 2 or num_neighbors > 3:
            return 0
        # Mantém-se viva
        return 1
    
    # Célula morta: torna-se viva com exatamente 3 vizinhos
    if num_neighbors == 3:
        return 1
    
    # Mantém-se morta
    return 0


# ---------------------------------------------------------------------------
# Execução Sequencial
# ---------------------------------------------------------------------------

def game_of_life_sequential(grid, generations):
    """
    Simula a evolução da grelha durante um número fixo de gerações,
    utilizando uma abordagem sequencial.
    
    O algoritmo cria uma nova grelha em cada geração, aplicando as regras
    de Conway a cada célula com base no estado da geração anterior.
    
    Args:
        grid (list[list[int]]): Grelha inicial (2D, valores 0 ou 1).
        generations (int): Número de gerações a simular (>= 0).
    
    Returns:
        list[list[int]]: Grelha após as gerações simuladas.
    
    Raises:
        ValueError: Se generations < 0.
    
    Exemplo:
        >>> grid = [[1, 0], [0, 1]]
        >>> resultado = game_of_life_sequential(grid, 5)
    """
    # Validar parâmetros
    if generations < 0:
        raise ValueError("O número de gerações não pode ser negativo")
    if not grid or not grid[0]:
        raise ValueError("A grelha não pode estar vazia")
    
    # Cópia profunda para não modificar a grelha original
    current_grid = deepcopy(grid)
    num_rows = len(current_grid)
    num_cols = len(current_grid[0])
    
    # Executar cada geração
    for _ in range(generations):
        # Inicializar grelha para a próxima geração
        next_grid = [[0 for _ in range(num_cols)] for _ in range(num_rows)]
        
        # Aplicar regras a cada célula
        for row in range(num_rows):
            for col in range(num_cols):
                num_neighbors = count_neighbors(current_grid, row, col)
                next_grid[row][col] = apply_rules(current_grid, row, col, num_neighbors)
        
        # Actualizar grelha para próxima iteração
        current_grid = next_grid
    
    return current_grid


def game_of_life_sequential_timeout(grid, timeout):
    """
    Simula a evolução da grelha durante um tempo limite (timeout),
    utilizando uma abordagem sequencial.
    
    O algoritmo executa quantas gerações conseguir no tempo especificado,
    retornando o estado final e o número de gerações completadas.
    
    Args:
        grid (list[list[int]]): Grelha inicial (2D, valores 0 ou 1).
        timeout (float): Tempo máximo de execução em segundos (> 0).
    
    Returns:
        tuple: (grelha_final, número_de_gerações_completadas)
            - grelha_final (list[list[int]]): Estado da grelha após timeout.
            - gerações (int): Número de gerações completadas.
    
    Raises:
        ValueError: Se timeout <= 0.
    
    Exemplo:
        >>> grid = [[1, 0], [0, 1]]
        >>> grid_final, gens = game_of_life_sequential_timeout(grid, 5.0)
    """
    # Validar parâmetros
    if timeout <= 0:
        raise ValueError("O timeout deve ser positivo")
    if not grid or not grid[0]:
        raise ValueError("A grelha não pode estar vazia")
    
    # Cópia profunda para não modificar a grelha original
    current_grid = deepcopy(grid)
    num_rows = len(current_grid)
    num_cols = len(current_grid[0])
    num_generations = 0
    
    # Registar tempo de início
    start_time = time.perf_counter()
    
    # Executar gerações até exceder timeout
    while time.perf_counter() - start_time < timeout:
        # Inicializar grelha para a próxima geração
        next_grid = [[0 for _ in range(num_cols)] for _ in range(num_rows)]
        
        # Aplicar regras a cada célula
        for row in range(num_rows):
            for col in range(num_cols):
                num_neighbors = count_neighbors(current_grid, row, col)
                next_grid[row][col] = apply_rules(current_grid, row, col, num_neighbors)
        
        # Actualizar grelha para próxima iteração
        current_grid = next_grid
        num_generations += 1
    
    return current_grid, num_generations


# ---------------------------------------------------------------------------
# Execução Paralela
# ---------------------------------------------------------------------------

def _divide_grid_into_regions(num_rows, num_workers):
    """
    Divide a grelha em regiões contíguas para distribuição a workers.
    
    Distribui equilibradamente as linhas da grelha entre workers.
    Se o número de linhas não é divisível pelo número de workers,
    as primeiras regiões recebem uma linha adicional.
    
    Args:
        num_rows (int): Número total de linhas da grelha.
        num_workers (int): Número de workers (regiões desejadas).
    
    Returns:
        list[tuple]: Lista de tuplos (start_row, end_row) para cada região.
    
    Exemplo:
        >>> _divide_grid_into_regions(10, 3)
        [(0, 4), (4, 8), (8, 10)]
    """
    regions = []
    effective_workers = min(num_workers, num_rows)
    rows_per_worker = num_rows // effective_workers
    remaining_rows = num_rows % effective_workers
    
    start_row = 0
    for worker_id in range(effective_workers):
        # Distribui o resto das linhas aos primeiros workers
        if worker_id < remaining_rows:
            end_row = start_row + rows_per_worker + 1
        else:
            end_row = start_row + rows_per_worker
        
        regions.append((start_row, end_row))
        start_row = end_row
    
    return regions


def _compute_region(args):
    """
    Calcula a próxima geração para uma região (slice) da grelha.
    
    Função executada por cada worker no pool. Recebe uma região contígua
    da grelha e aplica as regras de Conway a todas as células nessa região.
    
    Args:
        args (tuple): Tuplo contendo:
            - grid (list[list[int]]): Grelha atual completa.
            - start_row (int): Primeira linha da região.
            - end_row (int): Última linha (exclusiva) da região.
    
    Returns:
        list[list[int]]: Nova grelha para a região especificada.
    """
    grid, start_row, end_row = args
    total_rows = len(grid)
    total_cols = len(grid[0])
    
    # Inicializar região para a próxima geração
    region = [[0 for _ in range(total_cols)] for _ in range(end_row - start_row)]
    
    # Aplicar regras a cada célula da região
    for row in range(start_row, end_row):
        for col in range(total_cols):
            num_neighbors = count_neighbors(grid, row, col)
            # Armazenar no índice relativo da região
            region[row - start_row][col] = apply_rules(
                grid, row, col, num_neighbors
            )
    
    return region


def game_of_life_parallel(grid, generations, num_workers):
    """
    Simula a evolução da grelha durante um número fixo de gerações,
    recorrendo a múltiplos workers em paralelo.
    
    Algoritmo:
    1. Divide a grelha em regiões contíguas (por linhas)
    2. Cria um Pool de workers
    3. Em cada geração, distribui as regiões aos workers
    4. Sincroniza todos os workers antes da próxima geração
    5. Reconstrói a grelha completa a partir das regiões processadas
    
    Garantias:
    - Resultados idênticos à versão sequencial
    - Cada worker processa uma ou mais linhas contíguas
    - Gestão correta de fronteiras entre regiões (via count_neighbors)
    - Sincronização implícita via pool.map()
    
    Args:
        grid (list[list[int]]): Grelha inicial (2D, valores 0 ou 1).
        generations (int): Número de gerações a simular (>= 0).
        num_workers (int): Número de workers paralelos (> 0).
    
    Returns:
        list[list[int]]: Grelha após as gerações simuladas.
    
    Raises:
        ValueError: Se generations < 0 ou num_workers <= 0.
    
    Exemplo:
        >>> grid = [[1, 0], [0, 1]]
        >>> resultado = game_of_life_parallel(grid, 5, workers=2)
    """
    # Validar parâmetros
    if generations < 0:
        raise ValueError("O número de gerações não pode ser negativo")
    if num_workers <= 0:
        raise ValueError("O número de workers deve ser positivo")
    if not grid or not grid[0]:
        raise ValueError("A grelha não pode estar vazia")
    
    # Cópia profunda para não modificar a grelha original
    current_grid = deepcopy(grid)
    total_rows = len(current_grid)
    total_cols = len(current_grid[0])
    
    # Limitar workers ao número de linhas
    effective_workers = min(num_workers, total_rows)
    
    # Executar cada geração
    for _ in range(generations):
        # Dividir grelha em regiões para distribuição
        regions = _divide_grid_into_regions(total_rows, effective_workers)
        
        # Preparar argumentos para cada worker
        # (grelha completa + start_row + end_row)
        worker_args = [
            (current_grid, start_row, end_row)
            for start_row, end_row in regions
        ]
        
        # Processar regiões em paralelo e sincronizar
        with mp.Pool(processes=effective_workers) as pool:
            processed_regions = pool.map(_compute_region, worker_args)
        
        # Reconstruir grelha completa concatenando regiões
        next_grid = []
        for region in processed_regions:
            next_grid.extend(region)
        
        # Actualizar grelha para próxima iteração
        current_grid = next_grid
    
    return current_grid


def game_of_life_parallel_timeout(grid, timeout, num_workers):
    """
    Simula a evolução da grelha durante um tempo limite (timeout),
    recorrendo a múltiplos workers em paralelo.
    
    Similar a game_of_life_parallel(), mas executa quantas gerações
    conseguir no tempo especificado.
    
    Args:
        grid (list[list[int]]): Grelha inicial (2D, valores 0 ou 1).
        timeout (float): Tempo máximo de execução em segundos (> 0).
        num_workers (int): Número de workers paralelos (> 0).
    
    Returns:
        tuple: (grelha_final, número_de_gerações_completadas)
            - grelha_final (list[list[int]]): Estado da grelha após timeout.
            - gerações (int): Número de gerações completadas.
    
    Raises:
        ValueError: Se timeout <= 0 ou num_workers <= 0.
    
    Exemplo:
        >>> grid = [[1, 0], [0, 1]]
        >>> grid_final, gens = game_of_life_parallel_timeout(grid, 5.0, 2)
    """
    # Validar parâmetros
    if timeout <= 0:
        raise ValueError("O timeout deve ser positivo")
    if num_workers <= 0:
        raise ValueError("O número de workers deve ser positivo")
    if not grid or not grid[0]:
        raise ValueError("A grelha não pode estar vazia")
    
    # Cópia profunda para não modificar a grelha original
    current_grid = deepcopy(grid)
    total_rows = len(current_grid)
    total_cols = len(current_grid[0])
    num_generations = 0
    
    # Limitar workers ao número de linhas
    effective_workers = min(num_workers, total_rows)
    
    # Registar tempo de início
    start_time = time.perf_counter()
    
    # Executar gerações até exceder timeout
    while time.perf_counter() - start_time < timeout:
        # Dividir grelha em regiões para distribuição
        regions = _divide_grid_into_regions(total_rows, effective_workers)
        
        # Preparar argumentos para cada worker
        worker_args = [
            (current_grid, start_row, end_row)
            for start_row, end_row in regions
        ]
        
        # Processar regiões em paralelo e sincronizar
        with mp.Pool(processes=effective_workers) as pool:
            processed_regions = pool.map(_compute_region, worker_args)
        
        # Reconstruir grelha completa concatenando regiões
        next_grid = []
        for region in processed_regions:
            next_grid.extend(region)
        
        # Actualizar grelha para próxima iteração
        current_grid = next_grid
        num_generations += 1
    
    return current_grid, num_generations


# ---------------------------------------------------------------------------
# Benchmarking
# ---------------------------------------------------------------------------

def compare_game_of_life(grid, generations, max_workers):
    """
    Compara o desempenho da versão sequencial contra paralelas.
    
    Executa a simulação com diferentes números de workers e calcula
    speedup (aceleração) relativa à versão sequencial. Também verifica
    se os resultados são idênticos.
    
    Args:
        grid (list[list[int]]): Grelha inicial (2D, valores 0 ou 1).
        generations (int): Número de gerações a simular.
        max_workers (int): Número máximo de workers para testar.
    
    Returns:
        dict: Dicionário contendo:
            - 'generations': int, número de gerações
            - 'grid_size': tuple, (linhas, colunas)
            - 'sequential': {
                'time': float, tempo de execução sequencial,
                'grid': list, estado final da grelha
              }
            - 'parallel': {
                'tests': list de dicts, cada um contendo:
                    - 'workers': int, número de workers
                    - 'time': float, tempo de execução
                    - 'speedup': float, tempo_seq / tempo_par
                    - 'grid': list, estado final
                    - 'match_sequential': bool, idêntico ao sequencial?
              }
    
    Exemplo:
        >>> grid = [[1, 0], [0, 1]]
        >>> resultados = compare_game_of_life(grid, 10, 4)
    """
    # Validar parâmetros
    if generations <= 0:
        raise ValueError("Gerações deve ser > 0 para comparação")
    if max_workers <= 0:
        raise ValueError("max_workers deve ser > 0")
    
    results = {
        'generations': generations,
        'grid_size': (len(grid), len(grid[0])),
        'sequential': {},
        'parallel': {}
    }
    
    # Executar versão sequencial
    start_time = time.perf_counter()
    grid_sequential = game_of_life_sequential(grid, generations)
    time_sequential = time.perf_counter() - start_time
    
    results['sequential']['time'] = time_sequential
    results['sequential']['grid'] = grid_sequential
    
    # Testar diferentes números de workers
    results['parallel']['tests'] = []
    
    for num_workers in range(1, max_workers + 1):
        start_time = time.perf_counter()
        grid_parallel = game_of_life_parallel(grid, generations, num_workers)
        time_parallel = time.perf_counter() - start_time
        
        # Calcular speedup
        speedup = time_sequential / time_parallel if time_parallel > 0 else 0
        
        # Verificar se resultados são idênticos
        results_match = (grid_sequential == grid_parallel)
        
        test_result = {
            'workers': num_workers,
            'time': time_parallel,
            'speedup': speedup,
            'grid': grid_parallel,
            'match_sequential': results_match
        }
        
        results['parallel']['tests'].append(test_result)
    
    return results
