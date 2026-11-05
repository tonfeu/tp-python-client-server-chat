import tkinter as tk
from tkinter import messagebox
from client import Client


class ChatInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat TCP")
        self.root.geometry("420x550")
        self.root.minsize(350, 450)
        self.root.configure(bg="#111827")

        self.client = None
        self.polling = False

        self.create_login_window()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_entry(self, placeholder):
        entry = tk.Entry(
            self.root, font=("Arial", 12), bg="#1F2937", fg="white",
            insertbackground="white", relief="flat", justify="center"
        )
        entry.pack(pady=10, ipady=10, ipadx=15)
        entry.insert(0, placeholder)

        def clear_placeholder(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)

        entry.bind("<FocusIn>", clear_placeholder)
        return entry

    def create_login_window(self):
        self.clear_window()

        tk.Label(
            self.root, text="CHAT TCP", font=("Arial", 25, "bold"),
            fg="white", bg="#111827"
        ).pack(pady=(45, 10))

        tk.Label(
            self.root, text="Connecte-toi au serveur",
            font=("Arial", 12), fg="#9CA3AF", bg="#111827"
        ).pack(pady=5)

        self.username_entry = self.create_entry("Nom d'utilisateur")
        self.host_entry = self.create_entry("Adresse IP du serveur")
        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, "127.0.0.1")

        self.port_entry = self.create_entry("Port du serveur")
        self.port_entry.delete(0, tk.END)
        self.port_entry.insert(0, "59001")

        tk.Button(
            self.root, text="SE CONNECTER", font=("Arial", 12, "bold"),
            bg="#2563EB", fg="white", activebackground="#1D4ED8",
            relief="flat", cursor="hand2", command=self.connect
        ).pack(pady=25, ipadx=35, ipady=10)

    def connect(self):
        username = self.username_entry.get().strip()
        host = self.host_entry.get().strip()
        port_text = self.port_entry.get().strip()

        if not username or username == "Nom d'utilisateur" or not host:
            messagebox.showwarning("Champs manquants", "Veuillez remplir tous les champs.")
            return

        try:
            port = int(port_text)
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit être compris entre 1 et 65535.")
            return

        try:
            self.client = Client(username, host, port)
            self.client.listen()
            self.create_chat_window()
        except OSError as error:
            self.client = None
            messagebox.showerror(
                "Erreur de connexion",
                f"Impossible de se connecter au serveur.\n\n{error}"
            )

    def create_chat_window(self):
        self.clear_window()

        header = tk.Frame(self.root, bg="#1F2937", height=65)
        header.pack(fill="x")

        tk.Label(
            header, text=f"Chat TCP — {self.client.username}",
            font=("Arial", 15, "bold"), fg="white", bg="#1F2937"
        ).pack(side="left", padx=12, pady=15)

        tk.Button(
            header, text="Déconnexion", font=("Arial", 9),
            bg="#DC2626", fg="white", relief="flat",
            cursor="hand2", command=self.disconnect
        ).pack(side="right", padx=10, pady=15)

        messages_frame = tk.Frame(self.root, bg="#111827")
        messages_frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.messages = tk.Text(
            messages_frame, bg="#1F2937", fg="white",
            font=("Arial", 11), relief="flat", wrap="word",
            state="disabled", padx=10, pady=10
        )
        self.messages.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(messages_frame, command=self.messages.yview)
        scrollbar.pack(side="right", fill="y")
        self.messages.configure(yscrollcommand=scrollbar.set)

        self.messages.tag_config("system", foreground="#9CA3AF")
        self.messages.tag_config("message", foreground="#FFFFFF")

        input_frame = tk.Frame(self.root, bg="#111827")
        input_frame.pack(fill="x", padx=12, pady=12)

        self.message_entry = tk.Entry(
            input_frame, font=("Arial", 11), bg="#1F2937",
            fg="white", insertbackground="white", relief="flat"
        )
        self.message_entry.pack(
            side="left", fill="x", expand=True, ipady=12, padx=(0, 8)
        )
        self.message_entry.bind("<Return>", self.send_message)

        tk.Button(
            input_frame, text="Envoyer", font=("Arial", 10, "bold"),
            bg="#2563EB", fg="white", relief="flat",
            cursor="hand2", command=self.send_message
        ).pack(side="right", ipadx=10, ipady=8)

        self.add_message("Connecté au serveur.", "system")
        self.message_entry.focus_set()
        self.polling = True
        self.check_messages()

    def send_message(self, event=None):
        message = self.message_entry.get().strip()
        if not message:
            return

        if self.client is None or not self.client.listening:
            messagebox.showwarning("Déconnecté", "Vous n'êtes plus connecté au serveur.")
            return

        if self.client.send(message):
            self.message_entry.delete(0, tk.END)

    def add_message(self, message, tag="message"):
        self.messages.configure(state="normal")
        self.messages.insert(tk.END, message + "\n", tag)
        self.messages.see(tk.END)
        self.messages.configure(state="disabled")

    def check_messages(self):
        """Récupère les messages de la file depuis le thread Tkinter."""
        if not self.polling:
            return

        if self.client is not None:
            while not self.client.message_queue.empty():
                try:
                    message = self.client.message_queue.get_nowait()
                    self.add_message(message, "system" if message.startswith("ℹ️") else "message")
                except Exception:
                    break

            if not self.client.listening:
                self.add_message("Connexion terminée.", "system")
                self.polling = False
                self.client = None
                self.root.after(800, self.create_login_window)
                return

        self.root.after(100, self.check_messages)

    def disconnect(self):
        self.polling = False
        if self.client is not None:
            if self.client.listening:
                self.client.send("QUIT")
            self.client.tidy_up()
            self.client = None
        self.create_login_window()

    def close_app(self):
        self.polling = False
        if self.client is not None:
            if self.client.listening:
                self.client.send("QUIT")
            self.client.tidy_up()
            self.client = None
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatInterface(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()
