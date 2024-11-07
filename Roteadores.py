import socket
import time
import threading

class Router:
    def __init__(self, config_file):
        self.routing_table = {}
        self.neighbors = []
        self.port = 9000
        self.stop_signal = threading.Event()
        self.load_config(config_file)

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            for line in file:
                ip = line.strip()
                self.neighbors.append(ip)
                self.routing_table[ip] = {"metric": 1, "next_hop": ip, "last_update": time.time()}
        print("Initial Routing Table:", self.routing_table)

    def get_router_ip(self):
        # Ideally, retrieve this router's IP dynamically. For now, hardcoded.
        return "172.20.10.2"  # Substitute with the router's actual IP address.

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
                    sock.sendto(message.encode(), (neighbor_ip, self.port))
                print(f"Routing update sent to {neighbor_ip}: {message}")
            except Exception as e:
                print(f"Error sending routing update to {neighbor_ip}: {e}")

    def start_sending_updates(self, interval=15):
        def send_updates():
            while not self.stop_signal.is_set():
                self.send_routing_update()
                time.sleep(interval)

        update_thread = threading.Thread(target=send_updates)
        update_thread.start()
        return update_thread

    def start_receiving_updates(self):
        def receive_updates():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(("0.0.0.0", self.port))
                while not self.stop_signal.is_set():
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
                print(f"New router {new_ip} added with metric 1 via {sender_ip}")
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
                    print(f"Route updated for {dest_ip} with metric {metric} via {sender_ip}")
                elif sender_ip == self.routing_table[dest_ip]["next_hop"]:
                    self.routing_table[dest_ip]["last_update"] = time.time()
        elif message.startswith("!"):
            src_ip, dest_ip, text_message = message[1:].split(";")
            if dest_ip == self.get_router_ip():
                print(f"Message received from {src_ip}: {text_message}")
            else:
                next_hop = self.routing_table.get(dest_ip, {}).get("next_hop")
                if next_hop:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                            sock.sendto(message.encode(), (next_hop, self.port))
                        print(f"Message forwarded to {dest_ip} via {next_hop}")
                    except Exception as e:
                        print(f"Error forwarding message to {dest_ip} via {next_hop}: {e}")
                else:
                    print(f"No route to {dest_ip}")

    def send_text_message(self, destination_ip, message):
        text_message = f"!{self.get_router_ip()};{destination_ip};{message}"
        next_hop = self.routing_table.get(destination_ip, {}).get("next_hop")
        if next_hop:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(text_message.encode(), (next_hop, self.port))
                print(f"Text message sent to {destination_ip} via {next_hop}")
            except Exception as e:
                print(f"Error sending text message to {destination_ip} via {next_hop}: {e}")
        else:
            print(f"No route to {destination_ip}")

    def start_cleaning_old_routes(self, interval=5, timeout=35):
        def clean_routes():
            while not self.stop_signal.is_set():
                current_time = time.time()
                routes_to_delete = [ip for ip, info in self.routing_table.items()
                                    if info["next_hop"] in self.neighbors and
                                    current_time - info["last_update"] > timeout]
                for ip in routes_to_delete:
                    del self.routing_table[ip]
                    if ip in self.neighbors:
                        self.neighbors.remove(ip)
                    print(f"Route to {ip} removed due to timeout.")
                time.sleep(interval)

        clean_thread = threading.Thread(target=clean_routes)
        clean_thread.start()
        return clean_thread

    def display_routing_table(self):
        print("Updated Routing Table:")
        for ip, info in self.routing_table.items():
            print(f"Destination IP: {ip}, Metric: {info['metric']}, Next Hop: {info['next_hop']}")

    def stop(self):
        self.stop_signal.set()

# Exemplo de uso
router = Router("roteadores.txt")
router.start_sending_updates()
router.start_receiving_updates()
router.start_cleaning_old_routes()

# Display da tabela de roteamento a cada 30 segundos
def display_table_periodically(router, interval=30):
    while not router.stop_signal.is_set():
        router.display_routing_table()
        time.sleep(interval)

display_thread = threading.Thread(target=display_table_periodically, args=(router,))
display_thread.start()

# Para enviar uma mensagem de texto para outro roteador
# router.send_text_message("192.168.1.2", "Oi, tudo bem?")
