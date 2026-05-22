
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


def menu_find_max_prime(sock: socket.socket) -> None:
    """Recolhe timeout e invoca find_max_prime(timeout) no servidor."""
    try:
        timeout = int(input("  Tempo limite (segundos): "))
        if timeout <= 0:
            raise ValueError
    except ValueError:
        print("  [!] Introduza um número inteiro positivo.")
        return

    print(f"  A procurar durante {timeout}s... (aguarde)")
    result = rpc_call(sock, "find_max_prime", {"timeout": timeout})

    print(f"\n  Maior primo encontrado : {result}")
    print(f"  Notação científica     : {result:.6e}")
    print(f"  Número de dígitos      : {len(str(result))}\n")

OPCOES = {
    "1": ("Listar métodos disponíveis",              menu_list_methods),
    "2": ("Verificar se número é primo (is_prime)",  menu_is_prime),
    "3": ("Encontrar maior primo (find_max_prime)",  menu_find_max_prime),
    "0": ("Sair", None),
}

def print_menu():
    print("\n╔══════════════════════════════════════════╗")
    print("║         Cliente RPC — Números Primos     ║")
    print("╠══════════════════════════════════════════╣")
    for key, (desc, _) in OPCOES.items():
        print(f"║  [{key}] {desc:<38}║")
    print("╚══════════════════════════════════════════╝")

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