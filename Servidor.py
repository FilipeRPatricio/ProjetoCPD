"""
servidor.py - Servidor RPC sobre sockets TCP.

Disponibiliza remotamente as funções de primos e Game of Life através de um protocolo
request-response com mensagens JSON.

Protocolo:
  Pedido:           {"method": "nome", "params": {"p1": v1, ...}}
  Resposta sucesso: {"result": valor}
  Resposta erro:    {"error": "mensagem"}

Cada mensagem é terminada com '\n' para delimitar fronteiras no stream TCP.
"""

import socket
import threading
import json
import inspect

from Primos import find_max_prime_sequential, find_max_prime_parallel, is_prime
from Game_of_Life import (
    game_of_life_sequential_timeout,
    game_of_life_parallel_timeout,
)


HOST = "0.0.0.0"
PORT = 9000


# ---------------------------------------------------------------------------
# Wrappers exposto ao cliente
# ---------------------------------------------------------------------------

# Game of Life wrappers (necessários para renomear funções)

def game_of_life_sequential_wrapper(grid: list, timeout: int) -> tuple:
    """
    Executa simulação sequencial do Game of Life durante timeout segundos.

    Parâmetros:
        grid (list): grid inicial (lista de listas com 0s e 1s).
        timeout (int): tempo máximo de execução em segundos.

    Retorna:
        tuple: (grid_final, número_de_gerações_executadas)
    """
    return game_of_life_sequential_timeout(grid, timeout)


def game_of_life_parallel_wrapper(grid: list, timeout: int, workers: int) -> tuple:
    """
    Executa simulação paralela do Game of Life durante timeout segundos.

    Parâmetros:
        grid (list): grid inicial (lista de listas com 0s e 1s).
        timeout (int): tempo máximo de execução em segundos.
        workers (int): número de processos paralelos.

    Retorna:
        tuple: (grid_final, número_de_gerações_executadas)
    """
    return game_of_life_parallel_timeout(grid, timeout, workers)


# ---------------------------------------------------------------------------
# Registo de métodos — definido ANTES de list_methods()
# ---------------------------------------------------------------------------

METHODS = {
    # Números primos (agregados em Primos.py)
    "find_max_prime_sequential": find_max_prime_sequential,
    "find_max_prime_parallel": find_max_prime_parallel,
    "is_prime": is_prime,
    
    # Game of Life (com timeout)
    "game_of_life_sequential": game_of_life_sequential_wrapper,
    "game_of_life_parallel": game_of_life_parallel_wrapper,
    
    # Utilitário
    "list_methods": None,  # tratado internamente em handle_request()
}


# ---------------------------------------------------------------------------
# list_methods — usa introspeção sobre METHODS
# ---------------------------------------------------------------------------

def list_methods() -> list:
    """
    Devolve a lista de métodos disponíveis no servidor com nome, parâmetros
    e descrição, obtidos automaticamente por introspeção das funções.

    Retorna:
        list[dict]: lista com {name, params, description} por metodo.
    """
    result = []
    for name, func in METHODS.items():

        if func is None:
            result.append({
                "name": "list_methods",
                "params": [],
                "description": "Devolve a lista de operações disponíveis no servidor."
            })
            continue

        # extrair parâmetros e tipos via introspeção
        sig = inspect.signature(func)
        params = [
            {
                "name": p_name,
                "type": (
                    p.annotation.__name__
                    if p.annotation is not inspect.Parameter.empty
                    else "any"
                )
            }
            for p_name, p in sig.parameters.items()
        ]

        # primeira linha da docstring como descrição
        doc = inspect.getdoc(func) or ""
        description = doc.split("\n")[0] if doc else "Sem descrição."

        result.append({
            "name": name,
            "params": params,
            "description": description
        })

    return result


# ---------------------------------------------------------------------------
# Utilitários de comunicação
# ---------------------------------------------------------------------------

def send_message(sock: socket.socket, payload: dict) -> None:
    """
    Serializa payload como JSON e envia pelo socket, terminado com '\n'.

    Parâmetros:
        sock (socket.socket): socket de destino.
        payload (dict): dicionário a enviar.
    """
    data = json.dumps(payload) + "\n"
    sock.sendall(data.encode("utf-8"))


