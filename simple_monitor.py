#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版MaixPy音频监控器
"""

import serial
import json
import binascii
import time
from datetime import datetime

def main():
    # 配置
    PORT = '/dev/ttyUSB0'  # 根据实际情况修改
    BAUDRATE = 115200

    print("🎯 MaixPy音频监控器")
    print(f"连接设备: {PORT}")
    print("=" * 40)

    try:
        # 连接设备
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(1)
        print("✅ 设备连接成功")
        print("👂 等待音频数据...")
        print()

        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()

                if line.startswith('AUDIO_PACKET:'):
                    # 音频定位数据
                    try:
                        data = json.loads(line[13:])
                        now = datetime.now().strftime('%H:%M:%S')

                        print(f"🔊 [{now}] 声音检测")
                        print(f"   角度: {data.get('angle', 0)}°")
                        print(f"   强度: {data.get('intensity', 0)}")
                        print(f"   方向: {data.get('direction', 0)}")

                    except Exception as e:
                        print(f"❌ 数据解析错误: {e}")

                elif line.startswith('RAW_AUDIO:'):
                    # 原始音频数据
                    try:
                        audio_data = binascii.unhexlify(line[10:])
                        print(f"   📊 音频数据: {len(audio_data)}字节")
                    except:
                        print("   ❌ 音频数据错误")

                elif line and not line.startswith(('AUDIO_', 'RAW_', '>>>')):
                    # 设备其他输出
                    if line.strip():
                        print(f"[设备] {line}")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n👋 监控停止")

    except Exception as e:
        print(f"❌ 连接错误: {e}")
        print("\n故障排除:")
        print("1. 检查USB连接")
        print("2. 确认串口路径 (ls /dev/tty*)")
        print("3. 检查权限 (sudo chmod 666 /dev/ttyUSB0)")
        print("4. 确保MaixPy设备运行了音频检测脚本")

    finally:
        try:
            ser.close()
        except:
            pass

if __name__ == "__main__":
    main()