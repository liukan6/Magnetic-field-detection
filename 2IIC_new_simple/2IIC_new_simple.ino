#include <MLX90393.h>
#include <SD.h>
#include <SPI.h>
#include <Wire.h>

#define TCAADDR 0x70  // TCA9548A多路IIC

MLX90393 mlx;
MLX90393::txyz data; // 创建一个包含四个浮点数 (t, x, y, z) 的结构

unsigned long t;
float x0, y0, z0;

void setup() {
  Serial.begin(115200); // 初始化串口通信
  Wire.begin();         // 初始化I2C总线

  // 检查霍尔传感器是否正确启动
  while (mlx.begin() != MLX90393::STATUS_OK) {
    mlx.begin();
  }
  delay(100);
}

void loop() {
  t = millis();         // 获取当前时间（毫秒）

  mlx.readData(data);   // 读取霍尔传感器的数据
  x0 = data.x;
  y0 = data.y;
  z0 = data.z;

  // 打印时间和霍尔传感器的数据信息
  Serial.print(t);
  Serial.print("ms:");
  Serial.print(" ");
  Serial.print(x0);
  Serial.print(" ");
  Serial.print(y0);
  Serial.print(" ");
  Serial.println(z0);

  delay(100); // 延时100毫秒
}
