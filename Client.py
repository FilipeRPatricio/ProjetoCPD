
# cliente.py - Cliente interativo para o servidor RPC.

import socket
import json

# configuração tem que cuincidir com o servidor
HOST = '127.0.0.1'
PORT = 9000

# comunicação

def send_msg(sock:socket.socket, payload:dict) -> None:
    """
    Serializa `payload` como JSON e envia pelo socket, terminado com '\\n'.

    Parâmetros:
        sock (socket.socket): socket de destino.
        payload (dict): dicionário a enviar.
    """

    data = json.dumps(payload) + '\n'
    sock.sendall(data.encode("utf-8"))

def recv_msg(sock:socket.socket) -> dict:
    """
       Recebe dados do socket até encontrar '\\n' e desserializa o JSON.

       Parâmetros:
           sock (socket.socket): socket de origem.

       Retorna:
           dict: mensagem desserializada.

       Lança:
           ConnectionError: se a ligação for encerrada inesperadamente.
           ValueError: se o JSON for inválido.
       """
    buffer = b""
    while not buffer.endswith(b"\n"):
        chunk = sock.recv(1024)
        if not chunk:
            raise ConnectionError("LLigação fechada pelo servidor")
        buffer += chunk
    return json.loads(buffer.decode("utf-8").strip())

#Chamada RPC

def rpc_call(sock: socket.socket, method: str, params:dict) -> object:
    """
        Envia um pedido RPC ao servidor e devolve o resultado.

        Parâmetros:
            sock (socket.socket): socket ligado ao servidor.
            method (str): nome do método a invocar.
            params (dict): parâmetros da operação.

        Retorna:
            object: valor de 'result' da resposta.

        Lança:
            RuntimeError: se a resposta contiver 'error'.
            ConnectionError / ValueError: em caso de falha de comunicação.
        """
    request = {"method": method, "params": params}
    send_msg(sock, request)
    response = recv_msg(sock)
    if "error" in response:
        raise RuntimeError(f"Erro do servidor: {response['error']}")
    return response["result"]

# ---------------------------------------------------------------------------
# Funções de menu (uma por operação)
# ---------------------------------------------------------------------------

def menu_list_methods(sock: socket.socket) -> None:
    """Invoca list_methods() e apresenta os métodos disponíveis no servidor."""
    methods = rpc_call(sock, "list_methods", {})
    print("\n── Métodos disponíveis no servidor ──")
    for m in methods:
        params_str = ", ".join(
            f"{p['name']}: {p['type']}" for p in m["params"]
        ) or "(sem parâmetros)"
        print(f"  • {m['name']}({params_str})")
        print(f"    {m['description']}")
    print()


def menu_is_prime(sock: socket.socket) -> None:
    """Recolhe n e invoca is_prime(n) no servidor."""
    try:
        n = int(input("  Introduza o número a testar: "))
    except ValueError:
        print("  [!] Valor inválido. Introduza um número inteiro.")
        return

    result = rpc_call(sock, "is_prime", {"n": n})
    estado = "PRIMO ✓" if result else "NÃO É PRIMO ✗"
    print(f"\n  Resultado: {n} → {estado}\n")


def menu_find_max_prime_sequential(sock: socket.socket) -> None:
    """Recolhe timeout e invoca find_max_prime_sequential(timeout) no servidor."""
    try:
        timeout = int(input("  Tempo limite (segundos): "))
        if timeout <= 0:
            raise ValueError
    except ValueError:
        print("  [!] Introduza um número inteiro positivo.")
        return

    print(f"  A procurar (sequencial) durante {timeout}s... (aguarde)")
    result = rpc_call(sock, "find_max_prime_sequential", {"timeout": timeout})

    print(f"\n  Maior primo encontrado : {result}")
    print(f"  Notação científica     : {result:.6e}")
    print(f"  Número de dígitos      : {len(str(result))}\n")


def menu_find_max_prime_parallel(sock: socket.socket) -> None:
    """Recolhe timeout e workers, invoca find_max_prime_parallel(timeout, workers) no servidor."""
    try:
        timeout = int(input("  Tempo limite (segundos): "))
        workers = int(input("  Número de workers: "))
        if timeout <= 0 or workers <= 0:
            raise ValueError
    except ValueError:
        print("  [!] Introduza números inteiros positivos.")
        return

    print(f"  A procurar (paralelo com {workers} workers) durante {timeout}s... (aguarde)")
    result = rpc_call(sock, "find_max_prime_parallel", {"timeout": timeout, "workers": workers})

    print(f"\n  Maior primo encontrado : {result}")
    print(f"  Notação científica     : {result:.6e}")
    print(f"  Número de dígitos      : {len(str(result))}\n")


