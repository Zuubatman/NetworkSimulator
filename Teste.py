import socket
import threading
import time

class Roteador:
    def __init__(self, meu_ip):
        self.meu_ip = meu_ip
        self.tabela_de_roteamento = {}
        self.tempo_ultimo_anuncio = {}
        self.carregar_vizinhos()
        self.iniciar_escuta()
        threading.Thread(target=self.verificar_rotas).start()

    def carregar_vizinhos(self):
        with open("roteadores.txt", "r") as file:
            for linha in file:
                ip_vizinho = linha.strip()
                self.tabela_de_roteamento[ip_vizinho] = {'metric': 1, 'next_hop': ip_vizinho}
                self.tempo_ultimo_anuncio[ip_vizinho] = time.time()

    def iniciar_escuta(self):
        threading.Thread(target=self.receber_mensagens).start()

    def enviar_anuncio_de_rotas(self):
        mensagem = "".join([f"@{ip}-{dados['metric']}" for ip, dados in self.tabela_de_roteamento.items() if ip != self.meu_ip])
        for vizinho in self.tabela_de_roteamento.keys():
            if vizinho != self.meu_ip:
                self.enviar_mensagem(vizinho, mensagem)

    def enviar_mensagem(self, ip_destino, mensagem):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(mensagem.encode(), (ip_destino, 9000))
        sock.close()

    def receber_mensagens(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.meu_ip, 9000))
        while True:
            dados, endereco = sock.recvfrom(1024)
            mensagem = dados.decode()
            ip_vizinho = endereco[0]
            if mensagem.startswith("@"):
                self.processar_anuncio_de_rotas(ip_vizinho, mensagem)
            elif mensagem.startswith("*"):
                self.processar_anuncio_de_roteador(ip_vizinho)
            elif mensagem.startswith("!"):
                self.processar_mensagem_de_texto(mensagem)

    def processar_anuncio_de_rotas(self, ip_vizinho, mensagem):
        rotas_recebidas = mensagem.split("@")[1:]
        tabela_atualizada = False
        for rota in rotas_recebidas:
            ip_destino, metrica = rota.split("-")
            metrica = int(metrica) + 1
            if ip_destino not in self.tabela_de_roteamento or metrica < self.tabela_de_roteamento[ip_destino]['metric']:
                self.tabela_de_roteamento[ip_destino] = {'metric': metrica, 'next_hop': ip_vizinho}
                tabela_atualizada = True
                print(f"Tabela de roteamento atualizada: {self.tabela_de_roteamento}")
        self.tempo_ultimo_anuncio[ip_vizinho] = time.time()
        if tabela_atualizada:
            self.enviar_anuncio_de_rotas()

    def processar_anuncio_de_roteador(self, ip_vizinho):
        if ip_vizinho not in self.tabela_de_roteamento:
            self.tabela_de_roteamento[ip_vizinho] = {'metric': 1, 'next_hop': ip_vizinho}
            print(f"Novo roteador adicionado: {ip_vizinho}")
        self.tempo_ultimo_anuncio[ip_vizinho] = time.time()

    def verificar_rotas(self):
        while True:
            agora = time.time()
            rotas_a_remover = [ip for ip, ultimo_tempo in self.tempo_ultimo_anuncio.items() if agora - ultimo_tempo > 35]
            for ip in rotas_a_remover:
                print(f"Removendo rota para {ip} devido a inatividade.")
                del self.tabela_de_roteamento[ip]
                del self.tempo_ultimo_anuncio[ip]
            time.sleep(5)

    def exibir_tabela(self):
        print("Tabela de Roteamento Atual:")
        for ip, dados in self.tabela_de_roteamento.items():
            print(f"IP Destino: {ip}, Métrica: {dados['metric']}, Saída: {dados['next_hop']}")
        print("\n")

    def enviar_mensagem_texto(self, ip_destino, texto):
        if ip_destino == self.meu_ip:
            print("Você não pode enviar uma mensagem para si mesmo.")
            return
        mensagem = f"!{self.meu_ip};{ip_destino};{texto}"
        if ip_destino in self.tabela_de_roteamento:
            proximo_salto = self.tabela_de_roteamento[ip_destino]['next_hop']
            self.enviar_mensagem(proximo_salto, mensagem)
            print(f"Mensagem enviada para {ip_destino} via {proximo_salto}")
        else:
            print("Rota não encontrada para o IP de destino.")

    def processar_mensagem_de_texto(self, mensagem):
        _, ip_origem, ip_destino, texto = mensagem.split(";", 2)
        if ip_destino == self.meu_ip:
            print(f"Mensagem recebida de {ip_origem}: {texto}")
        else:
            if ip_destino in self.tabela_de_roteamento:
                proximo_salto = self.tabela_de_roteamento[ip_destino]['next_hop']
                print(f"Roteando mensagem de {ip_origem} para {ip_destino} via {proximo_salto}")
                self.enviar_mensagem(proximo_salto, mensagem)
            else:
                print(f"Rota não encontrada para {ip_destino}. Mensagem descartada.")

def menu(roteador):
    while True:
        print("\nMenu de Opções:")
        print("1 - Exibir Tabela de Roteamento")
        print("2 - Enviar Anúncio de Rotas Manualmente")
        print("3 - Verificar Rotas Inativas")
        print("4 - Enviar Mensagem de Texto")
        print("5 - Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == '1':
            roteador.exibir_tabela()
        elif opcao == '2':
            roteador.enviar_anuncio_de_rotas()
            print("Anúncio de rotas enviado.")
        elif opcao == '3':
            roteador.verificar_rotas()
            print("Verificação de rotas inativas concluída.")
        elif opcao == '4':
            ip_destino = input("Informe o IP de destino: ")
            texto = input("Digite a mensagem: ")
            roteador.enviar_mensagem_texto(ip_destino, texto)
        elif opcao == '5':
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    meu_ip = "10.132.249.122"  # Substitua pelo IP do roteador
    roteador = Roteador(meu_ip)
    menu(roteador)
