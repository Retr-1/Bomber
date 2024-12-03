import tkinter as tk


class Program:
    def __init__(self):
        self.window = tk.Tk()
        
        self.menu_frame = tk.Frame(master=self.window)
        self.menu_btn_play = tk.Button(master=self.menu_frame, text='Play', font='32 Helvetica')
        self.menu_btn_editor = tk.Button(master=self.menu_frame,text='Level Editor', font='32 Helvetica')
        self.menu_btn_play.pack()
        self.menu_btn_editor.pack()

        self.menu_frame.pack()
        