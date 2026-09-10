#  GSR皮肤电Arduino开发套件  (slug iqepdr0qglekrtc3, words 1617)


## 一、简介
GSR 代表皮肤电反应，是一种在皮肤电压测量方法。强烈的情绪会刺激你的交感神经系统，导致汗腺分泌更多的汗液。GSR 可以发现这种强烈的情绪通过简单的连接两个电极，一手的两个手指。这是一个有关情绪的项目，如睡眠质量监测。
人体是导电的，原理是当你说谎、激动、紧张的时候手指会出汗，出汗之后电位反应发生变化，我们的皮电传感器检测的就是电反应变化。
我们的工作时间是周一到周五的8.30-17.30，其他时间可以电话沟通
周六周日不在线，如果遇到产品不懂或者需要资料，可直接联系18862759823，微信同号
## 二、参数说明
检测皮肤电反应
电极用手指带
用于检测强烈的情绪
3.3V 和 5V 双模式
Ardunio 兼容 UNO NANO MINI
注意：此套件不作为医疗设备使用。
## 三、使用步骤(采用 Arduino uno 开发板)
## 1、产品清单
在拿到传感器套件后，让我们打开包装，看一看都包含哪些东西。
GSR皮肤电模块；
指套及连接线；
盾板；
Arduino uno开发板；
USB连接线。
[IMAGE: https://cdn.nlark.com/yuque/0/2023/jpeg/601548/1676256217316-03af3f0a-d6cf-4402-a4c8-56e3e0a0b6a9.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_65%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
## 2、接线
① 将绿色盾板和uno 单片机对插，盾板上有3个排母，分别为GND,VCC,A2（见下图👇👇👇）；
② 将GSR皮电传感器的排针一对一插入，指套插入到传感器上面的圆孔，注意一定要用力插到底插紧（见下图👇👇👇）；
[IMAGE: https://cdn.nlark.com/yuque/0/2023/jpeg/601548/1676256386229-005fed20-1261-4b31-b995-a80aa802a958.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_36%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
③ 若你没有盾板，需要自己准备杜邦线连接传感器和uno开发板，也一样。
GND-GND
5V-5V
out-A0
## 3、信号类型
传感器输出信号为：模拟信号。需要用单片机处理为：数字信号。
## 4、烧录代码
## ① 安装Arduino IDE
[YUQUE-DOC: 如何正确安装Arduino IDE？ https://sichiray-tech.yuque.com/dm0eyv/hx34hp/dqubiq?singleDoc#]
如已安装，此步可忽略。
## ② 复制代码
设备连接好后，打开已安装好的Arduino软件，将下面👇👇👇的GSR Arduino源码复制粘贴到Arduino IDE中；
​
```cpp
// Arduino code is available to download - link below the video
/* 
GSR connection pins to Arduino microcontroller
Arduino GSR
GND GND
5V VCC
A0 SIG
D13 RED LED
*/
/*
GSR, standing for galvanic skin response, is a method of 
measuring the electrical conductance of the skin. Strong 
emotion can cause stimulus to your sympathetic nervous 
system, resulting more sweat being secreted by the sweat 
glands. Grove – GSR allows you to spot such strong emotions 
by simple attaching two electrodes to two fingers on one hand,
an interesting gear to create emotion related projects, like 
sleep quality monitor. http://www.seeedstudio.com/wiki/Grove_-_GSR_Sensor
*/
const int LED=13;
const int GSR=A0;
int threshold=0;
int sensorValue;
void setup(){
 long sum=0;
 Serial.begin(9600);
 pinMode(LED,OUTPUT);
 digitalWrite(LED,LOW);
 delay(1000);
 for(int i=0;i60)
 {
 sensorValue=analogRead(GSR);
 temp = threshold - sensorValue;
 if(abs(temp)>60){
 digitalWrite(LED,HIGH);
 Serial.println("Emotion Changes Detected!");
 delay(3000);
 digitalWrite(LED,LOW);
 delay(1000);
 }
 }
}
```
[IMAGE: https://cdn.nlark.com/yuque/0/2020/png/314712/1583197949462-8ed25968-8bee-409d-9c71-9537cab50609.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_33%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
## ③ 查看端口
[YUQUE-DOC: 如何查看串口？ https://sichiray-tech.yuque.com/dm0eyv/hx34hp/segrlm?singleDoc#]
​
## ④ 选择端口和单片机类型
[YUQUE-DOC: Arduino IDE中如何选择端口和单片机类型？ https://sichiray-tech.yuque.com/dm0eyv/hx34hp/kqudokgmgqxxrhkg?singleDoc#]
## ⑤ 编译、上传
编译、上传成功后左下角会有上传成功提示（如下图👇👇👇）；
​
[IMAGE: https://cdn.nlark.com/yuque/0/2020/png/314712/1583198004457-c126e7a5-04df-4647-be4b-0bf57cd9fa86.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_33%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
## ⑥ 查看数据
点击右上角的串口监视器（如下图👇👇👇）；
[IMAGE: https://cdn.nlark.com/yuque/0/2020/png/314712/1583198167405-9395bcef-875b-4c19-9283-37b9da159461.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_13%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
就可以看到皮电数据（如下图👇👇👇）。
​
[IMAGE: https://cdn.nlark.com/yuque/0/2023/png/601548/1676256909301-e1e7f539-47e0-4c65-81b3-7a68dfb2c44d.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_37%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
## 如何计算电压？
比如读数500 除以arduino单片机AD位数 1024 乘以 3.3V基准电压 在除以2级放大
​
## 四、操作视频
[CARD thirdparty: {"entrance": "bilibili", "src": "https://player.bilibili.com/player.html?bvid=BV1zM411w73y", "url": "https://player.bilibili.com/player.html?bvid=BV1zM411w73y", "type": "bilibili", "id": "Yzrdc"}]
## 使用串口软件绘制波形
1、接线同上
代码需要替换成下面的代码
```c
/******************************************************************************
 * 无锡市思知瑞科技有限公司
 * 淘宝店铺：大脑实验室
 * 店铺网址：http://brainlab.taobao.com
 * 工作日联系电话：0510-66759621
******************************************************************************/
#include 
#include 
#define OLED_Address 0x3C
Adafruit_SSD1306 oled(128, 64);
#define DEBUG //取消注释，在上位机显示
typedef struct // 曲线参数
{
 float Draw_Buf[128]; // 曲线数据缓存
 float Draw_Min; // 缓存数据的最小值 单位为百分比
 float Draw_Max; // 缓存数据的最大值
} _DrawCurve; // 曲线参数
static _DrawCurve DrawCurve;
void PlotDataInput(_DrawCurve *Draw, float val) {
 uint8_t i;
 for (i = 1; i Draw_Buf[i - 1] = Draw->Draw_Buf[i];
 }
 Draw->Draw_Buf[127] = val;
 if (Draw->Draw_Buf[127] > 1)
 Draw->Draw_Buf[127] = 1;
 else if (Draw->Draw_Buf[127] Draw_Buf[127] = 0;
/******************************************************************************
 * 无锡市思知瑞科技有限公司
 * 淘宝店铺：大脑实验室
 * 店铺网址：http://brainlab.taobao.com
 * 工作日联系电话：0510-66759621
******************************************************************************/
 Draw->Draw_Max = 0;
 Draw->Draw_Min = 1;
 for (i = 0; i Draw_Min > (Draw->Draw_Buf[i])) {
 Draw->Draw_Min = Draw->Draw_Buf[i];
 Draw->Draw_Min = (float)((uint8_t)(Draw->Draw_Min * 100) / 5) / 20;
 if (Draw->Draw_Min Draw_Min = 0;
 if ((Draw->Draw_Max - Draw->Draw_Min) Draw_Max = Draw->Draw_Min + 0.05;
 } else if (Draw->Draw_Max Draw_Buf[i]) {
 Draw->Draw_Max = Draw->Draw_Buf[i];
 Draw->Draw_Max = (float)((uint8_t)(Draw->Draw_Max * 100) / 5 + 1) / 20;
 if (Draw->Draw_Max > 1.0)
 Draw->Draw_Max = 1.0;
 if ((Draw->Draw_Max - Draw->Draw_Min) Draw_Min = Draw->Draw_Max - 0.05;
 }
 }
}
void PlotDataPrint(_DrawCurve *Draw, int fllor, int upper, int lineColor) {
 for (int x = 1; x Draw_Max - Draw->Draw_Min); // Y轴缩放系数
 float last_y = upper - ((Draw->Draw_Buf[x - 1] - Draw->Draw_Min) * k);
 float now_y = upper - ((Draw->Draw_Buf[x] - Draw->Draw_Min) * k);
 oled.drawLine(x - 1, last_y, x, now_y, lineColor);
 }
}
void setup() {
#ifndef DEBUG
 oled.begin(SSD1306_SWITCHCAPVCC, OLED_Address);
 oled.clearDisplay();
#else
 Serial.begin(115200);
#endif
 delay(100);
}
void loop() {
 static uint16_t value = 0;
 value = analogRead(A0);
#ifndef DEBUG
 PlotDataInput(&DrawCurve, value / 1024.0); // 传入数据
 oled.clearDisplay();
 PlotDataPrint(&DrawCurve, 10, 60, WHITE); // 打印曲线
 oled.display();
#else
 Serial.println(value);
 delay(5);
#endif
}
/******************************************************************************
 * 无锡市思知瑞科技有限公司
 * 淘宝店铺：大脑实验室
 * 店铺网址：http://brainlab.taobao.com
 * 工作日联系电话：0510-66759621
******************************************************************************/
```
下载软件
[FILE: 思知瑞调试助手.rar -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/rar/314712/1683695771561-a715e572-1bff-4417-a8ab-1af080acab52.rar size=19848562]
下载下面的文件，打开软件。点文件，导入设置，选择此文件即可，在选择串口号，打开串口即可
[FILE: 皮电设置.ini -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/ini/601548/1682659774793-0682b0e7-22e2-41f9-8c94-c2053eda3739.ini size=6069]
[IMAGE: https://cdn.nlark.com/yuque/0/2023/png/601548/1682660029363-ddabe194-6a05-4ae0-a338-fc2f2104be31.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_55%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
## 操作录屏
[VIDEO: None 皮电上位机.mp4]
## 五、附赠资料
[FILE: arduino_入门到精通教程 24节.zip -> https://sichiray-tech.yuque.com/attachments/yuque/0/2022/zip/314712/1660529955017-a3a4f6b3-7690-46be-ad8f-a1bb5c447619.zip size=22592437]
## 常见问题
## 1、电反应测得是什么？
测得是电压变化
## 2、如何计算电压？
比如读数500 除以arduino单片机AD位数 1024 乘以 3.3V基准电压 在除以2级放大
​
​
​
​
​
​
👉  点击前往淘宝店铺购买：GSR皮肤电开发套件
​
​
[IMAGE: https://cdn.nlark.com/yuque/0/2023/jpeg/314712/1673925151128-ca922720-91f5-4e40-8626-5f5fefee4073.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_46%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
[IMAGE: https://cdn.nlark.com/yuque/0/2023/jpeg/314712/1673922911372-6735b779-c3ad-41c2-9617-be6a3689177b.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_55%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
👇👇👇👇👇👇👇👇
