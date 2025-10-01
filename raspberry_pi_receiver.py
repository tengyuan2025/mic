#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派端音频数据接收器
接收MaixPy设备传输的声音定位和原始音频数据
"""

import serial
import json
import binascii
import time
import numpy as np
from datetime import datetime
import os

class MaixAudioReceiver:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        """
        初始化音频接收器

        Args:
            port: 串口设备路径
            baudrate: 波特率
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.audio_data_buffer = []
        self.save_audio = True  # 是否保存音频数据

        # 创建数据保存目录
        self.data_dir = "maix_audio_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def connect(self):
        """连接串口设备"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"已连接到设备: {self.port}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("设备连接已断开")

    def save_audio_data(self, timestamp, audio_data, metadata):
        """保存音频数据到文件"""
        if not self.save_audio:
            return

        # 创建文件名
        dt = datetime.fromtimestamp(timestamp)
        filename = f"audio_{dt.strftime('%Y%m%d_%H%M%S_%f')}"

        # 保存原始音频数据（二进制）
        audio_file = os.path.join(self.data_dir, f"{filename}.raw")
        with open(audio_file, 'wb') as f:
            f.write(audio_data)

        # 保存元数据（JSON）
        meta_file = os.path.join(self.data_dir, f"{filename}.json")
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"音频数据已保存: {filename}")

    def process_audio_packet(self, packet_data):
        """处理音频定位数据包"""
        try:
            data = json.loads(packet_data)

            timestamp = data.get('timestamp', time.time())
            angle = data.get('angle', 0)
            intensity = data.get('intensity', 0)
            direction = data.get('direction', 0)
            all_directions = data.get('all_directions', [])

            # 打印声音定位信息
            dt = datetime.fromtimestamp(timestamp)
            print(f"\n[{dt.strftime('%H:%M:%S.%f')[:-3]}] 声音检测")
            print(f"  角度: {angle}度")
            print(f"  强度: {intensity}")
            print(f"  方向: {direction}")
            print(f"  所有方向强度: {all_directions}")

            # 返回数据用于后续处理
            return data

        except Exception as e:
            print(f"解析音频数据包错误: {e}")
            return None

    def process_raw_audio(self, hex_data):
        """处理原始音频数据"""
        try:
            # 将十六进制字符串转换为字节
            audio_bytes = binascii.unhexlify(hex_data)

            # 转换为numpy数组（16x16 = 256字节）
            if len(audio_bytes) == 256:
                audio_array = np.frombuffer(audio_bytes, dtype=np.uint8).reshape(16, 16)
                print(f"  原始音频数据: {len(audio_bytes)}字节 (16x16热力图)")

                # 显示音频强度统计
                print(f"  音频强度 - 最小: {audio_array.min()}, 最大: {audio_array.max()}, 平均: {audio_array.mean():.1f}")

                return audio_bytes
            else:
                print(f"  警告: 音频数据长度异常 ({len(audio_bytes)}字节)")
                return audio_bytes

        except Exception as e:
            print(f"解析原始音频数据错误: {e}")
            return None

    def run(self):
        """主运行循环"""
        if not self.connect():
            return

        print("开始接收音频数据...")
        print("按 Ctrl+C 停止接收")
        print("=" * 50)

        current_packet_data = None

        try:
            while True:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()

                    if line.startswith('AUDIO_PACKET:'):
                        # 处理音频定位数据包
                        packet_json = line[13:]  # 移除前缀
                        current_packet_data = self.process_audio_packet(packet_json)

                    elif line.startswith('RAW_AUDIO:'):
                        # 处理原始音频数据
                        hex_data = line[10:]  # 移除前缀
                        audio_data = self.process_raw_audio(hex_data)

                        # 如果有配对的数据包，保存完整数据
                        if current_packet_data and audio_data and self.save_audio:
                            self.save_audio_data(
                                current_packet_data['timestamp'],
                                audio_data,
                                current_packet_data
                            )
                        current_packet_data = None  # 重置

                    elif line and not line.startswith('AUDIO_') and not line.startswith('RAW_'):
                        # 显示其他日志信息
                        if line.strip():
                            print(f"[设备] {line}")

                time.sleep(0.001)  # 短暂延时

        except KeyboardInterrupt:
            print("\n\n接收停止")
        except Exception as e:
            print(f"接收错误: {e}")
        finally:
            self.disconnect()

def main():
    """主函数"""
    import sys

    # 检查串口设备
    port = '/dev/ttyUSB0'  # 默认设备
    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"MaixPy音频数据接收器")
    print(f"串口设备: {port}")
    print(f"波特率: 115200")

    receiver = MaixAudioReceiver(port=port)
    receiver.run()

if __name__ == "__main__":
    main()