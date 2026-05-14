import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
from copy import deepcopy
from Game_of_Life import game_of_life_sequential, game_of_life_parallel


class GameOfLifeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Game of Life - Simulador")
        self.root.geometry("900x700")
        
        self.rows = 50
        self.cols = 50
        self.cell_size = 8
        self.grid = [[random.randint(0, 1) for _ in range(self.cols)] for _ in range(self.rows)]
        self.prev = None
        self.gen = 0
        self.running = False
        self.par = False
        self.w = 2
        self.t0 = None
        self.timeout_val = 10
        
        self.setup_ui()
        
    def setup_ui(self):
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.btn_start = ttk.Button(control_frame, text="Iniciar", command=self.start_simulation)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_pause = ttk.Button(control_frame, text="Pausar", command=self.pause_simulation)
        self.btn_pause.pack(side=tk.LEFT, padx=5)
        
        self.btn_reset = ttk.Button(control_frame, text="Reiniciar", command=self.reset_grid)
        self.btn_reset.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(control_frame, text="Velocidade (ms):").pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.IntVar(value=50)
        speed_spin = ttk.Spinbox(control_frame, from_=10, to=1000, textvariable=self.speed_var, width=5)
        speed_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(control_frame, text="Timeout (s):").pack(side=tk.LEFT, padx=5)
        self.timeout_var = tk.IntVar(value=10)
        timeout_spin = ttk.Spinbox(control_frame, from_=1, to=300, textvariable=self.timeout_var, width=4)
        timeout_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.parallel_var = tk.BooleanVar(value=False)
        self.check_parallel = ttk.Checkbutton(control_frame, text="Paralelo", variable=self.parallel_var)
        self.check_parallel.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Workers:").pack(side=tk.LEFT, padx=5)
        self.workers_var = tk.IntVar(value=2)
        workers_spin = ttk.Spinbox(control_frame, from_=1, to=8, textvariable=self.workers_var, width=3)
        workers_spin.pack(side=tk.LEFT, padx=5)
        
        info_frame = ttk.Frame(self.root)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        self.info_label = ttk.Label(info_frame, text="Geração: 0 | Células vivas: 0 | Tempo: 0.0s", font=("Arial", 10))
        self.info_label.pack(side=tk.LEFT)
        
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size,
            bg="white",
            highlightthickness=1
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        result_frame = ttk.LabelFrame(self.root, text="Comparação de Resultados")
        result_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.result_label = ttk.Label(result_frame, text="Inicie a simulação para ver resultados", font=("Arial", 9))
        self.result_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.draw_grid()
        
    def draw_grid(self):
        self.canvas.delete("all")
        
        for row in range(self.rows):
            for col in range(self.cols):
                color = "black" if self.grid[row][col] == 1 else "white"
                
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")
        
        self.update_info()
        
    def update_info(self):
        live = sum(sum(row) for row in self.grid)
        mode = "Paralelo" if self.par else "Sequencial"
        elapsed = 0
        if self.t0:
            elapsed = time.perf_counter() - self.t0
        self.info_label.config(
            text=f"Geração: {self.gen} | Células vivas: {live} | Modo: {mode} | Tempo: {elapsed:.2f}s"
        )
        
    def on_canvas_click(self, event):
        if self.running:
            return
        
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = 1 - self.grid[row][col]
            self.draw_grid()
    
    def is_game_ended(self):
        live = sum(sum(row) for row in self.grid)
        
        if live == 0:
            return True, "população extinta"
        
        if self.prev and self.grid == self.prev:
            return True, "padrão estável"
        
        return False, None
        
    def next_generation(self):
        self.prev = deepcopy(self.grid)
        
        if self.par:
            self.grid = game_of_life_parallel(self.grid, 1, self.w)
        else:
            self.grid = game_of_life_sequential(self.grid, 1)
        
        self.gen += 1
        self.draw_grid()
        
    def start_simulation(self):
        self.running = True
        self.par = self.parallel_var.get()
        self.w = self.workers_var.get()
        self.timeout_val = self.timeout_var.get()
        self.t0 = time.perf_counter()
        self.gen = 0
        self.prev = None
        self.result_label.config(text="Simulação em execução...")
        self.simulate()
        
    def pause_simulation(self):
        self.running = False
        
    def reset_grid(self):
        self.running = False
        self.gen = 0
        self.prev = None
        self.t0 = None
        self.grid = [[random.randint(0, 1) for _ in range(self.cols)] for _ in range(self.rows)]
        self.result_label.config(text="Inicie a simulação para ver resultados")
        self.draw_grid()
        
    def simulate(self):
        if self.running:
            elapsed = time.perf_counter() - self.t0
            
            if elapsed >= self.timeout_val:
                live = sum(sum(row) for row in self.grid)
                
                msg = f"Timeout atingido ({self.timeout_val}s) | "
                msg += f"Gerações: {self.gen} | "
                msg += f"Células vivas: {live} | "
                msg += f"Tempo: {elapsed:.4f}s | "
                msg += f"Modo: {'Paralelo' if self.par else 'Sequencial'}"
                
                self.result_label.config(text=msg)
                self.running = False
                messagebox.showinfo("Fim", f"Tempo limite!\n\n{msg}")
                return
            
            self.next_generation()
            
            ended, reason = self.is_game_ended()
            
            if ended:
                elapsed = time.perf_counter() - self.t0
                live = sum(sum(row) for row in self.grid)
                
                msg = f"Jogo terminado ({reason}) | "
                msg += f"Gerações: {self.gen} | "
                msg += f"Células vivas: {live} | "
                msg += f"Tempo: {elapsed:.4f}s | "
                msg += f"Modo: {'Paralelo' if self.par else 'Sequencial'}"
                
                self.result_label.config(text=msg)
                self.running = False
                messagebox.showinfo("Fim", f"Jogo terminou!\n\n{msg}")
            else:
                self.root.after(self.speed_var.get(), self.simulate)
            

def main():
    root = tk.Tk()
    app = GameOfLifeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
