import multiprocessing as mp
from copy import deepcopy
import time


def count_neighbors(grid, row, col):
    count = 0
    rows = len(grid)
    cols = len(grid[0])
    
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                count += grid[nr][nc]
    
    return count


def apply_rules(grid, row, col, neighbors):
    cell = grid[row][col]
    
    if cell == 1:
        if neighbors < 2 or neighbors > 3:
            return 0
        return 1
    
    if neighbors == 3:
        return 1
    
    return 0


def game_of_life_sequential(grid, generations):
    g = deepcopy(grid)
    r, c = len(g), len(g[0])
    
    for _ in range(generations):
        next_g = [[0 for _ in range(c)] for _ in range(r)]
        
        for i in range(r):
            for j in range(c):
                neighbors = count_neighbors(g, i, j)
                next_g[i][j] = apply_rules(g, i, j, neighbors)
        
        g = next_g
    
    return g


def game_of_life_sequential_timeout(grid, timeout):
    g = deepcopy(grid)
    r, c = len(g), len(g[0])
    n = 0
    
    start = time.perf_counter()
    
    while time.perf_counter() - start < timeout:
        next_g = [[0 for _ in range(c)] for _ in range(r)]
        
        for i in range(r):
            for j in range(c):
                neighbors = count_neighbors(g, i, j)
                next_g[i][j] = apply_rules(g, i, j, neighbors)
        
        g = next_g
        n += 1
    
    return g, n


def compute_region(args):
    grid, sr, er = args
    rows = len(grid)
    cols = len(grid[0])
    
    region = [[0 for _ in range(cols)] for _ in range(er - sr)]
    
    for row in range(sr, er):
        for col in range(cols):
            neighbors = count_neighbors(grid, row, col)
            region[row - sr][col] = apply_rules(grid, row, col, neighbors)
    
    return region


def game_of_life_parallel(grid, generations, workers):
    g = deepcopy(grid)
    rows = len(g)
    cols = len(g[0])
    
    w = min(workers, rows)
    
    for _ in range(generations):
        regions = []
        rpw = rows // w
        rem = rows % w
        
        sr = 0
        for i in range(w):
            if i < rem:
                er = sr + rpw + 1
            else:
                er = sr + rpw
            
            regions.append((g, sr, er))
            sr = er
        
        with mp.Pool(processes=w) as pool:
            processed = pool.map(compute_region, regions)
        
        next_g = []
        for region in processed:
            next_g.extend(region)
        
        g = next_g
    
    return g


def game_of_life_parallel_timeout(grid, timeout, workers):
    g = deepcopy(grid)
    rows = len(g)
    cols = len(g[0])
    n = 0
    
    w = min(workers, rows)
    start = time.perf_counter()
    
    while time.perf_counter() - start < timeout:
        regions = []
        rpw = rows // w
        rem = rows % w
        
        sr = 0
        for i in range(w):
            if i < rem:
                er = sr + rpw + 1
            else:
                er = sr + rpw
            
            regions.append((g, sr, er))
            sr = er
        
        with mp.Pool(processes=w) as pool:
            processed = pool.map(compute_region, regions)
        
        next_g = []
        for region in processed:
            next_g.extend(region)
        
        g = next_g
        n += 1
    
    return g, n


def compare_game_of_life(grid, generations, max_workers):
    results = {
        'generations': generations,
        'grid_size': (len(grid), len(grid[0])),
        'sequential': {},
        'parallel': {}
    }
    
    start = time.perf_counter()
    grid_seq = game_of_life_sequential(grid, generations)
    time_seq = time.perf_counter() - start
    
    results['sequential']['time'] = time_seq
    results['sequential']['grid'] = grid_seq
    
    results['parallel']['tests'] = []
    
    for num_workers in range(1, max_workers + 1):
        start = time.perf_counter()
        grid_par = game_of_life_parallel(grid, generations, num_workers)
        time_par = time.perf_counter() - start
        
        speedup = time_seq / time_par if time_par > 0 else 0
        
        test_result = {
            'workers': num_workers,
            'time': time_par,
            'speedup': speedup,
            'grid': grid_par,
            'match_sequential': grid_seq == grid_par
        }
        
        results['parallel']['tests'].append(test_result)
    
    return results


