#include <Arduino.h>
#line 1 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino"
#include <MLX90393.h>
#include <SD.h>
#include <SPI.h>
#include <Wire.h>

#define TCAADDR 0x70 // TCA9548A多路IIC

MLX90393 mlx;
MLX90393::txyz data; // 创建一个包含四个浮点数 (t, x, y, z) 的结构

unsigned long t;
float x0, y0, z0, x=0, y=0, z=0;

#line 14 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino"
void setup();
#line 51 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino"
void loop();
#line 14 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino"
void setup()
{
    Serial.begin(115200); // 初始化串口通信
    Wire.begin();         // 初始化I2C总线

    // 检查霍尔传感器是否正确启动
    while (mlx.begin() != MLX90393::STATUS_OK)
    {
        mlx.begin();
    }
    delay(100);

    int n = 10; // 读取数据的次数
    float sumx = 0, sumy = 0, sumz = 0;
  
    for (int i = 0; i < n; i++) {
      mlx.readData(data);   // 读取霍尔传感器的数据
      sumx += data.x;
      sumy += data.y;
      sumz += data.z;
      delay(10); // 每次读取间隔 10 毫秒
    }

    // mlx.readData(data); // 读取霍尔传感器的数据
    x = sumx/n;
    y = sumy/n;
    z = sumz/n;

    Serial.print("x0=");
    Serial.print(x);
    Serial.print(", y0=");
    Serial.print(y);
    Serial.print(", z0=");
    Serial.print(z);
    Serial.println(";");// 打印地磁场数据
}

void loop()
{
    t = millis(); // 获取当前时间（毫秒）
    // x0=-17.18, y0=-54.79, z0=2.06;//0度位置校准
    // x0=-0.78, y0=-67.38, z0=2.80;//30度位置校准
    // x0=18.17, y0=-69.76, z0=2.43;//60度位置校准
    // x0=36.63, y0=-62.86, z0=2.26;//90度位置校准
    // x0=48.43, y0=-47.21, z0=1.93;//120度位置校准
    // x0=50.74, y0=-27.89, z0=2.00;//150度位置校准
    // x0=43.05, y0=-9.62, z0=2.39;//180度位置校准
    // x0=27.69, y0=2.56, z0=2.40;//210度位置校准
    // x0=7.72, y0=5.39, z0=2.48;//240度位置校准
    // x0=-10.70, y0=-1.27, z0=1.99;//270度位置校准
    // x0=-22.18, y0=-17.21, z0=2.07;//300度位置校准
    x0=-24.53, y0=-36.82, z0=2.19;//330度位置校准
        // x0=0, y0=0, z0=0;
    mlx.readData(data); // 读取霍尔传感器的数据
    x = data.x-x0;
    y = data.y-y0;
    z = data.z-z0;

    // 打印时间和霍尔传感器的数据信息
    Serial.print(t);
    Serial.print("ms:");
    Serial.print(" ");
    Serial.print(x);
    Serial.print(" ");
    Serial.print(y);
    Serial.print(" ");
    Serial.println(z);

    delay(100); // 延时100毫秒
}

