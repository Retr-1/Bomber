AIR = 0
WALL = 1
BARREL = 2
SPAWNPOINT = 3
SPEED_BUFF = 4
SPEED_DEBUFF = 5
RADIUS_BUFF = 6
RADIUS_DEBUFF = 7
FUSE_BUFF = 8
FUSE_DEBUFF = 9
COOLDOWN_BUFF = 10
COOLDOWN_DEBUFF = 11
SHIELD = 12

BLOCK_NAMES = ['air', 'wall', 'barrel', 'spawnpoint', 'speed+', 'speed-', 'radius+', 'radius-', 'fuse+', 'fuse-', 'cooldown+', 'cooldown-', 'shield']
BLOCK_VALUES = dict(zip(BLOCK_NAMES, range(len(BLOCK_NAMES))))

RED = 0
GREEN = 1
BLUE = 2
YELLOW = 3
CYAN = 4
PURPLE = 5
BLACK = 6
WHITE = 7

COLOR_NAMES = ['red','green','blue','yellow','cyan','purple','black','white']

MOVING_UP = 1
MOVING_DOWN = 0b10
MOVING_LEFT = 0b100
MOVING_RIGHT = 0b1000