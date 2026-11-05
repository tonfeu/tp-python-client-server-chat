
import socket  # permet de créer une communication réseau entre deux programmes
import sys  # permet de quitter le programme et d'interagir avec l'interpréteur Python
import time  # permet de gérer le temps
from clientthread import ClientListener  # importe la classe ClientListener depuis clientthread.py
import threading


class Server:

    """ Classe Server : représente le serveur TCP.
    Elle permet d'accepter les connexions des clients,
    de gérer leurs sockets et de diffuser leurs messages."""

    def __init__(self, port):  # constructeur

        """ Initialise le serveur. self représente l'objet lui-même.
        port : numéro du port sur lequel le serveur écoute.
        Ici, nous avons choisi 59001."""

        # Création d'une socket TCP IPv4
        # IPv4 permet d'identifier les machines sur le réseau avec une adresse IP.
        # TCP assure une transmission fiable et ordonnée des données.
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Association de la socket à toutes les interfaces réseau
        # '' signifie que le serveur accepte les connexions sur toutes les interfaces réseau locales
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(('', port))
        self.listener.listen(1)  # Mise en écoute du serveur

        print("Listening on port", port)

        # Liste contenant les sockets des clients connectés
        self.clients_sockets = []
        self.lock = threading.Lock()

    def run(self):
        """
        Lance le serveur et attend les connexions des clients.
        Chaque nouveau client est géré par un thread indépendant.
        """

        while True:  # boucle infinie car le serveur doit rester actif
            print("listening new customers")

            try:
                # Accepte une nouvelle connexion
                client_socket, client_adress = self.listener.accept()

            except OSError as erreur:
                """OSError permet de capturer les erreurs liées aux opérations système et réseau.
                as erreur permet de récupérer le détail de l'erreur."""
                print("Erreur lors de l'acceptation d'un client :", erreur)
                break

            # Ajoute la socket du nouveau client à la liste
            with self.lock:
                self.clients_sockets.append(client_socket)

            print("Start the thread for client:", client_adress)

            # Création et démarrage d'un thread pour gérer ce client
            client_thread = ClientListener(self, client_socket, client_adress)
            client_thread.start()  # méthode qui démarre le thread

            time.sleep(0.1)  # met en pause le thread principal pendant 0,1 seconde

    def remove_socket(self, socket):
        """
        Supprime la socket d'un client de la liste des clients connectés.
        socket : socket du client à supprimer.
        """

        with self.lock:
            if socket in self.clients_sockets:
                self.clients_sockets.remove(socket)

    def echo(self, data):
        """
        Diffuse un message à tous les clients connectés.
        data : message à envoyer aux clients.
        """

        print("echoing:", data)  # exemple : bonjour !

        # Copie la liste des clients pour éviter de la modifier pendant le parcours
        with self.lock:
            clients = self.clients_sockets.copy()

        # Parcourt toutes les sockets des clients connectés
        for sock in clients:
            try:
                sock.sendall(data.encode("UTF-8"))  # envoie le message encodé en UTF-8

            except OSError as erreur:
                print("Impossible d'envoyer le message à un client :", erreur)
                self.remove_socket(sock)

                try:
                    sock.close()
                except OSError:
                    pass


# Point d'entrée du programme
if __name__ == "__main__":  # permet de vérifier si le fichier est exécuté directement

    # Création du serveur sur le port 59001
    server = Server(59001)

    # Démarrage du serveur
    server.run()
