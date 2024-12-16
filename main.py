import tkinter as tk
from tkinter import ttk
import constants
from PIL import Image, ImageTk, ImageDraw
from tkinter.filedialog import asksaveasfile, askopenfile
import spritesheeter
import random
import os
import time
import numpy as np

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

def load_gif(filepath, width, height):
    gif = Image.open(filepath)
    i = 0
    frames = []
    while True:
        try:
            gif.seek(i)
            image = resize_to_fit(gif.convert('RGBA'), width, height)
            # image: Image
            pixels = np.array(image)
            # print(pixels.shape)
            for y in range(image.height):
                for x in range(image.width):
                    # print(pixels[x,y,0:3])
                    if sum(pixels[x,y,0:3]) < 100:
                        pixels[y,x] = [0,0,0,0]
                    else:
                        new_pixel = pixels[y,x]
                        new_pixel[3] = 150
                        pixels[y,x] = new_pixel
            # print('end')
            image = Image.fromarray(pixels, 'RGBA')
            # image.show()
            frames.append(ImageTk.PhotoImage(image))
            i += 1
        except Exception as e:
            print(e)
            break
    return frames


def load_and_flatten_spritesheet(blocksize, filepath, alpha_threshold=0, min_length=0):
    split = spritesheeter.split(filepath, alpha_threshold, min_length)
    s = []
    for row in split:
        s += row
    return list(map(ImageTk.PhotoImage, map(lambda x: resize_to_fit(x, blocksize, blocksize), s)))

def tint_image(image, color):
    r,g,b,a = image.split()
    factor = 0.4
    
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
    elif color == constants.CYAN:
        r = Image.eval(r, lambda x: x*factor)
        return Image.merge('RGBA', (r,g,b,a))
    elif color == constants.PURPLE:
        g = Image.eval(g, lambda x: x*factor)
        return Image.merge('RGBA', (r,g,b,a))
    elif color == constants.BLACK:
        r = Image.eval(r, lambda x: x*factor)
        g = Image.eval(g, lambda x: x*factor)
        b = Image.eval(b, lambda x: x*factor)
        return Image.merge('RGBA', (r,g,b,a))
    elif color == constants.WHITE:
        r = Image.eval(r, lambda x: min(255, x*(1+factor)))
        g = Image.eval(g, lambda x: min(255, x*(1+factor)))
        b = Image.eval(b, lambda x: min(255, x*(1+factor)))
        return Image.merge('RGBA', (r,g,b,a))
    
    return image
    
def resize_with_padding(image, desired_size):
    """
    Resize an image to the desired size, maintaining the aspect ratio
    and padding with zeros.
    
    Args:
        image (PIL.Image.Image): The input image.
        desired_size (tuple): The desired size as (width, height).

    Returns:
        PIL.Image.Image: The resized image with padding.
    """
    # Resize the image while maintaining the aspect ratio
    image.thumbnail(desired_size)
    
    # Create a new blank image with the desired size and a black background
    padded_image = Image.new("RGBA", desired_size, (0, 0, 0, 0))
    
    # Calculate the position to paste the resized image
    paste_position = (
        (desired_size[0] - image.width) // 2,
        (desired_size[1] - image.height) // 2,
    )
    
    # Paste the resized image onto the canvas
    padded_image.paste(image, paste_position)
    
    return padded_image
    
def create_scalers(image, blocksize, topleft=0.7):
    positive = resize_with_padding(image, (blocksize, blocksize))
    negative = positive.copy()

    a = (blocksize*topleft, blocksize*0.2)
    b = (blocksize*(topleft-0.2), blocksize*.45)
    c = (blocksize*(topleft+0.2), blocksize*.45)
    d = (blocksize*(topleft-0.1), blocksize*.6)
    e = (blocksize*(topleft+0.1), blocksize*.6)
    f = (d[0], b[1])
    g = (e[0], c[1])

    draw = ImageDraw.Draw(positive)
    draw.polygon((a,c,g,e,d,f,b), fill='green')

    a = (blocksize*(topleft-0.1), blocksize*0.2)
    b = (blocksize*(topleft+0.1), blocksize*0.2)
    c = (blocksize*(topleft-0.2), blocksize*.35)
    d = (blocksize*(topleft+0.2), blocksize*.35)
    e = (blocksize*topleft, blocksize*.6)
    f = (a[0] ,c[1])
    g = (b[0], d[1])

    draw = ImageDraw.Draw(negative)
    draw.polygon((a,b,g,d,e,c,f), fill='red')

    return (ImageTk.PhotoImage(positive), ImageTk.PhotoImage(negative))

def randchoice(items, probabilities):
    s = 0
    c = random.random()
    for i in range(len(items)):
        s += probabilities[i]
        if s >= c:
            return items[i]
        

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
    def __init__(self, frames, frame_length, canvas, canvas_x, canvas_y, func_on_end=None, destroy_reference_on_end=False, duration=None):

        self.canvas:tk.Canvas = canvas
        self.frames = frames
        if not frame_length:
            self.frame_length = int(duration/len(frames))
            # print(self.frame_length, 'fl')
        else:
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


