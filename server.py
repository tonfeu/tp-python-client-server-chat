import socket  # permet de créer une communication réseau entre deux programmes
import sys  # permet de quitter le programme et d'interagir avec l'interpréteur Python
import time  # permet de gérer le temps
from clientthread import ClientListener  # importe la classe ClientListener depuis clientthread.py
import threading

# AJOUT RECHERCHE AUTOMATIQUE : port UDP fixe sur lequel le serveur écoute les demandes de recherche.
# Les clients l'utilisent pour trouver les serveurs sans connaître leur adresse IP.
DISCOVERY_PORT = 59000

# AJOUT RECHERCHE AUTOMATIQUE : commande envoyée par un client pour demander "qui est là ?"
DISCOVERY_REQUEST = "DISCOVER_SERVERS"

# AJOUT RECHERCHE AUTOMATIQUE : commande spécifique par laquelle le serveur renvoie son nom.
# Format de la réponse : "SERVERNAME <port> <nom>"
DISCOVERY_REPLY = "SERVERNAME"


class Server:

    """ Classe Server : représente le serveur TCP.
    Elle permet d'accepter les connexions des clients,
    de gérer leurs sockets et de diffuser leurs messages."""

    def __init__(self, port, name="Serveur"):  # constructeur

        """ Initialise le serveur. self représente l'objet lui-même.
        port : numéro du port sur lequel le serveur écoute.
        Ici, nous avons choisi 59001.

        AJOUT RECHERCHE AUTOMATIQUE : name est le nom du serveur, renvoyé aux clients
        qui recherchent les serveurs disponibles (affiché dans leur liste)."""

        # AJOUT RECHERCHE AUTOMATIQUE : on mémorise le port et le nom pour pouvoir les envoyer aux clients
        self.port = port
        self.name = name

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

    def discovery_loop(self):
        """
        AJOUT RECHERCHE AUTOMATIQUE : écoute les demandes de recherche envoyées en UDP
        et répond avec le nom et le port du serveur.
        Cette méthode tourne dans un thread séparé pour ne pas bloquer le serveur de chat.
        """

        try:
            # Socket UDP (sans connexion) : adaptée aux petites questions/réponses de recherche
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp.bind(('', DISCOVERY_PORT))

        except OSError as erreur:
            # Le chat reste utilisable : seule la recherche automatique est indisponible
            print("Recherche automatique indisponible :", erreur)
            return

        print("Discovery listening on UDP port", DISCOVERY_PORT)

        while True:

            try:
                # Attend une demande d'un client et récupère son adresse pour lui répondre
                data, client_address = udp.recvfrom(1024)

            except OSError as erreur:
                print("Erreur dans la recherche automatique :", erreur)
                break

            # Ignore tout ce qui n'est pas la commande de recherche
            if data.decode("UTF-8", errors="ignore").strip() == DISCOVERY_REQUEST:

                reply = "{0} {1} {2}".format(DISCOVERY_REPLY, self.port, self.name)

                try:
                    udp.sendto(reply.encode("UTF-8"), client_address)
                except OSError as erreur:
                    print("Impossible de répondre à la recherche :", erreur)

    def run(self):
        """
        Lance le serveur et attend les connexions des clients.
        Chaque nouveau client est géré par un thread indépendant.
        """

        # AJOUT RECHERCHE AUTOMATIQUE : démarre le thread qui répond aux recherches des clients
        # daemon=True : le thread s'arrête automatiquement avec le programme principal
        discovery_thread = threading.Thread(target=self.discovery_loop, daemon=True)
        discovery_thread.start()

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

    # AJOUT RECHERCHE AUTOMATIQUE : demande le nom du serveur (celui qui s'affichera dans la liste des clients)
    # Si l'utilisateur appuie sur Entrée sans rien écrire, on utilise le nom de l'ordinateur
    name = input("Nom du serveur (Entrée = nom de l'ordinateur) : ").strip()
    if not name:
        name = socket.gethostname()

    # Création du serveur sur le port 59001
    server = Server(59001, name)

    # Démarrage du serveur
    server.run()