def recv_message(sock: socket.socket) -> dict:
    """
    Recebe dados do socket até encontrar '\n' e desserializa o JSON.

    Parâmetros:
        sock (socket.socket): socket de origem.

    Retorna:
        dict: mensagem desserializada.

    Lança:
        ConnectionError: se a ligação for fechada antes de receber dados.
        ValueError: se o JSON for inválido.
    """
    buffer = b""
    while not buffer.endswith(b"\n"):
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Ligação fechada pelo cliente.")
        buffer += chunk
    return json.loads(buffer.decode("utf-8").strip())


# ---------------------------------------------------------------------------
# Processamento de pedidos
# ---------------------------------------------------------------------------

def handle_request(request: dict) -> dict:
    """
    Valida e executa um pedido RPC, devolvendo a resposta adequada.

    Parâmetros:
        request (dict): pedido com campos 'method' e 'params'.

    Retorna:
        dict: {"result": ...} em sucesso ou {"error": ...} em falha.
    """
    # validar campos obrigatórios
    if "method" not in request:
        return {"error": "Campo 'method' ausente no pedido."}
    if "params" not in request or not isinstance(request["params"], dict):
        return {"error": "Campo 'params' ausente ou inválido (deve ser objeto JSON)."}

    method_name = request["method"]
    params = request["params"]

    # list_methods tratado internamente
    if method_name == "list_methods":
        return {"result": list_methods()}

    # verificar se o metodo existe
    if method_name not in METHODS:
        available = list(METHODS.keys())
        return {"error": f"Método '{method_name}' não encontrado. Disponíveis: {available}"}

    func = METHODS[method_name]

    # verificar parâmetros em falta
    sig = inspect.signature(func)
    expected = set(sig.parameters.keys())
    missing = expected - set(params.keys())
    if missing:
        return {"error": f"Parâmetros em falta para '{method_name}': {list(missing)}"}

    # executar função
    try:
        result = func(**params)
        return {"result": result}
    except TypeError as e:
        return {"error": f"Erro nos parâmetros de '{method_name}': {e}"}
    except Exception as e:
        return {"error": f"Erro interno ao executar '{method_name}': {e}"}


# ---------------------------------------------------------------------------
# Gestão de clientes (thread por cliente)
# ---------------------------------------------------------------------------

def handle_client(conn: socket.socket, addr: tuple) -> None:
    """
    Gere a sessão de um cliente em loop até este fechar a ligação.

    Executado numa thread dedicada por cada cliente ligado.

    Parâmetros:
        conn (socket.socket): socket da ligação com o cliente.
        addr (tuple): endereço (host, port) do cliente.
    """
    print(f"[+] Cliente ligado: {addr}")
    try:
        while True:
            try:
                request = recv_message(conn)
            except (ConnectionError, json.JSONDecodeError) as e:
                print(f"[-] {addr}: ligação terminada ({e})")
                break

            print(f"[>] {addr} pedido: {request.get('method', '?')}")
            response = handle_request(request)
            print(f"[<] {addr} resposta: {'result' if 'result' in response else 'error'}")

            try:
                send_message(conn, response)
            except OSError:
                print(f"[-] {addr}: erro ao enviar resposta.")
                break
    finally:
        conn.close()
        print(f"[-] Cliente desligado: {addr}")


# ---------------------------------------------------------------------------
# Servidor principal
# ---------------------------------------------------------------------------

def start_server(host: str = HOST, port: int = PORT) -> None:
    """
    Inicia o servidor TCP e aceita ligações de múltiplos clientes de forma
    concorrente, criando uma thread por cliente.

    Parâmetros:
        host (str): endereço de escuta.
        port (int): porta de escuta.
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(10)

    print(f"[*] Servidor RPC a escutar em {host}:{port}")
    print(f"[*] Métodos disponíveis: {list(METHODS.keys())}")

    try:
        while True:
            conn, addr = server_sock.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Servidor encerrado pelo utilizador.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_server()