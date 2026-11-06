import threading
import socket
import time
import re

DISCOVERY_PORT = 59000
DISCOVERY_REQUEST = "DISCOVER_SERVERS"
DISCOVERY_REPLY = "SERVERNAME"


def discover_servers(timeout=2):

    """ cherche les serveurs disponibles sur le réseau
    Envoie une demande en UDP (broadcast) et collecte les réponses pendant 'timeout' secondes
    Retourne une liste de tuples (nom, adresse IP, port), par exemple [("PC-Cerena", "192.168.1.25", 59001)]"""

    servers = []

    # Socket UDP : le mode broadcast permet d'envoyer la demande à tous les ordinateurs du réseau local
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.settimeout(0.5)  # évite de rester bloqué en attente d'une réponse

    try:
        # 255.255.255.255 = tout le réseau local ; 127.0.0.1 = cet ordinateur (serveur lancé sur la même machine)
        for destination in ("255.255.255.255", "127.0.0.1"):
            try:
                udp.sendto(DISCOVERY_REQUEST.encode("UTF-8"), (destination, DISCOVERY_PORT))
            except OSError as erreur:
                print("Erreur lors de la recherche vers", destination, ":", erreur)

        end_time = time.time() + timeout

        # Collecte les réponses jusqu'à la fin du délai
        while time.time() < end_time:

            try:
                data, address = udp.recvfrom(1024)

            except socket.timeout:
                continue  # aucune réponse pour l'instant, on réessaie

            except OSError as erreur:
                print("Erreur lors de la réception d'une réponse :", erreur)
                break

            text = data.decode("UTF-8", errors="ignore")

            # Réponse attendue : "SERVERNAME <port> <nom>"
            if text.startswith(DISCOVERY_REPLY + " "):

                parts = text.split(" ", 2)

                if len(parts) == 3 and parts[1].isdigit():

                    # On garde l'adresse IP d'où vient la réponse
                    server_info = (parts[2], address[0], int(parts[1]))

                    # Évite d'ajouter deux fois le même serveur (répondu via broadcast et via 127.0.0.1)
                    already_found = any(s[0] == server_info[0] and s[2] == server_info[2] for s in servers)

                    if not already_found:
                        servers.append(server_info)

    finally:
        udp.close()  # ferme toujours la socket, même en cas d'erreur

    return servers


