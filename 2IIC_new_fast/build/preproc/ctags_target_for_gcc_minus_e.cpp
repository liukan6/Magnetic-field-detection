# 1 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_fast\\2IIC_new_fast.ino"
# 2 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_fast\\2IIC_new_fast.ino" 2
# 3 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_fast\\2IIC_new_fast.ino" 2
# 4 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_fast\\2IIC_new_fast.ino" 2
# 5 "e:\\Repository\\Magnetic-field-detection\\2IIC_new_fast\\2IIC_new_fast.ino" 2



MLX90393 mlx;
MLX90393::txyz data;

unsigned long t;
float x0, y0, z0, x=0, y=0, z=0;

/* ====================== ★ 采样参数 ====================== */
const unsigned long Ts_us = 10000; // ★ 采样周期：10 ms → 100 Hz（可改）
unsigned long last_us = 0;
/* ======================================================= */

void setup()
{
    Serial.begin(115200);
    Wire.begin();

    Wire.setClock(400000); // ★ I2C 提速到 400 kHz

    // 检查 MLX90393 启动
    while (mlx.begin() != MLX90393::STATUS_OK) {
        // delay(10);
    }

    /* ====================== ★ 极速配置 ====================== */
    mlx.setOverSampling(0); // ★ 最低 OSR → 最快
    mlx.setGainSel(7); // ★ 最低增益，避免饱和
    mlx.setResolution(0, 0, 0); // ★ 最低分辨率 → 最快
    mlx.setDigitalFiltering(5); // 5档为100Hz，6档为50Hz，7档约27Hz
    mlx.setTemperatureOverSampling(5); // 极弱滤波
    /* ======================================================= */


    /* ===== 原有零点标定逻辑，完整保留 ===== */
    int n = 10;
    float sumx = 0, sumy = 0, sumz = 0;

    for (int i = 0; i < n; i++) {
        mlx.readData(data);
        sumx += data.x;
        sumy += data.y;
        sumz += data.z;
        // delay(10);
    }

    x0 = sumx / n;
    y0 = sumy / n;
    z0 = sumz / n;

    Serial.print("x0=");
    Serial.print(x0);
    Serial.print(", y0=");
    Serial.print(y0);
    Serial.print(", z0=");
    Serial.print(z0);
    Serial.println(";");
}

void loop()
{
    /* ====================== ★ 精确定时采样 ====================== */
    unsigned long now = micros();
    if (now - last_us < Ts_us) return;
    last_us = now;
    /* =========================================================== */

    t = millis();

    // 若使用角度查表校准，可在此处替换 x0,y0,z0
    // 当前保持你原有逻辑
    x0 = 0; y0 = 0; z0 = 0;

    mlx.readData(data);

    x = data.x - x0;
    y = data.y - y0;
    z = data.z - z0;

    /* ===== 原有串口输出，完整保留 ===== */
    Serial.print(t);
    Serial.print("ms:");
    Serial.print(" ");
    Serial.print(x);
    Serial.print(" ");
    Serial.print(y);
    Serial.print(" ");
    Serial.println(z);
}
