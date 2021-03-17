# -
**基于密集连接块和自注意力机制的腺体细胞分割方法**



**基本网络模型为**：



![基于密集连接块和自注意力机制的改进U-Net模型](https://github.com/BaoqiZhao/Dense-connective-blocks-and-self-attention-mechanism-based-glandular-cell-seg-mentation/blob/master/images/%E5%9F%BA%E4%BA%8E%E5%AF%86%E9%9B%86%E8%BF%9E%E6%8E%A5%E5%9D%97%E5%92%8C%E8%87%AA%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%9C%BA%E5%88%B6%E7%9A%84%E6%94%B9%E8%BF%9BU-Net%E6%A8%A1%E5%9E%8B.png)

在整个框架上，用密集连接块代替之前的卷积操作；在解码器端，把生成的特征图送入自注意力机制模块生成新的特征图，且和编码器端生成的特征图进行相加操作，最后将网路生成的高分辨率特征图通过1x1的卷积映射转化为通道数为2的特征图，送入softmax分类器以获得每个像素为细胞的概率值，得到细胞的分割概率图。



**密集连接块**

![image-20200822215205070](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822215205070.png)

将每经过一次卷积的特征图保留下来，最后合并所有的输出通道。



**自注意力机制**

![融合位置注意力模块和通道注意力模块](https://github.com/BaoqiZhao/Dense-connective-blocks-and-self-attention-mechanism-based-glandular-cell-seg-mentation/blob/master/images/%E8%9E%8D%E5%90%88%E4%BD%8D%E7%BD%AE%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%A8%A1%E5%9D%97%E5%92%8C%E9%80%9A%E9%81%93%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%A8%A1%E5%9D%97.png)

分为位置注意力模块和通道注意力模块。

**位置注意力模块**

![image-20200822215230320](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822215230320.png)

**通道注意力模块**

![image-20200822215250831](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822215250831.png)





**最后的分割效果**

![image-20200822215346884](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822215346884.png)

​						原图							GT						SegNet					 U-Net					 Ours
