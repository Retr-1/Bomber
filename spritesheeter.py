from PIL import Image
import numpy as np

def split_vertically(data, alpha_threshold=0):
    start = 0
    splits = []
    for x in range(data.shape[1]):
        if np.all(data[:,x,3] <= alpha_threshold):
            if start < x:
                splits.append(data[:,start:x,:])
            start = x+1

    if start < x:
        splits.append(data[:,start:x,:])
    
    return splits

def split_horizontally(data, alpha_threshold=0):
    splits = []
    start = 0
    for y in range(data.shape[0]):
        if np.all(data[y,:,3] <= alpha_threshold):
            if start < y:
                splits.append(data[start:y,:,:])
            start = y+1

    if start < y:
        splits.append(data[start:y,:,:])
    
    return splits


def split(filepath, alpha_threshold=0):
    image = Image.open(filepath).convert('RGBA')
    # print(image.mode)
    data = np.array(image)
    # print(data.shape)

    horizontal = split_horizontally(data, alpha_threshold)
    splits = []
    for x in horizontal:
        splits.append(split_vertically(x, alpha_threshold))

    # print(len(splits))
    for i in range(len(splits)):
        for j in range(len(splits[i])):
            splits[i][j] = Image.fromarray(splits[i][j])
    
    return splits

def split_and_save(filepath, alpha_threshold=0):
    splits = split(filepath, alpha_threshold)
    
    for i in range(len(splits)):
        for j in range(len(splits[i])):
            splits[i][j].save(f'computed/{filepath.split('/')[-1].split('.')[0]}_{i}_{j}.png')    
            
if __name__ == '__main__':
    split_and_save('assets/bomb.png', 50)
