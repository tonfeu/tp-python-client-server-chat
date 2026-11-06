import tkinter as tk  # bibliothèque standard de Python pour créer des interfaces graphiques
from tkinter import scrolledtext, messagebox  # zone de texte avec barre de défilement et boîtes de dialogue
import queue  # file d'attente utilisée pour passer les messages du thread réseau au thread Tkinter
import threading  # lance la recherche dans un thread pour ne pas figer la fenêtre
from client import Client, discover_servers  # réutilise la classe Client de client.py (toute la logique réseau reste là-bas)
# discover_servers : fonction de client.py qui cherche les serveurs disponibles sur le réseau


class ChatWindow:
    """ Elle affiche d'abord un écran de connexion puis l'écran de discussion"""

    def __init__(self, root):
       # root : fenêtre principale Tkinter

        self.root = root
        self.root.title("Chat client-serveur")

        self.client = None  # "Se connecter"

        """tk depose les message dans la file et la fenêtre les lit régulièrement dans check_queue()"""
        self.messages = queue.Queue()

        self.build_login_frame()
        self.build_chat_frame()

        self.show_login()

        # Si l'utilisateur ferme la fenêtre avec la croix, on se déconnecte proprement
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Lance la lecture régulière de la file de messages
        self.check_queue()


    def build_login_frame(self):
        """Construit l'écran de connexion : pseudo, adresse du serveur et port."""

        self.login_frame = tk.Frame(self.root, padx=20, pady=20)

        tk.Label(self.login_frame, text="Pseudo :").grid(row=0, column=0, sticky="e", pady=3)
        self.username_entry = tk.Entry(self.login_frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=3)

        tk.Label(self.login_frame, text="Serveur :").grid(row=1, column=0, sticky="e", pady=3)
        self.server_entry = tk.Entry(self.login_frame, width=25)
        self.server_entry.insert(0, "localhost")  
        self.server_entry.grid(row=1, column=1, pady=3)

        tk.Label(self.login_frame, text="Port :").grid(row=2, column=0, sticky="e", pady=3)
        self.port_entry = tk.Entry(self.login_frame, width=25)
        self.port_entry.insert(0, "59001")  # port choisi dans server.py
        self.port_entry.grid(row=2, column=1, pady=3)

        #  bouton qui lance la recherche des serveurs sur le réseau
        self.search_button = tk.Button(self.login_frame, text="Rechercher les serveurs", command=self.search_servers)
        self.search_button.grid(row=3, column=0, columnspan=2, pady=(10, 3))

        # liste des serveurs trouvés
        self.servers_listbox = tk.Listbox(self.login_frame, height=4, width=40, exportselection=False)
        self.servers_listbox.grid(row=4, column=0, columnspan=2, pady=3)

        # Cliquer sur un serveur de la liste remplit automatiquement les champs Serveur et Port
        self.servers_listbox.bind("<<ListboxSelect>>", self.on_server_selected)

        # Liste des serveurs trouvés, dans le même ordre que la Listbox
        self.found_servers = []

        tk.Button(self.login_frame, text="Se connecter", command=self.connect).grid(
            row=5, column=0, columnspan=2, pady=10)

        # Appuyer sur Entrée dans un champ équivaut à cliquer sur "Se connecter"
        self.root.bind("<Return>", lambda event: self.on_enter())

    def build_chat_frame(self):
        """Construit l'écran de discussion : historique, saisie et boutons."""

        self.chat_frame = tk.Frame(self.root, padx=10, pady=10)

        # Zone d'affichage des messages (lecture seule, avec barre de défilement)
        self.chat_area = scrolledtext.ScrolledText(
            self.chat_frame, width=60, height=20, state="disabled", wrap="word")
        self.chat_area.pack(fill="both", expand=True)

        # Ligne du bas : champ de saisie + boutons
        bottom = tk.Frame(self.chat_frame)
        bottom.pack(fill="x", pady=(8, 0))

        self.message_entry = tk.Entry(bottom)
        self.message_entry.pack(side="left", fill="x", expand=True)

        self.send_button = tk.Button(bottom, text="Envoyer", command=self.send_message)
        self.send_button.pack(side="left", padx=(5, 0))

        tk.Button(bottom, text="Quitter", command=self.quit_app).pack(side="left", padx=(5, 0))

    def show_login(self):
        #Affiche l'écran de connexion et cache l'écran de discussion
        self.chat_frame.pack_forget()
        self.login_frame.pack()
        self.username_entry.focus_set()

    def show_chat(self):
        #Affiche l'écran de discussion et cache l'écran de connexion
        self.login_frame.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.message_entry.focus_set()

    def on_enter(self):
        #Réagit à la touche Entrée selon l'écran affiché
        if self.client is None:
            self.connect()
        else:
            self.send_message()

    
    def search_servers(self):
        #AJOUT RECHERCHE AUTOMATIQUE : lance la recherche des serveurs sur le réseau

        # Désactive le bouton pendant la recherche et affiche un message d'attente
        self.search_button.config(state="disabled")
        self.servers_listbox.delete(0, "end")
        self.servers_listbox.insert("end", "Recherche en cours...")

        # La recherche dure quelques secondes : on la fait dans un thread pour ne pas figer la fenêtre
        threading.Thread(target=self.run_search, daemon=True).start()

    def run_search(self):
        
        servers = discover_servers()
        self.messages.put(("servers", servers))

    def on_server_selected(self, event):
       # remplit les champs Serveur et Port avec le serveur choisi dans la liste

        selection = self.servers_listbox.curselection()

        # Ignore le clic si rien n'est sélectionné ou si la liste ne contient qu'un message ("Aucun serveur trouvé")
        if not selection or selection[0] >= len(self.found_servers):
            return

        name, ip, port = self.found_servers[selection[0]]

        self.server_entry.delete(0, "end")
        self.server_entry.insert(0, ip)

        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, str(port))

    def connect(self):
        #Lit les champs de connexion, crée le Client et démarre l'écoute

        username = self.username_entry.get().strip()
        server = self.server_entry.get().strip()

        if not username or not server:
            messagebox.showwarning("Champs manquants", "Le pseudo et le serveur sont obligatoires.")
            return

        # Vérifie que le port saisi est un nombre entier (même contrôle que dans client.py)
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Port invalide", "Le port doit être un nombre entier.")
            return

        try:
            # on_message et on_disconnect sont les "callbacks" ajoutés dans client.py :
            # le Client les appelle quand il recoit un message ou perd la connexion
            self.client = Client(username, server, port,
                                 on_message=self.on_client_message,
                                 on_disconnect=self.on_client_disconnect)
        except OSError as erreur:
            # Le Client relève (raise) l'erreur de connexion : on l'affiche dans une boîte de dialogue
            self.client = None
            messagebox.showerror("Connexion impossible",
                                 "Impossible de se connecter au serveur :\n{0}".format(erreur))
            return

        # Démarre le thread qui reçoit les messages sans bloquer la fenêtre
        self.client.listen()

        self.show_chat()

    def send_message(self):
        #Envoie le texte saisi au serveur

        if self.client is None:
            return

        text = self.message_entry.get().strip()

        if not text:
            return  # on n'envoie pas de message vide

        self.message_entry.delete(0, "end")  # vide le champ de saisie

        if text == "QUIT":
            # Même commande que dans la version console
            self.quit_app()
        else:
            # Le serveur renvoie le message à tous les clients (y compris nous) :
            # il s'affichera donc via on_client_message()
            self.client.send(text)

    def quit_app(self):
        #Se déconnecte proprement du serveur puis ferme la fenêtre

        if self.client is not None and self.client.listening:
            self.client.send("QUIT")  # prévient le serveur du départ
            self.client.tidy_up()  # ferme la socket

        self.root.destroy()



    def on_client_message(self, text):
         # met seulement le texte dans la file

        self.messages.put(("message", text))

    def on_client_disconnect(self):
        #Appelée par le Client quand la connexion est fermée

        self.messages.put(("disconnect", None))

    def check_queue(self):
        ##Vérifie la file toutes les 100 ms et met à jour la fenêtre
        

        while not self.messages.empty():
            kind, text = self.messages.get()

            if kind == "message":
                self.display(text)

            elif kind == "servers":
                # AJOUT RECHERCHE AUTOMATIQUE : résultat de la recherche, text contient la liste des serveurs
                self.found_servers = text
                self.servers_listbox.delete(0, "end")

                for name, ip, port in self.found_servers:
                    # Affiche le nom du serveur (renvoyé par le serveur) avec son adresse
                    self.servers_listbox.insert("end", "{0}  ({1}:{2})".format(name, ip, port))

                if not self.found_servers:
                    self.servers_listbox.insert("end", "Aucun serveur trouvé")

                self.search_button.config(state="normal")  # réactive le bouton de recherche

            elif kind == "disconnect":
                self.display("*** Connexion fermée ***")

                # Désactive la saisie : on ne peut plus envoyer de messages
                self.message_entry.config(state="disabled")
                self.send_button.config(state="disabled")

        # after() reprogramme cette méthode dans 100 ms (boucle sans bloquer Tkinter)
        self.root.after(100, self.check_queue)

    def display(self, text):
        """Ajoute une ligne dans la zone de discussion et défile vers le bas."""

        self.chat_area.config(state="normal")  # il faut déverrouiller la zone pour écrire
        self.chat_area.insert("end", text + "\n")
        self.chat_area.config(state="disabled")  # puis la reverrouiller (lecture seule)
        self.chat_area.see("end")  # fait défiler jusqu'au dernier message


# Point d'entrée du programme avec interface graphique
if __name__ == "__main__":

    root = tk.Tk()  # création de la fenêtre principale
    app = ChatWindow(root)
    root.mainloop()  # boucle principale Tkinter : garde la fenêtre ouverte et réagit aux événements