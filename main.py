import tkinter as tk
from tkinter import ttk
import constants
from PIL import Image, ImageTk
from tkinter.filedialog import asksaveasfile, askopenfile
import spritesheeter
import random

def resize(image, width, height):
    if width is None and height is None:
        raise Exception('Both dimensions are None')
    
    aspect_ratio = image.width / image.height
    
    if width is None:
        return image.resize((int(height*aspect_ratio), height))
    if height is None:
        return image.resize((width, int(width/aspect_ratio)))
    return image.resize((width,height))

def resize_to_fit(image, width, height):
    if image.height > image.width:
        return resize(image, None, height)
    return resize(image, width, None)

def load_image(filepath, width=None, height=None):
    return resize(Image.open(filepath), width, height)

def load_sprite(blocksize, sprite_filepath):
    image = resize_to_fit(Image.open(sprite_filepath), blocksize, blocksize)
    sprite = ImageTk.PhotoImage(image) 
    return sprite

def tint_image(image, color):
    r,g,b,a = image.split()
    factor = 0.6
    
    if color == constants.RED:
        g = Image.eval(g, lambda x: x*factor)
        b = Image.eval(b, lambda x: x*factor)
        return Image.merge('RGBA', (r,g,b,a))
    elif color == constants.GREEN:
        r = Image.eval(r, lambda x: x*factor)
        b = Image.eval(b, lambda x: x*factor)
        return Image.merge('RGBA', (r,g,b,a))
    elif color == constants.BLUE:
        g = Image.eval(g, lambda x: x*factor)
        r = Image.eval(r, lambda x: x*factor)
        return Image.merge('RGBA', (r,g,b,a))
    elif color == constants.YELLOW:
        b = Image.eval(b, lambda x: x*factor)
        return Image.merge('RGBA', (r,g,b,a))



class Player:
    LOOKING_DOWN = 0
    LOOKING_UP = 1
    LOOKING_LEFT  = 2
    LOOKING_RIGHT = 3

    SPRITESHEET = spritesheeter.split('assets/player.png')

    def __init__(self, blocksize, color, bot, canvas_x, canvas_y):
        def convert(image):
            image = resize_to_fit(image, blocksize, blocksize)
            image = tint_image(image, color)
            return image
        
        self._images_pil = [ [convert(image) for image in row ] for row in self.SPRITESHEET ]
        self.sprites = [ [ImageTk.PhotoImage(image) for image in row] for row in self._images_pil ]
        self.sprites.append( [ ImageTk.PhotoImage(image.transpose(Image.FLIP_LEFT_RIGHT)) for image in self._images_pil[2]] )
        self.canvas_reference = None

        self.bot = bot
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y

    def first_draw(self, canvas):
        self.canvas_reference = canvas.create_image(self.canvas_x, self.canvas_y, self.sprites[self.LOOKING_DOWN][1])

        

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
        self.board = [[constants.AIR]*self.n_blocks for i in range(self.n_blocks)]
        self.board_references = [[None]*self.n_blocks for i in range(self.n_blocks)]
        self.canvas = tk.Canvas(master=self.frame, width=size, height=size)
        self.canvas.bind('<B1-Motion>', self.mouse_motion)
        self.canvas.bind('<Button-1>', lambda e: self.place_current(e.x, e.y))
        self.canvas.bind_all('1', lambda e: self.placing_combo.current(0))
        self.canvas.bind_all('2', lambda e: self.placing_combo.current(1))
        self.canvas.bind_all('3', lambda e: self.placing_combo.current(2))
        self.canvas.bind_all('4', lambda e: self.placing_combo.current(3))
        self.toolbar = tk.Frame(master=self.frame)
        self.load_btn = tk.Button(master=self.toolbar, text='Load Map', command=self.load)
        self.save_btn = tk.Button(master=self.toolbar, text='Save Map', command=self.save)
        self.placing_frame = tk.Frame(master=self.frame)
        combo_label = tk.Label(master=self.placing_frame, text='Placing: ')
        self.block_choice = tk.StringVar()
        self.placing_combo = ttk.Combobox(master=self.placing_frame, values=constants.BLOCK_NAMES, textvariable=self.block_choice, state='readonly')
        self.placing_combo.current(0)
        self.placing_combo.bind('<<ComboboxSelected>>', lambda x: print(x, self.block_choice.get()))

        self.toolbar.grid(row=0, column=0, sticky='w')
        self.load_btn.pack(side=tk.LEFT)
        self.save_btn.pack(side=tk.LEFT)
        self.canvas.grid(row=1, column=0)
        self.placing_frame.grid(row=2, column=0)
        combo_label.pack(side=tk.LEFT)
        self.placing_combo.pack(side=tk.LEFT)

        self.draw_grid()

        self.barrel = load_sprite(blocksize, 'assets/barrel.png')
        self.player = load_sprite(blocksize, 'assets/player_down_1.png')

    def draw_grid(self):
        for y in range(0, self.size, self.blocksize):
            self.canvas.create_line(0,y,self.size,y)
        
        for x in range(0, self.size, self.blocksize):
            self.canvas.create_line(x,0,x,self.size)

    def place_current(self, canvas_x, canvas_y):
        x = canvas_x//self.blocksize
        y = canvas_y//self.blocksize
        
        if x >= self.n_blocks or x < 0 or y >= self.n_blocks or y < 0:
            return
        
        new_block = constants.BLOCK_VALUES[self.block_choice.get()]

        if self.board[y][x] == new_block:
            return
        
        self.board[y][x] = new_block
        self.redraw_block(x,y)

    def redraw_block(self,x,y):
        if self.board_references[y][x]:
            self.canvas.delete(self.board_references[y][x])
            self.board_references[y][x] = None

        if self.board[y][x] == constants.WALL:
            # print('wall', x*self.blocksize, y*self.blocksize, x*self.blocksize+self.blocksize, y*self.blocksize+self.blocksize)
            self.board_references[y][x] = self.canvas.create_rectangle(x*self.blocksize, y*self.blocksize, x*self.blocksize+self.blocksize, y*self.blocksize+self.blocksize, fill='black')
        elif self.board[y][x] == constants.BARREL:
            ID = self.canvas.create_image(x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, image=self.barrel)
            self.board_references[y][x] = ID
        elif self.board[y][x] == constants.SPAWNPOINT:
            ID = self.canvas.create_image(x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, image=self.player)
            self.board_references[y][x] = ID


    def mouse_motion(self, event):
        # print(event.x, event.y)
        self.place_current(event.x, event.y)

    def redraw(self):
        for y in range(self.n_blocks):
            for x in range(self.n_blocks):
                self.redraw_block(x,y)

    def save(self):
        file = asksaveasfile(defaultextension=[('Bomber Map', '*.map')], filetypes=[('Bomber Map', '*.map')])
        file.write('\n'.join([ ' '.join([ str(self.board[y][x]) for x in range(self.n_blocks) ]) for y in range(self.n_blocks) ]))
        file.close()

    def load(self):
        file = askopenfile(defaultextension=[('Bomber Map', '*.map')], filetypes=[('Bomber Map', '*.map')])
        for y,line in enumerate(file):
            self.board[y] = list(map(int, line.split()))
        self.redraw()
        file.close()


