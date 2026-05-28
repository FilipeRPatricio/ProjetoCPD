import unittest
import time
import sys
from copy import deepcopy

# Importar módulos a testar
from Game_of_Life import (
    count_neighbors,
    apply_rules,
    game_of_life_sequential,
    game_of_life_sequential_timeout,
    game_of_life_parallel,
    game_of_life_parallel_timeout,
)
from Primos import is_prime, find_max_prime_sequential, find_max_prime_parallel


# =============================================================================
# TESTES DO GAME OF LIFE
# =============================================================================

class TestGameOfLifeHelpers(unittest.TestCase):
    """Testes das funções auxiliares do Game of Life."""
    
    def test_count_neighbors_interior_cell_all_alive(self):
        """Célula interior com todos os 8 vizinhos vivos."""
        grid = [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]
        # Célula central (1, 1)
        self.assertEqual(count_neighbors(grid, 1, 1), 8)
    
    def test_count_neighbors_interior_cell_none_alive(self):
        """Célula interior com nenhum vizinho vivo."""
        grid = [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]
        # Célula central (1, 1)
        self.assertEqual(count_neighbors(grid, 1, 1), 0)
    
    def test_count_neighbors_corner_cell(self):
        """Célula no canto tem apenas 3 vizinhos potenciais."""
        grid = [
            [1, 1, 0],
            [1, 0, 0],
            [0, 0, 0],
        ]
        # Célula no canto (0, 0) tem 2 vizinhos vivos
        self.assertEqual(count_neighbors(grid, 0, 0), 2)
    
    def test_count_neighbors_edge_cell(self):
        """Célula na aresta tem menos vizinhos."""
        grid = [
            [1, 1, 1],
            [0, 1, 0],
            [0, 0, 0],
        ]
        # Célula na aresta (0, 1) tem 3 vizinhos vivos: (0,0)=1, (0,2)=1, (1,1)=1
        self.assertEqual(count_neighbors(grid, 0, 1), 3)
    
    def test_apply_rules_underpopulation(self):
        """Célula viva com < 2 vizinhos morre (subpopulação)."""
        grid = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]
        # Célula (1, 1) viva com 1 vizinho → morre
        result = apply_rules(grid, 1, 1, 1)
        self.assertEqual(result, 0)
    
    def test_apply_rules_survival_2_neighbors(self):
        """Célula viva com 2 vizinhos sobrevive."""
        grid = [
            [1, 0, 1],
            [0, 1, 0],
            [0, 0, 0],
        ]
        # Célula (1, 1) viva com 2 vizinhos → sobrevive
        result = apply_rules(grid, 1, 1, 2)
        self.assertEqual(result, 1)
    
    def test_apply_rules_survival_3_neighbors(self):
        """Célula viva com 3 vizinhos sobrevive."""
        grid = [
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]
        # Célula (1, 1) viva com 3 vizinhos → sobrevive
        result = apply_rules(grid, 1, 1, 3)
        self.assertEqual(result, 1)
    
    def test_apply_rules_overpopulation(self):
        """Célula viva com > 3 vizinhos morre (sobrepopulação)."""
        grid = [
            [1, 1, 1],
            [1, 1, 0],
            [0, 0, 0],
        ]
        # Célula (1, 1) viva com 4 vizinhos → morre
        result = apply_rules(grid, 1, 1, 4)
        self.assertEqual(result, 0)
    
    def test_apply_rules_reproduction(self):
        """Célula morta com exatamente 3 vizinhos torna-se viva."""
        grid = [
            [1, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        # Célula (1, 1) morta com 3 vizinhos (futura célula viva)
        result = apply_rules(grid, 1, 1, 3)
        self.assertEqual(result, 1)
    
    def test_apply_rules_dead_cell_few_neighbors(self):
        """Célula morta com < 3 vizinhos permanece morta."""
        grid = [
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        # Célula (1, 1) morta com 1 vizinho → permanece morta
        result = apply_rules(grid, 1, 1, 1)
        self.assertEqual(result, 0)


class TestGameOfLifeSequential(unittest.TestCase):
    """Testes da versão sequencial do Game of Life."""
    
    def test_sequential_zero_generations(self):
        """Simular zero gerações retorna grelha idêntica."""
        grid = [[1, 0], [0, 1]]
        result = game_of_life_sequential(deepcopy(grid), 0)
        self.assertEqual(result, grid)
    
    def test_sequential_one_generation_simple(self):
        """Simular 1 geração com padrão simples."""
        # Um bloco (2x2) sobrevive indefinidamente
        grid = [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        result = game_of_life_sequential(deepcopy(grid), 1)
        # O bloco deve permanecer igual
        expected = [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        self.assertEqual(result, expected)
    
    def test_sequential_multiple_generations(self):
        """Simular múltiplas gerações."""
        grid = [[1, 0], [0, 1]]
        result = game_of_life_sequential(deepcopy(grid), 5)
        # Verifica que resultado é uma lista de listas com mesmas dimensões
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
    
    def test_sequential_does_not_modify_original(self):
        """Função não deve modificar grelha original."""
        grid = [[1, 0], [0, 1]]
        grid_copy = deepcopy(grid)
        _ = game_of_life_sequential(grid, 5)
        self.assertEqual(grid, grid_copy)
    
    def test_sequential_invalid_negative_generations(self):
        """Número negativo de gerações deve lançar ValueError."""
        grid = [[1, 0], [0, 1]]
        with self.assertRaises(ValueError):
            game_of_life_sequential(grid, -1)
    
    def test_sequential_empty_grid(self):
        """Grelha vazia deve lançar ValueError."""
        grid = []
        with self.assertRaises(ValueError):
            game_of_life_sequential(grid, 1)
    
    def test_sequential_single_row_grid(self):
        """Simular com grelha de uma linha."""
        grid = [[1, 1, 1]]
        result = game_of_life_sequential(deepcopy(grid), 1)
        # Verificar que não lança erro e retorna estrutura válida
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 3)
    
    def test_sequential_large_grid(self):
        """Simular com grelha maior."""
        grid = [[i % 2 for i in range(10)] for _ in range(10)]
        result = game_of_life_sequential(deepcopy(grid), 3)
        # Verificar dimensões
        self.assertEqual(len(result), 10)
        self.assertEqual(len(result[0]), 10)
        # Verificar que contém apenas 0 e 1
        for row in result:
            for cell in row:
                self.assertIn(cell, [0, 1])


class TestGameOfLifeSequentialTimeout(unittest.TestCase):
    """Testes da versão sequencial com timeout."""
    
    def test_sequential_timeout_basic(self):
        """Executar com timeout e obter resultado válido."""
        grid = [[1, 0], [0, 1]]
        result_grid, num_gens = game_of_life_sequential_timeout(deepcopy(grid), 1.0)
        
        # Verificar estrutura
        self.assertEqual(len(result_grid), 2)
        self.assertEqual(len(result_grid[0]), 2)
        self.assertIsInstance(num_gens, int)
        self.assertGreaterEqual(num_gens, 0)
    
    def test_sequential_timeout_respects_timeout(self):
        """Validar que respeita o timeout (aproximadamente)."""
        grid = [[1, 0], [0, 1]]
        timeout = 0.1
        
        start = time.perf_counter()
        _, _ = game_of_life_sequential_timeout(deepcopy(grid), timeout)
        elapsed = time.perf_counter() - start
        
        # Deve terminar no tempo especificado (com margem de 50%)
        self.assertLess(elapsed, timeout * 1.5)
    
    def test_sequential_timeout_invalid_timeout(self):
        """Timeout inválido (zero ou negativo) deve lançar ValueError."""
        grid = [[1, 0], [0, 1]]
        
        with self.assertRaises(ValueError):
            game_of_life_sequential_timeout(grid, 0)
        
        with self.assertRaises(ValueError):
            game_of_life_sequential_timeout(grid, -1.0)
    
    def test_sequential_timeout_empty_grid(self):
        """Grelha vazia deve lançar ValueError."""
        grid = []
        with self.assertRaises(ValueError):
            game_of_life_sequential_timeout(grid, 1.0)


class TestGameOfLifeParallel(unittest.TestCase):
    """Testes da versão paralela do Game of Life."""
    
    def test_parallel_zero_generations(self):
        """Simular zero gerações retorna grelha idêntica."""
        grid = [[1, 0], [0, 1]]
        result = game_of_life_parallel(deepcopy(grid), 0, 2)
        self.assertEqual(result, grid)
    
    def test_parallel_matches_sequential(self):
        """Resultado paralelo deve ser idêntico ao sequencial."""
        grid = [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        
        seq_result = game_of_life_sequential(deepcopy(grid), 3)
        par_result = game_of_life_parallel(deepcopy(grid), 3, 2)
        
        self.assertEqual(seq_result, par_result)
    
    def test_parallel_with_different_worker_counts(self):
        """Validar com diferentes números de workers."""
        grid = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
        
        for workers in [1, 2, 3, 4]:
            result = game_of_life_parallel(deepcopy(grid), 2, workers)
            # Verificar estrutura
            self.assertEqual(len(result), 3)
            self.assertEqual(len(result[0]), 3)
    
    def test_parallel_invalid_negative_generations(self):
        """Gerações negativas devem lançar ValueError."""
        grid = [[1, 0], [0, 1]]
        with self.assertRaises(ValueError):
            game_of_life_parallel(grid, -1, 2)
    
    def test_parallel_invalid_zero_workers(self):
        """Zero workers deve lançar ValueError."""
        grid = [[1, 0], [0, 1]]
        with self.assertRaises(ValueError):
            game_of_life_parallel(grid, 1, 0)
    
    def test_parallel_workers_more_than_rows(self):
        """Número de workers > linhas deve funcionar (limitado internamente)."""
        grid = [[1, 0], [0, 1]]  # 2 linhas
        result = game_of_life_parallel(deepcopy(grid), 2, 10)  # 10 workers
        # Deve funcionar e retornar resultado válido
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)


class TestGameOfLifeParallelTimeout(unittest.TestCase):
    """Testes da versão paralela com timeout."""
    
    def test_parallel_timeout_basic(self):
        """Executar com timeout e obter resultado válido."""
        grid = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
        result_grid, num_gens = game_of_life_parallel_timeout(
            deepcopy(grid), 1.0, 2
        )
        
        # Verificar estrutura
        self.assertEqual(len(result_grid), 3)
        self.assertEqual(len(result_grid[0]), 3)
        self.assertIsInstance(num_gens, int)
        self.assertGreaterEqual(num_gens, 0)
    
    def test_parallel_timeout_respects_timeout(self):
        """Validar que respeita o timeout (aproximadamente)."""
        grid = [[1, 0], [0, 1]]
        timeout = 0.1
        
        start = time.perf_counter()
        _, _ = game_of_life_parallel_timeout(deepcopy(grid), timeout, 2)
        elapsed = time.perf_counter() - start
        
        # Deve terminar no tempo especificado (com margem de 50%)
        self.assertLess(elapsed, timeout * 1.5)
    
    def test_parallel_timeout_invalid_timeout(self):
        """Timeout inválido deve lançar ValueError."""
        grid = [[1, 0], [0, 1]]
        
        with self.assertRaises(ValueError):
            game_of_life_parallel_timeout(grid, 0, 2)
        
        with self.assertRaises(ValueError):
            game_of_life_parallel_timeout(grid, -1.0, 2)
    
    def test_parallel_timeout_invalid_workers(self):
        """Workers inválidos devem lançar ValueError."""
        grid = [[1, 0], [0, 1]]
        
        with self.assertRaises(ValueError):
            game_of_life_parallel_timeout(grid, 1.0, 0)


# =============================================================================
# TESTES DOS NÚMEROS PRIMOS
# =============================================================================

class TestIsPrime(unittest.TestCase):
    """Testes da função is_prime()."""
    
    def test_is_prime_negative_numbers(self):
        """Números negativos não são primos."""
        self.assertFalse(is_prime(-1))
        self.assertFalse(is_prime(-2))
        self.assertFalse(is_prime(-10))
    
    def test_is_prime_zero_and_one(self):
        """Zero e um não são primos."""
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(1))
    
    def test_is_prime_small_primes(self):
        """Primeiros primos devem ser identificados."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        for p in primes:
            self.assertTrue(is_prime(p), f"{p} deveria ser primo")
    
    def test_is_prime_small_composites(self):
        """Números compostos não devem ser identificados como primos."""
        composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20]
        for c in composites:
            self.assertFalse(is_prime(c), f"{c} não deveria ser primo")
    
    def test_is_prime_large_prime(self):
        """Teste com números primos grandes."""
        large_primes = [97, 101, 103, 107, 109, 113, 127, 131, 137, 139]
        for p in large_primes:
            self.assertTrue(is_prime(p), f"{p} deveria ser primo")
    
    def test_is_prime_large_composite(self):
        """Teste com números compostos grandes."""
        large_composites = [100, 121, 143, 169, 187, 209, 221, 247, 253, 289]
        for c in large_composites:
            self.assertFalse(is_prime(c), f"{c} não deveria ser primo")
    
    def test_is_prime_mersenne_primes(self):
        """Testes com primos de Mersenne conhecidos."""
        mersenne_primes = [3, 7, 31, 127]
        for p in mersenne_primes:
            self.assertTrue(is_prime(p), f"Primo de Mersenne {p} deveria ser primo")


class TestFindMaxPrimeSequential(unittest.TestCase):
    """Testes da procura sequencial de primos."""
    
    def test_sequential_timeout_short(self):
        """Teste com timeout muito curto."""
        result = find_max_prime_sequential(0.01)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 2)
        # Deve encontrar pelo menos 2
        self.assertTrue(is_prime(result))
    
    def test_sequential_timeout_medium(self):
        """Teste com timeout médio."""
        result = find_max_prime_sequential(0.5)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 2)
        self.assertTrue(is_prime(result))
    
    def test_sequential_increasing_timeout(self):
        """Timeout maior deve encontrar primos maiores ou iguais."""
        result1 = find_max_prime_sequential(0.05)
        result2 = find_max_prime_sequential(0.2)
        
        # result2 (timeout maior) deve ser >= result1
        self.assertGreaterEqual(result2, result1)
    
    def test_sequential_result_is_prime(self):
        """Resultado deve ser sempre um número primo."""
        result = find_max_prime_sequential(0.1)
        self.assertTrue(is_prime(result))


class TestFindMaxPrimeParallel(unittest.TestCase):
    """Testes da procura paralela de primos."""
    
    def test_parallel_timeout_short(self):
        """Teste paralelo com timeout curto."""
        result = find_max_prime_parallel(0.01, 2)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 2)
        self.assertTrue(is_prime(result))
    
    def test_parallel_single_worker(self):
        """Teste paralelo com um único worker (equivalente a sequencial)."""
        result = find_max_prime_parallel(0.1, 1)
        self.assertIsInstance(result, int)
        self.assertTrue(is_prime(result))
    
    def test_parallel_multiple_workers(self):
        """Teste com múltiplos workers."""
        for workers in [1, 2, 4]:
            result = find_max_prime_parallel(0.1, workers)
            self.assertIsInstance(result, int)
            self.assertTrue(is_prime(result))
    
    def test_parallel_result_is_prime(self):
        """Resultado paralelo deve ser sempre primo."""
        result = find_max_prime_parallel(0.1, 2)
        self.assertTrue(is_prime(result))
    
    def test_parallel_increasing_timeout(self):
        """Timeout maior deve encontrar primos maiores ou iguais."""
        result1 = find_max_prime_parallel(0.05, 2)
        result2 = find_max_prime_parallel(0.15, 2)
        
        # result2 (timeout maior) deve ser >= result1
        self.assertGreaterEqual(result2, result1)


# =============================================================================
# SUITE DE TESTES E EXECUÇÃO
# =============================================================================

def run_tests():
    """Executa todos os testes com formatação de saída."""
    # Criar loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar testes
    suite.addTests(loader.loadTestsFromTestCase(TestGameOfLifeHelpers))
    suite.addTests(loader.loadTestsFromTestCase(TestGameOfLifeSequential))
    suite.addTests(loader.loadTestsFromTestCase(TestGameOfLifeSequentialTimeout))
    suite.addTests(loader.loadTestsFromTestCase(TestGameOfLifeParallel))
    suite.addTests(loader.loadTestsFromTestCase(TestGameOfLifeParallelTimeout))
    suite.addTests(loader.loadTestsFromTestCase(TestIsPrime))
    suite.addTests(loader.loadTestsFromTestCase(TestFindMaxPrimeSequential))
    suite.addTests(loader.loadTestsFromTestCase(TestFindMaxPrimeParallel))
    
    # Executar com verbosidade
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retornar status
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
