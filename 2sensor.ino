#include <MLX90393.h>
//#include <GravityRtc.h>


#include <SD.h>
#include <SPI.h>
#include <Wire.h>

#define TCAADDR 0x70  //TCA9548A多路IIC

//GravityRtc rtc;     //RTC Initialization

MLX90393 mlx;
MLX90393::txyz data; //Create a structure, called data, of four floats (t, x, y, and z)

float x1;float y1;float z1;
float x0;float y0;float z0;
float x2;float y2;float z2;

void setup()
{ 
  Serial.begin(9600);
  Wire.begin();
  
  tcaselect(0);while(mlx.begin() != MLX90393::STATUS_OK){mlx.begin();}delay(20);
//  tcaselect(0);
//  mlx.readData(data); //Read the values from the sensor1
//  x0 = data.x; y0 = data.y; z0 = data.z;
//  Serial.print("x0=");Serial.print(x0);Serial.print("y0=");Serial.print(y0);Serial.print("z0=");Serial.print(z0);//磁膜1信号
  tcaselect(1);while(mlx.begin() != MLX90393::STATUS_OK){mlx.begin();}delay(20);
  
}

void loop()
{

  tcaselect(0);
  mlx.readData(data); //Read the values from the sensor1
  x1 = data.x-45.375; y1 = data.y+49.725; z1 = data.z-z0;
  //rtc.read(); //读取时间
   
  tcaselect(1);
  mlx.readData(data); //Read the values from the sensor1
  x2 = data.x+15.6; y2 = data.y+50.55; z2 = data.z;
  
  Serial.print(" Film1:");Serial.print(x1);Serial.print(" ");Serial.print(y1);Serial.print(" ");Serial.print(z1);//磁膜1信号
  Serial.print(" Geo: ");Serial.print(x2);Serial.print(" ");Serial.print(y2);Serial.print(" ");Serial.print(z2);//记录地磁
  Serial.println();  
     
}


void tcaselect(uint8_t i)    //从机选择函数
{
  if (i > 7) return;
  Wire.begin();
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission(); 
}
