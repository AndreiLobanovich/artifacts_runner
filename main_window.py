import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from character.Tasks import TMPCharacter, GatherTask, CraftingTask, FightTask, DepositTask, RetrieveFromBankTask
from dotenv import load_dotenv, set_key
import os

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
CHARACTER_NAME = os.getenv("CHARACTER_NAME")

def save_config(api_token, character_name):
    with open(".env", "w") as f:
        f.write(f"API_TOKEN={api_token}\n")
        f.write(f"CHARACTER_NAME={character_name}\n")

def update_api_token_and_name(api_token, character_name):
    global API_TOKEN
    global CHARACTER_NAME
    API_TOKEN = api_token
    CHARACTER_NAME = character_name

def get_all_items():
    return [
        "iron_ore",
        "iron_sword",
        "iron",
        "wood",
        "gold",
        "diamond",
    ]

class TaskScheduler:
    def __init__(self, character_name):
        self.character = TMPCharacter(name=character_name, weapon=None, tool=None)
        self.tasks = []
        self.running = False
        self.task_loop = None

    def add_task(self, task_type, *args):
        if task_type == "Gather":
            self.tasks.append(GatherTask(self.character, *args))
        elif task_type == "Craft":
            self.tasks.append(CraftingTask(self.character, *args))
        elif task_type == "Fight":
            self.tasks.append(FightTask(self.character, *args))
        elif task_type == "Deposit":
            self.tasks.append(DepositTask(self.character, *args))
        elif task_type == "Retrieve":
            self.tasks.append(RetrieveFromBankTask(self.character, **dict(args)))
        else:
            messagebox.showerror("Task Error", "Unknown task type.")

    def start_tasks(self):
        if self.running:
            return
        self.running = True
        self.task_loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.run_tasks())
        threading.Thread(target=self.task_loop.run_forever).start()

    async def run_tasks(self):
        while self.tasks and self.running:
            task = self.tasks.pop(0)
            try:
                await task()
            except Exception as e:
                messagebox.showerror("Task Error", f"An error occurred: {e}")
        self.running = False

    def stop_tasks(self):
        self.running = False

def start_tasks():
    scheduler.start_tasks()

def stop_tasks():
    scheduler.stop_tasks()

def add_task():
    task_type = task_type_var.get()
    item = item_combobox.get()
    try:
        quantity = int(quantity_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid quantity.")
        return

    if not item:
        messagebox.showerror("Input Error", "Please select an item.")
        return

    params = (item, quantity)
    if task_type in ["Gather", "Craft"]:
        scheduler.add_task(task_type, *params)
    elif task_type == "Deposit" or task_type == "Retrieve":
        scheduler.add_task(task_type, item=item, quantity=quantity)
    else:
        messagebox.showerror("Task Error", "Unsupported task type.")

def update_task_options(*args):
    task_type = task_type_var.get()
    item_combobox.set("")
    quantity_entry.delete(0, tk.END)

    if task_type in ["Gather", "Craft", "Fight"]:
        item_combobox['values'] = get_all_items()
        item_combobox['state'] = 'normal'
        quantity_label.grid(row=2, column=0, padx=10, pady=5)
        quantity_entry.grid(row=2, column=1, padx=10, pady=5)
    elif task_type == "Deposit" or task_type == "Retrieve":
        item_combobox['values'] = get_all_items()
        item_combobox['state'] = 'normal'
        quantity_label.grid_forget()
        quantity_entry.grid_forget()
    else:
        item_combobox['values'] = []
        item_combobox['state'] = 'disabled'

def save_settings():
    api_token = api_token_entry.get()
    character_name = character_name_entry.get()
    if not api_token or not character_name:
        messagebox.showerror("Input Error", "Please enter both API Token and Character Name.")
        return
    save_config(api_token, character_name)
    update_api_token_and_name(api_token, character_name)
    messagebox.showinfo("Settings", "Configuration saved successfully.")
    global scheduler
    scheduler = TaskScheduler(character_name=character_name)

root = tk.Tk()
root.title("Task Scheduler")

settings_frame = ttk.LabelFrame(root, text="Settings")
settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

api_token_label = ttk.Label(settings_frame, text="API Token:")
api_token_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

api_token_entry = ttk.Entry(settings_frame)
api_token_entry.grid(row=0, column=1, padx=5, pady=5)

character_name_label = ttk.Label(settings_frame, text="Character Name:")
character_name_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

character_name_entry = ttk.Entry(settings_frame)
character_name_entry.grid(row=1, column=1, padx=5, pady=5)

save_button = ttk.Button(settings_frame, text="Save Settings", command=save_settings)
save_button.grid(row=2, column=0, columnspan=2, pady=10)

task_type_var = tk.StringVar()
task_type_var.set("Gather")
task_type_var.trace_add("write", update_task_options)

task_type_frame = ttk.LabelFrame(root, text="Task Type")
task_type_frame.grid(row=1, column=0, padx=10, pady=10)

gather_rb = ttk.Radiobutton(task_type_frame, text="Gather", variable=task_type_var, value="Gather")
gather_rb.grid(row=0, column=0, padx=5, pady=5)

craft_rb = ttk.Radiobutton(task_type_frame, text="Craft", variable=task_type_var, value="Craft")
craft_rb.grid(row=1, column=0, padx=5, pady=5)

fight_rb = ttk.Radiobutton(task_type_frame, text="Fight", variable=task_type_var, value="Fight")
fight_rb.grid(row=2, column=0, padx=5, pady=5)

deposit_rb = ttk.Radiobutton(task_type_frame, text="Deposit", variable=task_type_var, value="Deposit")
deposit_rb.grid(row=3, column=0, padx=5, pady=5)

retrieve_rb = ttk.Radiobutton(task_type_frame, text="Retrieve", variable=task_type_var, value="Retrieve")
retrieve_rb.grid(row=4, column=0, padx=5, pady=5)

item_label = ttk.Label(root, text="Item:")
item_label.grid(row=2, column=0, padx=10, pady=5)

item_combobox = ttk.Combobox(root, values=get_all_items())
item_combobox.grid(row=2, column=1, padx=10, pady=5)
item_combobox.set("Select item")

quantity_label = ttk.Label(root, text="Quantity:")
quantity_label.grid(row=3, column=0, padx=10, pady=5)

quantity_entry = ttk.Entry(root)
quantity_entry.grid(row=3, column=1, padx=10, pady=5)

add_task_button = ttk.Button(root, text="Add Task", command=add_task)
add_task_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

start_button = ttk.Button(root, text="Start", command=start_tasks)
start_button.grid(row=5, column=0, padx=10, pady=10)

stop_button = ttk.Button(root, text="Stop", command=stop_tasks)
stop_button.grid(row=5, column=1, padx=10, pady=10)

scheduler = TaskScheduler(character_name=CHARACTER_NAME)

root.mainloop()
