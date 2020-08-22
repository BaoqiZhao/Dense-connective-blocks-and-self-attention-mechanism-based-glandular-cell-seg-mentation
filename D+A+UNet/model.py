'''

'''
from uNet.layer import (conv2d, deconv2d, max_pool_2x2, crop_and_concat, weight_xavier_init, bias_variable)
import tensorflow as tf
import numpy as np
import os
import cv2


def deconv_relu(x, kernal, scope = None):
    with tf.name_scope(scope):
        W = weight_xavier_init(shape = kernal, n_inputs = kernal[0] * kernal[1] * kernal[-1], n_outputs = kernal[-2],
                               activefunction = 'relu', variable_name = scope + 'W')
        B = bias_variable([kernal[-2]], variable_name = scope + 'B')
        deconv = deconv2d(x, W) + B
        deconv = tf.nn.relu(deconv)
        return deconv


def normalizationlayer(x, is_train, norm_type = None, scope = None):
    with tf.name_scope(scope + norm_type):
        if norm_type == None:
            output = x
        elif norm_type == 'batch':
            output = tf.contrib.layers.batch_norm(x, center = True, scale = True, is_training = is_train)
        return output

def conv_bn_relu_drop(x, kernal, phase, drop, scope = None):
    with tf.name_scope(scope):
        W = weight_xavier_init(shape = kernal, n_inputs = kernal[0] * kernal[1] * kernal[2], n_outputs = kernal[-1],
                               activefunction = 'relu', variable_name = scope + 'conv_W')
        B = bias_variable([kernal[-1]], variable_name = scope + 'conv_B')
        conv = conv2d(x, W) + B
        conv = normalizationlayer(conv, is_train=phase, norm_type='batch', scope = scope + 'normalization')
        conv = tf.nn.dropout(tf.nn.relu(conv), drop, name = scope + 'conv_dropout')
        return conv
def resnet_Add(x1, x2):
    if x1.get_shape().as_list()[3] != x2.get_shape().as_list()[3]:
        residual_connection = x2 + tf.pad(x1, [[0, 0], [0, 0], [0, 0],[0, 0],
                                               [0, x2.get_shape().as_list()[3] -
                                                x1.get_shape().as_list()[3]]])
    else:
        residual_connection = x2 + x1
    return residual_connection
def positionAttentionblock(x, inputfilter, outputfilter, kernal_size=1, scope=None):
    with tf.name_scope(scope):
        m_batchsize, H, W, C = x.get_shape().as_list()

        kernalquery = (kernal_size, kernal_size, inputfilter, outputfilter)

        BW = weight_xavier_init(shape = kernalquery,
                                    n_inputs = kernalquery[0] * kernalquery[1] * kernalquery[2],
                                    n_outputs = kernalquery[-1], activefunction = 'relu',
                                    variable_name = scope + 'conv_BW')
        BB = bias_variable([kernalquery[-1]], variable_name = scope +  'conv_BB')
        B_conv = conv2d(x, BW) + BB
        B_conv_new = tf.reshape(B_conv, [-1, H * W])

        CW = weight_xavier_init(shape = kernalquery,
                                n_inputs = kernalquery[0] * kernalquery[1] * kernalquery[2],
                                n_outputs = kernalquery[-1], activefunction = 'relu',
                                variable_name = scope + 'conv_CW')
        CB = bias_variable([kernalquery[-1]], variable_name = scope + 'conv_CB')
        C_conv = conv2d(x, CW) + CB
        C_conv_new = tf.reshape(C_conv, [-1, H * W])

        energy = tf.multiply(B_conv_new, C_conv_new)
        attention = tf.nn.sigmoid(energy)

        DW = weight_xavier_init(shape = kernalquery,
                                n_inputs = kernalquery[0] * kernalquery[1] * kernalquery[2],
                                n_outputs = kernalquery[-1], activefunction = 'relu',
                                variable_name= scope + 'convDW')
        DB = bias_variable([kernalquery[-1]], variable_name = scope + 'conv_DB')
        D_conv = conv2d(x, DW) + DB
        D_conv_new = tf.reshape(D_conv, [-1, H * W])

        out = tf.multiply(attention, D_conv_new)
        out_new = tf.reshape(out, [-1, H, W, C])

        out_new = resnet_Add(out_new, x)
        return out_new

