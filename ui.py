import tkinter as tk
import math
from os import system

FONT = ('Helvetica', '12')

class Window(tk.Frame):
    def __init__(self, master, send_func, quit_func):
        self.user_input = tk.StringVar()
        self.user_input_answer= tk.StringVar()
        self.frame = tk.Frame(master)
        self.frame.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.create_widgets(send_func, quit_func)
        self.waiting = False
        self.question_buttons = []
        self.question_answer = tk.StringVar()
        self.sound = False

    def create_widgets(self, send_func, quit_func):

        for x in range(30):
            tk.Grid.columnconfigure(self.frame, x, weight=1)

        for y in range(40):
            tk.Grid.rowconfigure(self.frame, y, weight=1)

        self.chat_box = tk.Text(master=self.frame)
        self.chat_box.grid(column=0, row=0, columnspan=15, rowspan=30, sticky=tk.N+tk.S+tk.E+tk.W)
        self.chat_box.configure(state='disabled')
        self.chat_box.config({"background": "light grey"})

        self.user_textbox = tk.Entry(master=self.frame, textvariable=self.user_input, font=FONT)
        self.user_textbox.grid(column=3, row=32, columnspan=9, rowspan=2, sticky=tk.N+tk.S+tk.E+tk.W)
        self.user_textbox.bind('<Return>', (lambda event: self.send_message(send_func)))

        self.send_btn = tk.Button(master=self.frame, text="Send", command= lambda: self.send_message(send_func))
        self.send_btn.grid(column=3, row=34, columnspan=5, rowspan=1, sticky=tk.N+tk.S+tk.E+tk.W)

        self.play_btn = tk.Button(master=self.frame, text="Sound off", command= lambda: self.switch_sound())
        self.play_btn.grid(column=8, row=34, columnspan=4, rowspan=1, sticky=tk.N+tk.S+tk.E+tk.W)

        self.quit = tk.Button(master=self.frame, text="QUIT", fg="red",
                              command=quit_func)
        self.quit.grid(column=5, row=35, columnspan=5, rowspan=1, sticky=tk.N+tk.S+tk.E+tk.W)

        self.dic_label = tk.Label(master=self.frame, text="Dictionary", font = "Helvetica 16 bold")
        self.dic_label.grid(column=16, row=0, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)

        self.def_label = tk.Label(master=self.frame, text="Definitions", font = "Helvetica 14 bold")
        self.def_label.grid(column=16, row=1, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)

        self.reading_label = tk.Label(master=self.frame, text="Reading", font = "Helvetica 14 bold")
        self.reading_label.grid(column=16, row=7, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)

        self.type_label = tk.Label(master=self.frame, text="Word type", font = "Helvetica 14 bold")
        self.type_label.grid(column=16, row=13, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)

        self.question_label = tk.Label(master=self.frame, text="Question", font = "Helvetica 14 bold")
        self.question_label.grid(column=16, row=20, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)

        self.def_label_arr = []
        self.reading_label_arr = []
        self.type_label_arr = []
        for i in range(5):
            self.def_label_arr.append(tk.Label(master=self.frame, text=""))
            self.def_label_arr[-1].grid(column=16, row=2+i, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)
            self.reading_label_arr.append(tk.Label(master=self.frame, text=""))
            self.reading_label_arr[-1].grid(column=16, row=8+i, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)
            self.type_label_arr.append(tk.Label(master=self.frame, text=""))
            self.type_label_arr[-1].grid(column=16, row=14+i, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)
        

    def send_message(self, ex_func):
            msg_in = self.user_input.get()
            self.user_input.set("")
            self.chat_box.configure(state='normal')
            self.chat_box.insert('end', "\n"+"You: " + msg_in)
            if not self.waiting:
                response = "Bot: " + str(ex_func(msg_in))
                self.chat_box.insert('end', "\n"+response)
                start = self.chat_box.index("1.0+%d chars" % (len(self.chat_box.get("1.0",tk.END))-len(response)-1))
                end = self.chat_box.index("1.0+%d chars" % (len(self.chat_box.get("1.0",tk.END))-1))
                self.chat_box.tag_add('color', start, end) 
                self.chat_box.tag_configure('color',foreground="dark slate blue")
                self.chat_box.configure(state='disabled')
            else:
                self.user_input_answer.set(msg_in)

    def add_reply(self, msg, wait=False):
        self.waiting = wait
        self.chat_box.configure(state='normal')
        message = "Bot: " + msg
        self.chat_box.insert('end', "\n"+str(message))
        start = self.chat_box.index("1.0+%d chars" % (len(self.chat_box.get("1.0",tk.END))-len(message)-1))
        end = self.chat_box.index("1.0+%d chars" % (len(self.chat_box.get("1.0",tk.END))-1))
        self.chat_box.tag_add('color', start, end) 
        self.chat_box.tag_configure('color',foreground="dark slate blue")
        self.chat_box.configure(state='disabled')

        if self.sound:
            self.play_sound(msg)

        if wait:
            self.user_textbox.wait_variable(self.user_input_answer)
            msg = self.user_input_answer.get()
            self.user_input_answer.set("")
            return msg
        return None

    def update_dict(self, result):
        for i in range(5):
            self.def_label_arr[i].config(text=(result.definitions[i] if i < len(result.definitions) else ""))
            self.reading_label_arr[i].config(text=(result.readings[i] if i < len(result.readings) else ""))
            self.type_label_arr[i].config(text=(result.types[i] if i < len(result.types) else ""))


    def ask(self, msg, answers):
        self.waiting = True

        question_label = tk.Label(master=self.frame, text=msg)
        question_label.grid(column=16, row=21, columnspan = 8, sticky=tk.N+tk.S+tk.E+tk.W)

        for a in answers:
            self.question_buttons.append(tk.Button(master=self.frame, text=a, command=lambda a=a: self.question_answer.set(a)))
            self.question_buttons[-1].grid(column=16+(len(self.question_buttons)%4)*2, row=21+math.ceil(len(self.question_buttons)/4), sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.question_buttons[0].wait_variable(self.question_answer)
        
        for btn in self.question_buttons:
            btn.grid_remove()

        question_label.grid_remove()
        self.question_buttons = []

        answer = self.question_answer.get()
        self.question_answer.set("")
        print(answer)
        return answer

    def switch_sound(self):
        self.sound = self.sound == False
        self.play_btn.config(text=("Sound on" if self.sound else "Sound off"))


    def play_sound(self, msg):
        
        system(f'say {msg}')