class Client:
    """Classe Client: représente un utilisateur du chat
    elle permet de se connecter au serveur, d'envoyer
    des messages et de recevoir les messages des autres clients"""

    def __init__(self, username, server, port, on_message=None, on_disconnect=None):
        """Initialise le client et établit la connexion au serveur
        username: nom de l'utilisateur
        server: adresse IP ou nom du serveur
        port : port de communication du serveur

          avec l'utilisation de tkinter:
        on_message : fonction appelée à chaque message reçu (utilisée par l'interface Tkinter).
        on_disconnect : fonction appelée quand la connexion se ferme (utilisée par l'interface Tkinter).
        Si ces paramètres ne sont pas fournis, le client fonctionne comme avant, dans la console."""

        self.username = username

        self.on_message = on_message
        self.on_disconnect = on_disconnect

        # AMÉLIORATION : initialise l'état d'écoute avant la connexion
        self.listening = False

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# Création d'une socket TCP IPv4
            self.socket.connect((server, port)) # Connexion au serveur

            print("Connexion au serveur réussie.")

            # AMÉLIORATION : active l'écoute uniquement après une connexion réussie
            self.listening = True

            self.send("USERNAME {0}".format(username))# Envoie le nom de l'utilisateur au serveur

        # AMÉLIORATION : capture les erreurs liées à la création de la socket ou à la connexion
        except OSError as erreur:
            print("Impossible de se connecter au serveur :", erreur)

            # AMÉLIORATION : transmet l'erreur au programme principal
            # AJOUT TKINTER : l'interface attrape cette exception pour afficher une boîte de dialogue d'erreur
            raise

    def notify_gui(self, text):
        """
     envoie un texte à l'interface"""

        if self.on_message:
            self.on_message(text)

    def listener(self):
        """Attend et reçoit les messages envoyés par le serveur
        """

        while self.listening:

            try:
                # recoit les données envoyées par le serveur
                data = self.socket.recv(1024)

                #détecte la fermeture de la connexion par le serveur
                if not data:
                    print("Le serveur a fermé la connexion.")
                    # prévient aussi la fenêtre pour que l'utilisateur voie le message
                    self.notify_gui("Le serveur a fermé la connexion.")
                    break

                # Décode les données reçues en texte UTF-8
                data = data.decode('UTF-8')

            # AMÉLIORATION : capture les erreurs liées à la réception réseau
            except OSError as erreur:
                # AJOUT TKINTER : si on a nous-mêmes fermé la connexion (bouton Quitter),
                # l'erreur est normale : on sort de la boucle sans afficher de message d'erreur
                if not self.listening:
                    break
                print("Erreur lors de la réception des données :", erreur)
                self.notify_gui("Erreur lors de la réception des données : {0}".format(erreur))
                break

            # AMÉLIORATION : détecte les erreurs de décodage UTF-8
            except UnicodeDecodeError:
                print("Erreur : le message reçu possède un encodage invalide.")
                self.notify_gui("Erreur : le message reçu possède un encodage invalide.")
                break

            self.handle_msg(data)# Traite le message reçu

            time.sleep(0.1)

        # AMÉLIORATION : ferme la connexion lorsque la réception s'arrête
        self.tidy_up()

    def listen(self):
        """
        Crée et démarre un thread pour recevoir les messages
        sans bloquer l'envoi des messages par l'utilisateur.
        """

        self.listen_thread = threading.Thread(target=self.listener)

        self.listen_thread.daemon = True  # Le thread s'arrête automatiquement avec le programme principal

        # Démarrage du thread
        self.listen_thread.start()

    def send(self, message):
        """
        Envoie un message au serveur.

        message : texte saisi par l'utilisateur.
        """

        # AMÉLIORATION : empêche l'envoi si la connexion est fermée
        if not self.listening:
            print("Impossible d'envoyer le message : vous n'êtes pas connecté.")
            # AJOUT TKINTER : informe aussi la fenêtre
            self.notify_gui("Impossible d'envoyer le message : vous n'êtes pas connecté.")
            return

        try:
            # Vérifie si le message correspond à la commande USERNAME
            username_result = re.search('^USERNAME (.*)$', message)

            if not username_result and message != "QUIT":

                # Ajoute le nom de l'utilisateur devant son message
                message = "{0}: {1}".format(self.username, message)

            # Encode le message en UTF-8 et l'envoie au serveur
            self.socket.sendall(message.encode("UTF-8"))

        # AMÉLIORATION : récupère le détail des erreurs d'envoi
        except OSError as erreur:
            print("Erreur lors de l'envoi du message :", erreur)
            self.notify_gui("Erreur lors de l'envoi du message : {0}".format(erreur))
            self.tidy_up()

    def tidy_up(self):
        """
        Ferme la connexion du client et arrête son écoute.
        """

        # AMÉLIORATION : évite de fermer plusieurs fois la même connexion
        if not self.listening:
            return

        self.listening = False

        try:
            # Fermeture de la socket
            self.socket.close()

        # AMÉLIORATION : gère les erreurs pouvant survenir pendant la fermeture
        except OSError as erreur:
            print("Erreur lors de la fermeture de la connexion :", erreur)

        # AJOUT TKINTER : prévient l'interface que la connexion est terminée
        # (elle pourra désactiver le champ de saisie et le bouton Envoyer)
        if self.on_disconnect:
            self.on_disconnect()

    def handle_msg(self, data):
        """
        Analyse les messages reçus du serveur.

        data : message reçu.
        """

        if data == "QUIT":

            # Ferme la connexion si le serveur envoie QUIT
            self.tidy_up()

        elif data == "":

            # Ferme la connexion si le serveur ne transmet plus de données
            self.tidy_up()

        else:

            # Affiche le message reçu
            # AJOUT TKINTER : le serveur peut regrouper plusieurs messages dans un même paquet TCP,
            # on les sépare donc ligne par ligne (le serveur termine chaque message par un retour à la ligne)
            for line in data.splitlines():

                if self.on_message:
                    # Mode Tkinter : on donne la ligne à l'interface graphique
                    self.on_message(line)
                else:
                    # Mode console : comportement d'origine (affichage avec print)
                    print(line)


# Point d'entrée du programme client
if __name__ == "__main__":

    try:
        # Demande les informations de connexion à l'utilisateur
        username = input("username: ")
        server = input("server: ")

        # AMÉLIORATION : vérifie que le port saisi est un nombre entier
        port = int(input("port: "))

        # Création du client
        client = Client(username, server, port)

        # Démarrage de l'écoute des messages
        client.listen()

        message = ""

        # Permet d'envoyer des messages jusqu'à la commande QUIT
        while message != "QUIT" and client.listening:

            message = input()

            if client.listening:
                client.send(message)

        # AMÉLIORATION : ferme proprement la connexion après QUIT
        if client.listening:
            client.tidy_up()

    # AMÉLIORATION : gère une saisie incorrecte du port
    except ValueError:
        print("Erreur : le port doit être un nombre entier.")

    # AMÉLIORATION : gère les erreurs de connexion
    except OSError:
        print("Le client n'a pas pu démarrer.")

    # AMÉLIORATION : permet de quitter proprement avec CTRL+C
    except KeyboardInterrupt:
        print("\nDéconnexion demandée.")