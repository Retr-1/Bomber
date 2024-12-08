import tkinter as tk
from tkinter import ttk
import constants
from PIL import Image, ImageTk
from tkinter.filedialog import asksaveasfile, askopenfile
import spritesheeter
import random
import os

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

def load_and_flatten_spritesheet(blocksize, filepath, alpha_threshold=0, min_length=0):
    split = spritesheeter.split(filepath, alpha_threshold, min_length)
    s = []
    for row in split:
        s += row
    return list(map(ImageTk.PhotoImage, map(lambda x: resize_to_fit(x, blocksize, blocksize), s)))

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

class ManualAnimation:
    def __init__(self, frames, frame_length):
        # frame_length is in ms

        self.frames = frames
        self.time = 0
        self.frame_length = frame_length
        self.total_length = self.frame_length*len(self.frames)
        self.current_frame = frames[0]

    def step(self, dt):
        self.time = (self.time + dt) % self.total_length
        self.current_frame = self.frames[self.time // self.frame_length]
        

class AnimationPlayer:
    def __init__(self, frames, frame_length, canvas, canvas_x, canvas_y, func_on_end=None, destroy_reference_on_end=False):
        self.canvas:tk.Canvas = canvas
        self.frames = frames
        self.frame_length = frame_length
        self.index = 0
        self.canvas_reference = None
        self.canvas_x = canvas_x
        self.cavnas_y = canvas_y
        self.func_on_end = func_on_end
        self.destroy_reference_on_end = destroy_reference_on_end

    def next_frame(self):
        self.index += 1

        if self.index >= len(self.frames):
            if self.func_on_end:
                self.func_on_end()
            if self.destroy_reference_on_end:
                self.canvas.delete(self.canvas_reference)
            return
        
        self.canvas.itemconfigure(self.canvas_reference, image=self.frames[self.index])
        self.canvas.after(self.frame_length, self.next_frame)

    def play(self):
        self.canvas_reference = self.canvas.create_image(self.canvas_x, self.cavnas_y, image=self.frames[self.index])
        self.canvas.after(self.frame_length, self.next_frame)




class Player:
    LOOKING_DOWN = 0
    LOOKING_UP = 1
    LOOKING_LEFT  = 2
    LOOKING_RIGHT = 3

    SPRITESHEET = spritesheeter.split('assets/player.png')

    def __init__(self, blocksize, color, bot, canvas_x, canvas_y, canvas):
        def convert(image):
            image = resize_to_fit(image, blocksize, blocksize)
            image = tint_image(image, color)
            return image
        
        self._images_pil = [ [convert(image) for image in row ] for row in self.SPRITESHEET ]
        self.sprites = [ [ImageTk.PhotoImage(image) for image in row] for row in self._images_pil ]
        self.sprites.append( [ ImageTk.PhotoImage(image.transpose(Image.FLIP_LEFT_RIGHT)) for image in self._images_pil[2]] )
        self.canvas_reference = None
        self.canvas:tk.Canvas = canvas
        self.bot = bot
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y
        self.moving = 0
        self.dead = False
        
        self.speed = blocksize//8
        self.bomb_cooldown = 100
        self.bomb_speed = 100
        self.bomb_range = 4

        self.animation = None
        self.blocksize = blocksize

    def start_moving(self, direction):
        # print(self.canvas_x, direction, 's')
        if not self.moving & (1<<direction):
            self.moving |= (1<<direction)
            self.animation = self.create_moving_animation()
        # print(self.animation, self.moving, self.moving & constants.MOVING_DOWN)

    def stop_moving(self, direction):
        # print(self.canvas_x, direction, 'e')
        self.moving ^= (1<<direction)&self.moving

        if self.moving == 0:
            for d,s in [(constants.MOVING_UP, self.LOOKING_UP), (constants.MOVING_DOWN, self.LOOKING_DOWN),(constants.MOVING_LEFT, self.LOOKING_LEFT),(constants.MOVING_RIGHT, self.LOOKING_RIGHT)]:
                if d & (1<<direction):
                    self.animation = ManualAnimation([self.sprites[s][1]], 100)
        else:
            self.animation = self.create_moving_animation()


    def create_moving_animation(self):
        FRAME_LENGTH = 100
        if self.moving & constants.MOVING_UP:
            return ManualAnimation(self.sprites[self.LOOKING_UP] + self.sprites[self.LOOKING_UP][-2:0:-1], FRAME_LENGTH*3//2)
        elif self.moving & constants.MOVING_DOWN:
            return ManualAnimation(self.sprites[self.LOOKING_DOWN] + self.sprites[self.LOOKING_DOWN][-2:0:-1], FRAME_LENGTH*3//2)
        elif self.moving & constants.MOVING_LEFT:
            return ManualAnimation(self.sprites[self.LOOKING_LEFT], FRAME_LENGTH)
        elif self.moving & constants.MOVING_RIGHT:
            return ManualAnimation(self.sprites[self.LOOKING_RIGHT], FRAME_LENGTH)
        
        return None

    def draw(self):
        if self.canvas_reference == None:
            sprite = self.sprites[self.LOOKING_DOWN][1]
            self.canvas_reference = self.canvas.create_image(self.canvas_x, self.canvas_y, image=sprite, anchor='center')

        

class Subprogram:
    def __init__(self, master):
        self.frame = tk.Frame(master=master)

class RangePicker(Subprogram):
    def __init__(self, master, label_text, min, max, default):
        super().__init__(master)
        self.min = min
        self.max = max
        self.left_btn = tk.Button(master=self.frame, text='-', command=lambda: self.add(-1))
        self.right_btn = tk.Button(master=self.frame, text='+', command=lambda: self.add(1))
        self.count = default
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

    def get(self):
        return self.count

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
        # self.placing_combo.bind('<<ComboboxSelected>>', lambda x: print(x, self.block_choice.get()))

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
        bomb_and_explosion = load_and_flatten_spritesheet(self.blocksize+10, 'assets/bomb.png', 50, 20)
        self.bomb_frames = bomb_and_explosion[:4]
        self.explosion_frames = bomb_and_explosion[4:-1]
        # self.fire_frames = load_and_flatten_spritesheet(self.blocksize+10, 'assets/fire.png', 0, 40)
        self.death_frames = load_and_flatten_spritesheet(self.blocksize+30, 'assets/death.png', 0, 40)


    def redraw_block(self, x=None, y=None, canvas_x=None, canvas_y=None):
        if x == None:
            x = canvas_x//self.blocksize
        if y == None:
            y = canvas_y//self.blocksize

        if self.canvas_references[y][x]:
            self.canvas.delete(self.canvas_references[y][x])
        
        if self.board[y][x] == constants.WALL:
            # print('wall', x*self.blocksize, y*self.blocksize, x*self.blocksize+self.blocksize, y*self.blocksize+self.blocksize)
            self.canvas_references[y][x] = self.canvas.create_rectangle(x*self.blocksize, y*self.blocksize, x*self.blocksize+self.blocksize, y*self.blocksize+self.blocksize, fill='black')
        elif self.board[y][x] == constants.BARREL:
            ID = self.canvas.create_image(x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, image=self.barrel)
            self.canvas_references[y][x] = ID

    def initialize(self, n_humans, n_bots, game_map):
        self.n_humans = n_humans
        self.n_bots = n_bots
        
        with open('./maps/' + game_map, 'r') as f:
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

        # (UP,DOWN,LEFT,RIGHT,BOMB)
        BINDS = (('w','s','a','d','q'), ("Up", "Down", "Left", "Right", '/'))
        self.players = []
        for i in range(n_humans):
            x,y = spawnpoints[i]
            self.players.append(Player(self.blocksize, i, False, x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, self.canvas))
            for j in range(4):
                self.canvas.bind_all(f'<KeyPress-{BINDS[i][j]}>', lambda event, j=j, player=self.players[i]: player.start_moving(j))
                self.canvas.bind_all(f'<KeyRelease-{BINDS[i][j]}>', lambda event, j=j, player=self.players[i]: player.stop_moving(j))
            self.canvas.bind_all(f'{BINDS[i][4]}', lambda event, player=self.players[i]: self.drop_bomb(player))

        for j in range(n_bots):
            x,y = spawnpoints[j+n_humans]
            self.players.append(Player(self.blocksize, j+n_humans, True, x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, self.canvas))

        for player in self.players:
            player.draw()

    def drop_bomb(self, player):
        if player.dead:
            return
        
        print('drop', player.canvas_x)
        gridx,gridy = player.canvas_x//self.blocksize*self.blocksize + self.blocksize/2, player.canvas_y//self.blocksize*self.blocksize + self.blocksize/2
        animation = AnimationPlayer(self.bomb_frames, 300, self.canvas, gridx, gridy, lambda: self.explode_bomb(player, gridx, gridy), True)
        animation.play()

    def explode_bomb(self, placed_by:Player, canvas_x, canvas_y):
        print('exploding...', len(self.explosion_frames))
        # self.canvas.delete(bomb_reference)

        animation = AnimationPlayer(self.explosion_frames, 100, self.canvas, canvas_x, canvas_y, destroy_reference_on_end=True)
        animation.play()
        # fire_animation = AnimationPlayer(self.fire_frames, 40, self.canvas, canvas_x, canvas_y, destroy_reference_on_end=True)
        # fire_animation.play()

        x,y = canvas_x//self.blocksize, canvas_y//self.blocksize
        for dx,dy in ((0,-1), (0,1), (-1,0), (1,0)):
            for i in range(1, placed_by.bomb_range):
                nx,ny = int(x+dx*i), int(y+dy*i)

                if nx < 0 or nx >= self.n_blocks or ny < 0 or ny >= self.n_blocks or self.board[ny][nx] == constants.WALL:
                    break

                if self.board[ny][nx] == constants.BARREL:
                    self.board[ny][nx] = constants.AIR
                    self.canvas.delete(self.canvas_references[ny][nx])
                    self.canvas_references[ny][nx] = None

                for player in self.players:
                    px,py = player.canvas_x//self.blocksize, player.canvas_y//self.blocksize
                    if px == nx and py == ny:
                        self.hit(player)

                animation = AnimationPlayer(self.explosion_frames, 100, self.canvas, nx*self.blocksize+self.blocksize/2, ny*self.blocksize+self.blocksize/2, destroy_reference_on_end=True)
                animation.play()

    def hit(self, player:Player):
        player.dead = True
        self.canvas.delete(player.canvas_reference)
        player.canvas_reference = None
        # AnimationPlayer(self.death_frames, 100, self.canvas, player.canvas_x, player.canvas_y, destroy_reference_on_end=True).play()

    def loop(self):
        for player in self.players:
            if player.dead:
                continue

            player:Player

            move = [0,0]
            if player.moving & constants.MOVING_UP:
                move[1] -= 1
            if player.moving & constants.MOVING_DOWN:
                move[1] += 1
            if player.moving & constants.MOVING_LEFT:
                move[0] -= 1
            if player.moving & constants.MOVING_RIGHT:
                move[0] += 1
            
            value = (move[0]**2 + move[1]**2)**0.5

            if value != 0:
                move = (int(move[0]/value*player.speed), int(move[1]/value*player.speed))

                oldx,oldy = (player.canvas_x)//self.blocksize, (player.canvas_y)//self.blocksize

                player.canvas_x += move[0]
                player.canvas_y += move[1]

                x,y = (player.canvas_x)//self.blocksize, (player.canvas_y)//self.blocksize
                # print(x,y)
                if x < 0 or x >= self.n_blocks or self.board[oldy][x] != constants.AIR:
                    player.canvas_x -= move[0]
                if y < 0 or y >= self.n_blocks or self.board[y][oldx] != constants.AIR:
                    player.canvas_y -= move[1]

            if player.animation:
                player.animation.step(16)
                self.canvas.itemconfigure(player.canvas_reference, image=player.animation.current_frame)
                self.canvas.tag_raise(player.canvas_reference)
                # print(player.animation.time)
            
            self.canvas.coords(player.canvas_reference, player.canvas_x, player.canvas_y)
            x,y = (player.canvas_x)//self.blocksize, (player.canvas_y)//self.blocksize + 1
            for x in range(x-1, x+2):
                if 0 <= y < self.n_blocks and 0 <= x < self.n_blocks:
                    # self.redraw_block(x, y)
                    if self.canvas_references[y][x]:
                        self.canvas.tag_raise(self.canvas_references[y][x])

        self.canvas.after(16, self.loop)

                

class LevelSelector(Subprogram):
    def __init__(self, master, func_from_level_select_to_menu, func_start_game):
        super().__init__(master)
        
        self.lvl_label = tk.Label(master=self.frame, text='Select Level: ')
        self.map_name = tk.StringVar()
        self.lvl_combox = ttk.Combobox(master=self.frame, textvariable=self.map_name, state='readonly')
        self.lvl_combox['values'] = os.listdir('maps/')
        self.lvl_combox.current(0)
        self.lvl_combox.bind('<<ComboboxSelected>>', self.selection_changed)
        self.human_count = RangePicker(self.frame, 'Number of Players: ', 0, 4, 1)
        self.bot_count = RangePicker(self.frame, 'Number of Bots: ', 0, 4, 1)
        self.play_btn = tk.Button(master=self.frame, text='Start the game', command=func_start_game)
        self.menu_btn = tk.Button(master=self.frame, text='Back to menu', command=func_from_level_select_to_menu)

        self.lvl_label.grid(row=0, column=0)
        self.lvl_combox.grid(row=0, column=1)
        self.human_count.frame.grid(row=1, column=0, columnspan=2)
        self.bot_count.frame.grid(row=2, column=0, columnspan=2)
        self.menu_btn.grid(row=3, column=0, sticky='nswe')
        self.play_btn.grid(row=3, column=1, sticky='nswe')

        self.max_players = self.get_max_players(self.map_name.get())
        # print(self.max_players)

    def selection_changed(self, event):
        self.max_players = self.get_max_players(self.map_name.get())
        # print(self.max_players, event)

    def get_max_players(self, map_name):
        with open('./maps/' + map_name, 'r') as f:
            return f.read().count(str(constants.SPAWNPOINT))

class Program:
    def __init__(self):
        self.window = tk.Tk()
        self.size = 800
        self.blocksize = 40
        
        self.menu_frame = tk.Frame(master=self.window)
        self.menu_btn_play = tk.Button(master=self.menu_frame, text='Play', font='Helvetica 32', command=self.from_menu_to_level_select)
        self.menu_btn_editor = tk.Button(master=self.menu_frame,text='Level Editor', font='Helvetica 32', command=self.from_menu_to_editor)

        self.menu_btn_play.grid(row=0, column=0, sticky='nswe')
        self.menu_btn_editor.grid(row=1, column=0, sticky='nswe')


        self.level_selector = LevelSelector(self.window, self.from_level_select_to_menu, self.start_game)

        self.level_editor = LevelEditor(self.window, self.size, self.blocksize)

        self.game = Game(self.window, self.size, self.blocksize)

        self.menu_frame.pack()

    def from_menu_to_level_select(self):
        self.menu_frame.pack_forget()
        self.level_selector.frame.pack()

    def start_game(self):
        print(self.level_selector.human_count.get(), self.level_selector.bot_count.get(), self.level_selector.map_name.get())
        self.game.initialize(self.level_selector.human_count.get(), self.level_selector.bot_count.get(), self.level_selector.map_name.get())
        self.game.loop()
        self.level_selector.frame.pack_forget()
        self.game.frame.pack()

    def from_level_select_to_menu(self):
        self.level_selector.frame.pack_forget()
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
        