class Game(Subprogram):
    def __init__(self, master, size, blocksize):
        super().__init__(master)
        self.size = size
        self.blocksize = blocksize
        self.n_blocks = size//blocksize
        self.canvas = tk.Canvas(width=size, height=size, master=self.frame)
        self.canvas.pack()
        self.board = [[None]*self.n_blocks for i in range(self.n_blocks)]
        self.canvas_references = [[None]*self.n_blocks for i in range(self.n_blocks)]
        self.barrel = load_sprite(blocksize, 'assets/barrel.png')


    def redraw_block(self, x=None, y=None, canvas_x=None, canvas_y=None):
        if not x and not y:
            x,y = canvas_x//self.blocksize, canvas_y//self.blocksize

        if self.canvas_references[y][x]:
            self.canvas.delete(self.canvas_references[y][x])
        
        if self.board[y][x] == constants.WALL:
            # print('wall', x*self.blocksize, y*self.blocksize, x*self.blocksize+self.blocksize, y*self.blocksize+self.blocksize)
            self.board_references[y][x] = self.canvas.create_rectangle(x*self.blocksize, y*self.blocksize, x*self.blocksize+self.blocksize, y*self.blocksize+self.blocksize, fill='black')
        elif self.board[y][x] == constants.BARREL:
            ID = self.canvas.create_image(x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, image=self.barrel)
            self.board_references[y][x] = ID

    def initialize(self, n_humans, n_bots, game_map):
        self.n_humans = n_humans
        self.n_bots = n_bots
        
        with open(game_map, 'r') as f:
            self.board = [[int(itm) for itm in line.split()] for line in f]

        spawnpoints = []
        for y in range(self.n_blocks):
            for x in range(self.n_blocks):
                if self.board[y][x] == constants.SPAWNPOINT:
                    spawnpoints.append((x,y))
                    self.board[y][x] = constants.AIR
                else:
                    self.redraw_block(x,y)

        random.shuffle(spawnpoints)

        self.players = []
        for i in range(n_humans):
            x,y = spawnpoints[i]
            self.players.append(Player(self.blocksize, i, False, x*self.blocksize, y*self.blocksize))
        for j in range(n_bots):
            x,y = spawnpoints[j+n_humans]
            self.players.append(Player(self.blocksize, j+n_humans, True, x*self.blocksize, y*self.blocksize))

                




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

    # print(Player.SPRITESHEET)
    # Player.SPRITESHEET[0][0].show()
    # player = Player(40, constants.GREEN)
    # player._images_pil[0][1].show()
    # canvas = tk.Canvas(width=500,height=500)
    # canvas.create_image(100,100,image=player.sprites[3][1])
    # canvas.create_image(100,200,image=player.sprites[2][1])
    # canvas.pack()

    tk.mainloop()
        
