from PIL import Image
import numpy as np

def split_vertically(data, alpha_threshold=0, min_length=0):
    start = -1
    end = -1
    splits = []
    for x in range(data.shape[1]):
        if np.all(data[:,x,3] <= alpha_threshold):
            if x-start >= min_length and start != -1:
                splits.append(data[:,start:end+1,:])
                start = -1
                end = -1
        else:
            if start == -1:
                start = x
            end = x

    if start < end and end-start >= min_length:
        splits.append(data[:,start:end+1,:])
    
    return splits

def split_horizontally(data, alpha_threshold=0, min_length=0):
    splits = []
    start = -1
    end = -1
    for y in range(data.shape[0]):
        if np.all(data[y,:,3] <= alpha_threshold):
            if y-start >= min_length and start != -1:
                # print(start,end)
                splits.append(data[start:end+1,:,:])
                start = -1
                end = -1
        else:
            if start == -1:
                start = y
            end = y

    if start < end and end-start >= min_length:
        splits.append(data[start:end+1,:,:])
    
    return splits


def split(filepath, alpha_threshold=0, min_length=0):
    image = Image.open(filepath).convert('RGBA')
    # print(image.mode)
    data = np.array(image)
    # print(data.shape)

    horizontal = split_horizontally(data, alpha_threshold, min_length)

    # for x in horizontal:
        # Image.fromarray(x).show()
        # print(x)
        # pass
    # print(horizontal[-1], np.nonzero(horizontal[-1]), horizontal[-1][0,256])
    # return

    splits = []
    for x in horizontal:
        splits.append(split_vertically(x, alpha_threshold, min_length))

    # print(len(splits))
    for i in range(len(splits)):
        for j in range(len(splits[i])):
            splits[i][j] = Image.fromarray(splits[i][j])
    
    return splits

def split_and_save(filepath, alpha_threshold=0, min_length=0):
    splits = split(filepath, alpha_threshold, min_length)
    
    for i in range(len(splits)):
        for j in range(len(splits[i])):
            splits[i][j].save(f'computed/{filepath.split('/')[-1].split('.')[0]}_{i}_{j}.png')    
            
if __name__ == '__main__':
    import os
    for x in os.listdir('./computed'):
        os.remove(f'./computed/{x}')
    split_and_save('assets/fire.png', 0, 40)
