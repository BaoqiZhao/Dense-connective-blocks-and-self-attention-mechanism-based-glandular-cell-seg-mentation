# -
**基于密集连接块和自注意力机制的腺体细胞分割方法**



**基本网络模型为**：

![image-20200822205824209](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822205824209.png)

在整个框架上，用密集连接块代替之前的卷积操作；在解码器端，把生成的特征图送入自注意力机制模块生成新的特征图，且和编码器端生成的特征图进行相加操作，最后将网路生成的高分辨率特征图通过1x1的卷积映射转化为通道数为2的特征图，送入softmax分类器以获得每个像素为细胞的概率值，得到细胞的分割概率图。



**密集连接块**

![image-20200822210420659](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822210420659.png)

将每经过一次卷积的特征图保留下来，最后合并所有的输出通道。



**自注意力机制**

![image-20200822210601458](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822210601458.png)

分为位置注意力模块和通道注意力模块。

**位置注意力模块**

![image-20200822210639088](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822210639088.png)

**通道注意力模块**

![image-20200822210742917](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822210742917.png)





最后的分割效果

![image-20200822210916909](C:\Users\Mosu\AppData\Roaming\Typora\typora-user-images\image-20200822210916909.png)

​						原图							GT						SegNet					 U-Net					 Ours