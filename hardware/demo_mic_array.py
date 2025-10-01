from Maix import MIC_ARRAY as mic
import lcd
import time
import json
import binascii

# 角度映射：12个LED对应的角度（度）
ANGLE_MAP = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]

# 声音强度阈值，超过此值才记录日志
SOUND_THRESHOLD = 5

# 是否传输原始音频数据
SEND_RAW_AUDIO = True

print("麦克风阵列初始化中...")
lcd.init()
mic.init()
#mic.init(i2s_d0=23, i2s_d1=22, i2s_d2=21, i2s_d3=20, i2s_ws=19, i2s_sclk=18, sk9822_dat=24, sk9822_clk=25)

#mic.init(i2s_d0=20, i2s_d1=21, i2s_d2=15, i2s_d3=8, i2s_ws=7, i2s_sclk=6, sk9822_dat=25, sk9822_clk=24)# for maix cube

print("开始声音检测和定位...")
print("声音强度阈值:", SOUND_THRESHOLD)
print("等待声音输入...")
print("=" * 50)

loop_count = 0

while True:
    loop_count += 1
    imga = mic.get_map()
    b = mic.get_dir(imga)  # b是包含12个方向强度值的元组
    a = mic.set_led(b,(0,0,255))
    imgb = imga.resize(160,160)
    imgc = imgb.to_rainbow(1)
    a = lcd.display(imgc)

    # 分析声音方向和强度
    if b:  # 确保有数据
        direction_intensities = list(b)  # 转换为列表便于处理
        max_intensity = max(direction_intensities)
        max_direction = direction_intensities.index(max_intensity)
        max_angle = ANGLE_MAP[max_direction]

        # 当检测到声音强度超过阈值时记录日志和传输数据
        if max_intensity > SOUND_THRESHOLD:
            timestamp = time.time()
            print("检测到声音! 角度: %d度 | 强度: %d | 方向: %d | 详细数据: %s" % (max_angle, max_intensity, max_direction, str(direction_intensities)))

            # 准备传输数据
            data_packet = {
                "type": "audio_detection",
                "timestamp": timestamp,
                "angle": max_angle,
                "intensity": max_intensity,
                "direction": max_direction,
                "all_directions": direction_intensities,
                "audio_map": list(imga.data) if SEND_RAW_AUDIO else None
            }

            # 通过串口发送JSON数据
            json_str = json.dumps(data_packet)
            print("AUDIO_PACKET:" + json_str)

            # 如果需要发送原始音频数据（16x16字节数组）
            if SEND_RAW_AUDIO and imga.data:
                # 将音频热力图数据转换为十六进制字符串
                audio_hex = binascii.hexlify(imga.data).decode('ascii')
                print("RAW_AUDIO:" + audio_hex)

    # 添加小延时避免日志刷屏
    time.sleep(0.01)
mic.deinit()
