#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版树莓派音频接收器 - 实时监控
"""

import serial
import json
import binascii
import time
from datetime import datetime

def main():
    # 配置串口（根据实际情况修改）
    PORT = '/dev/ttyUSB0'  # 或 /dev/ttyACM0
    BAUDRATE = 115200

    try:
        # 连接串口
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        print(f"✓ 已连接到 {PORT}")
        print("等待音频数据...")
        print("=" * 50)

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()

                if line.startswith('AUDIO_PACKET:'):
                    # 解析音频定位数据
                    try:
                        data = json.loads(line[13:])
                        timestamp = data.get('timestamp', time.time())
                        dt = datetime.fromtimestamp(timestamp)

                        print(f"\n🔊 [{dt.strftime('%H:%M:%S')}] 检测到声音!")
                        print(f"   角度: {data.get('angle', 0)}°")
                        print(f"   强度: {data.get('intensity', 0)}")
                        print(f"   方向: {data.get('direction', 0)}")

                    except Exception as e:
                        print(f"❌ 数据解析错误: {e}")

                elif line.startswith('RAW_AUDIO:'):
                    # 原始音频数据
                    hex_data = line[10:]
                    try:
                        audio_bytes = binascii.unhexlify(hex_data)
                        print(f"   📊 原始音频: {len(audio_bytes)}字节")
                    except Exception as e:
                        print(f"❌ 音频数据错误: {e}")

                elif line and not line.startswith(('AUDIO_', 'RAW_')):
                    # 设备其他输出
                    if line.strip():
                        print(f"[设备] {line}")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\n👋 接收停止")
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        print("请检查:")
        print("1. 设备是否连接")
        print("2. 串口设备路径是否正确")
        print("3. 是否有权限访问串口")
    finally:
        try:
            ser.close()
        except:
            pass

if __name__ == "__main__":
    main()