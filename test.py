from __future__ import division
from uNet.model import unet2dModule
import numpy as np
import pandas as pd
import cv2
import  os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]='6'




def train():
    '''
    Preprocessing for dataset
    '''
    # Read  data set (Train data from CSV file)
    csvmaskdata = pd.read_csv('GlandsMask.csv')
    csvimagedata = pd.read_csv('GlandsImage.csv')
    maskdata = csvmaskdata.iloc[:, :].values
    imagedata = csvimagedata.iloc[:, :].values
    # shuffle imagedata and maskdata together
    perm = np.arange(len(csvimagedata))
    np.random.shuffle(perm)
    imagedata = imagedata[perm]
    maskdata = maskdata[perm]

    unet2d = unet2dModule(512, 512, channels=3, costname="dice coefficient")
    unet2d.train(imagedata, maskdata, "/home/ubuntu/PycharmProjects/VnetFamily/Dual attention UNet/model/unet2dglandceil.pd",
                 "log/", 0.0005, 0.8, 100000, 2)


def predict():

    #true_img = cv2.imread("/home/ubuntu/PycharmProjects/VnetFamily/uNet/Data/test/Image/%D.bmp", cv2.IMREAD_COLOR)
    #for i in range(136, 150):
    true_img = cv2.imread("/home/ubuntu/PycharmProjects/VnetFamily/Dual attention UNet/Data/test/Image/27.bmp", cv2.IMREAD_COLOR)
    #cv2.imwrite(true_img)
    test_images = true_img.astype(np.float)
    # convert from [0:255] => [0.0:1.0]
    test_images = np.multiply(test_images, 1.0 / 255.0)
    unet2d = unet2dModule(512, 512, 3)
    predictvalue = unet2d.prediction("/home/ubuntu/PycharmProjects/VnetFamily/Dual attention UNet/model/unet2dglandceil.pd",
                                     test_images)

    cv2.imwrite("/home/ubuntu/PycharmProjects/VnetFamily/Dual attention UNet/Data/test/mask/27.bmp", predictvalue)


def main(argv):
    if argv == 1:
        train()
    if argv == 2:
        predict()


if __name__ == "__main__":
    main(1)