"""
GoL_Client_GUI.py - Cliente RPC com Interface Gráfica para Game of Life

Interface tkinter integrada com cliente RPC para executar o Game of Life
no servidor e visualizar os resultados em tempo real.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import json
import random
import threading


# ---------------------------------------------------------------------------
# Funções RPC
# ---------------------------------------------------------------------------

def send_msg(sock: socket.socket, payload: dict) -> None:
    """Serializa e envia mensagem JSON pelo socket."""
    data = json.dumps(payload) + '\n'
    sock.sendall(data.encode("utf-8"))


def recv_msg(sock: socket.socket) -> dict:
    """Recebe e desserializa mensagem JSON do socket."""
    buffer = b""
    while not buffer.endswith(b"\n"):
        chunk = sock.recv(1024)
        if not chunk:
            raise ConnectionError("Ligação fechada pelo servidor")
        buffer += chunk
    return json.loads(buffer.decode("utf-8").strip())


def rpc_call(sock: socket.socket, method: str, params: dict) -> object:
    """Envia pedido RPC ao servidor e devolve o resultado."""
    request = {"method": method, "params": params}
    send_msg(sock, request)
    response = recv_msg(sock)
    if "error" in response:
        raise RuntimeError(f"Erro do servidor: {response['error']}")
    return response["result"]


# ---------------------------------------------------------------------------
# Interface Gráfica do Game of Life
# ---------------------------------------------------------------------------

class GameOfLifeGUI:
    def __init__(self, root, sock: socket.socket):
        self.root = root
        self.sock = sock
        
        self.root.title("Game of Life - Cliente RPC")
        self.root.geometry("1100x850")
        
        # Parâmetros do jogo
        self.rows = 50
        self.cols = 50
        self.cell_size = 10
        self.grid = [[random.randint(0, 1) for _ in range(self.cols)] for _ in range(self.rows)]
        
        self.simulating = False
        self.result_grid = None
        self.generations_executed = 0
        
        self.setup_ui()
        self.update_canvas()
        
    def setup_ui(self):
        """Configura a interface do utilizador."""
        
        # ===== Painel de Controlo (topo) =====
        control_frame = ttk.LabelFrame(self.root, text="Controlo da Simulação", padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Linha 1: Botões principais
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.btn_sequential = ttk.Button(
            button_frame, text="▶ Executar (Sequencial)", 
            command=self.run_sequential
        )
        self.btn_sequential.pack(side=tk.LEFT, padx=5)
        
        self.btn_parallel = ttk.Button(
            button_frame, text="▶ Executar (Paralelo)", 
            command=self.run_parallel
        )
        self.btn_parallel.pack(side=tk.LEFT, padx=5)
        
        self.btn_reset = ttk.Button(
            button_frame, text="🔄 Reiniciar Grid", 
            command=self.reset_grid
        )
        self.btn_reset.pack(side=tk.LEFT, padx=5)
        
        self.btn_random = ttk.Button(
            button_frame, text="🎲 Aleatório", 
            command=self.random_grid
        )
        self.btn_random.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = ttk.Button(
            button_frame, text="⊘ Limpar", 
            command=self.clear_grid
        )
        self.btn_clear.pack(side=tk.LEFT, padx=5)
        
        # Linha 2: Parâmetros
        params_frame = ttk.Frame(control_frame)
        params_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        ttk.Label(params_frame, text="Timeout (s):").pack(side=tk.LEFT, padx=5)
        self.timeout_var = tk.IntVar(value=5)
        timeout_spin = ttk.Spinbox(
            params_frame, from_=1, to=60, textvariable=self.timeout_var, width=5
        )
        timeout_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(params_frame, text="Workers:").pack(side=tk.LEFT, padx=15)
        self.workers_var = tk.IntVar(value=4)
        workers_spin = ttk.Spinbox(
            params_frame, from_=1, to=16, textvariable=self.workers_var, width=5
        )
        workers_spin.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(
            params_frame, text="Pronto", foreground="green", font=("Arial", 9, "bold")
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # ===== Painel Principal (esquerda + direita) =====
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ===== Canvas do Grid (esquerda) =====
        canvas_frame = ttk.LabelFrame(main_frame, text="Grid Inicial", padding=5)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        info_frame = ttk.Frame(canvas_frame)
        info_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.canvas_info = ttk.Label(info_frame, text="Células vivas: 0 | Clique para alternar células")
        self.canvas_info.pack(side=tk.LEFT)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size,
            bg="white",
            highlightthickness=2,
            highlightbackground="black"
        )
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # ===== Painel de Resultados (direita) =====
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding=10)
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Abas: Info e Grid Final
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba 1: Informações
        info_tab = ttk.Frame(self.notebook)
        self.notebook.add(info_tab, text="Informações")
        
        self.result_text = scrolledtext.ScrolledText(
            info_tab, width=35, height=20, font=("Courier", 9)
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.clear_results()
        
        # Aba 2: Grid Final
        grid_tab = ttk.Frame(self.notebook)
        self.notebook.add(grid_tab, text="Grid Final")
        
        self.result_canvas = tk.Canvas(
            grid_tab,
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size,
            bg="white",
            highlightthickness=2,
            highlightbackground="black"
        )
        self.result_canvas.pack(pady=10, padx=10)
        
    def update_canvas(self):
        """Desenha o grid inicial no canvas."""
        self.canvas.delete("all")
        
        # Desenhar células
        for row in range(self.rows):
            for col in range(self.cols):
                color = "black" if self.grid[row][col] == 1 else "white"
                
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")
        
        # Atualizar informação
        live = sum(sum(row) for row in self.grid)
        self.canvas_info.config(text=f"Células vivas: {live}")
        
    def draw_result_grid(self):
        """Desenha o grid final no canvas de resultados."""
        if self.result_grid is None:
            return
        
        self.result_canvas.delete("all")
        
        for row in range(len(self.result_grid)):
            for col in range(len(self.result_grid[0])):
                color = "black" if self.result_grid[row][col] == 1 else "white"
                
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                self.result_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")
    
    def on_canvas_click(self, event):
        """Manipula cliques no canvas para alternar células."""
        if self.simulating:
            return
        
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = 1 - self.grid[row][col]
            self.update_canvas()
    
    def reset_grid(self):
        """Reinicia o grid com configuração aleatória."""
        self.grid = [[random.randint(0, 1) for _ in range(self.cols)] for _ in range(self.rows)]
        self.update_canvas()
    
    def random_grid(self):
        """Preenche o grid com valores aleatórios (30% vivos)."""
        self.grid = [[random.choices([0, 1], weights=[70, 30])[0] for _ in range(self.cols)] for _ in range(self.rows)]
        self.update_canvas()
    
    def clear_grid(self):
        """Limpa o grid (todas as células mortas)."""
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.update_canvas()
    
    def clear_results(self):
        """Limpa a área de resultados."""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Aguardando simulação...\n")
        self.result_text.config(state=tk.DISABLED)
    
    def run_sequential(self):
        """Executa simulação sequencial no servidor."""
        thread = threading.Thread(target=self._run_sequential_thread)
        thread.daemon = True
        thread.start()
    
    def _run_sequential_thread(self):
        """Thread para execução sequencial (não bloqueia a UI)."""
        try:
            self.simulating = True
            self.status_label.config(text="A executar (sequencial)...", foreground="orange")
            self.root.update()
            
            timeout = self.timeout_var.get()
            
            # Fazer chamada RPC
            result = rpc_call(
                self.sock, 
                "game_of_life_sequential", 
                {
                    "grid": self.grid,
                    "timeout": timeout
                }
            )
            
            self.result_grid, self.generations_executed = result
            self.display_results("Sequencial", timeout)
            self.draw_result_grid()
            
            self.status_label.config(text="Concluído", foreground="green")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na simulação:\n{str(e)}")
            self.status_label.config(text="Erro", foreground="red")
        finally:
            self.simulating = False
    
    def run_parallel(self):
        """Executa simulação paralela no servidor."""
        thread = threading.Thread(target=self._run_parallel_thread)
        thread.daemon = True
        thread.start()
    
    def _run_parallel_thread(self):
        """Thread para execução paralela (não bloqueia a UI)."""
        try:
            self.simulating = True
            self.status_label.config(text="A executar (paralelo)...", foreground="orange")
            self.root.update()
            
            timeout = self.timeout_var.get()
            workers = self.workers_var.get()
            
            # Fazer chamada RPC
            result = rpc_call(
                self.sock, 
                "game_of_life_parallel", 
                {
                    "grid": self.grid,
                    "timeout": timeout,
                    "workers": workers
                }
            )
            
            self.result_grid, self.generations_executed = result
            self.display_results("Paralelo", timeout, workers)
            self.draw_result_grid()
            
            self.status_label.config(text="Concluído", foreground="green")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na simulação:\n{str(e)}")
            self.status_label.config(text="Erro", foreground="red")
        finally:
            self.simulating = False
    
    def display_results(self, mode: str, timeout: int, workers: int = None):
        """Apresenta os resultados da simulação."""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        # Calcular estatísticas
        initial_live = sum(sum(row) for row in self.grid)
        final_live = sum(sum(row) for row in self.result_grid)
        initial_size = len(self.grid) * len(self.grid[0])
        final_size = len(self.result_grid) * len(self.result_grid[0])
        
        # Formatação da saída
        output = f"""
╔════════════════════════════════════════╗
║      RESULTADOS DA SIMULAÇÃO            ║
╚════════════════════════════════════════╝

  Modo de Execução: {mode}
  
  ┌─ Parâmetros ──────────────────────┐
  │  Timeout: {timeout}s
"""
        if workers:
            output += f"  │  Workers: {workers}\n"
        
        output += f"""  └───────────────────────────────────┘
  
  ┌─ Resultados ───────────────────────┐
  │  Gerações Executadas: {self.generations_executed}
  │
  │  Grid Inicial ({len(self.grid)}x{len(self.grid[0])}):
  │    • Células Vivas: {initial_live}
  │    • Percentagem: {(initial_live/initial_size*100):.1f}%
  │
  │  Grid Final ({len(self.result_grid)}x{len(self.result_grid[0])}):
  │    • Células Vivas: {final_live}
  │    • Percentagem: {(final_live/final_size*100):.1f}%
  │    • Variação: {final_live - initial_live:+d}
  └───────────────────────────────────┘
"""
        
        self.result_text.insert(tk.END, output)
        self.result_text.config(state=tk.DISABLED)
