import numpy as np
import cv2
import os
import io
import sys
from PIL import Image

import torch
import torchvision.transforms as transforms
from torch.utils.data import Dataset

import utils # some data preprocessing funcs in utils/data_utils.py


# implement your dataset here

class ImageDataset(Dataset):

    def __init__(self, config, phase):
        '''
        config: data config
        phase: train or val
        '''
        assert phase in ['train', 'val']
        self.img_transform = transforms.Compose([
            transforms.Normalize(config['data_mean'], config['data_div'])
        ])
        with open(config['{}_list.txt'], 'r') as f:
            lines = f.readlines()
        self.fns = [os.path.join(config['{}_root'], l.split()[0]) for l in lines]
        self.labels = [int(l.strip().split()[1]) for l in lines]
        self.crop_size = config['crop_size']
        self.short_size = config.get('short_size', None)
        self.long_size = config.get('long_size', None)
        self.phase = phase
        self.aug = config['aug']

    def __len__(self):
        return len(self.fns)

    def __getitem__(self, idx):
        img_fn = self.fns[idx]
        label = self.lablels[idx]
        image = np.array(Image.open(img_fn).convert('RGB'))

        # resize w.r.t. short size or long size
        if self.short_size is not None or self.long_size is not None:
            image = utils.image_resize(
                image, short_size=self.short_size, long_size=self.long_size)

        # crop
        centerx = image.shape[1] // 2
        centery = image.shape[0] // 2
        sizex, sizey = self.crop_size
        if self.phase == 'train':
            centerx += np.random.uniform(*self.aug['shift']) * image.shape[1]
            centery += np.random.uniform(*self.aug['shift']) * image.shape[0]
            scale = np.random.uniform(*self.aug['scale'])
            sizex *= scale
            sizey *= scale
        bbox = [centerx - sizex / 2, centery - sizey / 2, sizex, sizey]
        image = cv2.resize(utils.crop_padding(image, bbox, pad_value=(0, 0, 0)),
                           self.crop_size, interpolation=cv2.INTER_CUBIC)

        # transform
        image = torch.from_numpy(image.astype(np.float32)).transpose((2, 0, 1)) # 3HW
        image = self.transforms(image)
        return image, label
        image