def menu_game_of_life_sequential(sock: socket.socket) -> None:
    """Executa simulação sequencial do Game of Life com timeout."""
    try:
        rows = int(input("  Linhas do grid (50): "))
        cols = int(input("  Colunas do grid (50): "))
        timeout = int(input("  Tempo limite (segundos): "))
        
        if rows <= 0 or cols <= 0 or timeout <= 0:
            print("  [!] Valores devem ser positivos.")
            return
        
        # gerar grid aleatório
        import random
        grid = [[random.randint(0, 1) for _ in range(cols)] for _ in range(rows)]
        
        print(f"  A simular ({rows}x{cols}) durante {timeout}s... (aguarde)")
        result = rpc_call(sock, "game_of_life_sequential", {
            "grid": grid,
            "timeout": timeout
        })
        
        final_grid, generations = result
        print(f"\n  Simulação sequencial concluída")
        print(f"  Gerações executadas: {generations}")
        print(f"  Tempo limite: {timeout}s\n")
        
    except ValueError:
        print("  [!] Entrada inválida. Introduza números inteiros.")
    except RuntimeError as e:
        print(f"  [!] {e}")


def menu_game_of_life_parallel(sock: socket.socket) -> None:
    """Executa simulação paralela do Game of Life com timeout."""
    try:
        rows = int(input("  Linhas do grid (50): "))
        cols = int(input("  Colunas do grid (50): "))
        timeout = int(input("  Tempo limite (segundos): "))
        workers = int(input("  Número de workers (4): "))
        
        if rows <= 0 or cols <= 0 or timeout <= 0 or workers <= 0:
            print("  [!] Valores devem ser positivos.")
            return
        
        # gerar grid aleatório
        import random
        grid = [[random.randint(0, 1) for _ in range(cols)] for _ in range(rows)]
        
        print(f"  A simular ({rows}x{cols}) com {workers} workers durante {timeout}s... (aguarde)")
        result = rpc_call(sock, "game_of_life_parallel", {
            "grid": grid,
            "timeout": timeout,
            "workers": workers
        })
        
        final_grid, generations = result
        print(f"\n  Simulação paralela concluída")
        print(f"  Workers: {workers}")
        print(f"  Gerações executadas: {generations}")
        print(f"  Tempo limite: {timeout}s\n")
        
    except ValueError:
        print("  [!] Entrada inválida. Introduza números inteiros.")
    except RuntimeError as e:
        print(f"  [!] {e}")


OPCOES = {
    "1": ("Listar métodos disponíveis",                               menu_list_methods),
    "2": ("Verificar se número é primo",                              menu_is_prime),
    "3": ("Encontrar maior primo - Sequencial",         menu_find_max_prime_sequential),
    "4": ("Encontrar maior primo - Paralelo",           menu_find_max_prime_parallel),
    "5": ("Game of Life - Simulação sequencial",        menu_game_of_life_sequential),
    "6": ("Game of Life - Simulação paralela",          menu_game_of_life_parallel),
    "0": ("Sair", None),
}

def print_menu():
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║    Cliente RPC — Números Primos + Game of Life            ║")
    print("╠════════════════════════════════════════════════════════════╣")
    for key, (desc, _) in OPCOES.items():
        print(f"║  [{key}] {desc:<50}║")
    print("╚════════════════════════════════════════════════════════════╝")

def run_client(host=HOST, port=PORT):
    print(f"\nA ligar ao servidor {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print("Ligação estabelecida.\n")
    except ConnectionRefusedError:
        print(f"[!] Não foi possível ligar a {host}:{port}. O servidor está ativo?")
        return

    try:
        while True:
            print_menu()
            opcao = input("\nOpção: ").strip()
            if opcao == "0":
                print("Até logo!")
                break
            elif opcao in OPCOES:
                _, func = OPCOES[opcao]
                try:
                    func(sock)
                except RuntimeError as e:
                    print(f"\n  [!] {e}\n")
                except (ConnectionError, ValueError) as e:
                    print(f"\n  [!] Erro de comunicação: {e}")
                    break
            else:
                print("  [!] Opção inválida.")
    finally:
        sock.close()

if __name__ == "__main__":
    run_client()