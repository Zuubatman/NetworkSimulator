import socket
import time
import threading  # Adicione esta linha para importar threading

# Resto do código


class Router:
    def __init__(self, config_file):
        self.routing_table = {}  # Estrutura {IP_destino: {"metric": métrica, "next_hop": IP de saída}}
        self.neighbors = []
        self.load_config(config_file)
        
    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            for line in file:
                ip = line.strip()
                self.neighbors.append(ip)
                self.routing_table[ip] = {"metric": 1, "next_hop": ip}
        print("Tabela de roteamento inicial:", self.routing_table)
        
    def format_routing_message(self):
        message_parts = []
        for ip, info in self.routing_table.items():
            if ip != self.get_router_ip():
                message_parts.append(f"{ip}-{info['metric']}")
        return "@" + "@".join(message_parts)
    
    def send_routing_update(self):
        message = self.format_routing_message()
        for neighbor_ip in self.neighbors:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(message.encode(), (neighbor_ip, 5000))
                print(f"Mensagem de rotas enviada para {neighbor_ip}: {message}")
            except Exception as e:
                print(f"Erro ao enviar mensagem de rotas para {neighbor_ip}: {e}")

    def get_router_ip(self):
        # Implementação simples para obter o IP do próprio roteador
        return "192.168.1.1"  # Substitua pelo IP real do roteador

    def send_announcement(self):
        announcement_message = f"*{self.get_router_ip()}"
        for neighbor_ip in self.neighbors:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(announcement_message.encode(), (neighbor_ip, 5000))
                print(f"Mensagem de anúncio enviada para {neighbor_ip}: {announcement_message}")
            except Exception as e:
                print(f"Erro ao enviar mensagem de anúncio para {neighbor_ip}: {e}")
                
    def start_network(self):
        # Envia o anúncio do roteador ao entrar na rede
        self.send_announcement()
        # Em seguida, inicia a troca periódica de atualizações de roteamento
        self.start_sending_updates()

    def start_sending_updates(self, interval=15):
        def send_updates():
            while True:
                self.send_routing_update()
                time.sleep(interval)
                
        update_thread = threading.Thread(target=send_updates)
        update_thread.daemon = True
        update_thread.start()

# Exemplo de uso
router = Router("config.txt")
router.start_network()
