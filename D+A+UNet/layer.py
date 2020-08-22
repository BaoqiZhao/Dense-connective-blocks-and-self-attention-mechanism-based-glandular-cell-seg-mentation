'''
covlution layer，pool layer，initialization。。。。
'''
import tensorflow as tf
import numpy as np


# Weight initialization (Xavier's init)
def weight_xavier_init(shape, n_inputs, n_outputs, activefunction='sigmoid', uniform=True, variable_name=None):
    if activefunction == 'sigmoid':
        if uniform:
            init_range = tf.sqrt(6.0 / (n_inputs + n_outputs))
            initial = tf.random_uniform(shape, -init_range, init_range)
            return tf.Variable(initial, name=variable_name)
        else:
            stddev = tf.sqrt(2.0 / (n_inputs + n_outputs))
            initial = tf.truncated_normal(shape, mean=0.0, stddev=stddev)
            return tf.Variable(initial, name=variable_name)
    elif activefunction == 'relu':
        if uniform:
            init_range = tf.sqrt(6.0 / (n_inputs + n_outputs)) * np.sqrt(2)
            initial = tf.random_uniform(shape, -init_range, init_range)
            return tf.Variable(initial, name=variable_name)
        else:
            stddev = tf.sqrt(2.0 / (n_inputs + n_outputs)) * np.sqrt(2)
            initial = tf.truncated_normal(shape, mean=0.0, stddev=stddev)
            return tf.Variable(initial, name=variable_name)
    elif activefunction == 'tan':
        if uniform:
            init_range = tf.sqrt(6.0 / (n_inputs + n_outputs)) * 4
            initial = tf.random_uniform(shape, -init_range, init_range)
            return tf.Variable(initial, name=variable_name)
        else:
            stddev = tf.sqrt(2.0 / (n_inputs + n_outputs)) * 4
            initial = tf.truncated_normal(shape, mean=0.0, stddev=stddev)
            return tf.Variable(initial, name=variable_name)

# Bias initialization
def bias_variable(shape, variable_name=None):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial, name=variable_name)


# 2D convolution
def conv2d(x, W, strides=1):
    conv_2d = tf.nn.conv2d(x, W, strides=[1, strides, strides, 1], padding='SAME')
    return conv_2d


# 2D deconvolution
def deconv2d(x, W, stride=2):
    x_shape = tf.shape(x)
    output_shape = tf.stack([x_shape[0], x_shape[1] * stride, x_shape[2] * stride, x_shape[3] // stride])
    return tf.nn.conv2d_transpose(x, W, output_shape, strides=[1, stride, stride, 1], padding='SAME')


# Max Pooling
def max_pool_2x2(x):
    pool2d = tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    return pool2d


# Unet crop and concat
def crop_and_concat(x1, x2):
    #print(x1.shape)
    #print(x2.shape)
    x1_shape = tf.shape(x1)
    x2_shape = tf.shape(x2)
    #print(x1_shape.shape)
    #print(x2_shape.shape)
    # offsets for the top left corner of the crop
    #print(x1_shape[1])
    #print(x2_shape[1])
    offsets = [0, (x1_shape[1] - x2_shape[1]) // 2, (x1_shape[2] - x2_shape[2]) // 2, 0]
    size = [-1, x2_shape[1], x2_shape[2], -1]
    #print(offsets)
    #print(size)
    ##print("hhhhhhh")
    #print((x1_shape[2] - x2_shape[2]) // 2)
    x1_crop = tf.slice(x1, offsets, size)#input begin size
    return tf.concat([x1_crop, x2], 3)

