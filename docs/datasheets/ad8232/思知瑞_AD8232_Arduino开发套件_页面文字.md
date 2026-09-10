# Arduino开发套件  (slug xcc21h2u7ps3dird, words 939)


## 一、Arduino IDE下载安装
[YUQUE-DOC: 如何正确安装Arduino IDE？ https://sichiray-tech.yuque.com/docs/share/f4417d1e-f94a-4053-829d-792979f55633?#]
​
## 二、Arduino驱动
[YUQUE-DOC: CH341驱动安装 https://sichiray-tech.yuque.com/dm0eyv/wvt08q/kb1xhz]
​
## 四、电极贴位置
​
红色：右胸
​
绿色：左胸
​
橙色：右腹
[IMAGE: https://cdn.nlark.com/yuque/0/2023/png/601548/1676216339931-bc439903-ed5e-425e-808c-a58d678dd182.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_10%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
8232模块--uno单片机
3.3v----------5v
gnd----------gnd
out-----------a0
lo- ---------11
L0+ ---------10
​
## 五、复制下面Arduino示例代码到arduino IDE上传
## 采样率 100Hz，放大倍数 100倍
```c
/******************************************************************************
 * 无锡市思知瑞科技有限公司
 * 淘宝店铺：大脑实验室
 * 店铺网址：http://brainlab.taobao.com
 * 工作日联系电话：0510-66759621
******************************************************************************/
void setup() {
 // initialize the serial communication:
 Serial.begin(9600);
 pinMode(10, INPUT); // Setup for leads off detection LO +
 pinMode(11, INPUT); // Setup for leads off detection LO -
}
void loop() {
 if((digitalRead(10) == 1)||(digitalRead(11) == 1)){
 Serial.println('!');
 }
 else{
 // send the value of analog input 0:
 Serial.println(analogRead(A0));
 }
 //Wait for a bit to keep serial data from saturating
 delay(1);
}
/******************************************************************************
 * 无锡市思知瑞科技有限公司
 * 淘宝店铺：大脑实验室
 * 店铺网址：http://brainlab.taobao.com
 * 工作日联系电话：0510-66759621
******************************************************************************/
```
上传成功，点开工具，串口绘图器，波特率9600即可显示数据
​
​
## 六、使用processing看波形
## Processing下载安装
（请根据系统版本下载对应的软件）
​
[FILE: 上位机32位平台.zip -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/zip/314712/1678179484121-4ad6ee98-5f07-4aed-a2a4-afe37bfcf324.zip size=113274496]
[FILE: 上位机64位平台.zip -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/zip/314712/1678179484293-d5835ddc-7c73-4986-9fe8-47eba98750f1.zip size=114769586]
## 七、Processing源码
```c
/******************************************************************************
http://brainlab.taobao.com
0510-66759621
******************************************************************************/
import processing.serial.*;
Serial myPort; // The serial port
int xPos = 1; // horizontal position of the graph
float height_old = 0;
float height_new = 0;
float inByte = 0;
void setup () {
 // set the window size:
 size(1000, 400); 
 // List all the available serial ports
 println(Serial.list());
 // Open whatever port is the one you're using.
 myPort = new Serial(this, Serial.list()[2], 9600);
 // don't generate a serialEvent() unless you get a newline character:
 myPort.bufferUntil('\n');
 // set inital background:
 background(0xff);
}
void draw () {
 // everything happens in the serialEvent()
}
void serialEvent (Serial myPort) {
 // get the ASCII string:
 String inString = myPort.readStringUntil('\n');
 if (inString != null) {
 // trim off any whitespace:
 inString = trim(inString);
 // If leads off detection is true notify with blue line
 if (inString.equals("!")) { 
 stroke(0, 0, 0xff); //Set stroke to blue ( R, G, B)
 inByte = 512; // middle of the ADC range (Flat Line)
 }
 // If the data is good let it through
 else {
 stroke(0xff, 0, 0); //Set stroke to red ( R, G, B)
 inByte = float(inString); 
 }
 //Map and draw the line for new data point
 inByte = map(inByte, 0, 1023, 0, height);
 height_new = height - inByte; 
 line(xPos - 1, height_old, xPos, height_new);
 height_old = height_new;
 // at the edge of the screen, go back to the beginning:
 if (xPos >= width) {
 xPos = 0;
 background(0xff);
 } 
 else {
 // increment the horizontal position:
 xPos++;
 }
 }
}
/******************************************************************************
http://brainlab.taobao.com
0510-66759621
******************************************************************************/
```
打开processing 示例，点击第一个运行图标，即可看到数据
​
​
## 八、Processing报错处理
processing上位机代码报错：注意数字要根据串口的数量去修改对应的数字
[IMAGE: https://cdn.nlark.com/yuque/0/2020/jpeg/601548/1590398563197-0f6c17f7-4600-477c-8ad3-5e037b770c5f.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_22%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
有使用processing 版本过高代码也会报错，必须要使用我们资料里面给的processing版本2.1.2
[IMAGE: https://cdn.nlark.com/yuque/0/2020/jpeg/601548/1590398617164-d76e7964-d38b-4c20-b0ba-0d442d78b470.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_115%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
## 接示波器视频
gnd-gnd
3.3v-5v
out-接示波器钩子
​
[FILE: a83c6b3966494cde55f9162e4bdee12c.mp4 -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/mp4/601548/1684401731241-f3945e7e-d38d-4993-b98d-db8cc203aeeb.mp4 size=3089733]
[FILE: 6ff55849cdb1b07c0f40955ac2ed794b.mp4 -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/mp4/601548/1684401743942-a55c0f45-7c04-4b25-8721-7c7da01096c0.mp4 size=3036040]
## 九、相关资料下载
[FILE: AD8232_中文芯片手册.pdf -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/pdf/314712/1678179484429-40f01276-987d-4ee8-a35b-60bafdd7ee72.pdf size=869587]
[FILE: AD8232英文手册.pdf -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/pdf/314712/1678179484571-4222414e-22d9-4e8c-a8aa-1c05cc60861c.pdf size=660661]
[FILE: AD8232与Arduino接线图.pdf -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/pdf/314712/1678179484665-faac3a08-eeac-4fd9-8601-98cacb245643.pdf size=4974328]
[FILE: 单模块心电说明书(AD8232).pdf -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/pdf/314712/1678179484780-e3e6130a-5800-4406-965d-5f3e4daf5b27.pdf size=558328]
AD8232模块原理图
[IMAGE: https://cdn.nlark.com/yuque/0/2022/jpeg/314712/1662515158681-e02102ad-9029-4072-af6b-da7b3ab9f059.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_47%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
## 十、操作视频
[VIDEO: None ad8232 Arduino.mp4]
## 十一、辅助资料
[FILE: arduino_入门到精通教程 24节.zip -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/zip/314712/1678179484877-56cb003e-e18d-4767-a9a8-170030ffe16c.zip size=22592437]
[FILE: Processing_中文开发教程.pdf -> https://sichiray-tech.yuque.com/attachments/yuque/0/2023/pdf/314712/1678179485035-870eafb3-4e5c-4985-b172-53554f17931e.pdf size=733658]
[YUQUE-DOC: 脉搏心率关系 https://sichiray-tech.yuque.com/dm0eyv/qkkes1/dcv5gv]
## 十二、FAQ常见问题
波形不对
[IMAGE: https://cdn.nlark.com/yuque/0/2023/png/601548/1681726842116-31186078-3b67-4b00-9a51-460a8c36f8da.png?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_24%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
笔记本电脑电源拔掉，隔绝50hz工频干扰；
电极贴贴的位置不对；
电极贴没有换新。
---
​
​
👉 点击前往淘宝店铺购买：AD8232 Arduino开发套件
​
我们的工作时间是周一到周五的8.30-17.30，其他时间可以电话沟通
周六周日不在线，如果遇到产品不懂或者其他咨询，可直接联系18862759823，微信同号
[IMAGE: https://cdn.nlark.com/yuque/0/2023/jpeg/314712/1673925151128-ca922720-91f5-4e40-8626-5f5fefee4073.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_46%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
[IMAGE: https://cdn.nlark.com/yuque/0/2023/jpeg/314712/1673922911372-6735b779-c3ad-41c2-9617-be6a3689177b.jpeg?x-oss-process=image%2Fwatermark%2Ctype_d3F5LW1pY3JvaGVp%2Csize_55%2Ctext_5peg6ZSh5oCd55-l55Ge56eR5oqA%2Ccolor_FFFFFF%2Cshadow_50%2Ct_80%2Cg_se%2Cx_10%2Cy_10]
👇👇👇👇👇👇👇👇