class CanvasButton:
    def __init__(self, x1, y1, x2, y2, canvas, color, text='', command=lambda: None):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.canvas: tk.Canvas = canvas
        self.color = color
        self.text = text
        self.command = command

        self.rect_reference = None
        self.text_reference = None

        self.hovered = False
        self.placed = False


    def click(self, event):
        if self.placed and self.x2 >= event.x >= self.x1 and self.y2 >= event.y >= self.y1:
            self.command()

    def place(self):
        self.placed = True
        self.rect_reference = self.canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, outline=self.color)
        self.text_reference = self.canvas.create_text((self.x1+self.x2)/2, (self.y1+self.y2)/2, text=self.text, fill=self.color)

    def hover(self, event):
        if not self.placed:
            return
        
        if self.x2 >= event.x >= self.x1 and self.y2 >= event.y >= self.y1:
            if not self.hovered:
                self.hovered = True
                self.canvas.itemconfigure(self.rect_reference, fill=self.color)
                self.canvas.itemconfigure(self.text_reference, fill='black' if self.color in ('white','yellow') else 'white')
        elif self.hovered:
            self.hovered = False
            self.canvas.itemconfigure(self.rect_reference, fill='')
            self.canvas.itemconfigure(self.text_reference, fill=self.color)

    def destroy(self):
        self.hovered = False
        self.placed = False
        self.canvas.delete(self.rect_reference)
        self.canvas.delete(self.text_reference)
        self.rect_reference = None
        self.text_reference = None

    def set_color(self, color):
        self.color = color

        if not self.placed:
            return

        if self.hovered:
            self.canvas.itemconfigure(self.rect_reference, fill=self.color)
            self.canvas.itemconfigure(self.text_reference, fill='black' if self.color in ('white','yellow') else 'white')
        else:
            self.canvas.itemconfigure(self.rect_reference, fill='')
            self.canvas.itemconfigure(self.text_reference, fill=self.color)

