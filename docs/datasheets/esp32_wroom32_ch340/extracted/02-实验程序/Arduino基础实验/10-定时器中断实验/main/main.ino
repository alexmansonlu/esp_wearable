/* 
 * 实验名称：定时器中断实验
 * 
 * 接线说明：LED模块-->ESP32 IO
 *         (D1)-->(15)
 * 
 * 实验现象：程序下载成功后，D1指示灯间隔0.5s状态翻转
 * 
 */

#include "public.h"
#include "led.h"
#include "time.h"


//定义全局变量


void setup() {
  led_init();
  time0_init(500000);//定时500ms
  
}

void loop() {
  
}
