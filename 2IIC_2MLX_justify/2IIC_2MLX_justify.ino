#include <MLX90393.h>
#include <Wire.h>

#define TCAADDR 0x70

MLX90393 mlx;
MLX90393::txyz data;

const int FLT_MAX = 1e6;
// ===== S0 =====
float x0max = -FLT_MAX, x0min = FLT_MAX;
float y0max = -FLT_MAX, y0min = FLT_MAX;
float z0max = -FLT_MAX, z0min = FLT_MAX;

// ===== S1 =====
float x1max = -FLT_MAX, x1min = FLT_MAX;
float y1max = -FLT_MAX, y1min = FLT_MAX;
float z1max = -FLT_MAX, z1min = FLT_MAX;

unsigned long startTime;
const int calibTime = 15000; // 15秒

// ---------------- TCA选择 ----------------
void tcaselect(uint8_t i)
{
  if (i > 7) return;
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

void setup()
{
  Serial.begin(115200);
  Wire.begin();

  // 初始化 S0
  tcaselect(0);
  while (mlx.begin() != MLX90393::STATUS_OK) {
    Serial.println("S0 init failed...");
    delay(500);
  }

  // 初始化 S1
  tcaselect(1);
  while (mlx.begin() != MLX90393::STATUS_OK) {
    Serial.println("S1 init failed...");
    delay(500);
  }

  Serial.println("=== Dual Sensor Calibration Start ===");
  Serial.println("Rotate BOTH sensors together!");

  startTime = millis();
}

void loop()
{
  // ===== S0 =====
  tcaselect(0);
  mlx.readData(data);

  if (data.x > x0max) x0max = data.x;
  if (data.x < x0min) x0min = data.x;
  if (data.y > y0max) y0max = data.y;
  if (data.y < y0min) y0min = data.y;
  if (data.z > z0max) z0max = data.z;
  if (data.z < z0min) z0min = data.z;

  // ===== S1 =====
  tcaselect(1);
  mlx.readData(data);

  if (data.x > x1max) x1max = data.x;
  if (data.x < x1min) x1min = data.x;
  if (data.y > y1max) y1max = data.y;
  if (data.y < y1min) y1min = data.y;
  if (data.z > z1max) z1max = data.z;
  if (data.z < z1min) z1min = data.z;

  // 实时显示
  Serial.println("Collecting...");

  // ===== 结束 =====
  if (millis() - startTime > calibTime)
  {
    float x0off = (x0max + x0min) / 2.0;
    float y0off = (y0max + y0min) / 2.0;
    float z0off = (z0max + z0min) / 2.0;

    float x1off = (x1max + x1min) / 2.0;
    float y1off = (y1max + y1min) / 2.0;
    float z1off = (z1max + z1min) / 2.0;

    Serial.println("=== Calibration Done ===");

    Serial.println("S0 offset:");
    Serial.print("x0off="); Serial.print(x0off); Serial.println("; ");
    Serial.print("y0off="); Serial.print(y0off); Serial.println("; ");
    Serial.print("z0off="); Serial.print(z0off); Serial.println("; ");

    Serial.println("S1 offset:");
    Serial.print("x1off="); Serial.print(x1off); Serial.println("; ");
    Serial.print("y1off="); Serial.print(y1off); Serial.println("; ");
    Serial.print("z1off="); Serial.print(z1off); Serial.println("; ");

    while (1);
  }

  delay(50);
}