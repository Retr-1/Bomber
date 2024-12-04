import tkinter as tk
from tkinter import ttk
import constatnts

class Subprogram:
    def __init__(self, master):
        self.frame = tk.Frame(master=master)

class RangePicker(Subprogram):
    def __init__(self, master, label_text, min, max):
        super().__init__(master)
        self.min = min
        self.max = max
        self.left_btn = tk.Button(master=self.frame, text='-', command=lambda: self.add(-1))
        self.right_btn = tk.Button(master=self.frame, text='+', command=lambda: self.add(1))
        self.count = min
        self.count_label = tk.Label(master=self.frame, text=f'{self.count}')
        self.label = tk.Label(master=self.frame, text=label_text)
        
        self.label.pack(side=tk.LEFT)
        self.left_btn.pack(side=tk.LEFT)
        self.count_label.pack(side=tk.LEFT)
        self.right_btn.pack(side=tk.LEFT)      

    def add(self, x):
        if self.min <= self.count+x <= self.max:
            self.count += x
            self.count_label.configure(text=f'{self.count}')

class LevelEditor(Subprogram):
    def __init__(self, master, size, blocksize):
        super().__init__(master)
        self.blocksize = blocksize
        self.size = size
        self.n_blocks = self.size//self.blocksize
        self.canvas = tk.Canvas(master=self.frame, width=size, height=size)
        self.toolbar = tk.Frame(master=self.frame)
        self.load_btn = tk.Button(master=self.toolbar, text='Load Map')
        self.save_btn = tk.Button(master=self.toolbar, text='Save Map')
        self.placing_frame = tk.Frame(master=self.frame)
        combo_label = tk.Label(master=self.placing_frame, text='Placing: ')
        self.placing = tk.StringVar()
        self.placing_combo = ttk.Combobox(master=self.placing_frame, values=constatnts.BLOCK_NAMES, textvariable=self.placing, state='readonly')
        self.placing_combo.current(0)
        self.placing_combo.bind('<<ComboboxSelected>>', lambda x: print(x, self.placing.get()))

        self.toolbar.grid(row=0, column=0, sticky='w')
        self.load_btn.pack(side=tk.LEFT)
        self.save_btn.pack(side=tk.LEFT)
        self.canvas.grid(row=1, column=0)
        self.placing_frame.grid(row=2, column=0)
        combo_label.pack(side=tk.LEFT)
        self.placing_combo.pack(side=tk.LEFT)

        self.draw_grid()

    def draw_grid(self):
        for y in range(0, self.size, self.blocksize):
            self.canvas.create_line(0,y,self.size,y)
        
        for x in range(0, self.size, self.blocksize):
            self.canvas.create_line(x,0,x,self.size)


    def save(self):
        pass




class Program:
    def __init__(self):
        self.window = tk.Tk()
        
        self.menu_frame = tk.Frame(master=self.window)
        self.menu_btn_play = tk.Button(master=self.menu_frame, text='Play', font='Helvetica 32', command=self.from_menu_to_level_select)
        self.menu_btn_editor = tk.Button(master=self.menu_frame,text='Level Editor', font='Helvetica 32', command=self.from_menu_to_editor)

        self.menu_btn_play.grid(row=0, column=0, sticky='nswe')
        self.menu_btn_editor.grid(row=1, column=0, sticky='nswe')

        
        self.level_selector_frame = tk.Frame(master=self.window)
        self.level_selector_lvl_label = tk.Label(master=self.level_selector_frame, text='Select Level: ')
        self.level_selector_n = tk.StringVar()
        self.level_selector_lvl_combox = ttk.Combobox(master=self.level_selector_frame, textvariable=self.level_selector_n, state='readonly')
        self.level_selector_lvl_combox['values'] = ('A*', 'Center', 'Stars')
        self.level_selector_lvl_combox.current(0)
        self.level_selector_human_count = RangePicker(self.level_selector_frame, 'Number of Players: ', 0, 10)
        self.level_selector_bot_count = RangePicker(self.level_selector_frame, 'Number of Bots: ', 0, 10)
        self.level_selector_play_btn = tk.Button(master=self.level_selector_frame, text='Start the game', command=self.start_game)
        self.level_selector_menu_btn = tk.Button(master=self.level_selector_frame, text='Back to menu', command=self.from_level_select_to_menu)

        self.level_selector_lvl_label.grid(row=0, column=0)
        self.level_selector_lvl_combox.grid(row=0, column=1)
        self.level_selector_human_count.frame.grid(row=1, column=0, columnspan=2)
        self.level_selector_bot_count.frame.grid(row=2, column=0, columnspan=2)
        self.level_selector_menu_btn.grid(row=3, column=0, sticky='nswe')
        self.level_selector_play_btn.grid(row=3, column=1, sticky='nswe')


        self.level_editor = LevelEditor(self.window, 800, 40)


        self.menu_frame.pack()

    def from_menu_to_level_select(self):
        self.menu_frame.pack_forget()
        self.level_selector_frame.pack()

    def start_game(self):
        pass

    def from_level_select_to_menu(self):
        self.level_selector_frame.pack_forget()
        self.menu_frame.pack()

    def from_menu_to_editor(self):
        self.menu_frame.pack_forget()
        self.level_editor.frame.pack()

if __name__ == '__main__':
    p = Program()
    tk.mainloop()
        
