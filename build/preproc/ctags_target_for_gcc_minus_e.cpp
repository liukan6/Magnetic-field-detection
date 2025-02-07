# 1 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino"
# 2 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino" 2
# 3 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino" 2
# 4 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino" 2
# 5 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_simple\\2IIC_new_simple.ino" 2



MLX90393 mlx;
MLX90393::txyz data; // 创建一个包含四个浮点数 (t, x, y, z) 的结构

unsigned long t;
float x0, y0, z0, x, y, z;

void setup()
{
    Serial.begin(115200); // 初始化串口通信
    Wire.begin(); // 初始化I2C总线

    // 检查霍尔传感器是否正确启动
    while (mlx.begin() != MLX90393::STATUS_OK)
    {
        mlx.begin();
    }
    delay(100);

    mlx.readData(data); // 读取霍尔传感器的数据
    x = data.x;
    y = data.y;
    z = data.z;
    Serial.print("x0=");
    Serial.print(x);
    Serial.print(", y0=");
    Serial.print(y);
    Serial.print(", z0=");
    Serial.println(z);// 打印地磁场数据
}

void loop()
{
    t = millis(); // 获取当前时间（毫秒）
    x0=220.20, y0=148.95, z0=-1.45;
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