def channelAttentionblock(x, scope = None):
    with tf.name_scope(scope):
        m_batchsize, H, W , C = x.get_shape().as_list()

        proj_query = tf.reshape(x, [-1, C])
        proj_key = tf.reshape(x, [-1, C])
        proj_query = tf.transpose(proj_query, [1, 0])

        energy = tf.matmul(proj_query, proj_key)
        attention = tf.nn.sigmoid(energy)

        proj_value = tf.reshape(x, [-1, C])
        proj_value = tf.transpose(proj_value, [1, 0])
        out = tf.matmul(attention, proj_value)

        out = tf.reshape(out, [-1, H, W , C])
        out = resnet_Add(out, x)
        return out

def _create_conv_net(X, image_width, image_height, image_channel, phase, drop_conv, n_class=1):
    inputX = tf.reshape(X, [-1, image_width, image_height, image_channel])  # shape=(?, 32, 32, 1)
    # UNet model
    # layer1->convolution
    layer0 = conv_bn_relu_drop(x = inputX, kernal = [3, 3, image_channel, 32], phase= phase, drop = drop_conv, scope = 'layer0')
    layer1 = conv_bn_relu_drop(x = layer0, kernal= [3, 3, 32, 32], phase = phase, drop=drop_conv, scope = 'layer1')

    pool1 = max_pool_2x2(layer1)

    # layer2->convolution
    layer2 = conv_bn_relu_drop(x = pool1, kernal = [3, 3, 32, 64], phase= phase, drop = drop_conv, scope= 'layer2_1')
    layer2 = conv_bn_relu_drop(x = layer2, kernal=[3, 3, 64, 64], phase = phase, drop = drop_conv, scope = 'layer2_2')

    pool2 = max_pool_2x2(layer2)

    # layer3->convolution
    layer3 = conv_bn_relu_drop(x = pool2, kernal= [3, 3, 64, 128], phase = phase, drop=drop_conv, scope = 'layer3_1')
    layer3 = conv_bn_relu_drop(x = layer3, kernal= [3, 3, 128, 128], phase = phase, drop=drop_conv, scope = 'layer3_2')

    pool3 = max_pool_2x2(layer3)

    # layer4->convolution
    layer4 = conv_bn_relu_drop(x = pool3, kernal= [3, 3, 128, 256], phase=phase, drop=drop_conv, scope = 'layer4_1')
    layer4 = conv_bn_relu_drop(x = layer4, kernal=[3, 3, 256, 256], phase=phase, drop=drop_conv, scope= 'layer4_2')

    pool4 = max_pool_2x2(layer4)

    # layer5->convolution
    layer5 = conv_bn_relu_drop(x = pool4, kernal= [3, 3, 256, 512], phase=phase, drop=drop_conv, scope='layer5_1')
    layer5 = conv_bn_relu_drop(x = layer5, kernal=[3, 3, 512, 512], phase=phase, drop = drop_conv, scope='layer5_2')

    # layer6->deconvolution

    deconv1 = deconv_relu(x = layer5, kernal=[3, 3, 256, 512], scope = 'deconv1')

    #dual model1
    pos_attenfeat1 = conv_bn_relu_drop(x = layer4, kernal = (3, 3, 256, 256 // 2), phase = phase, drop = drop_conv,
                                       scope = 'dual_layer1_1')
    pos_attenfeat1 = positionAttentionblock(x = pos_attenfeat1, inputfilter=256 // 2, outputfilter=256 // 2, scope = 'dual_pos_atten1')

    pos_attenfeat1 = conv_bn_relu_drop(x = pos_attenfeat1, kernal = (3, 3, 256 //2, 256 // 2), phase=phase, drop = drop_conv,
                                       scope = 'dual_layer1_2')
    cha_attenfeat1 = conv_bn_relu_drop(x = layer4, kernal=(3, 3, 256, 256 // 2), phase=phase, drop=drop_conv,
                                       scope = 'dual_layer1_3')
    cha_attenfeat1 = channelAttentionblock(cha_attenfeat1, 'dual_cha_atten1')
    cha_attenfeat1 = conv_bn_relu_drop(x = cha_attenfeat1, kernal = (3, 3, 256 // 2, 256 // 2), phase=phase, drop=drop_conv,
                                       scope='dual_layer1_4')
    feat_sum1 = resnet_Add(pos_attenfeat1, cha_attenfeat1)
    sasc_output1 = conv_bn_relu_drop(x = feat_sum1, kernal=(1, 1, 256 // 2, 256), phase=phase, drop=drop_conv,
                                     scope='dual_layer1_5')

    layer6 = crop_and_concat(sasc_output1, deconv1)


    # layer7->convolution
    layer6 = conv_bn_relu_drop(x = layer6, kernal= [3, 3, 512, 256], phase=phase, drop=drop_conv, scope = 'layer6_1')

    layer6 = conv_bn_relu_drop(x = layer6, kernal= [3, 3, 256, 256], phase= phase, drop=drop_conv, scope = 'layer6_2')

    deconv2 = deconv_relu(layer6, kernal=[3, 3, 128, 256], scope = 'deconv2')

    #dual model2
    pos_attenfeat2 = conv_bn_relu_drop(x = layer3, kernal=(3, 3, 128, 128 // 2), phase=phase, drop=drop_conv,
                                       scope='dual_layer2_1')
    pos_attenfeat2 = positionAttentionblock(pos_attenfeat2, inputfilter=128 // 2, outputfilter=128 // 2, scope='dual_pos_atten2')
    pos_attenfeat2 = conv_bn_relu_drop(x = pos_attenfeat2, kernal=(3, 3, 128 // 2, 128 // 2), phase=phase, drop=drop_conv,
                                       scope='dual_layer2_2')
    cha_attenfeat2 = conv_bn_relu_drop(x = layer3, kernal=(3, 3, 128, 128 // 2), phase=phase, drop=drop_conv,
                                       scope='dual_layer2_3')
    cha_attenfeat2 = channelAttentionblock(x = cha_attenfeat2, scope = 'dual_cha_atten2')
    cha_attenfeat2 = conv_bn_relu_drop(x = cha_attenfeat2, kernal=(3, 3, 128 // 2, 128 // 2), phase=phase, drop = drop_conv,
                                       scope='dual_layer2_4')
    feat_sum2 = resnet_Add(pos_attenfeat2, cha_attenfeat2)
    sasc_output2 = conv_bn_relu_drop(x = feat_sum2, kernal=(1, 1, 128 // 2, 128), phase=phase, drop=drop_conv,
                                     scope = 'dual_layer2_5')

    layer7 = crop_and_concat(sasc_output2, deconv2)

    # layer9->convolution
    layer7 = conv_bn_relu_drop(x = layer7, kernal= [3, 3, 256, 128], phase=phase, drop=drop_conv, scope = 'layer7_1')

    layer7 = conv_bn_relu_drop(x = layer7, kernal = [3, 3, 128, 128], phase=phase, drop=drop_conv, scope='layer7_2')


    # layer10->deconvolution
    deconv3 = deconv_relu(x = layer7, kernal= [3, 3, 64, 128], scope = 'deconv3')

    #dual model3
    pos_attenfeat3 = conv_bn_relu_drop(x = layer2, kernal=(3, 3, 64, 64 // 2), phase=phase, drop=drop_conv,
                                       scope = 'dual_layer3_1')
    pos_attenfeat3 = positionAttentionblock(x = pos_attenfeat3, inputfilter=64 // 2, outputfilter=64 // 2, scope = 'dual_pos_atten3')
    pos_attenfeat3 = conv_bn_relu_drop(x = pos_attenfeat3, kernal=(3, 3, 64 // 2, 64 // 2), phase=phase, drop=drop_conv,
                                       scope = 'dual_layer3_2')
    cha_attenfeat3 = conv_bn_relu_drop(x = layer2, kernal=(3, 3, 64, 64 // 2), phase=phase, drop=drop_conv,
                                       scope = 'dual_layer3_3')
    cha_attenfeat3 = channelAttentionblock(x = cha_attenfeat3, scope='dual_cha_atten3')
    cha_attenfeat3 = conv_bn_relu_drop(x = cha_attenfeat3, kernal=(3, 3, 64 // 2, 64 // 2), phase=phase, drop=drop_conv,
                                       scope='dual_layer3_4')
    feat_sum3 = resnet_Add(pos_attenfeat3, cha_attenfeat3)
    sasc_output3 = conv_bn_relu_drop(x = feat_sum3, kernal=(1, 1, 64 // 2, 64), phase=phase, drop=drop_conv,
                                     scope='dual_layer3_5')
    layer8 = crop_and_concat(sasc_output3, deconv3)

    # layer11->convolution
    layer8 = conv_bn_relu_drop(x = layer8, kernal= [3, 3, 128, 64], phase=phase, drop=drop_conv, scope='layer8_1')

    layer8 = conv_bn_relu_drop(x = layer8, kernal= [3, 3, 64, 64], phase=phase, drop=drop_conv, scope='layer8_2')

    deconv4 = deconv_relu(layer8, kernal=[3, 3, 32, 64], scope='deconv4')

    #dual model4
    pos_attenfeat4 = conv_bn_relu_drop(x = layer1, kernal=(3, 3, 32, 32 // 2), phase=phase, drop=drop_conv,
                                       scope='dual_layer4_1')
    pos_attenfeat4 = positionAttentionblock(x = pos_attenfeat4, inputfilter=32 // 2, outputfilter=32 // 2, scope = 'dual_pos_atten4')
    pos_attenfeat4 = conv_bn_relu_drop(x = pos_attenfeat4, kernal=(3, 3, 32 //2, 32 // 2), phase=phase, drop=drop_conv,
                                       scope = 'dual_layer4_2')
    cha_attenfeat4 = conv_bn_relu_drop(x = layer1, kernal=(3, 3, 32, 32 //2), phase=phase, drop=drop_conv,
                                       scope='dual_layer4_3')
    cha_attenfeat4 = channelAttentionblock(x = cha_attenfeat4, scope = 'dual_cha_atten4')
    cha_attenfeat4 = conv_bn_relu_drop(x = cha_attenfeat4, kernal=(3, 3, 32 //2, 32//2), phase=phase, drop=drop_conv,
                                       scope='dual_layer4_5')
    feat_sum4 = resnet_Add(pos_attenfeat4, cha_attenfeat4)
    sasc_output4 = conv_bn_relu_drop(x = feat_sum4, kernal=(1, 1, 32 //2, 32), phase=phase, drop=drop_conv,
                                     scope='dual_layer4_5')

    layer9 = crop_and_concat(sasc_output4, deconv4)

    # layer 13->convolution
    layer9 = conv_bn_relu_drop(x = layer9, kernal=[3, 3, 64, 32], phase=phase, drop=drop_conv, scope='layer9_1')

    layer9 = conv_bn_relu_drop(x = layer9, kernal=[3, 3, 32, 32], phase=phase, drop=drop_conv, scope='layer9_2')

    # layer14->output
    W14 = weight_xavier_init(shape=[1, 1, 32, n_class], n_inputs=1 * 1 * 32, n_outputs=n_class)
    B14 = bias_variable([n_class])
    output_map = tf.nn.sigmoid(conv2d(layer9, W14) + B14, name='output')
    return output_map


def _next_batch(train_images, train_labels, batch_size, index_in_epoch):
    start = index_in_epoch
    index_in_epoch += batch_size

    num_examples = train_images.shape[0]
    # when all trainig data have been already used, it is reorder randomly
    if index_in_epoch > num_examples:
        # shuffle the data
        perm = np.arange(num_examples)
        np.random.shuffle(perm)
        train_images = train_images[perm]
        train_labels = train_labels[perm]
        # start next epoch
        start = 0
        index_in_epoch = batch_size
        assert batch_size <= num_examples
    end = index_in_epoch
    return train_images[start:end], train_labels[start:end], index_in_epoch


class unet2dModule(object):
    """
    A unet2d implementation

    :param image_height: number of height in the input image
    :param image_width: number of width in the input image
    :param channels: number of channels in the input image
    :param n_class: number of output labels
    :param costname: name of the cost function.Default is "cross_entropy"
    """

    def __init__(self, image_height, image_width, channels=1, costname="dice coefficient"):
        self.image_with = image_width
        self.image_height = image_height
        self.channels = channels

        self.X = tf.placeholder("float", shape=[None, image_height, image_width, channels], name="Input")
        self.Y_gt = tf.placeholder("float", shape=[None, image_height, image_width, 1], name="Output_GT")
        self.lr = tf.placeholder('float', name="Learning_rate")
        self.phase = tf.placeholder(tf.bool, name="Phase")
        self.drop_conv = tf.placeholder('float', name="DropOut")

        self.Y_pred = _create_conv_net(self.X, image_width, image_height, channels, self.phase, self.drop_conv)

        self.cost = self.__get_cost(costname)
        self.accuracy = -self.__get_cost(costname)

    def __get_cost(self, cost_name):
        H, W, C = self.Y_gt.get_shape().as_list()[1:]
        if cost_name == "dice coefficient":
            smooth = 1e-5
            pred_flat = tf.reshape(self.Y_pred, [-1, H * W * C])
            true_flat = tf.reshape(self.Y_gt, [-1, H * W * C])
            intersection = 2 * tf.reduce_sum(pred_flat * true_flat, axis=1) + smooth
            denominator = tf.reduce_sum(pred_flat, axis=1) + tf.reduce_sum(true_flat, axis=1) + smooth
            loss = -tf.reduce_mean(intersection / denominator)
        if cost_name == "pixelwise_cross entroy":
            assert (C == 1)
            flat_logit = tf.reshape(self.Y_pred, [-1])
            flat_label = tf.reshape(self.Y_gt, [-1])
            loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=flat_logit, labels=flat_label))
        return loss

    def train(self, train_images, train_lanbels, model_path, logs_path, learning_rate,
              dropout_conv=0.8, train_epochs=1000, batch_size=2):
        train_op = tf.train.AdamOptimizer(self.lr).minimize(self.cost)

        init = tf.global_variables_initializer()
        saver = tf.train.Saver(tf.all_variables())

        tf.summary.scalar("loss", self.cost)
        tf.summary.scalar("accuracy", self.accuracy)
        merged_summary_op = tf.summary.merge_all()
        sess = tf.InteractiveSession(config=tf.ConfigProto(allow_soft_placement=True))
        summary_writer = tf.summary.FileWriter(logs_path, graph=tf.get_default_graph())
        sess.run(init)
        if os.path.isfile(model_path):
            saver.restore(sess, model_path)

        DISPLAY_STEP = 1
        index_in_epoch = 0

        for i in range(train_epochs):
            # get new batch
            batch_xs_path, batch_ys_path, index_in_epoch = _next_batch(train_images, train_lanbels, batch_size,
                                                                       index_in_epoch)
            batch_xs = np.empty((len(batch_xs_path), self.image_height, self.image_with, self.channels))
            batch_ys = np.empty((len(batch_ys_path), self.image_height, self.image_with, 1))

            for num in range(len(batch_xs_path)):
                image = cv2.imread(batch_xs_path[num][0], cv2.IMREAD_COLOR)
               # cv2.imwrite('image_src.bmp', image)
                label = cv2.imread(batch_ys_path[num][0], cv2.IMREAD_GRAYSCALE)
                #cv2.imwrite('zbqzbq.bmp', label)
                batch_xs[num, :, :, :] = np.reshape(image, (self.image_height, self.image_with, self.channels))
                batch_ys[num, :, :, :] = np.reshape(label, (self.image_height, self.image_with, 1))
               # print("ffffffffffffffffffff")
            # Extracting images and labels from given data
            batch_xs = batch_xs.astype(np.float)
            batch_ys = batch_ys.astype(np.float)
            # Normalize from [0:255] => [0.0:1.0]
            batch_xs = np.multiply(batch_xs, 1.0 / 255.0)
            batch_ys = np.multiply(batch_ys, 1.0 / 255.0)
            # check progress on every 1st,2nd,...,10th,20th,...,100th... step
            if i % DISPLAY_STEP == 0 or (i + 1) == train_epochs:
                train_loss, train_accuracy = sess.run([self.cost, self.accuracy], feed_dict={self.X: batch_xs,
                                                                                             self.Y_gt: batch_ys,
                                                                                             self.lr: learning_rate,
                                                                                             self.phase: 1,
                                                                                             self.drop_conv: dropout_conv})
                pred = sess.run(self.Y_pred, feed_dict={self.X: batch_xs,
                                                        self.Y_gt: batch_ys,
                                                        self.phase: 1,
                                                        self.drop_conv: 1})
                result = np.reshape(pred[0], (512, 512))
                result = result.astype(np.float32) * 255.
                result = np.clip(result, 0, 255).astype('uint8')
                cv2.imwrite("result.bmp", result)
                print('epochs %d training_loss ,Training_accuracy => %.5f,%.5f ' % (i, train_loss, train_accuracy))
                if i % (DISPLAY_STEP * 10) == 0 and i:
                    DISPLAY_STEP *= 10

                    # train on batch
            _, summary = sess.run([train_op, merged_summary_op], feed_dict={self.X: batch_xs,
                                                                            self.Y_gt: batch_ys,
                                                                            self.lr: learning_rate,
                                                                            self.phase: 1,
                                                                            self.drop_conv: dropout_conv})
            summary_writer.add_summary(summary, i)
        summary_writer.close()

        save_path = saver.save(sess, model_path)
        print("Model saved in file:", save_path)

    def prediction(self, model_path, test_images):
        init = tf.global_variables_initializer()
        saver = tf.train.Saver()
        sess = tf.InteractiveSession()
        sess.run(init)
        saver.restore(sess, model_path)

        test_images = np.reshape(test_images, (1, test_images.shape[0], test_images.shape[1], self.channels))
        # test_label = cv2.imread("D:\Data\GlandCeil\Test\Mask\\train_37_anno.bmp", 0)
        # test_label = np.multiply(test_label, 1.0 / 255.0)
        # test_label = np.reshape(test_label, (1, test_label.shape[0], test_label.shape[1], 1))
        pred = sess.run(self.Y_pred, feed_dict={self.X: test_images,
                                                self.phase: 1,
                                                self.drop_conv: 1})
        result = np.reshape(pred, (test_images.shape[1], test_images.shape[2]))
        result = result.astype(np.float32) * 255.
        result = np.clip(result, 0, 255).astype('uint8')
        return result
