# Pulsesensor 脉搏传感器  (slug sonzrn48r5gn29pa, words 703)


## 一、介绍
PulseSensor是 一款用于脉搏心率测量的光电发射式模拟传感器。将其佩戴在手指或耳垂等处，通过导线连接可将采集到的模拟信号传输给Arduino等单片机用来转换为数字信号，再通过Arduino单片机简单计算后就可以得到心率数值，此外还可以将脉搏波形上传到电脑上显示波形。PulseSensor是一款开源硬件，提供对应的Arduino程序和上位机Processing程序。其适用于心率方面的科学研究和教学演示，也非常适合用于二次开发。
## 二、技术规格
电路板直径：16mm
电路板厚度：1.6mm（普通PCB板厚度）
LED峰值波长：515nm
供电电压：3.3V或5V均可
输出信号类型：模拟信号
输出信号大小：0~3.3V（3.3V电源）或 0~5V（5V电源）
​
## 三、脉搏传感器引脚说明
[IMAGE: https://cdn.nlark.com/yuque/0/2023/png/601548/1676217382962-0e9ac81a-afaf-492b-8d12-cc9371bc38c6.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_15%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
​
​
从左往右依次为：
​
模拟信号输出端（0~3.0V）
电源输入正极（3.3 ~ 5.5V）
电源输入负极
## 四、操作使用步骤
## 1. 硬件配置
Arduino UNO控制板（或类似）*1；
脉搏传感器 *1；
绑带 *1。
## 2. 软件配置
Arduino IDE（推荐1.8.2及以上）
[YUQUE-DOC: 如何正确安装Arduino IDE？ https://sichiray-tech.yuque.com/dm0eyv/hx34hp/dqubiq?singleDoc#]
​
## 3. 接线
GND-GND
5V-5V
sig-A0
## 4. 示例代码
## ① 下载代码
[FILE: arduino示例源码.rar -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/rar/314712/1678179484462-c7f1fdb7-f50b-4b8c-8eda-a56804b0ba28.rar size=3829]
请自行下载并解压。
必须解压后再打开源码，否则会报错
​
## ② 打开代码
解压后，双击打开文件夹，如下图看见两个Arduino程序文件；
[IMAGE: https://cdn.nlark.com/yuque/0/2023/png/314712/1677830075602-00800365-b90d-4d77-a194-97e965db79eb.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_13%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
双击打开后一个PulseSensorAmped..文件。
​
## ③ 选择单片机类型和端口
[YUQUE-DOC: Arduino IDE中如何选择端口和单片机类型？ https://sichiray-tech.yuque.com/dm0eyv/hx34hp/kqudokgmgqxxrhkg?singleDoc#]
## ④ 烧录代码
[YUQUE-DOC: 如何烧录代码？ https://www.yuque.com/cs/pzvlfp/fe8k5g]
## 5. 数据结果
## ① 上位机
## a. 下载上位机
代码上传成功后，下载下面的👇👇👇电脑端上位机
[FILE: 脉搏传感器Pluse Sensor上位机.rar -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/rar/314712/1678179484550-18457f8f-a66f-472b-a4dc-ff6cb200479f.rar size=34425765]
请自行下载并解压安装。
## 
[IMAGE: https://cdn.nlark.com/yuque/0/2023/png/314712/1677830554086-90339c72-232a-4ae8-84dd-f392d2ed3ba1.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_39%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
## b. 选择端口和波特率
选择正确的端口和波特率，即可出现波形。
​
 选择端口 
[YUQUE-DOC: 如何查看串口？ https://sichiray-tech.yuque.com/dm0eyv/hx34hp/segrlm?singleDoc#]
 波特率 115200
## c. 上位机操作视频
[VIDEO: None 脉搏传感器上位机 (1).mp4]
​
## ② 串口助手
## 
## 五、连接示波器
[VIDEO: None 脉搏示波器.mp4]
​
​
## 六、模块原理图、说明书
[FILE: PulseSensor原理图.pdf -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/pdf/314712/1678179484673-6a73b151-51b4-4465-9986-376ed17379a1.pdf size=21245]
[FILE: PulseSensor说明书.pdf -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/pdf/314712/1678179484791-3ff68450-be48-48e2-842a-9df7ffa39361.pdf size=921471]
👉 点击前往淘宝购买：PulseSensor脉搏传感器
[IMAGE: https://cdn.nlark.com/yuque/0/2023/jpeg/314712/1673925151128-ca922720-91f5-4e40-8626-5f5fefee4073.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_46%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqAMDUxMC02Njc1OTYyMQ%3D%3D%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10%2Fresize%2Cw_937%2Climit_0%2Finterlace%2C1%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_27%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
[IMAGE: https://cdn.nlark.com/yuque/0/2023/jpeg/314712/1673922911372-6735b779-c3ad-41c2-9617-be6a3689177b.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_55%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqAMDUxMC02Njc1OTYyMQ%3D%3D%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10%2Fresize%2Cw_937%2Climit_0%2Finterlace%2C1%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_27%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
👇👇👇👇👇👇👇👇
