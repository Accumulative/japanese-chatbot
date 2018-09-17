# GREETINGS = ["こんにちは", "はい"]

from bot import Bot
from ui import Window
import tkinter as tk

def send_message(msg_in):
    return thebot.respond(msg_in)

def exit_program():
    # thebot.manager.save()
    raise SystemExit()
    

root = tk.Tk()
tk.Grid.rowconfigure(root, 0, weight=1)
tk.Grid.columnconfigure(root, 0, weight=1)
app = Window(root, send_message, exit_program)
thebot = Bot(app.add_reply, app.ask, app.update_dict)

root.mainloop()