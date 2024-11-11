from socket import *
import threading
import time

serverPort = 9000  # Porta padrão de comunicação dos roteadores
serverIP = '192.168.15.130'  # Substitua pelo IP deste roteador

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
            # Evita adicionar uma rota para o próprio IP
            if neighbor_ip != serverIP:
                neighbors.append(neighbor_ip)
                routing_table[neighbor_ip] = {"metric": 1, "next_hop": neighbor_ip, "last_update": time.time()}
    print("Tabela de roteamento inicial:", routing_table)

# Função para enviar tabela de roteamento para vizinhos (Mensagem 1)
def send_routing_table():
    # Exclui o próprio IP das mensagens de tabela de roteamento enviadas aos vizinhos
    message = "@" + "@".join(f"{ip}-{info['metric']}" for ip, info in routing_table.items() if ip != serverIP)
    for neighbor_ip in neighbors:
        try:
            serverSocket.sendto(message.encode(), (neighbor_ip, serverPort))
            print(f"Tabela de roteamento enviada para {neighbor_ip}: {message}")
        except Exception as e:
            print(f"Erro ao enviar tabela para {neighbor_ip}: {e}")

# Função para anunciar o roteador ao entrar na rede (Mensagem 2)
def send_announcement():
    message = f"*{serverIP}"
    for neighbor_ip in neighbors:
        try:
            serverSocket.sendto(message.encode(), (neighbor_ip, serverPort))
            print(f"Anúncio enviado para {neighbor_ip}: {message}")
        except Exception as e:
            print(f"Erro ao enviar anúncio para {neighbor_ip}: {e}")

# Função para atualizar a tabela de roteamento ao receber uma tabela de um vizinho
def update_routing_table(received_message, sender_ip):
    updates = False
    routes = received_message[1:].split("@")
    for route in routes:
        dest_ip, metric = route.split("-")
        metric = int(metric) + 1
        if dest_ip != serverIP:  # Evita adicionar rota para o próprio IP
            if dest_ip not in routing_table or metric < routing_table[dest_ip]["metric"]:
                routing_table[dest_ip] = {"metric": metric, "next_hop": sender_ip, "last_update": time.time()}
                updates = True
    if updates:
        send_routing_table()

# Função para tratar mensagens recebidas
def handle_message(message, clientAddress):
    if message.startswith("@"):
        # Mensagem de tabela de roteamento
        update_routing_table(message, clientAddress[0])
    elif message.startswith("*"):
        # Mensagem de anúncio de roteador
        neighbor_ip = message[1:]
        if neighbor_ip != serverIP and neighbor_ip not in routing_table:
            routing_table[neighbor_ip] = {"metric": 1, "next_hop": neighbor_ip, "last_update": time.time()}
            if neighbor_ip not in neighbors:
                neighbors.append(neighbor_ip)
    elif message.startswith("!"):
        # Mensagem de texto para roteamento
        _, ip_dest, text = message[1:].split(";", 2)
        if ip_dest == serverIP:
            print(f"Mensagem recebida: {text} (de {clientAddress[0]})")
        else:
            if ip_dest in routing_table:
                next_hop = routing_table[ip_dest]["next_hop"]
                serverSocket.sendto(message.encode(), (next_hop, serverPort))
                print(f"Roteando mensagem para {ip_dest} via {next_hop}")
            else:
                print(f"Rota para {ip_dest} desconhecida. Mensagem não enviada.")

# Função para remover rotas inativas
def clean_inactive_routes():
    while True:
        current_time = time.time()
        to_remove = [ip for ip, info in routing_table.items() if current_time - info["last_update"] > 35]
        for ip in to_remove:
            del routing_table[ip]
            if ip in neighbors:
                neighbors.remove(ip)
            print(f"Rota para {ip} removida por inatividade")
        time.sleep(5)

# Função para ouvir mensagens de outros roteadores
def listen():
    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)
            handle_message(message.decode(), clientAddress)
        except timeout:
            continue

# Menu interativo para o usuário
def menu():
    while True:
        print("\nMENU:")
        print("1. Ver tabela de roteamento")
        print("2. Enviar mensagem de texto para outro roteador")
        print("3. Sair")
        
        choice = input("Escolha uma opção:\n").strip()
        
        if choice == '1':
            display_routing_table()
        elif choice == '2':
            ip_dest = input("Digite o IP de destino: ").strip()
            message = input("Digite a mensagem: ").strip()
            send_message(ip_dest, message)
        elif choice == '3':
            print("Encerrando roteador.")
            break
        else:
            print("Opção inválida. Tente novamente.")

# Função para enviar uma mensagem de texto para outro roteador
def send_message(ip_dest, message):
    routing_message = f"!{serverIP};{ip_dest};{message}"
    if ip_dest in routing_table:
        next_hop = routing_table[ip_dest]["next_hop"]
        serverSocket.sendto(routing_message.encode(), (next_hop, serverPort))
        print(f"Enviando mensagem para {ip_dest} via {next_hop}")
    else:
        print(f"Rota para {ip_dest} desconhecida. Mensagem não enviada.")

# Função para exibir a tabela de roteamento atual
def display_routing_table():
    print("\nTabela de Roteamento Atualizada:")
    for ip, info in routing_table.items():
        print(f"IP de Destino: {ip}, Métrica: {info['metric']}, IP de Saída: {info['next_hop']}")
    print("")

# Função principal para iniciar o roteador e executar suas ações
def run():
    load_config()
    send_announcement()  # Anunciar a presença ao entrar na rede

    # Inicializa as threads para ouvir mensagens e limpar rotas
    threading.Thread(target=listen, daemon=True).start()
    threading.Thread(target=clean_inactive_routes, daemon=True).start()

    # Enviar tabela de roteamento a cada 15 segundos
    threading.Thread(target=periodic_send_routing_table, daemon=True).start()
    
    # Iniciar o menu interativo
    menu()

# Função para enviar a tabela de roteamento periodicamente
def periodic_send_routing_table():
    while True:
        send_routing_table()
        time.sleep(15)

run()
