#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速MaixPy控制脚本 - 一键启动音频检测
"""

import serial
import time
import json
import binascii
from datetime import datetime

def connect_and_run():
    """连接设备并运行音频检测"""

    # 配置
    PORT = '/dev/ttyUSB0'  # 根据实际情况修改
    BAUDRATE = 115200

    print("🔌 正在连接MaixPy设备...")

    try:
        # 连接串口
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(2)
        print(f"✅ 已连接到 {PORT}")

        # 激活REPL
        ser.write(b'\r\n')
        time.sleep(0.5)
        ser.flushInput()

        print("📤 正在上传音频检测脚本...")

        # 停止当前程序
        ser.write(b'\x03')  # Ctrl+C
        time.sleep(0.5)

        # 简化的音频检测脚本
        script_lines = [
            "from Maix import MIC_ARRAY as mic",
            "import lcd, time, json, binascii",
            "",
            "ANGLE_MAP = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]",
            "SOUND_THRESHOLD = 5",
            "",
            "print('初始化麦克风阵列...')",
            "lcd.init()",
            "mic.init()",
            "print('开始声音检测...')",
            "",
            "while True:",
            "    imga = mic.get_map()",
            "    b = mic.get_dir(imga)",
            "    mic.set_led(b,(0,0,255))",
            "    lcd.display(imga.resize(160,160).to_rainbow(1))",
            "    ",
            "    if b:",
            "        intensities = list(b)",
            "        max_intensity = max(intensities)",
            "        if max_intensity > SOUND_THRESHOLD:",
            "            max_dir = intensities.index(max_intensity)",
            "            angle = ANGLE_MAP[max_dir]",
            "            data = {'angle': angle, 'intensity': max_intensity, 'direction': max_dir, 'all_directions': intensities}",
            "            print('AUDIO_PACKET:' + json.dumps(data))",
            "            if imga.data:",
            "                print('RAW_AUDIO:' + binascii.hexlify(imga.data).decode('ascii'))",
            "    time.sleep(0.01)"
        ]

        # 逐行发送代码
        for line in script_lines:
            cmd = line + '\r\n'
            ser.write(cmd.encode())
            time.sleep(0.05)  # 等待设备处理

        print("🚀 脚本已启动，开始监听音频数据...")
        print("=" * 50)

        # 监听数据
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()

                if line.startswith('AUDIO_PACKET:'):
                    try:
                        data = json.loads(line[13:])
                        dt = datetime.now()
                        print(f"\n🔊 [{dt.strftime('%H:%M:%S')}] 检测到声音!")
                        print(f"   角度: {data.get('angle', 0)}°")
                        print(f"   强度: {data.get('intensity', 0)}")
                        print(f"   方向: {data.get('direction', 0)}")
                    except:
                        pass

                elif line.startswith('RAW_AUDIO:'):
                    try:
                        audio_data = binascii.unhexlify(line[10:])
                        print(f"   📊 原始音频: {len(audio_data)}字节")
                    except:
                        pass

                elif line and not line.startswith(('>>>', 'AUDIO_', 'RAW_')):
                    print(f"[设备] {line}")

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n\n⏹️ 停止监听")
        try:
            ser.write(b'\x03')  # 停止设备上的程序
            time.sleep(0.5)
        except:
            pass

    except Exception as e:
        print(f"❌ 错误: {e}")
        print("\n故障排除:")
        print("1. 检查设备连接")
        print("2. 确认串口路径 (/dev/ttyUSB0 或 /dev/ttyACM0)")
        print("3. 检查权限: sudo usermod -a -G dialout $USER")

    finally:
        try:
            ser.close()
            print("🔌 设备连接已断开")
        except:
            pass

if __name__ == "__main__":
    print("🎯 快速MaixPy音频检测控制器")
    print("按 Ctrl+C 停止")
    print("=" * 50)
    connect_and_run()