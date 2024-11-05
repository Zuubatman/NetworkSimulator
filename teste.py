import socket
import time
import threading

class Router:
    def __init__(self, config_file):
        self.routing_table = {}
        self.neighbors = []
        self.load_config(config_file)
        self.port = 5000

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            for line in file:
                ip = line.strip()
                self.neighbors.append(ip)
                self.routing_table[ip] = {"metric": 1, "next_hop": ip, "last_update": time.time()}
        print("Tabela de roteamento inicial:", self.routing_table)

    def format_routing_message(self):
        message_parts = []
        for ip, info in self.routing_table.items():
            if ip != self.get_router_ip():
                message_parts.append(f"{ip}-{info['metric']}")
        return "@" + "@".join(message_parts)
    
    def send_routing_update(self):
        message = self.format_routing_message()
        # Enviar mensagens de rota apenas para IPs ativos na lista de vizinhos
        for neighbor_ip in self.neighbors:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(message.encode(), (neighbor_ip, self.port))
                print(f"Mensagem de rotas enviada para {neighbor_ip}: {message}")
            except Exception as e:
                print(f"Erro ao enviar mensagem de rotas para {neighbor_ip}: {e}")

    def get_router_ip(self):
        return "192.168.1.1"

    def send_announcement(self):
        announcement_message = f"*{self.get_router_ip()}"
        for neighbor_ip in self.neighbors:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(announcement_message.encode(), (neighbor_ip, self.port))
                print(f"Mensagem de anúncio enviada para {neighbor_ip}: {announcement_message}")
            except Exception as e:
                print(f"Erro ao enviar mensagem de anúncio para {neighbor_ip}: {e}")

    def start_network(self):
        self.send_announcement()
        send_update_thread = self.start_sending_updates()
        receive_update_thread = self.start_receiving_updates()
        clean_routes_thread = self.start_cleaning_old_routes()
        
        send_update_thread.join()
        receive_update_thread.join()
        clean_routes_thread.join()

    def start_sending_updates(self, interval=15):
        def send_updates():
            while True:
                self.send_routing_update()
                time.sleep(interval)

        update_thread = threading.Thread(target=send_updates)
        update_thread.start()
        return update_thread

    def start_receiving_updates(self):
        def receive_updates():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(("0.0.0.0", self.port))
                while True:
                    data, addr = sock.recvfrom(1024)
                    self.process_received_message(data.decode(), addr[0])

        receive_thread = threading.Thread(target=receive_updates)
        receive_thread.start()
        return receive_thread

    def process_received_message(self, message, sender_ip):
        if message.startswith("*"):
            new_ip = message[1:]
            if new_ip not in self.routing_table:
                self.routing_table[new_ip] = {"metric": 1, "next_hop": sender_ip, "last_update": time.time()}
                print(f"Novo roteador {new_ip} adicionado com métrica 1 via {sender_ip}")
                if new_ip not in self.neighbors:
                    self.neighbors.append(new_ip)
        elif message.startswith("@"):
            routes = message[1:].split("@")
            for route in routes:
                dest_ip, metric = route.split("-")
                metric = int(metric) + 1
                if (dest_ip not in self.routing_table or 
                    metric < self.routing_table[dest_ip]["metric"]):
                    self.routing_table[dest_ip] = {"metric": metric, "next_hop": sender_ip, "last_update": time.time()}
                    print(f"Rota atualizada para {dest_ip} com métrica {metric} via {sender_ip}")
                elif sender_ip == self.routing_table[dest_ip]["next_hop"]:
                    self.routing_table[dest_ip]["last_update"] = time.time()

    def start_cleaning_old_routes(self, interval=5, timeout=35):
        def clean_routes():
            while True:
                current_time = time.time()
                routes_to_delete = [ip for ip, info in self.routing_table.items()
                                    if info["next_hop"] in self.neighbors and
                                    current_time - info["last_update"] > timeout]
                for ip in routes_to_delete:
                    # Remove IP inativo da tabela de roteamento e da lista de vizinhos
                    del self.routing_table[ip]
                    if ip in self.neighbors:
                        self.neighbors.remove(ip)
                    print(f"Rota para {ip} removida devido à falta de atualizações.")
                time.sleep(interval)

        clean_thread = threading.Thread(target=clean_routes)
        clean_thread.start()
        return clean_thread

    def display_routing_table(self):
        print("Tabela de Roteamento Atualizada:")
        for ip, info in self.routing_table.items():
            print(f"IP de Destino: {ip}, Métrica: {info['metric']}, IP de Saída: {info['next_hop']}")

# Exemplo de uso
router = Router("config.txt")
router.start_network()

# Exibição periódica da tabela de roteamento
def display_table_periodically(router, interval=30):
    while True:
        router.display_routing_table()
        time.sleep(interval)

display_thread = threading.Thread(target=display_table_periodically, args=(router,))
display_thread.start()
