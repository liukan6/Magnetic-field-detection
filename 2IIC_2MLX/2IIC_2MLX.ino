#include <MLX90393.h>
#include <Wire.h>

#define TCAADDR 0x70  // TCA9548A地址

MLX90393 mlx;
MLX90393::txyz data;

unsigned long t;

// 两个传感器数据
float x0, y0, z0;
float x1, y1, z1;
float x0off, y0off, z0off;
float x1off, y1off, z1off;

// -------------------- I2C通道选择 --------------------
void tcaselect(uint8_t i)
{
  if (i > 7) return;

  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

// -------------------- 初始化单个MLX --------------------
bool initMLX(uint8_t channel)
{
  tcaselect(channel);
  delay(10);

  if (mlx.begin() != MLX90393::STATUS_OK)
  {
    return false;
  }
  return true;
}

// -------------------- setup --------------------
void setup()
{
  Serial.begin(115200);
  Wire.begin();
  delay(100);

  // 初始化 SC0 (通道0)
  if (!initMLX(0))
  {
    Serial.println("MLX90393 on SC0 init failed!");
  }

  // 初始化 SC1 (通道1)
  if (!initMLX(1))
  {
    Serial.println("MLX90393 on SC1 init failed!");
  }

  Serial.println("Init done.");
}

float dx = 40.38;
float dy = 108.39;
float dz = 63.20;

// float dx = 0;
// float dy = 0;
// float dz = 0;

float x1c, y1c, z1c;
float dxs, dys, dzs;

void loop()
{
  t = millis();

  // ===== S0 =====
  tcaselect(0);
  delayMicroseconds(200);
  mlx.readData(data);
  x0 = data.x-x0off;
  y0 = data.y-y0off;
  z0 = data.z-z0off;

  // ===== S1 =====
  tcaselect(1);
  delayMicroseconds(200);
  mlx.readData(data);
  x1 = data.x-x1off;
  y1 = data.y-y1off;
  z1 = data.z-z1off;

  // ===== S1补偿 =====
  x1c = x1 - dx;
  y1c = y1 - dy;
  z1c = z1 - dz;

  // ===== 差值 =====
  dxs = x0 - x1c;
  dys = y0 - y1c;
  dzs = z0 - z1c;

  // ===== 输出 =====
  Serial.print(t);
  Serial.print(" ms | ");

  Serial.print("S0: ");
  Serial.print(x0); Serial.print(" ");
  Serial.print(y0); Serial.print(" ");
  Serial.print(z0);

  Serial.print(" || S1c: ");
  Serial.print(x1c); Serial.print(" ");
  Serial.print(y1c); Serial.print(" ");
  Serial.print(z1c);

  Serial.print(" || Δ: ");
  Serial.print(dxs); Serial.print(" ");
  Serial.print(dys); Serial.print(" ");
  Serial.print(dzs);

  Serial.println();

  delay(10);
}