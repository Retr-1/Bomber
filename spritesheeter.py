from PIL import Image
import numpy as np

def split_vertically(data):
    start = 0
    splits = []
    for x in range(data.shape[1]):
        if np.all(data[:,x,3] == 0):
            if start < x:
                splits.append(data[:,start:x,:])
            start = x+1

    if start < x:
        splits.append(data[:,start:x,:])
    
    return splits

def split_horizontally(data):
    splits = []
    start = 0
    for y in range(data.shape[0]):
        if np.all(data[y,:,3] == 0):
            if start < y:
                splits.append(data[start:y,:,:])
            start = y+1

    if start < y:
        splits.append(data[start:y,:,:])
    
    return splits

def split(filepath):
    image = Image.open(filepath).convert('RGBA')
    # print(image.mode)
    data = np.array(image)
    # print(data.shape)

    horizontal = split_horizontally(data)
    splits = []
    for x in horizontal:
        splits.append(split_vertically(x))

    # print(len(splits))
    for i in range(len(splits)):
        for j in range(len(splits[i])):
            Image.fromarray(splits[i][j]).save(f'computed/{filepath.split('/')[-1].split('.')[0]}_{i}_{j}.png')

    
            

split('assets/player.png')
