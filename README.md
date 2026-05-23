# README - Justificação dos Algoritmos

## 📋 Índice
1. [Números Primos](#números-primos)
2. [Game of Life](#game-of-life)
3. [Comparação de Abordagens](#comparação-de-abordagens)

---

## 🔢 Números Primos

### Problema
Encontrar o **maior número primo possível dentro de um tempo limite (timeout)**, explorando paralelamente o espaço de procura.

### Solução 1: Verificação de Primalidade - `is_prime(n)`

#### Algoritmo: Wheel Factorization Base 6

```python
def is_prime(n: int) -> bool:
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
        divisor += 6  # Testar apenas 6k±1
    return True
```

#### Justificativa

**Complexidade: O(√n)**
- Testar divisibilidade até √n é suficiente
- Se n não tem divisor até √n, então é primo

**Wheel Factorization Base 6**
- Todos os primos > 3 têm forma 6k±1
- Elimina 2 (pares) e 3 (múltiplos de 3) antes do loop
- Loop testa apenas 6k±1: 5, 7, 11, 13, 17, 19, 23, 25, ...
- Reduz iterações em 66% (apenas 4 de 6 números testados)

**Comparação com alternativas:**

| Método | Iterações (n=1M) | Tempo (relativo) | Observações |
|--------|------------------|-----------------|------------|
| Brute force | 1.000.000 | 1.0x | Ineficiente |
| Testar até √n | 1.000 | 0.001x | Aceitável |
| Wheel base 6 | 333 | 0.0003x | **Escolhido ✓** |
| Miller-Rabin | Probabilístico | 0.0002x | Biblioteca externa ✗ |

**Escolha:** Wheel factorization base 6
- Máxima eficiência com código simples
- Sem dependências externas
- Ganho significativo em números grandes

---

### Solução 2: Exploração Sequencial - `find_max_prime_sequential(timeout)`

#### Algoritmo

```
Inicializar:
  - n = 10^12 + 1 (número grande para encontrar primos significativos)
  - best_prime = 2
  - start_time = agora()

Enquanto (agora() - start_time < timeout):
  Se is_prime(n):
    best_prime = n
  n += 2  (incrementar de 2 em 2, apenas números ímpares)

Retornar best_prime
```

#### Justificativa

**Espaço de Procura**
- Começar em 10^12 + 1 garante primos grandes
- Incrementar de 2 em 2 (apenas números ímpares)
- Números pares nunca são primos (exceto 2)

**Resposta Temporal**
- Tempo total = timeout (máximo permitido)
- Melhor resultado progressivo (qualquer primo encontrado é válido)

**Comparação com alternativas:**

| Estratégia | Tempo | Resultado | Observações |
|-----------|-------|-----------|------------|
| Fixo (N gerações) | Variável | Garantido | Tempo imprevisível |
| **Timeout** | Fixo | Best-effort | **Escolhido ✓** |
| Aleatório | Variável | Imprevisível | Pode perder bons candidatos |

**Escolha:** Abordagem sequencial com timeout
- Simplicidade (baseline para comparação com paralelo)
- Determinismo temporal
- Sem overhead de sincronização

---

### Solução 3: Exploração Paralela - `find_max_prime_parallel(timeout, workers)`

#### Algoritmo

```
Inicializar:
  - start_number = 10^15
  - jump = 100_000_000
  - best_prime = Value(2)  [Memória partilhada]
  - lock = Lock()
  - stop_event = Event()

Para cada worker_id de 0 a workers-1:
  Criar Process(_worker_find_max_prime, args=(...))
  Iniciar process.start()

[Processo principal]
  Aguardar time.sleep(timeout)
  Sinalizar stop_event.set()
  Aguardar process.join() para todos

Retornar best_prime.value
```

#### Justificativa

**Divisão de Espaço de Procura**

Cada worker testa números diferentes sem sobreposição:

```
Worker 0: 10^15,      10^15 + 4*100M,  10^15 + 8*100M, ...
Worker 1: 10^15 + 1*J, 10^15 + 5*100M,  10^15 + 9*100M, ...
Worker 2: 10^15 + 2*J, 10^15 + 6*100M, 10^15 + 10*100M, ...
Worker 3: 10^15 + 3*J, 10^15 + 7*100M, 10^15 + 11*100M, ...

Padrão: n = start + worker_id*J + k*(workers*J)
```

**Vantagens:**
- Sem sobreposição de espaço
- Distribuição equilibrada
- Cobertura maior em paralelo

**Sincronização - Escolha: PROCESSOS (não threads)**

| Aspecto | Threads | Processos | Escolha |
|---------|---------|-----------|---------|
| **GIL (Global Lock)** | Bloqueia em CPU-bound ✗ | Sem GIL ✓ | **Processos** |
| Paralelismo Real | Simulado | Real | **Processos** |
| is_prime() Performance | ~1x | ~3.8x (4 cores) | **Processos** |
| Overhead | Baixo | Moderado | Compensado |
| Comunicação Inter-processos | Fácil (sem GIL) | Value+Lock | **Processos** |

**Razão: Python GIL**
```
Threads em Python:
  - Um único thread executa por vez (GIL)
  - Para problemas CPU-bound: sem ganho
  - Performance: ~1x (ou pior)

Processos:
  - Cada processo: interpreter Python próprio
  - Sem GIL: verdadeiro paralelismo
  - Performance: ~3.8x com 4 cores
  - Ideal para CPU-bound como is_prime()
```

**Comunicação de Resultado**
```python
best_prime = Value('Q', 2)  # Inteiro 64-bit partilhado
lock = Lock()               # Protege actualizações

# No worker:
with lock:
    if current_number > best_prime.value:
        best_prime.value = current_number
```

**Sincronização de Paragem**
```python
stop_event = Event()

# Em cada worker:
while not stop_event.is_set():
    # processar...

# No principal:
time.sleep(timeout)
stop_event.set()          # Sinaliza paragem
for p in processes:
    p.join()              # Aguarda término
```

**Comparação de Estratégias Paralelas:**

| Estratégia | Overhead | Escalabilidade | Sincronização | Escolha |
|-----------|----------|-----------------|---------------|---------|
| Manual (Process) | Médio | Boa | Lock+Event | **Escolhido ✓** |
| Pool | Baixo | Boa | Implícita | Menos controlo |
| Threads | Baixo | Nenhuma (GIL) | Simples | Inadequado |
| asyncio | Baixo | Boa (I/O) | Simples | Inadequado (CPU) |

**Escolha:** Processos com sincronização manual
- Verdadeiro paralelismo em CPU-bound
- Controlo fino sobre distribuição
- Comunicação segura com Value+Lock

---

## 🎮 Game of Life

### Problema
Simular a evolução de um autómato celular (Game of Life) com **N gerações ou timeout**, com versão paralela.

### Solução 1: Verificação de Vizinhança - `count_neighbors(grid, row, col)`

#### Algoritmo

```python
def count_neighbors(grid, row, col):
    # Examinar 8 vizinhos (Moore neighborhood)
    for delta_row in [-1, 0, 1]:
        for delta_col in [-1, 0, 1]:
            if delta_row == 0 and delta_col == 0:
                continue
            nr, nc = row + delta_row, col + delta_col
            if 0 <= nr < rows and 0 <= nc < cols:
                count += grid[nr][nc]
    return count
```

#### Justificativa

**Moore Neighborhood (8 vizinhos)**
- Vizinhança padrão de Conway
- Células adjacentes: horizontal, vertical, diagonal

**Fronteiras Não-Cíclicas**
- Validação `0 <= nr < rows and 0 <= nc < cols`
- Células nas fronteiras têm menos vizinhos
- Conforme especificação: "grelha não é cíclica"

**Complexidade: O(1) por célula**
- 8 vizinhos máximo
- Constante independente de N

---

### Solução 2: Aplicação de Regras - `apply_rules(grid, row, col, neighbors)`

#### Regras de Conway

```
Célula Viva (1):
  - < 2 vizinhos → Morre (subpopulação)
  - 2-3 vizinhos → Vive
  - > 3 vizinhos → Morre (sobrepopulação)

Célula Morta (0):
  - == 3 vizinhos → Torna-se viva (reprodução)
  - Caso contrário → Permanece morta
```

#### Justificativa

**Simplicidade + Complexidade**
- Regras simples (locais)
- Comportamento complexo (global)

**Sincronismo de Gerações**
- Todas as células evoluem simultaneamente
- Baseado em estado anterior (não atualizado in-place)

---

### Solução 3: Exploração Sequencial - `game_of_life_sequential(grid, generations)`

#### Algoritmo

```
Para cada geração de 1 a N:
  Criar grelha vazia (next_grid)
  Para cada célula (row, col):
    neighbors = count_neighbors(grid, row, col)
    next_grid[row][col] = apply_rules(grid, row, col, neighbors)
  Actualizar: grid = next_grid

Retornar grid
```

#### Justificativa

**Estrutura**
- Simples e direta (baseline)
- Fácil de validar correção
- Sem overhead de sincronização

**Complexidade por Geração: O(rows × cols)**
- Testar cada célula uma vez
- Total N gerações: O(N × rows × cols)

**Comparação com alternativas:**

| Estratégia | Estrutura | Complexidade | Vantagem |
|-----------|-----------|--------------|----------|
| Sequencial | 2 loops aninhados | O(N×R×C) | Simples ✓ |
| In-place | 1 passe | Ineficiente | Errado |
| Quadtree | Comprimida | Complexa | Overhead |

**Escolha:** Sequencial direta
- Correção garantida
- Benchmark para paralelo
- Sem complexidades desnecessárias

---

### Solução 4: Exploração Paralela - `game_of_life_parallel(grid, generations, workers)`

#### Algoritmo

```
Para cada geração de 1 a N:
  Dividir grelha em regiões (contíguas por linhas)
  Para cada region (start_row, end_row):
    Criar tarefa: compute_region(grid, start_row, end_row)
  
  Executar Pool.map(compute_region, regions)
  [Sincronização implícita - aguarda todos]
  
  Concatenar regiões → grid = next_grid

Retornar grid
```

#### Justificativa

**Divisão: POR LINHAS (não quadrantes)**

```
Opção 1: Quadrantes (2x2)
  ┌─────────────┬─────────────┐
  │   Worker 0  │   Worker 1  │
  ├─────────────┼─────────────┤
  │   Worker 2  │   Worker 3  │
  └─────────────┴─────────────┘
  ✗ Muitas fronteiras horizontais
  ✗ Regiões quadradas (não necessário)

Opção 2: Linhas (ESCOLHIDO)
  ┌─────────────────────────────┐
  │ Worker 0: rows 0-10         │
  ├─────────────────────────────┤
  │ Worker 1: rows 10-20        │
  ├─────────────────────────────┤
  │ Worker 2: rows 20-30        │
  ├─────────────────────────────┤
  │ Worker 3: rows 30-40        │
  └─────────────────────────────┘
  ✓ Fronteiras minimizadas
  ✓ Distribuição equilibrada
  ✓ Fácil de implementar
```

**Por que divisão por linhas é melhor:**
```
Fronteiras entre regiões:
  - Linhas: 2 linhas de fronteira (top/bottom)
  - Quadrantes: 4 linhas (4 workers)
  
Eficiência de Cache:
  - Linhas: Contíguas na memória
  - Quadrantes: Dispersas

Distribuição:
  - Linhas: Equilibrada (rows // workers)
  - Quadrantes: Pode ser desigual
```

**Distribuição Equilibrada**

```python
rows_per_worker = rows // workers
remaining_rows = rows % workers

# Primeiros `remaining_rows` workers recebem +1 linha
# Exemplo: 50 linhas, 4 workers
#   Worker 0: rows 0-13   (14 linhas)
#   Worker 1: rows 13-26  (13 linhas)
#   Worker 2: rows 26-39  (13 linhas)
#   Worker 3: rows 39-50  (11 linhas)
```

**Sincronização: Pool vs Manual**

| Aspecto | Manual | Pool | Escolha |
|---------|--------|------|---------|
| Simplicidade | Complexo | Simples | **Pool ✓** |
| Sincronização | Manual join() | Implícita | **Pool ✓** |
| Escalabilidade | Boa | Boa | **Pool ✓** |
| Overhead | Médio | Baixo | **Pool ✓** |

```python
# Escolhido: Pool com .map()
with mp.Pool(processes=workers) as pool:
    processed = pool.map(compute_region, regions)
    # Sincronização implícita (bloqueia até todos)

# Razão: 
# - map() sincroniza automaticamente
# - Sem risk de deadlock
# - Código mais limpo
```

**Correção Garantida**

```python
# Validação: resultado paralelo == resultado sequencial
match_sequential = (grid_sequential == grid_parallel)

# Garantido porque:
# 1. count_neighbors: acessa apenas células existentes
# 2. Regiões não se sobrepõem
# 3. Sincronização completa entre gerações
# 4. Cada célula processada exatamente uma vez
```

**Comparação com alternativas:**

| Estratégia | Paralelismo | Sincronização | Complexidade | Correção |
|-----------|------------|---------------|------------|----------|
| Sequencial | Nenhum | N/A | Simples | ✓ |
| **Pool com map()** | N workers | Implícita | Média | ✓ |
| Manual Process | N workers | Manual | Complexa | ⚠️ |
| Threads | Simulado (GIL) | Manual | Complexa | ✗ |

**Escolha:** Pool com .map()
- Simplicidade máxima
- Sincronização automática
- Ganho real de performance

---

## 🔄 Comparação de Abordagens

### Números Primos vs Game of Life

| Aspecto | Números Primos | Game of Life |
|---------|---------------|----|
| **Natureza** | CPU-bound (cálculo) | CPU-bound (cálculo) |
| **Comunicação** | Mínima (best_prime) | Nenhuma (apenas sincronização) |
| **Paralelização** | **Processos** (GIL importante) | **Pool** (conveniência) |
| **Sincronização** | Lock + Event | Implícita (map) |
| **Divisão** | Espaço de procura | Espaço de dados (grelha) |
| **Complexidade** | Simples (1D) | Moderada (2D) |

### Por que Escolhas Diferentes?

**Números Primos: Processos com Sincronização Manual**
- Comunicação simples (um valor)
- Controlo fino necessário (distribuição de espaço)
- is_prime() muito intensiva → GIL crítico
- Overhead inicial compensado

**Game of Life: Pool com map()**
- Comunicação nenhuma (apenas sincronização)
- Distribuição padrão (linhas)
- Melhor relação simplicidade/performance
- Sincronização implícita suficiente

---

## 📈 Performance Esperada

### Números Primos (timeout=5s)

```
1 Worker (sequencial): ~1.0x
4 Processos:           ~3.5x - 3.8x
8 Processos:           ~7.0x - 7.5x (num_cores dependent)
```

**Ganho Real:** Processadores multi-core explorados completamente

### Game of Life (50×50 grid, 100 gerações)

```
1 Worker:    ~50ms
4 Workers:   ~20ms  (2.5x)
8 Workers:   ~15ms  (3.3x)
```

**Ganho:** Limitado por sincronização (map) entre gerações

---

## 🎯 Conclusão

### Números Primos
✓ **Wheel factorization base 6** para is_prime
✓ **Sequencial simples** como baseline
✓ **Processos + manual sync** para paralelo (GIL é crítico)
✓ **Divisão de espaço** sem sobreposição

### Game of Life
✓ **Moore neighborhood** (8 vizinhos)
✓ **Regras de Conway** tradicionais
✓ **Divisão por linhas** (distribuição equilibrada)
✓ **Pool com map()** para paralelismo (simplicidade)

Ambas as soluções balanceiam **correção**, **performance** e **simplicidade**.
