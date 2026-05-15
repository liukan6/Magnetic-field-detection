#include <MLX90393.h>
#include <Wire.h>

#define TCAADDR 0x70
#define LED_PIN 13   // Mega2560 板载LED

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

  mlx.setOverSampling(0);
  mlx.setGainSel(7);
  mlx.setResolution(0, 0, 0);
  mlx.setDigitalFiltering(5);
  mlx.setTemperatureOverSampling(5);

  return true;
}

// -------------------- LED同步信号 --------------------
void syncSignal()
{
  // LED亮
  digitalWrite(LED_PIN, HIGH);

  // 串口输出 → 触发TX灯闪
  Serial.println("SYNC");

  delay(100);  // 保证视频能拍到

  digitalWrite(LED_PIN, LOW); //闪烁完之后亮的那下是开始
}

// -------------------- setup --------------------
void setup()
{
  pinMode(LED_PIN, OUTPUT);

  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);
  delay(1000);   // 等待串口稳定（关键！）

  // ===== 同步信号 =====
  syncSignal();

  // 初始化 SC0
  while (!initMLX(0))
  {
    Serial.println("MLX90393 on SC0 init failed!");
  }

  // 初始化 SC1
  while (!initMLX(1))
  {
    Serial.println("MLX90393 on SC1 init failed!");
  }

  Serial.println("Init done.");

  // Offset
  x0off=63.08; y0off=-90.37; z0off=47.80;
  x1off=63.23; y1off=-63.45; z1off=61.59;
}

// ===== 补偿参数 =====
float dx = 24.35;
float dy = 81.47;
float dz = 51.94;

float x1c, y1c, z1c;
float dxs, dys, dzs;

// -------------------- loop --------------------
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

  // ===== 补偿 =====
  x1c = x1 - dx;
  y1c = y1 - dy;
  z1c = z1 - dz;

  // ===== 差值 =====
  dxs = x0 - x1c;
  dys = y0 - y1c;
  dzs = z0 - z1c;

  // ===== 输出 =====
  Serial.print(t);
  Serial.print("ms: ");
  Serial.print(dxs); Serial.print(" ");
  Serial.print(dys); Serial.print(" ");
  Serial.print(dzs);
  Serial.println();
}