import time
import threading

class Router:
    def __init__(self, config_file):
        self.routing_table = {}  # Estrutura {IP_destino: {"metric": métrica, "next_hop": IP de saída}}
        self.neighbors = []
        self.last_update = {}  # Última vez que recebemos uma atualização de cada vizinho
        self.load_config(config_file)
        
    def load_config(self, config_file):
        # Lê o arquivo e inicializa a tabela de roteamento com métrica 1 para os vizinhos
        with open(config_file, 'r') as file:
            for line in file:
                ip = line.strip()
                self.neighbors.append(ip)
                self.routing_table[ip] = {"metric": 1, "next_hop": ip}
                self.last_update[ip] = time.time()  # Marca a última atualização como o tempo atual
        print("Tabela de roteamento inicial:", self.routing_table)
        
    def display_routing_table(self):
        print("Tabela de Roteamento Atualizada:")
        for ip, info in self.routing_table.items():
            print(f"IP de Destino: {ip}, Métrica: {info['metric']}, IP de Saída: {info['next_hop']}")

# Teste de Inicialização
router = Router("config.txt")
router.display_routing_table()
