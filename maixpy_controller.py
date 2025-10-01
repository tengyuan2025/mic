#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过PySerial控制MaixPy设备
自动上传代码、执行脚本并接收数据
"""

import serial
import time
import json
import binascii
import threading
from datetime import datetime

class MaixPyController:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        """
        初始化MaixPy控制器

        Args:
            port: 串口设备路径
            baudrate: 波特率
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connected = False
        self.receiving = False

    def connect(self):
        """连接到MaixPy设备"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # 等待设备稳定
            self.connected = True
            print(f"✓ 已连接到MaixPy设备: {self.port}")

            # 发送换行符激活REPL
            self.ser.write(b'\r\n')
            time.sleep(0.1)

            # 清空缓冲区
            self.ser.flushInput()
            return True

        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        self.receiving = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.connected = False
            print("设备连接已断开")

    def send_command(self, command, wait_for_response=True, timeout=5):
        """
        发送命令到MaixPy设备

        Args:
            command: 要执行的Python命令
            wait_for_response: 是否等待响应
            timeout: 超时时间

        Returns:
            设备响应内容
        """
        if not self.connected:
            print("❌ 设备未连接")
            return None

        try:
            # 发送命令
            cmd = command.strip() + '\r\n'
            self.ser.write(cmd.encode())

            if not wait_for_response:
                return True

            # 等待响应
            response_lines = []
            start_time = time.time()

            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                        # 如果看到提示符，表示命令执行完成
                        if line.endswith('>>> ') or '>>> ' in line:
                            break
                time.sleep(0.01)

            return '\n'.join(response_lines)

        except Exception as e:
            print(f"❌ 发送命令错误: {e}")
            return None

    def upload_and_run_script(self, script_content, filename='/flash/current_script.py'):
        """
        上传并运行Python脚本

        Args:
            script_content: 脚本内容
            filename: 在设备上保存的文件名
        """
        print(f"📤 正在上传脚本到 {filename}...")

        # 停止当前运行的程序
        self.send_command('\x03', wait_for_response=False)  # Ctrl+C
        time.sleep(0.5)

        # 创建文件并写入内容
        lines = script_content.split('\n')

        # 开始写入文件
        self.send_command(f"f = open('{filename}', 'w')")

        for line in lines:
            # 转义特殊字符
            escaped_line = line.replace('\\', '\\\\').replace("'", "\\'")
            cmd = f"f.write('{escaped_line}\\n')"
            self.send_command(cmd, wait_for_response=False)
            time.sleep(0.01)  # 短暂延时避免缓冲区溢出

        # 关闭文件
        self.send_command("f.close()")
        print("✓ 脚本上传完成")

        # 运行脚本
        print("🚀 正在运行脚本...")
        self.send_command(f"exec(open('{filename}').read())", wait_for_response=False)
        time.sleep(1)

    def start_audio_monitoring(self):
        """开始音频监控"""
        self.receiving = True

        def monitor_thread():
            print("👂 开始监听音频数据...")
            while self.receiving:
                try:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('utf-8', errors='ignore').strip()

                        if line.startswith('AUDIO_PACKET:'):
                            self.process_audio_packet(line[13:])
                        elif line.startswith('RAW_AUDIO:'):
                            self.process_raw_audio(line[10:])
                        elif line and not line.startswith(('AUDIO_', 'RAW_', '>>>')):
                            print(f"[设备] {line}")

                    time.sleep(0.001)

                except Exception as e:
                    if self.receiving:
                        print(f"❌ 监听错误: {e}")
                    break

        # 启动监听线程
        self.monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
        self.monitor_thread.start()

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

        except Exception as e:
            print(f"❌ 解析音频数据包错误: {e}")

    def process_raw_audio(self, hex_data):
        """处理原始音频数据"""
        try:
            audio_bytes = binascii.unhexlify(hex_data)
            print(f"   📊 原始音频: {len(audio_bytes)}字节")
        except Exception as e:
            print(f"❌ 解析原始音频数据错误: {e}")

    def stop_script(self):
        """停止当前运行的脚本"""
        print("⏹️ 停止脚本...")
        self.send_command('\x03', wait_for_response=False)  # Ctrl+C
        time.sleep(0.5)
        self.receiving = False

def load_mic_array_script():
    """加载麦克风阵列脚本内容"""
    script_path = '/Users/yushuangyang/workspace/MaixPy-v1_scripts/hardware/demo_mic_array.py'
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # 如果文件不存在，返回基础脚本
        return '''
from Maix import MIC_ARRAY as mic
import lcd
import time
import json
import binascii

ANGLE_MAP = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
SOUND_THRESHOLD = 5
SEND_RAW_AUDIO = True

print("麦克风阵列初始化中...")
lcd.init()
mic.init()

print("开始声音检测和定位...")
print("声音强度阈值:", SOUND_THRESHOLD)
print("等待声音输入...")

while True:
    imga = mic.get_map()
    b = mic.get_dir(imga)
    a = mic.set_led(b,(0,0,255))
    imgb = imga.resize(160,160)
    imgc = imgb.to_rainbow(1)
    a = lcd.display(imgc)

    if b:
        direction_intensities = list(b)
        max_intensity = max(direction_intensities)
        max_direction = direction_intensities.index(max_intensity)
        max_angle = ANGLE_MAP[max_direction]

        if max_intensity > SOUND_THRESHOLD:
            timestamp = time.time()
            print("检测到声音! 角度: %d度 | 强度: %d | 方向: %d" % (max_angle, max_intensity, max_direction))

            data_packet = {
                "type": "audio_detection",
                "timestamp": timestamp,
                "angle": max_angle,
                "intensity": max_intensity,
                "direction": max_direction,
                "all_directions": direction_intensities,
                "audio_map": list(imga.data) if SEND_RAW_AUDIO else None
            }

            json_str = json.dumps(data_packet)
            print("AUDIO_PACKET:" + json_str)

            if SEND_RAW_AUDIO and imga.data:
                audio_hex = binascii.hexlify(imga.data).decode('ascii')
                print("RAW_AUDIO:" + audio_hex)

    time.sleep(0.01)
'''

def main():
    """主函数"""
    print("🎯 MaixPy设备控制器")
    print("=" * 50)

    # 创建控制器实例
    controller = MaixPyController(port='/dev/ttyUSB0')  # 根据实际情况修改端口

    try:
        # 连接设备
        if not controller.connect():
            return

        # 加载并上传脚本
        script_content = load_mic_array_script()
        controller.upload_and_run_script(script_content)

        # 开始音频监控
        controller.start_audio_monitoring()

        print("\n✅ 系统运行中...")
        print("按 Ctrl+C 停止监控")
        print("=" * 50)

        # 保持运行
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 正在停止...")
        controller.stop_script()

    except Exception as e:
        print(f"❌ 运行错误: {e}")

    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()