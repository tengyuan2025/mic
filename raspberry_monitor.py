#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派MaixPy设备监控器 - 纯数据接收
假设MaixPy设备已运行音频检测脚本
"""

import serial
import time
import json
import binascii
from datetime import datetime

class MaixPyMonitor:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        """
        初始化监控器

        Args:
            port: 串口设备路径
            baudrate: 波特率
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connected = False

    def connect(self):
        """连接到MaixPy设备"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(1)  # 等待连接稳定
            self.connected = True
            print(f"✅ 已连接到MaixPy设备: {self.port}")
            return True

        except Exception as e:
            print(f"❌ 连接失败: {e}")
            print("请检查:")
            print("1. 设备是否已连接")
            print("2. 串口路径是否正确")
            print("3. 权限设置: sudo usermod -a -G dialout $USER")
            return False

    def disconnect(self):
        """断开连接"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.connected = False
            print("🔌 设备连接已断开")

    def send_simple_command(self, command):
        """发送简单命令（如停止脚本）"""
        if self.connected:
            try:
                self.ser.write(command.encode())
                time.sleep(0.1)
            except Exception as e:
                print(f"❌ 发送命令失败: {e}")

    def process_audio_packet(self, packet_data):
        """处理音频定位数据包"""
        try:
            data = json.loads(packet_data)
            timestamp = data.get('timestamp', time.time())
            dt = datetime.fromtimestamp(timestamp)

            print(f"\n🔊 [{dt.strftime('%H:%M:%S')}] 检测到声音!")
            print(f"   角度: {data.get('angle', 0)}°")
            print(f"   强度: {data.get('intensity', 0)}")
            print(f"   方向: {data.get('direction', 0)}")

            # 可选：显示所有方向的详细数据
            all_dirs = data.get('all_directions', [])
            if all_dirs:
                print(f"   详细强度: {all_dirs}")

            return data

        except Exception as e:
            print(f"❌ 解析音频数据包错误: {e}")
            return None

    def process_raw_audio(self, hex_data):
        """处理原始音频数据"""
        try:
            audio_bytes = binascii.unhexlify(hex_data)
            print(f"   📊 原始音频: {len(audio_bytes)}字节")

            # 可选：显示音频数据统计
            if len(audio_bytes) == 256:  # 16x16热力图
                import numpy as np
                audio_array = np.frombuffer(audio_bytes, dtype=np.uint8)
                print(f"   音频统计 - 最小: {audio_array.min()}, 最大: {audio_array.max()}, 平均: {audio_array.mean():.1f}")

            return audio_bytes

        except Exception as e:
            print(f"❌ 解析原始音频数据错误: {e}")
            return None

    def monitor(self):
        """开始监控数据"""
        if not self.connected:
            print("❌ 设备未连接")
            return

        print("👂 开始监听音频数据...")
        print("等待MaixPy设备发送数据...")
        print("=" * 50)

        try:
            while True:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()

                    if line.startswith('AUDIO_PACKET:'):
                        # 处理音频定位数据
                        packet_data = line[13:]
                        self.process_audio_packet(packet_data)

                    elif line.startswith('RAW_AUDIO:'):
                        # 处理原始音频数据
                        hex_data = line[10:]
                        self.process_raw_audio(hex_data)

                    elif line and not line.startswith(('AUDIO_', 'RAW_', '>>>')):
                        # 显示设备其他输出
                        if line.strip():
                            print(f"[设备] {line}")

                time.sleep(0.001)  # 短暂延时

        except KeyboardInterrupt:
            print("\n\n⏹️ 停止监听")

        except Exception as e:
            print(f"❌ 监听错误: {e}")

    def stop_device_script(self):
        """发送停止信号到设备"""
        print("📤 发送停止信号到设备...")
        self.send_simple_command('\x03')  # Ctrl+C
        time.sleep(0.5)

def main():
    """主函数"""
    import sys

    print("🎯 MaixPy设备音频数据监控器")
    print("=" * 50)

    # 检查串口设备参数
    port = '/dev/ttyUSB0'
    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"串口设备: {port}")
    print("波特率: 115200")
    print()

    # 创建监控器
    monitor = MaixPyMonitor(port=port)

    try:
        # 连接设备
        if not monitor.connect():
            return

        print("ℹ️  确保MaixPy设备已运行音频检测脚本")
        print("   如需停止设备脚本，按 Ctrl+\\ ")
        print("   如需退出监控，按 Ctrl+C")
        print()

        # 开始监控
        monitor.monitor()

    except KeyboardInterrupt:
        print("\n\n👋 正在退出...")

    except Exception as e:
        print(f"❌ 运行错误: {e}")

    finally:
        monitor.disconnect()

if __name__ == "__main__":
    main()