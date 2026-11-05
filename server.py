import socket
import threading
from clientthread import ClientListener


class Server:
    """Serveur TCP qui accepte les clients et diffuse leurs messages."""

    def __init__(self, port=59001):
        self.port = port
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("0.0.0.0", port))
        self.listener.listen()
        self.clients_sockets = []
        self.lock = threading.Lock()
        self.running = True

    def run(self):
        print(f"Serveur démarré. En attente sur le port {self.port}...")
        try:
            while self.running:
                try:
                    client_socket, client_address = self.listener.accept()
                except OSError:
                    if self.running:
                        print("Erreur pendant l'acceptation d'un client.")
                    break

                with self.lock:
                    self.clients_sockets.append(client_socket)

                print(f"Connexion de {client_address}")
                thread = ClientListener(self, client_socket, client_address)
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\nArrêt du serveur demandé.")
        finally:
            self.stop()

    def echo(self, data):
        """Envoie le message à tous les clients connectés."""
        encoded = data.encode("utf-8")
        failed = []

        # Le verrou empêche deux diffusions simultanées de mélanger leurs envois.
        with self.lock:
            for client_socket in self.clients_sockets:
                try:
                    client_socket.sendall(encoded)
                except OSError as error:
                    print("Erreur d'envoi à un client :", error)
                    failed.append(client_socket)

            for client_socket in failed:
                if client_socket in self.clients_sockets:
                    self.clients_sockets.remove(client_socket)
                try:
                    client_socket.close()
                except OSError:
                    pass

    def remove_socket(self, client_socket):
        with self.lock:
            if client_socket in self.clients_sockets:
                self.clients_sockets.remove(client_socket)

    def stop(self):
        self.running = False
        try:
            self.listener.close()
        except OSError:
            pass

        with self.lock:
            clients = self.clients_sockets[:]
            self.clients_sockets.clear()

        for client_socket in clients:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                client_socket.close()
            except OSError:
                pass


if __name__ == "__main__":
    server = Server(59001)
    server.run()
