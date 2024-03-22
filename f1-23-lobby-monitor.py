import tkinter as tk
from tkinter import ttk
import csv
from telemetry_manager import F12023TelemetryManager
import threading
from threading import Lock
from f1_types import *


class LobbyInfo:
    def __init__(self):

        self.m_lock: Lock = Lock()
        self.m_lobby_info: PacketLobbyInfoData = None

    def update(self, packet: PacketLobbyInfoData) -> None:

        with self.m_lock:

            self.m_lobby_info = packet

    def dumpToFile(self, file_name: str) -> str:

        return f"Data dumped to {file_name}"

    def getDataList(self) -> List[Any]:

        if self.m_lobby_info is None:
            return []
        if len(self.m_lobby_info.m_lobbyPlayers) == 0:
            return []
        ret_list = []
        for index, player in enumerate(self.m_lobby_info.m_lobbyPlayers):
            ret_list.append([
                index,
                player.m_name,
                str(player.m_teamId),
                str(player.m_aiControlled),
                str(player.m_nationality),
                str(player.m_platform),
                str(player.m_carNumber),
                str(player.m_readyStatus)
            ])
        return ret_list
g_lobby_info_data_table = LobbyInfo()

def lobbyInfoDataCallback(packet: PacketLobbyInfoData) -> None:

    global g_lobby_info_data_table
    g_lobby_info_data_table.update(packet)

def f1TelemetryThread(
    port_number: int) -> None:
    """Entry point to start the F1 23 telemetry client.

    Args:
        port_number (int): Port number for the telemetry client.
    """

    telemetry_manager = F12023TelemetryManager(port_number)
    telemetry_manager.registerCallback(F1PacketType.LOBBY_INFO, lobbyInfoDataCallback)

    telemetry_manager.run()

class TableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Data Table")

        self.table_frame = ttk.Frame(root)
        self.table_frame.grid(row=0, column=0, sticky="nsew")

        # Create a table
        self.tree = ttk.Treeview(self.table_frame, columns=(
            "Index",
            "Name",
            "Team",
            "Is AI",
            "Nationality",
            "Platform",
            "Number",
            "Status"), show="headings")
        self.tree.heading("Index", text="Index")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Team", text="Team")
        self.tree.heading("Is AI", text="Is AI")
        self.tree.heading("Platform", text="Platform")
        self.tree.heading("Nationality", text="Nationality")
        self.tree.heading("Number", text="Number")
        self.tree.heading("Status", text="Status")
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Create a scroll bar
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Set scrollbar to treeview
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Center all columns
        for column in ("Index", "Name", "Team", "Is AI", "Nationality", "Platform", "Number", "Status"):
            self.tree.column(column, anchor="center")

        # Create a button to dump data to a file
        self.dump_button = ttk.Button(root, text="Dump to File", command=self.dump_data)
        self.dump_button.grid(row=1, column=0, sticky="ew")

        # Create a label to display status
        self.status_label = ttk.Label(root, text="")
        self.status_label.grid(row=2, column=0, sticky="ew")

        # Create a label to display messages
        self.message_label = ttk.Label(root, text="")
        self.message_label.grid(row=3, column=0, sticky="ew")

        # Configure resizing behavior
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=0)
        root.grid_rowconfigure(2, weight=0)
        root.grid_rowconfigure(3, weight=0)
        root.grid_columnconfigure(0, weight=1)

        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # Start updating table with live data
        self.update_table()

    def update_table(self):
        """
        Update the table with the provided data.

        Args:
            data (list): A 2D list containing data to populate the table.
                        Each inner list represents a row in the table with attributes in the order:
                        [Index, Name, Team, Platform, Number, Status]
        """

        global g_lobby_info_data_table
        table_data = g_lobby_info_data_table.getDataList()

        # Clear any previous error message
        self.message_label.config(text="")

        # Clear previous data
        self.tree.delete(*self.tree.get_children())

        # Insert new data into the table
        for row in table_data:
            self.tree.insert("", "end", values=row)

        # Schedule next update after 1 second
        self.root.after(1000, self.update_table)

    def dump_data(self):
        # In a real scenario, you would dump actual data to a file
        # For demonstration purposes, let's create a CSV file with the current data
        global g_lobby_info_data_table
        file_name = 'test.json'
        status_message = g_lobby_info_data_table.dumpToFile(file_name)
        self.status_label.config(text=status_message)
        return status_message, file_name

if __name__ == "__main__":

    # First init the telemetry client on a main thread
    port_number=20777
    client_thread = threading.Thread(target=f1TelemetryThread,
                                    args=(port_number,))
    client_thread.daemon = True
    client_thread.start()

    root = tk.Tk()
    app = TableApp(root)
    root.mainloop()