class BombProperties:
    def __init__(self, x, y, radius, explodes_at=0):
        self.x = x
        self.y = y
        self.radius = radius
        self.explodes_at = explodes_at

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
        self.color = color
        self.canvas_reference = None
        self.shield_canvas_reference = None
        self.canvas:tk.Canvas = canvas
        self.bot = bot
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y
        self.moving = 0
        self.dead = False
        self.time_of_last_bomb = 0
        self.speed_to_frame_length_scaler = blocksize / 0.08
        
        self.speed = 1
        self.bomb_cooldown = 2 # seconds
        self.bomb_fuse = 1500 # ms
        self.bomb_radius = 3 # tiles
        self.shielded = False

        self.animation = ManualAnimation([self.sprites[self.LOOKING_DOWN][1]], 100)
        self.animation_direction = 0
        self.shield_animation = None
        self.blocksize = blocksize

    def move(self, code):
        if code == 0:
            self.animation_direction = 0
            for d,s in [(constants.MOVING_UP, self.LOOKING_UP), (constants.MOVING_DOWN, self.LOOKING_DOWN),(constants.MOVING_LEFT, self.LOOKING_LEFT),(constants.MOVING_RIGHT, self.LOOKING_RIGHT)]:
                if d & self.moving:
                    self.animation = ManualAnimation([self.sprites[s][1]], 100)
                    break
            self.moving = 0
        else:
            self.moving = code
            self.animation = self.create_moving_animation()

    def start_moving(self, direction):
        self.move(self.moving | (1<<direction))

    def stop_moving(self, direction):
        self.move(self.moving ^ ((1<<direction)&self.moving))


    def create_moving_animation(self):
        FRAME_LENGTH =  int(100/self.speed)
        # print(FRAME_LENGTH, 'fr')
        # frame_length = x / speed
        # 100 = x / blocksize/800
        if self.moving & constants.MOVING_UP:
            if self.animation_direction == constants.MOVING_UP:
                return self.animation
            self.animation_direction = constants.MOVING_UP
            return ManualAnimation(self.sprites[self.LOOKING_UP] + [self.sprites[self.LOOKING_UP][1]], FRAME_LENGTH*3//2)
        elif self.moving & constants.MOVING_DOWN:
            if self.animation_direction == constants.MOVING_DOWN:
                return self.animation
            self.animation_direction = constants.MOVING_DOWN
            return ManualAnimation(self.sprites[self.LOOKING_DOWN] + [self.sprites[self.LOOKING_DOWN][1]], FRAME_LENGTH*3//2)
        elif self.moving & constants.MOVING_LEFT:
            if self.animation_direction == constants.MOVING_LEFT:
                return self.animation
            self.animation_direction = constants.MOVING_LEFT
            return ManualAnimation(self.sprites[self.LOOKING_LEFT], FRAME_LENGTH)
        elif self.moving & constants.MOVING_RIGHT:
            if self.animation_direction == constants.MOVING_RIGHT:
                return self.animation
            self.animation_direction = constants.MOVING_RIGHT
            return ManualAnimation(self.sprites[self.LOOKING_RIGHT], FRAME_LENGTH)
        
        return self.animation

    def draw(self):
        if self.canvas_reference == None:
            sprite = self.sprites[self.LOOKING_DOWN][1]
            self.canvas_reference = self.canvas.create_image(self.canvas_x, self.canvas_y, image=sprite, anchor='center')

    x = property(lambda self: self.canvas_x//self.blocksize)
    y = property(lambda self: self.canvas_y//self.blocksize)


class Bot(Player):
    def __init__(self, blocksize, color, bot, canvas_x, canvas_y, canvas, func_speed_to_pixels_per_second, func_drop_bomb):
        super().__init__(blocksize, color, bot, canvas_x, canvas_y, canvas)
        self.func_speed_to_pixels_per_second = func_speed_to_pixels_per_second
        self.func_drop_bomb = func_drop_bomb

    def evaluate(self, board, bombs:set[BombProperties], players):
        def can_safely_detonate(x, y):
            pass

        def closest_path_to_safety(x, y, forbidden):
            batch = [[(x,y)]]
            visited = set()
            while True:
                # print(batch)
                if len(batch) == 0:
                    return []
                
                path = batch.pop(0)
                px,py = path[-1][0], path[-1][1]

                if not path[-1] in forbidden:
                    return path
                
                for nx,ny in [(px,py+1), (px,py-1), (px+1, py), (px-1, py)]:
                    if w > nx >= 0 and h > ny >= 0 and (not (nx,ny) in visited) and (not board[ny][nx] in [constants.WALL, constants.BARREL]):
                        new_path = path + [(nx,ny)]
                        visited.add((nx,ny))
                        batch.append(new_path)

        def enemy_in_range(x, y):
            for player in players:
                if player is self:
                    continue
                dx,dy = player.x-x, player.y-y
                if dx*dy == 0 and abs(dx+dy) < self.bomb_radius:
                    return True
            return False
        
        def mark_bomb(bomb:BombProperties, forbidden:set):
            forbidden.add((bomb.x, bomb.y))
            for dx in range(1, bomb.radius):
                forbidden.add((bomb.x+dx, bomb.y))
                forbidden.add((bomb.x-dx, bomb.y))
            for dy in range(1, bomb.radius):
                forbidden.add((bomb.x, bomb.y+dy))
                forbidden.add((bomb.x, bomb.y-dy))
        
        def can_safely_detonate(x, y):
            extra_forbidden = forbidden.copy()
            my_bomb = BombProperties(x, y, self.bomb_radius)
            mark_bomb(my_bomb, extra_forbidden)
            path_to_safety = closest_path_to_safety(x, y, extra_forbidden)
            blocks = len(path_to_safety)-1
            if blocks == -1:
                return False
            pixel_distance = blocks*self.blocksize
            return pixel_distance/pixel_speed < self.bomb_fuse/1000


        x,y = int(self.canvas_x//self.blocksize), int(self.canvas_y//self.blocksize)
        h,w = len(board), len(board[0])
        pixel_speed = self.func_speed_to_pixels_per_second(self.speed)

        forbidden = set() # tiles with upcoming explosion
        for bomb in bombs:
            mark_bomb(bomb, forbidden)

        if (x,y) in forbidden:
            # print('DANGER')
            # is endangered get to closesest safe spot
            path_to_safety = closest_path_to_safety(x, y, forbidden)
            if len(path_to_safety) == 0:
                # print('No choice')
                return
            # print(path_to_safety)
            dx,dy = path_to_safety[1][0] - x, path_to_safety[1][1] - y
            
            if dx == -1:
                self.move(constants.MOVING_LEFT)
            elif dx == 1:
                self.move(constants.MOVING_RIGHT)
            elif dy == -1:
                self.move(constants.MOVING_UP)
            elif dy == 1:
                self.move(constants.MOVING_DOWN)
        elif time.time()-self.time_of_last_bomb > self.bomb_cooldown and enemy_in_range(x, y) and can_safely_detonate(x, y):
            print(f'{self.color} is dropping !')
            self.func_drop_bomb()
        else:
            self.move(0)









class Subprogram:
    def __init__(self, master):
        self.frame = tk.Frame(master=master)

class RangePicker(Subprogram):
    def __init__(self, master, label_text, min, max, default, func_can_add=lambda x: True):
        super().__init__(master)
        self.min = min
        self.max = max
        self.func_can_add = func_can_add
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
        if self.min <= self.count+x <= self.max and self.func_can_add(x):
            self.count += x
            self.count_label.configure(text=f'{self.count}')

    def get(self):
        return self.count
    
    def hard_set(self, x):
        self.count = x
        self.count_label.configure(text=f'{self.count}')


class LevelEditor(Subprogram):
    def __init__(self, master, size, blocksize, func_back_to_menu):
        super().__init__(master)
        self.blocksize = blocksize
        self.size = size
        self.n_blocks = self.size//self.blocksize
        self.board = [[constants.AIR]*self.n_blocks for i in range(self.n_blocks)]
        self.board_references = [[None]*self.n_blocks for i in range(self.n_blocks)]
        self.canvas = tk.Canvas(master=self.frame, width=size, height=size)
        self.canvas.bind('<B1-Motion>', self.mouse_motion)
        self.canvas.bind('<Button-1>', lambda e: self.place_current(e.x, e.y))
        # self.canvas.bind_all('1', lambda e: self.placing_combo.current(0))
        # self.canvas.bind_all('2', lambda e: self.placing_combo.current(1))
        # self.canvas.bind_all('3', lambda e: self.placing_combo.current(2))
        # self.canvas.bind_all('4', lambda e: self.placing_combo.current(3))
        for i in range(9):
            self.canvas.bind_all(str(i+1), lambda e, i=i: self.placing_combo.current(i))
        self.canvas.bind_all('0', lambda e: self.placing_combo.current(9))

        self.toolbar = tk.Frame(master=self.frame)
        self.load_btn = tk.Button(master=self.toolbar, text='Load Map', command=self.load)
        self.save_btn = tk.Button(master=self.toolbar, text='Save Map', command=self.save)
        self.back_to_menu_btn = tk.Button(master=self.toolbar, text='Back to menu', command=func_back_to_menu)
        self.reset_btn = tk.Button(master=self.toolbar, text='Reset', command=self.reset)
        self.placing_frame = tk.Frame(master=self.frame)
        combo_label = tk.Label(master=self.placing_frame, text='Placing: ')
        self.block_choice = tk.StringVar()
        self.placing_combo = ttk.Combobox(master=self.placing_frame, values=constants.BLOCK_NAMES, textvariable=self.block_choice, state='readonly')
        self.placing_combo.current(0)
        # self.placing_combo.bind('<<ComboboxSelected>>', lambda x: print(x, self.block_choice.get()))

        self.toolbar.grid(row=0, column=0, sticky='nswe')
        self.load_btn.pack(side=tk.LEFT, anchor='w')
        self.save_btn.pack(side=tk.LEFT, anchor='w')
        self.back_to_menu_btn.pack(side=tk.RIGHT, anchor='e')
        self.reset_btn.pack(side=tk.RIGHT, anchor='e')
        self.canvas.grid(row=1, column=0)
        self.placing_frame.grid(row=2, column=0)
        combo_label.pack(side=tk.LEFT)
        self.placing_combo.pack(side=tk.LEFT)

        self.draw_grid()

        self.sprites = dict()
        self.sprites[constants.BARREL] = load_sprite(blocksize, 'assets/barrel.png')
        self.sprites[constants.SPAWNPOINT] = load_sprite(blocksize, 'assets/player_down_1.png')
        self.sprites[constants.SPEED_BUFF], self.sprites[constants.SPEED_DEBUFF] = create_scalers(Image.open('assets/speed.png'), self.blocksize)
        self.sprites[constants.RADIUS_BUFF], self.sprites[constants.RADIUS_DEBUFF] = create_scalers(Image.open('assets/radius.png'), self.blocksize, 0.8)
        self.sprites[constants.FUSE_BUFF], self.sprites[constants.FUSE_DEBUFF] = create_scalers(Image.open('assets/fuse.png'), self.blocksize, 0.2)
        self.sprites[constants.COOLDOWN_BUFF], self.sprites[constants.COOLDOWN_DEBUFF] = create_scalers(Image.open('assets/cooldown.png'), self.blocksize, 0.8)
        self.sprites[constants.SHIELD] = load_sprite(blocksize, 'assets/shield.png')

    def reset(self):
        for y in range(self.n_blocks):
            for x in range(self.n_blocks):
                self.board[y][x] = constants.AIR
                self.redraw_block(x, y)

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

        if self.board[y][x] == new_block or (self.board[y][x] != constants.AIR and new_block != constants.AIR):
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
        elif self.board[y][x] in self.sprites:
            ID = self.canvas.create_image(x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, image=self.sprites[self.board[y][x]])
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
        if not file:
            return
        file.write('\n'.join([ ' '.join([ str(self.board[y][x]) for x in range(self.n_blocks) ]) for y in range(self.n_blocks) ]))
        file.close()

    def load(self):
        file = askopenfile(defaultextension=[('Bomber Map', '*.map')], filetypes=[('Bomber Map', '*.map')])
        if not file:
            return
        for y,line in enumerate(file):
            self.board[y] = list(map(int, line.split()))
        self.redraw()
        file.close()



class Game(Subprogram):
    def __init__(self, master, size, blocksize, func_back_to_menu=lambda: None):
        super().__init__(master)
        self.size = size
        self.blocksize = blocksize
        self.n_blocks = size//blocksize
        self.canvas = tk.Canvas(width=size, height=size, master=self.frame)
        self.canvas.pack()
        self.board = [[None]*self.n_blocks for i in range(self.n_blocks)]
        self.canvas_references = [[None]*self.n_blocks for i in range(self.n_blocks)]
        self.game_map = None
        self.paused = True
        self.players = []
        self.bots = []
        self.bombs:list[BombProperties] = set()
        self.func_back_to_menu = func_back_to_menu
        bomb_and_explosion = load_and_flatten_spritesheet(self.blocksize+10, 'assets/bomb.png', 50, 20)
        self.bomb_frames = bomb_and_explosion[:4]
        self.explosion_frames = bomb_and_explosion[4:-1]
        self.player_shield_frames = load_gif('assets/shield_equipped.gif', blocksize+25, blocksize+25)
        # print(self.player_shield_frames)
        self.shadow = ImageTk.PhotoImage(Image.new('RGBA', (self.size, self.size), (0,0,0,120)))

        self.play_again_btn = CanvasButton(size/2-size/4, size/2 + 30, size/2-10, size/2 + 100, self.canvas, 'RED', 'Play Again')
        self.menu_btn = CanvasButton(size/2+10, size/2 + 30, size/2+10+size/4, size/2 + 100, self.canvas, 'RED', 'Back to Menu')
        
        self.canvas.bind('<Button-1>', self._mouse1)
        self.canvas.bind('<Motion>', self._mousemove)
        # self.fire_frames = load_and_flatten_spritesheet(self.blocksize+10, 'assets/fire.png', 0, 40)
        # self.death_frames = load_and_flatten_spritesheet(self.blocksize+30, 'assets/death.png', 0, 40)

        self.sprites = dict()
        self.sprites[constants.BARREL] = load_sprite(blocksize, 'assets/barrel.png')
        self.sprites[constants.SPAWNPOINT] = load_sprite(blocksize, 'assets/player_down_1.png')
        self.sprites[constants.SPEED_BUFF], self.sprites[constants.SPEED_DEBUFF] = create_scalers(Image.open('assets/speed.png'), self.blocksize)
        self.sprites[constants.RADIUS_BUFF], self.sprites[constants.RADIUS_DEBUFF] = create_scalers(Image.open('assets/radius.png'), self.blocksize, 0.8)
        self.sprites[constants.FUSE_BUFF], self.sprites[constants.FUSE_DEBUFF] = create_scalers(Image.open('assets/fuse.png'), self.blocksize, 0.2)
        self.sprites[constants.COOLDOWN_BUFF], self.sprites[constants.COOLDOWN_DEBUFF] = create_scalers(Image.open('assets/cooldown.png'), self.blocksize, 0.8)
        self.sprites[constants.SHIELD] = load_sprite(blocksize, 'assets/shield.png')

        self.trinket_probabilities = [0]*9
        tp = self.trinket_probabilities
        tp[constants.SPEED_BUFF-4] =  10
        tp[constants.SPEED_DEBUFF-4] = 10
        tp[constants.FUSE_BUFF-4] = 8
        tp[constants.FUSE_DEBUFF-4] = 8
        tp[constants.COOLDOWN_BUFF-4] = 6
        tp[constants.COOLDOWN_DEBUFF-4] = 6
        tp[constants.RADIUS_BUFF-4] = 4
        tp[constants.RADIUS_DEBUFF-4] = 4
        tp[constants.SHIELD-4] = 5
        s = sum(tp)
        for i in range(len(tp)):
            tp[i] /= s
        # print(self.trinket_probabilities)


    def _mouse1(self, event):
        self.play_again_btn.click(event)
        self.menu_btn.click(event)

    def _mousemove(self, event):
        self.play_again_btn.hover(event)
        self.menu_btn.hover(event)

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
        elif self.board[y][x] in self.sprites:
            ID = self.canvas.create_image(x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, image=self.sprites[self.board[y][x]])
            self.canvas_references[y][x] = ID

    def initialize(self, n_humans, n_bots, game_map):
        self.n_humans = n_humans
        self.n_bots = n_bots
        self.game_map = game_map
        self.paused = True
        
        with open('./maps/' + game_map, 'r') as f:
            self.board = [[int(itm) for itm in line.split()] for line in f]

        spawnpoints = []
        for y in range(self.n_blocks):
            for x in range(self.n_blocks):
                if self.board[y][x] == constants.SPAWNPOINT:
                    spawnpoints.append((x,y))
                    self.board[y][x] = constants.AIR
                
                self.redraw_block(x,y)

        random.shuffle(spawnpoints)

        # (UP,DOWN,LEFT,RIGHT,BOMB)
        BINDS = (('w','s','a','d','q'), ("Up", "Down", "Left", "Right", '/'), ('i','k','j','l','u'), ('t','g','f','h','r'))
        for i in range(n_humans):
            x,y = spawnpoints[i]
            self.players.append(Player(self.blocksize, i, False, x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, self.canvas))
            for j in range(4):
                self.canvas.bind_all(f'<KeyPress-{BINDS[i][j]}>', lambda event, j=j, player=self.players[i]: player.start_moving(j))
                self.canvas.bind_all(f'<KeyRelease-{BINDS[i][j]}>', lambda event, j=j, player=self.players[i]: player.stop_moving(j))
            self.canvas.bind_all(f'{BINDS[i][4]}', lambda event, player=self.players[i]: self.drop_bomb(player))

        for j in range(n_bots):
            x,y = spawnpoints[j+n_humans]
            bot = Bot(self.blocksize, j+n_humans, True, x*self.blocksize+self.blocksize//2, y*self.blocksize+self.blocksize//2, self.canvas, lambda x: self.blocksize/15*x*60, None)
            bot.func_drop_bomb = lambda b=bot: self.drop_bomb(b)
            self.players.append(bot)
            self.bots.append(bot)

        for player in self.players:
            player.draw()

    def drop_bomb(self, player:Player):
        if player.dead or time.time() - player.time_of_last_bomb < player.bomb_cooldown or self.paused:
            return
        
        x,y = int(player.canvas_x//self.blocksize), int(player.canvas_y//self.blocksize)
        if (x, y) in self.bombs:
            return
        
        # print(time.time())
        print('drop', player.color, self.bombs)

        bomb = BombProperties(x,y,player.bomb_radius)
        canvas_x,canvas_y = x*self.blocksize + self.blocksize/2, y*self.blocksize + self.blocksize/2
        player.time_of_last_bomb = time.time()
        self.bombs.add(bomb)
        animation = AnimationPlayer(self.bomb_frames, None, self.canvas, canvas_x, canvas_y, lambda: self.explode_bomb(bomb), True, player.bomb_fuse)
        animation.play()

    def explode_bomb(self, bomb:BombProperties):
        # print('exploding...', len(self.explosion_frames))
        canvas_x, canvas_y = bomb.x*self.blocksize + self.blocksize/2, bomb.y*self.blocksize + self.blocksize/2
        animation = AnimationPlayer(self.explosion_frames, 100, self.canvas, canvas_x, canvas_y, destroy_reference_on_end=True)
        animation.play()
        # fire_animation = AnimationPlayer(self.fire_frames, 40, self.canvas, canvas_x, canvas_y, destroy_reference_on_end=True)
        # fire_animation.play()

        x,y = bomb.x, bomb.y

        for player in self.players:
            px,py = player.canvas_x//self.blocksize, player.canvas_y//self.blocksize
            if px == x and py == y:
                self.hit(player)

        for dx,dy in ((0,-1), (0,1), (-1,0), (1,0)):
            for i in range(1, bomb.radius):
                nx,ny = int(x+dx*i), int(y+dy*i)

                if nx < 0 or nx >= self.n_blocks or ny < 0 or ny >= self.n_blocks or self.board[ny][nx] == constants.WALL:
                    break

                if self.board[ny][nx] == constants.BARREL:
                    if random.random() < 0.5:
                        self.board[ny][nx] = randchoice(list(range(4,13)), self.trinket_probabilities)
                    else:
                        self.board[ny][nx] = constants.AIR

                    self.redraw_block(nx, ny)

                for player in self.players:
                    px,py = player.canvas_x//self.blocksize, player.canvas_y//self.blocksize
                    if px == nx and py == ny:
                        self.hit(player)

                animation = AnimationPlayer(self.explosion_frames, 100, self.canvas, nx*self.blocksize+self.blocksize/2, ny*self.blocksize+self.blocksize/2, destroy_reference_on_end=True)
                animation.play()
        
        self.bombs.remove(bomb)

    def hit(self, player:Player):
        if player.shielded:
            player.shielded = False
            player.shield_animation = None
            self.canvas.delete(player.shield_canvas_reference)
            player.shield_canvas_reference = None
        else:
            player.dead = True
            self.canvas.delete(player.canvas_reference)
            player.canvas_reference = None
        
        # AnimationPlayer(self.death_frames, 100, self.canvas, player.canvas_x, player.canvas_y, destroy_reference_on_end=True).play()

    def start(self):
        def update():
            dtime = time.time() - stime

            if True: #dtime > 3:
                self.canvas.delete(shadow_reference)
                self.canvas.delete(text_reference)
                self.paused = False
                self.loop()
                return
            
            self.canvas.itemconfigure(text_reference, text=f'{3-int(dtime)}', font=f'Helvetica {int(MAX_FONT_SIZE-FONT_DELTA*(dtime%1))}')
            self.canvas.after(16, update)
        
        MAX_FONT_SIZE = 50
        FONT_DELTA = 20
        stime = time.time()
        shadow_reference = self.canvas.create_image(0,0, image=self.shadow, anchor='nw')
        text_reference = self.canvas.create_text(self.size/2, self.size/2, anchor='center', text='3', font=f'Helvetica {MAX_FONT_SIZE}')

        self.canvas.after(16, update)

    def loop(self):
        for bot in self.bots:
            bot:Bot
            bot.evaluate(self.board, self.bombs, self.players)

        n_alive = 0
        for player in sorted(self.players, key=lambda player: player.canvas_y):
            if player.dead:
                continue

            n_alive += 1
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
                SCALE = self.blocksize/15*player.speed
                move = (move[0]/value*SCALE, move[1]/value*SCALE)
                oldx,oldy = int(player.canvas_x//self.blocksize), int(player.canvas_y//self.blocksize)

                player.canvas_x += move[0]
                player.canvas_y += move[1]

                x,y = int(player.canvas_x//self.blocksize), int(player.canvas_y//self.blocksize)
                # print(x,y)
                if x < 0 or x >= self.n_blocks or self.board[oldy][x] in [constants.WALL, constants.BARREL]:
                    player.canvas_x -= move[0]
                if y < 0 or y >= self.n_blocks or self.board[y][oldx] in [constants.WALL, constants.BARREL]:
                    player.canvas_y -= move[1]

            if player.animation:
                player.animation.step(16)
                self.canvas.itemconfigure(player.canvas_reference, image=player.animation.current_frame)
                self.canvas.tag_raise(player.canvas_reference)

                if player.shield_animation:
                    player.shield_animation.step(16)
                    self.canvas.itemconfigure(player.shield_canvas_reference, image=player.shield_animation.current_frame)
                    self.canvas.tag_raise(player.shield_canvas_reference)

                # print(player.animation.time)
            # print(player.shield_canvas_reference, player.canvas_x, player.canvas_y)
            self.canvas.coords(player.canvas_reference, player.canvas_x, player.canvas_y)
            if player.shield_canvas_reference != None:
                self.canvas.coords(player.shield_canvas_reference, player.canvas_x, player.canvas_y)
            
            x,y = int(player.canvas_x//self.blocksize), int(player.canvas_y//self.blocksize)
            
            match self.board[y][x]:
                case constants.SPEED_BUFF:
                    player.speed *= 1.2
                case constants.SPEED_DEBUFF:
                    player.speed /= 1.2
                case constants.RADIUS_BUFF:
                    player.bomb_radius += 1
                case constants.RADIUS_DEBUFF:
                    player.bomb_radius = max(player.bomb_radius-1, 1)
                case constants.FUSE_BUFF:
                    player.bomb_fuse /= 1.2
                case constants.FUSE_DEBUFF:
                    player.bomb_fuse *= 1.2
                case constants.COOLDOWN_BUFF:
                    player.bomb_cooldown /= 1.4
                case constants.COOLDOWN_DEBUFF:
                    player.bomb_cooldown *= 1.4
                case constants.SHIELD:
                    if not player.shielded:
                        player.shielded = True
                        player.shield_animation = ManualAnimation(self.player_shield_frames, 150)
                        player.shield_canvas_reference = self.canvas.create_image(player.canvas_x, player.canvas_y, image=self.player_shield_frames[0])

            if constants.SHIELD >= self.board[y][x] >= constants.SPEED_BUFF:
                self.board[y][x] = constants.AIR
                self.redraw_block(x,y)

            y += 1
            for x in range(x-1, x+2):
                if 0 <= y < self.n_blocks and 0 <= x < self.n_blocks:
                    # self.redraw_block(x, y)
                    if self.canvas_references[y][x]:
                        self.canvas.tag_raise(self.canvas_references[y][x])

        if n_alive < 2:
            self.endgame(n_alive)
        else:
            self.canvas.after(16, self.loop)

    def endgame(self, n_alive):
        def clean():
            self.canvas.delete(shadow_reference)
            self.canvas.delete(text_reference)
            self.play_again_btn.destroy()
            self.menu_btn.destroy()
            for player in self.players:
                player:Player
                if player.canvas_reference:
                    self.canvas.delete(player.canvas_reference)
                if player.shield_canvas_reference:
                    self.canvas.delete(player.shield_canvas_reference)
            self.players.clear()
            self.bots.clear()

        def restart():
            clean()
            self.initialize(self.n_humans, self.n_bots, self.game_map)
            print('calling start')
            self.start()

        def back_to_menu():
            clean()
            self.func_back_to_menu()

        self.paused = True
        shadow_reference = self.canvas.create_image(0, 0, anchor='nw', image=self.shadow)
        FONT = 'Helvetica 40'

        if n_alive == 0:
            text = 'Tie'
            color = 'white'
        else:
            alive = None
            for player in self.players:
                player: Player
                if not player.dead:
                    alive = player
                    break
            text = f'{constants.COLOR_NAMES[player.color].capitalize()} wins!!!'
            color = constants.COLOR_NAMES[player.color]

        text_reference = self.canvas.create_text(self.size/2, self.size/2-30, text=text, fill=color, anchor='center', font=FONT)
        self.play_again_btn.set_color(color)
        self.play_again_btn.command = restart
        self.menu_btn.command = back_to_menu
        self.menu_btn.set_color(color)
        self.play_again_btn.place()
        self.menu_btn.place()
                        

class LevelSelector(Subprogram):
    def __init__(self, master, func_from_level_select_to_menu, func_start_game):
        super().__init__(master)

        def can_add(x):
            return self.human_count.get()+self.bot_count.get()+x <= self.max_players
    
        def play():
            if self.human_count.get()+self.bot_count.get() >= 2 and self.max_players >= 2:
                func_start_game()
        
        self.lvl_label = tk.Label(master=self.frame, text='Select Level: ')
        self.map_name = tk.StringVar()
        self.lvl_combox = ttk.Combobox(master=self.frame, textvariable=self.map_name, state='readonly')
        self.lvl_combox['values'] = os.listdir('maps/')
        self.lvl_combox.current(0)
        self.lvl_combox.bind('<<ComboboxSelected>>', self.selection_changed)
        self.human_count = RangePicker(self.frame, 'Number of Players: ', 0, 4, 1, can_add)
        self.bot_count = RangePicker(self.frame, 'Number of Bots: ', 0, 4, 1, can_add)
        self.play_btn = tk.Button(master=self.frame, text='Start the game', command=play)
        self.menu_btn = tk.Button(master=self.frame, text='Back to menu', command=func_from_level_select_to_menu)

        self.lvl_label.grid(row=0, column=0)
        self.lvl_combox.grid(row=0, column=1)
        self.human_count.frame.grid(row=1, column=0, columnspan=2)
        self.bot_count.frame.grid(row=2, column=0, columnspan=2)
        self.menu_btn.grid(row=3, column=0, sticky='nswe')
        self.play_btn.grid(row=3, column=1, sticky='nswe')

        self.max_players = self.get_max_players(self.map_name.get())
        # print(self.max_players)

    def refresh(self):
        self.lvl_combox.configure(values=os.listdir('maps/'))
        self.selection_changed()

    def selection_changed(self, event=None):
        self.max_players = self.get_max_players(self.map_name.get())
        if self.human_count.get()+self.bot_count.get() > self.max_players:
            self.human_count.hard_set(1)
            self.bot_count.hard_set(1)
        
        if self.max_players < 2:
            self.play_btn.configure(state=tk.DISABLED)
        else:
            self.play_btn.configure(state=tk.NORMAL)
        # print(self.max_players, event)

    def get_max_players(self, map_name):
        with open('./maps/' + map_name, 'r') as f:
            return f.read().count(str(constants.SPAWNPOINT))

class Program:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Bomber')
        self.size = 800
        self.blocksize = 40
        
        self.menu_frame = tk.Frame(master=self.window)
        self.menu_logo_image = ImageTk.PhotoImage(Image.open('assets/logo.jpg'))
        self.menu_logo = tk.Label(master=self.menu_frame, image=self.menu_logo_image)
        self.menu_btn_play = tk.Button(master=self.menu_frame, text='Play', font='Helvetica 26', command=self.from_menu_to_level_select)
        self.menu_btn_editor = tk.Button(master=self.menu_frame,text='Level Editor', font='Helvetica 26', command=self.from_menu_to_editor)

        self.menu_logo.grid(row=0, column=0, sticky='nswe')
        self.menu_btn_play.grid(row=1, column=0, sticky='nswe')
        self.menu_btn_editor.grid(row=2, column=0, sticky='nswe')


        self.level_selector = LevelSelector(self.window, self.from_level_select_to_menu, self.start_game)

        self.level_editor = LevelEditor(self.window, self.size, self.blocksize, self.from_editor_to_menu)

        self.game = Game(self.window, self.size, self.blocksize, self.from_game_to_menu)

        self.menu_frame.pack()

    def from_game_to_menu(self):
        self.game.frame.pack_forget()
        self.menu_frame.pack()

    def from_editor_to_menu(self):
        self.level_editor.frame.pack_forget()
        self.menu_frame.pack()

    def from_menu_to_level_select(self):
        self.menu_frame.pack_forget()
        self.level_selector.refresh()
        self.level_selector.frame.pack()

    def start_game(self):
        print(self.level_selector.human_count.get(), self.level_selector.bot_count.get(), self.level_selector.map_name.get())
        self.game.initialize(self.level_selector.human_count.get(), self.level_selector.bot_count.get(), self.level_selector.map_name.get())
        self.game.start()
        self.level_selector.frame.pack_forget()
        self.game.frame.pack()
        self.game.frame.focus_set()

    def from_level_select_to_menu(self):
        self.level_selector.frame.pack_forget()
        self.menu_frame.pack()

    def from_menu_to_editor(self):
        self.menu_frame.pack_forget()
        self.level_editor.frame.pack()

if __name__ == '__main__':
    p = Program()
    # a,b = create_scalers(Image.open('assets/fuse.png'), 100, 0.2)
    # a,b = create_scalers(Image.open('assets/radius.png'), 100)
    # a.show()
    # b.show()

    # print(Player.SPRITESHEET)
    # Player.SPRITESHEET[0][0].show()
    # player = Player(40, constants.GREEN)
    # player._images_pil[0][1].show()
    # canvas = tk.Canvas(width=500,height=500)
    # canvas.create_image(100,100,image=player.sprites[3][1])
    # canvas.create_image(100,200,image=player.sprites[2][1])
    # canvas.pack()

    tk.mainloop()
        
