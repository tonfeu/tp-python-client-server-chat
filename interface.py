
import tkinter as tk

from tkinter import messagebox
from client import Client
print("1 - Interface.py est exécuté")

class ChatInterface:

    def __init__(self, root):

        self.root = root
        self.root.title("Chat TCP")
        self.root.geometry("420x550")
        self.root.resizable(False, False)
        self.root.configure(bg="#111827")

        self.client = None
        self.checking_messages = False

        self.create_login_window()

    # -------------------------
    # FENÊTRE DE CONNEXION
    # -------------------------

    def create_login_window(self):

        self.clear_window()

        title = tk.Label(
            self.root,
            text="CHAT TCP",
            font=("Arial", 25, "bold"),
            fg="white",
            bg="#111827"
        )
        title.pack(pady=35)

        subtitle = tk.Label(
            self.root,
            text="Connecte-toi au serveur",
            font=("Arial", 12),
            fg="#9CA3AF",
            bg="#111827"
        )
        subtitle.pack(pady=5)

        self.username_entry = self.create_entry(
            "Nom d'utilisateur"
        )

        self.host_entry = self.create_entry(
            "Adresse IP du serveur"
        )
        self.host_entry.insert(0, "127.0.0.1")

        self.port_entry = self.create_entry(
            "Port du serveur"
        )
        self.port_entry.insert(0, "59001")

        connect_button = tk.Button(
            self.root,
            text="SE CONNECTER",
            font=("Arial", 12, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.connect
        )
        connect_button.pack(
            pady=25,
            ipadx=35,
            ipady=10
        )

    def create_entry(self, placeholder):

        entry = tk.Entry(
            self.root,
            font=("Arial", 12),
            bg="#1F2937",
            fg="white",
            insertbackground="white",
            relief="flat",
            justify="center"
        )

        entry.pack(
            pady=10,
            ipady=10,
            ipadx=15
        )

        entry.insert(0, placeholder)

        entry.bind(
            "<FocusIn>",
            lambda event: self.clear_placeholder(
                entry,
                placeholder
            )
        )

        return entry

    def clear_placeholder(self, entry, placeholder):

        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    # -------------------------
    # CONNEXION AU SERVEUR
    # -------------------------

    def connect(self):

        username = self.username_entry.get().strip()
        host = self.host_entry.get().strip()
        port_text = self.port_entry.get().strip()

        if not username or not host or not port_text:

            messagebox.showwarning(
                "Champs manquants",
                "Veuillez remplir tous les champs."
            )
            return

        try:

            port = int(port_text)

            if not 1 <= port <= 65535:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Erreur",
                "Le port doit être un nombre entre 1 et 65535."
            )
            return

        try:

            # Création du client et connexion automatique
            self.client = Client(
                username,
                host,
                port
            )

            # Démarrage du thread de réception
            self.client.listen()

            # Affichage de la fenêtre de discussion
            self.create_chat_window()

        except OSError as error:

            self.client = None

            messagebox.showerror(
                "Erreur de connexion",
                "Impossible de se connecter au serveur.\n\n{0}".format(
                    error
                )
            )

    # -------------------------
    # FENÊTRE DE CHAT
    # -------------------------

    def create_chat_window(self):

        self.clear_window()

        header = tk.Frame(
            self.root,
            bg="#1F2937",
            height=65
        )
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="Chat TCP",
            font=("Arial", 17, "bold"),
            fg="white",
            bg="#1F2937"
        )
        title.pack(
            side="left",
            padx=15,
            pady=15
        )

        disconnect_button = tk.Button(
            header,
            text="Déconnexion",
            font=("Arial", 9),
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.disconnect
        )
        disconnect_button.pack(
            side="right",
            padx=10,
            pady=15
        )

        self.messages_frame = tk.Frame(
            self.root,
            bg="#111827"
        )

        self.messages_frame.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        self.messages = tk.Text(
            self.messages_frame,
            bg="#1F2937",
            fg="white",
            font=("Arial", 11),
            relief="flat",
            wrap="word",
            state="disabled",
            padx=10,
            pady=10
        )

        self.messages.pack(
            fill="both",
            expand=True
        )

        self.messages.tag_config(
            "system",
            foreground="#9CA3AF"
        )

        self.messages.tag_config(
            "message",
            foreground="#FFFFFF"
        )

        input_frame = tk.Frame(
            self.root,
            bg="#111827"
        )

        input_frame.pack(
            fill="x",
            padx=12,
            pady=12
        )

        self.message_entry = tk.Entry(
            input_frame,
            font=("Arial", 11),
            bg="#1F2937",
            fg="white",
            insertbackground="white",
            relief="flat"
        )

        self.message_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=12,
            padx=(0, 8)
        )

        self.message_entry.bind(
            "<Return>",
            lambda event: self.send_message()
        )

        send_button = tk.Button(
            input_frame,
            text="Envoyer",
            font=("Arial", 10, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.send_message
        )

        send_button.pack(
            side="right",
            ipadx=10,
            ipady=8
        )

        self.add_message(
            "Connecté au serveur.",
            "system"
        )

        # Vérification régulière des nouveaux messages
        self.check_messages()

    # -------------------------
    # ENVOI D'UN MESSAGE
    # -------------------------

    def send_message(self):

        message = self.message_entry.get().strip()

        if not message:
            return

        if self.client is None or not self.client.listening:

            messagebox.showwarning(
                "Déconnecté",
                "Vous n'êtes plus connecté au serveur."
            )
            return

        self.client.send(message)

        if self.client.listening:
            self.message_entry.delete(0, tk.END)

    # -------------------------
    # AFFICHAGE DES MESSAGES
    # -------------------------

    def add_message(self, message, tag="message"):

        self.messages.config(state="normal")

        self.messages.insert(
            tk.END,
            message + "\n",
            tag
        )

        self.messages.see(tk.END)

        self.messages.config(state="disabled")

    def check_messages(self):

        if self.client is None:
            self.checking_messages = False
            return

        try:

            while not self.client.message_queue.empty():

                message = self.client.message_queue.get_nowait()

                self.add_message(message)

        except Exception as error:

            print("Erreur de réception :", error)

        if self.client is not None and self.client.listening:

            self.root.after(
                100,
                self.check_messages
            )

        else:

            self.checking_messages = False

    # -------------------------
    # DÉCONNEXION
    # -------------------------

    def disconnect(self):

        if self.client is not None:

            try:

                if self.client.listening:
                    self.client.send("QUIT")

                self.client.tidy_up()

            except Exception as error:

                print(
                    "Erreur pendant la déconnexion :",
                    error
                )

            self.client = None

        self.create_login_window()

    # -------------------------
    # FERMETURE DE L'APPLICATION
    # -------------------------

    def close_app(self):

        if self.client is not None:

            try:

                if self.client.listening:
                    self.client.send("QUIT")

                self.client.tidy_up()

            except Exception as error:

                print(
                    "Erreur pendant la fermeture :",
                    error
                )

        self.root.destroy()

    # -------------------------
    # NETTOYAGE DE LA FENÊTRE
    # -------------------------

    def clear_window(self):

        for widget in self.root.winfo_children():
            widget.destroy()


# -------------------------
# LANCEMENT DE L'APPLICATION
# -------------------------

if __name__ == "__main__":

    root = tk.Tk()

    app = ChatInterface(root)

    root.protocol(
        "WM_DELETE_WINDOW",
        app.close_app
    )

    root.mainloop()
    """
if __name__ == "__main__":

    print("2 - Entrée dans le programme principal")

    root = tk.Tk()

    print("3 - Fenêtre Tkinter créée")

    app = ChatInterface(root)

    print("4 - Interface créée")

    root.protocol("WM_DELETE_WINDOW", app.close_app)

    print("5 - Lancement de mainloop")

    root.mainloop()"""
