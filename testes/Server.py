from socket import *
import threading
import time

serverPort = 9000
serverIP = '192.168.15.130'  # Substitua pelo IP do roteador

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind((serverIP, serverPort))
serverSocket.settimeout(2)

routing_table = {}  # Estrutura: {IP_destino: {"metric": métrica, "next_hop": IP de saída, "last_update": timestamp}}
neighbors = []  # Lista de IPs vizinhos

# Função para ler arquivo de configuração de vizinhos
def load_config():
    with open("roteadores.txt", "r") as file:
        for line in file:
            neighbor_ip = line.strip()
            neighbors.append(neighbor_ip)
            routing_table[neighbor_ip] = {"metric": 1, "next_hop": neighbor_ip, "last_update": time.time()}

# Função para enviar tabela de roteamento para vizinhos (Mensagem 1)
def send_routing_table():
    message = "@" + "@".join(f"{ip}-{info['metric']}" for ip, info in routing_table.items())
    for neighbor_ip in neighbors:
        serverSocket.sendto(message.encode(), (neighbor_ip, serverPort))
    print("Tabela de roteamento enviada:", message)

# Função para anunciar o roteador ao entrar na rede (Mensagem 2)
def send_announcement():
    message = f"*{serverIP}"
    for neighbor_ip in neighbors:
        serverSocket.sendto(message.encode(), (neighbor_ip, serverPort))
    print("Anúncio enviado:", message)

# Função para atualizar a tabela de roteamento ao receber uma tabela de um vizinho
def update_routing_table(received_message, sender_ip):
    updates = False
    routes = received_message[1:].split("@")
    for route in routes:
        dest_ip, metric = route.split("-")
        metric = int(metric) + 1
        if dest_ip not in routing_table or metric < routing_table[dest_ip]["metric"]:
            routing_table[dest_ip] = {"metric": metric, "next_hop": sender_ip, "last_update": time.time()}
            updates = True
    if updates:
        send_routing_table()

# Função para tratar mensagens recebidas
def handle_message(message, clientAddress):
    if message.startswith("@"):
        update_routing_table(message, clientAddress[0])
    elif message.startswith("*"):
        neighbor_ip = message[1:]
        routing_table[neighbor_ip] = {"metric": 1, "next_hop": neighbor_ip, "last_update": time.time()}
    elif message.startswith("!"):
        _, ip_dest, text = message[1:].split(";", 2)
        if ip_dest == serverIP:
            print(f"Mensagem recebida: {text}")
        else:
            next_hop = routing_table[ip_dest]["next_hop"]
            serverSocket.sendto(message.encode(), (next_hop, serverPort))

# Função para remover rotas inativas
def clean_inactive_routes():
    while True:
        current_time = time.time()
        to_remove = [ip for ip, info in routing_table.items() if current_time - info["last_update"] > 35]
        for ip in to_remove:
            del routing_table[ip]
            neighbors.remove(ip) if ip in neighbors else None
            print(f"Rota para {ip} removida por inatividade")
        time.sleep(5)

# Thread para ouvir mensagens de outros roteadores
def listen():
    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)
            handle_message(message.decode(), clientAddress)
        except timeout:
            continue

# Inicializa o servidor com threads para enviar, receber e limpar rotas
def run():
    load_config()
    send_announcement()
    threading.Thread(target=listen).start()
    threading.Thread(target=clean_inactive_routes).start()
    while True:
        send_routing_table()
        time.sleep(15)

run()
