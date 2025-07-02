import pyautogui
import time
import signal
import sys
import random
from PIL import Image, ImageDraw
import numpy as np
import os
from datetime import datetime

# --- 1. 参数配置 ---
# 游戏状态检测相关
LEVEL_CLEAR_CHECK_COORD = (1470, 410)  # 检测关卡完成的坐标
LEVEL_CLEAR_COLOR = (255, 255, 255)    # 关卡完成时的目标颜色 (你需要根据实际截图调整)
COLOR_TOLERANCE = 30                    # 颜色容差

# 动作坐标配置
# 阶段1：进入关卡
JOYSTICK_START = (1225, 334)           # 摇杆起始位置
JOYSTICK_DRAG_DISTANCE = 100           # 向右拖拽距离
MAP_SELECT_COORDS = [                  # 地图选择坐标序列
    (1350, 307),
    (1267, 205),
    (1746, 404)
]

# 阶段2：清理关卡
ATTACK_COORD = (1779, 400)             # 攻击坐标
SKILL_COORD = (1787, 250)               # 技能坐标

# 阶段3：返回城镇
RETURN_TO_TOWN_COORDS = [              # 返回城镇坐标序列
    (1750, 88),
    (1725, 425),
    (1533, 291)
]

# 时间配置
JOYSTICK_HOLD_DURATION = 1.0           # 摇杆拖拽持续时间
ATTACK_CHECK_INTERVAL = 0.5            # 攻击时检查间隔
ATTACK_HOLD_DURATION = 0.7             # 单次攻击持续时间（秒）- 可调参数
FINAL_ATTACK_DURATION = 0.4            # 最后一次攻击持续时间（秒）- 可调参数
MAX_ATTACK_DURATION = 100               # 最大攻击时间（秒）
ACTION_DELAY_MIN = 0.5                 # 动作间最小延迟
ACTION_DELAY_MAX = 1.5                 # 动作间最大延迟

# 人性化参数
COORD_VARIATION = 3                    # 坐标随机偏移范围
MAX_CYCLES = 100                       # 最大循环次数

# 调试和控制参数
VERBOSE_MODE = False                   # 详细输出模式（默认关闭）
POST_LOOP_WAIT_TIME = 3.0             # 每轮循环完成后在城镇的等待时间（秒）

# 全局变量
should_stop = False
color_timeline = []  # 存储颜色变化记录

def add_human_variation(x, y, variation=COORD_VARIATION):
    """为坐标添加随机偏移，模拟人类操作的不精确性"""
    new_x = x + random.randint(-variation, variation)
    new_y = y + random.randint(-variation, variation)
    return new_x, new_y

def human_click(x, y, description="点击"):
    """执行人性化的点击"""
    if should_stop:
        return
    
    click_x, click_y = add_human_variation(x, y)
    move_duration = random.uniform(0.1, 0.3)
    
    print(f"  {description}坐标: ({click_x}, {click_y})")
    pyautogui.moveTo(click_x, click_y, duration=move_duration)
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.click()

def human_drag(start_x, start_y, end_x, end_y, duration=1.0, description="拖拽"):
    """执行人性化的拖拽操作"""
    if should_stop:
        return
    
    start_x, start_y = add_human_variation(start_x, start_y)
    end_x, end_y = add_human_variation(end_x, end_y)
    
    print(f"  {description}: 从 ({start_x}, {start_y}) 到 ({end_x}, {end_y})")
    
    # 移动到起始位置
    pyautogui.moveTo(start_x, start_y, duration=random.uniform(0.2, 0.4))
    time.sleep(random.uniform(0.1, 0.2))
    
    # 执行拖拽
    pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
    time.sleep(random.uniform(0.1, 0.3))

def get_pixel_color(x, y):
    """获取指定坐标的像素颜色"""
    try:
        screenshot = pyautogui.screenshot()
        color = screenshot.getpixel((x, y))
        return color
    except Exception as e:
        print(f"获取像素颜色时出错: {e}")
        return None

def save_debug_screenshot(x, y, color, filename_prefix="debug"):
    """保存调试截图，标记检测点位置"""
    try:
        screenshot = pyautogui.screenshot()
        draw = ImageDraw.Draw(screenshot)
        
        # 绘制红色十字标记检测点
        cross_size = 20
        line_width = 3
        
        # 水平线
        draw.line([x - cross_size, y, x + cross_size, y], fill='red', width=line_width)
        # 垂直线
        draw.line([x, y - cross_size, x, y + cross_size], fill='red', width=line_width)
        
        # 绘制检测区域框
        box_size = 10
        draw.rectangle([x - box_size, y - box_size, x + box_size, y + box_size], 
                      outline='yellow', width=2)
        
        # 添加颜色信息文本
        text = f"Color: {color} at ({x}, {y})"
        draw.text((x + 30, y - 30), text, fill='white')
        draw.text((x + 29, y - 31), text, fill='black')  # 阴影效果
        
        # 保存截图
        timestamp = int(time.time())
        filename = f"{filename_prefix}_{timestamp}.png"
        screenshot.save(filename)
        print(f"  调试截图已保存: {filename}")
        return filename
    except Exception as e:
        print(f"保存调试截图时出错: {e}")
        return None

def show_detection_point_preview():
    """显示检测点预览（在开始游戏前）"""
    print("\n=== 调试模式：检测点预览 ===")
    print(f"检测坐标: {LEVEL_CLEAR_CHECK_COORD}")
    
    # 获取当前颜色
    current_color = get_pixel_color(LEVEL_CLEAR_CHECK_COORD[0], LEVEL_CLEAR_CHECK_COORD[1])
    print(f"当前颜色: {current_color}")
    
    if current_color:
        is_black = not is_not_black(current_color)
        print(f"是否为黑色: {is_black}")
        
        # 保存预览截图
        filename = save_debug_screenshot(
            LEVEL_CLEAR_CHECK_COORD[0], 
            LEVEL_CLEAR_CHECK_COORD[1], 
            current_color, 
            "preview"
        )
        
        if filename:
            print(f"请查看截图 {filename} 确认检测点位置是否正确")
            print("红色十字标记为检测点，黄色框为检测区域")

def visualize_detection_area():
    """在屏幕上短暂显示检测区域"""
    try:
        # 尝试导入tkinter
        import tkinter as tk
        
        root = tk.Tk()
        root.attributes('-alpha', 0.7)  # 半透明
        root.attributes('-topmost', True)  # 置顶
        root.overrideredirect(True)  # 无边框
        
        # 设置窗口位置和大小
        size = 40
        x = LEVEL_CLEAR_CHECK_COORD[0] - size//2
        y = LEVEL_CLEAR_CHECK_COORD[1] - size//2
        root.geometry(f"{size}x{size}+{x}+{y}")
        root.configure(bg='red')
        
        # 显示3秒后自动关闭
        def close_window():
            root.destroy()
        
        root.after(3000, close_window)
        
        print("  红色方块显示检测区域位置（3秒后自动消失）")
        root.mainloop()
        
    except ImportError:
        print("  tkinter模块不可用，使用替代方案...")
        print("  将在游戏过程中显示实时颜色时间线")
        print(f"  监控坐标: {LEVEL_CLEAR_CHECK_COORD}")
        print("  ⚫ = 灰色系（关卡进行中）")
        print("  🎨 = 彩色（关卡完成）")
    except Exception as e:
        print(f"可视化显示出错: {e}")
        print("  将使用终端颜色时间线显示")

def visualize_color(color, description=""):
    """可视化颜色 - 创建颜色样本图片"""
    try:
        # 处理RGBA和RGB格式
        if len(color) == 4:  # RGBA
            rgb_color = color[:3]  # 取前3个值
            alpha = color[3]
            color_type = "RGBA"
        else:  # RGB
            rgb_color = color
            alpha = 255
            color_type = "RGB"
        
        # 创建颜色样本图片
        img_size = (200, 100)
        img = Image.new('RGB', img_size, rgb_color)
        draw = ImageDraw.Draw(img)
        
        # 添加颜色信息文本
        text_lines = [
            f"颜色: {color}",
            f"格式: {color_type}",
            f"RGB: {rgb_color}",
            f"Alpha: {alpha}" if len(color) == 4 else "",
            f"十六进制: #{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}",
            description
        ]
        
        # 绘制文本（黑色背景，白色文字）
        y_offset = 5
        for line in text_lines:
            if line:  # 跳过空行
                # 绘制文字阴影
                draw.text((6, y_offset + 1), line, fill='black')
                # 绘制文字
                draw.text((5, y_offset), line, fill='white')
                y_offset += 12
        
        # 保存颜色样本
        timestamp = int(time.time())
        filename = f"color_sample_{timestamp}.png"
        img.save(filename)
        
        print(f"  颜色样本已保存: {filename}")
        print(f"  颜色分析:")
        print(f"    RGB值: R={rgb_color[0]}, G={rgb_color[1]}, B={rgb_color[2]}")
        print(f"    十六进制: #{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}")
        if len(color) == 4:
            print(f"    透明度: {alpha}/255 ({alpha/255*100:.1f}%)")
        
        # 颜色分析
        brightness = sum(rgb_color) / 3
        if brightness < 50:
            color_desc = "很暗的颜色"
        elif brightness < 100:
            color_desc = "较暗的颜色"
        elif brightness < 150:
            color_desc = "中等亮度"
        elif brightness < 200:
            color_desc = "较亮的颜色"
        else:
            color_desc = "很亮的颜色"
        
        print(f"    亮度: {brightness:.1f}/255 ({color_desc})")
        
        # 主要颜色成分分析
        max_component = max(rgb_color)
        if rgb_color[0] == max_component and rgb_color[0] > rgb_color[1] + 20 and rgb_color[0] > rgb_color[2] + 20:
            print(f"    主要成分: 红色偏向")
        elif rgb_color[1] == max_component and rgb_color[1] > rgb_color[0] + 20 and rgb_color[1] > rgb_color[2] + 20:
            print(f"    主要成分: 绿色偏向")
        elif rgb_color[2] == max_component and rgb_color[2] > rgb_color[0] + 20 and rgb_color[2] > rgb_color[1] + 20:
            print(f"    主要成分: 蓝色偏向")
        else:
            print(f"    主要成分: 灰色/混合色")
        
        return filename
        
    except Exception as e:
        print(f"颜色可视化出错: {e}")
        return None

def normalize_color(color):
    """标准化颜色格式，将RGBA转换为RGB"""
    if color is None:
        return None
    
    if len(color) == 4:  # RGBA
        return color[:3]  # 返回RGB部分
    else:  # 已经是RGB
        return color

def is_colorful(color, gray_threshold=40):
    """检查颜色是否不是灰色（关卡完成）- 模糊检测"""
    if color is None:
        return False
    
    # 标准化颜色格式
    rgb_color = normalize_color(color)
    if rgb_color is None:
        return False
    
    r, g, b = rgb_color
    
    # 计算颜色的饱和度和亮度
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    
    # 饱和度 = (最大值 - 最小值) / 最大值
    if max_val == 0:
        saturation = 0
    else:
        saturation = (max_val - min_val) / max_val * 100
    
    # 亮度 = 平均值
    brightness = (r + g + b) / 3
    
    # 颜色差异度 = RGB值之间的最大差异
    color_diff = max_val - min_val
    
    # 判断是否为彩色（非灰色）
    # 1. 饱和度足够高 (颜色鲜艳)
    # 2. 或者颜色差异度足够大 (RGB值差距大)
    # 3. 并且不是太暗的颜色
    is_colorful_result = (
        (saturation > 15 or color_diff > gray_threshold) and  # 有足够的颜色差异
        brightness > 20  # 不是太暗
    )
    
    return is_colorful_result

def analyze_color_properties(color):
    """分析颜色属性"""
    if color is None:
        return "无效颜色"
    
    rgb_color = normalize_color(color)
    if rgb_color is None:
        return "无效颜色"
    
    r, g, b = rgb_color
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    brightness = (r + g + b) / 3
    
    if max_val == 0:
        saturation = 0
    else:
        saturation = (max_val - min_val) / max_val * 100
    
    color_diff = max_val - min_val
    
    # 颜色类型判断
    if saturation < 10 and color_diff < 20:
        color_type = "灰色系"
    elif saturation > 30:
        color_type = "鲜艳色彩"
    elif color_diff > 40:
        color_type = "有色彩倾向"
    else:
        color_type = "淡色系"
    
    return f"{color_type} (饱和度:{saturation:.1f}%, 亮度:{brightness:.1f}, 色差:{color_diff})"

def is_not_black(color, black_threshold=30):
    """检查颜色是否不是黑色（关卡完成）- 保留原方法作为备用"""
    if color is None:
        return False
    
    # 标准化颜色格式
    rgb_color = normalize_color(color)
    if rgb_color is None:
        return False
    
    # 如果RGB三个值中任意一个超过阈值，就认为不是黑色
    return any(c > black_threshold for c in rgb_color)

def color_matches(color1, color2, tolerance=COLOR_TOLERANCE):
    """检查两个颜色是否在容差范围内匹配"""
    if color1 is None or color2 is None:
        return False
    
    return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

def wait_for_color_change(x, y, target_color, timeout=MAX_ATTACK_DURATION, check_interval=ATTACK_CHECK_INTERVAL):
    """等待指定坐标的颜色变为目标颜色"""
    start_time = time.time()
    print(f"  开始监控坐标 ({x}, {y}) 的颜色变化...")
    print(f"  目标颜色: {target_color}")
    
    while time.time() - start_time < timeout and not should_stop:
        current_color = get_pixel_color(x, y)
        if current_color:
            print(f"  当前颜色: {current_color}")
            if color_matches(current_color, target_color):
                print(f"  ✓ 检测到目标颜色！")
                return True
        
        time.sleep(check_interval)
    
    print(f"  ✗ 超时或被中断，未检测到目标颜色")
    return False

def random_action_delay():
    """动作之间的随机延迟"""
    delay = random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX)
    time.sleep(delay)

def enter_level():
    """阶段1：进入关卡"""
    print("\n=== 阶段1：进入关卡 ===")
    
    # 1. 拖拽摇杆
    print("1. 拖拽摇杆向右...")
    end_x = JOYSTICK_START[0] + JOYSTICK_DRAG_DISTANCE
    end_y = JOYSTICK_START[1]
    human_drag(JOYSTICK_START[0], JOYSTICK_START[1], end_x, end_y, 
              JOYSTICK_HOLD_DURATION, "摇杆拖拽")
    
    random_action_delay()
    
    # 2. 点击地图选择序列
    print("2. 选择地图...")
    for i, (x, y) in enumerate(MAP_SELECT_COORDS):
        if should_stop:
            break
        print(f"  地图选择步骤 {i+1}/3")
        human_click(x, y, f"地图选择{i+1}")
        random_action_delay()
    
    print("✓ 进入关卡完成")

def log_color_change(timestamp, color, is_colorful_status, description=""):
    """记录颜色变化到时间线"""
    global color_timeline
    
    # 标准化颜色用于显示
    display_color = normalize_color(color)
    
    entry = {
        'timestamp': timestamp,
        'time_str': datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3],
        'color': color,  # 保存原始颜色
        'display_color': display_color,  # 用于显示的RGB颜色
        'is_colorful': is_colorful_status,
        'description': description
    }
    color_timeline.append(entry)
    
    # 只在详细模式下显示实时颜色变化
    if VERBOSE_MODE:
        status_char = "🎨" if is_colorful_status else "⚫"
        color_format = f"RGBA{color}" if len(color) == 4 else f"RGB{color}"
        color_analysis = analyze_color_properties(color)
        print(f"  [{entry['time_str']}] {status_char} {color_format} - {color_analysis} - {description}")
        
        # 如果检测到彩色，创建颜色样本
        if is_colorful_status:
            print(f"    📸 检测到彩色（关卡完成），正在生成颜色样本...")
            visualize_color(color, f"关卡完成检测 - {description}")
    else:
        # 简化模式：只显示关键状态变化
        if is_colorful_status:
            print(f"  ✓ 检测到关卡完成！")
        elif description and "攻击1中" in description:  # 只在第一次攻击时显示状态
            print(f"  ⚫ 关卡进行中...")

def save_color_timeline():
    """保存颜色时间线到文件"""
    if not color_timeline:
        return
    
    timestamp = int(time.time())
    filename = f"color_timeline_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("颜色检测时间线报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"检测坐标: {LEVEL_CLEAR_CHECK_COORD}\n")
            f.write(f"总记录数: {len(color_timeline)}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("时间\t\t颜色\t\t\t状态\t描述\n")
            f.write("-" * 80 + "\n")
            
            for entry in color_timeline:
                status = "灰色系" if entry['is_colorful'] else "淡色系"
                f.write(f"{entry['time_str']}\t{entry['color']}\t\t{status}\t{entry['description']}\n")
        
        print(f"\n颜色时间线已保存到: {filename}")
        
    except Exception as e:
        print(f"保存颜色时间线时出错: {e}")

def display_color_timeline_summary():
    """显示颜色时间线摘要"""
    if not color_timeline:
        print("没有颜色记录")
        return
    
    print("\n" + "="*60)
    print("颜色检测时间线摘要")
    print("="*60)
    
    colorful_count = sum(1 for entry in color_timeline if entry['is_colorful'])
    non_colorful_count = len(color_timeline) - colorful_count
    
    print(f"总检测次数: {len(color_timeline)}")
    print(f"灰色检测: {colorful_count} 次")
    print(f"彩色检测: {non_colorful_count} 次")
    
    if color_timeline:
        print(f"开始时间: {color_timeline[0]['time_str']}")
        print(f"结束时间: {color_timeline[-1]['time_str']}")
        
        # 显示最后几次检测
        print(f"\n最后5次检测:")
        for entry in color_timeline[-5:]:
            status_char = "🎨" if entry['is_colorful'] else "⚫"
            print(f"  [{entry['time_str']}] {status_char} {entry['color']}")

def get_pixel_color_with_logging(x, y, description=""):
    """获取像素颜色并记录到时间线"""
    color = get_pixel_color(x, y)
    if color:
        is_colorful_status = is_colorful(color)
        log_color_change(time.time(), color, is_colorful_status, description)
    return color

def clear_level():
    """阶段2：清理关卡"""
    print("\n=== 阶段2：清理关卡 ===")
    
    print("开始攻击，同时监控关卡完成状态...")
    if VERBOSE_MODE:
        print("  检测逻辑：当指定坐标不是灰色时，关卡完成")
        print(f"  监控坐标: {LEVEL_CLEAR_CHECK_COORD}")
        print("  实时颜色时间线:")
        print("  ⚫ = 灰色系（关卡进行中）  🎨 = 彩色（关卡完成）")
        print("  注意：颜色可能显示为RGB或RGBA格式")
    
    # 首先点击技能
    print("点击技能...")
    human_click(SKILL_COORD[0], SKILL_COORD[1], "技能激活")
    time.sleep(random.uniform(0.3, 0.6))  # 技能激活延迟
    
    # 移动到攻击位置
    attack_x, attack_y = add_human_variation(ATTACK_COORD[0], ATTACK_COORD[1])
    pyautogui.moveTo(attack_x, attack_y, duration=random.uniform(0.2, 0.4))
    time.sleep(random.uniform(0.1, 0.2))
    
    start_time = time.time()
    attack_count = 0
    
    while time.time() - start_time < MAX_ATTACK_DURATION and not should_stop:
        attack_count += 1
        if VERBOSE_MODE:
            print(f"\n  第 {attack_count} 次攻击（持续 {ATTACK_HOLD_DURATION} 秒）...")
        elif attack_count == 1:
            print("  开始攻击循环...")
        
        # 开始攻击
        pyautogui.mouseDown()
        if VERBOSE_MODE:
            print(f"    鼠标按下，攻击坐标: ({attack_x}, {attack_y})")
        
        # 持续攻击，同时检查关卡是否完成
        hold_start_time = time.time()
        level_completed = False
        
        while time.time() - hold_start_time < ATTACK_HOLD_DURATION and not should_stop:
            # 每0.1秒检查一次关卡状态（使用带记录的函数）
            current_color = get_pixel_color_with_logging(
                LEVEL_CLEAR_CHECK_COORD[0], 
                LEVEL_CLEAR_CHECK_COORD[1], 
                f"攻击{attack_count}中"
            )
            
            if current_color and is_colorful(current_color):
                level_completed = True
                if VERBOSE_MODE:
                    print(f"\n    ✓ 检测到彩色，关卡完成！")
                    print(f"    原始颜色: {current_color}")
                    print(f"    RGB部分: {normalize_color(current_color)}")
                    print(f"    颜色分析: {analyze_color_properties(current_color)}")
                    
                    # 保存关卡完成时的调试截图
                    save_debug_screenshot(
                        LEVEL_CLEAR_CHECK_COORD[0], 
                        LEVEL_CLEAR_CHECK_COORD[1], 
                        current_color, 
                        "level_complete"
                    )
                break
            time.sleep(0.1)
        
        # 释放攻击
        pyautogui.mouseUp()
        if VERBOSE_MODE:
            print(f"    攻击释放")
        
        # 如果关卡完成，执行额外的攻击
        if level_completed:
            if VERBOSE_MODE:
                print(f"  关卡已完成，执行最后一次攻击（{FINAL_ATTACK_DURATION} 秒）...")
            else:
                print("  执行最后一次攻击...")
            time.sleep(random.uniform(0.1, 0.3))  # 短暂间隔
            pyautogui.mouseDown()
            if VERBOSE_MODE:
                print(f"    最后攻击开始")
            time.sleep(FINAL_ATTACK_DURATION)
            pyautogui.mouseUp()
            if VERBOSE_MODE:
                print(f"    最后攻击结束")
            
            # 攻击完成后暂停2秒
            print("  攻击完成，暂停2秒后返回城镇...")
            time.sleep(2.0)
            
            print("✓ 关卡清理完成！")
            return True
        
        # 如果关卡未完成，短暂休息后继续
        if not should_stop:
            rest_time = random.uniform(0.2, 0.5)
            if VERBOSE_MODE:
                print(f"    休息 {rest_time:.1f} 秒后继续...")
            time.sleep(rest_time)
    
    print("✗ 关卡清理超时或被中断")
    return False

def return_to_town():
    """阶段3：返回城镇"""
    print("\n=== 阶段3：返回城镇 ===")
    
    for i, (x, y) in enumerate(RETURN_TO_TOWN_COORDS):
        if should_stop:
            break
        print(f"  返回城镇步骤 {i+1}/3")
        human_click(x, y, f"返回城镇{i+1}")
        random_action_delay()
    
    print("✓ 返回城镇完成")

def post_loop_town_behavior():
    """每轮循环完成后在城镇的行为：等待3秒，然后左右拖拽"""
    print(f"\n=== 城镇等待和移动 ===")
    print(f"等待 {POST_LOOP_WAIT_TIME} 秒...")
    
    # 等待3秒，可被中断
    for i in range(int(POST_LOOP_WAIT_TIME)):
        if should_stop:
            return
        print(f"  等待中... {int(POST_LOOP_WAIT_TIME)-i} 秒")
        time.sleep(1)
    
    if should_stop:
        return
    
    print("开始城镇移动...")
    
    # 向左拖拽0.5秒
    print("  向左移动 0.5 秒...")
    left_end_x = JOYSTICK_START[0] - JOYSTICK_DRAG_DISTANCE
    left_end_y = JOYSTICK_START[1]
    human_drag(JOYSTICK_START[0], JOYSTICK_START[1], left_end_x, left_end_y, 
              0.5, "向左拖拽")
    
    if should_stop:
        return
    
    # 短暂停顿
    time.sleep(random.uniform(0.2, 0.4))
    
    # 向右拖拽1.5秒
    print("  向右移动 1.5 秒...")
    right_end_x = JOYSTICK_START[0] + JOYSTICK_DRAG_DISTANCE
    right_end_y = JOYSTICK_START[1]
    human_drag(JOYSTICK_START[0], JOYSTICK_START[1], right_end_x, right_end_y, 
              1.5, "向右拖拽")
    
    print("✓ 城镇移动完成")

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global should_stop
    print("\n检测到 Ctrl+C，正在安全退出...")
    should_stop = True
    
    # 显示颜色时间线摘要
    display_color_timeline_summary()
    
    # 保存颜色时间线到文件
    save_color_timeline()

# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)

def main():
    """主程序循环"""
    print("智能游戏自动化脚本已启动...")
    print(f"关卡完成检测坐标: {LEVEL_CLEAR_CHECK_COORD}")
    print(f"检测逻辑: 当该坐标不是灰色时，判定关卡完成")
    print(f"最大循环次数: {MAX_CYCLES}")
    print(f"详细输出模式: {'开启' if VERBOSE_MODE else '关闭'}")
    print("按 Ctrl+C 可以随时停止脚本。")

    # 调试预览功能（仅在详细模式下显示）
    if VERBOSE_MODE:
        print("\n" + "="*50)
        show_detection_point_preview()
        print("="*50)
        
        # 询问是否要显示检测区域
        try:
            response = input("\n是否要在屏幕上显示检测区域？(y/n): ").lower().strip()
            if response in ['y', 'yes', '是']:
                visualize_detection_area()
        except:
            pass
    
    # 倒计时，给用户时间切换窗口
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print("开始执行！")

    try:
        cycle_count = 0
        
        while cycle_count < MAX_CYCLES and not should_stop:
            cycle_count += 1
            print(f"\n{'='*50}")
            print(f"第 {cycle_count} 轮游戏循环")
            print(f"{'='*50}")
            
            # 阶段1：进入关卡
            if not should_stop:
                enter_level()
            
            # 等待5秒让关卡加载完成
            if not should_stop:
                print("\n等待关卡加载完成...")
                for i in range(5):
                    if should_stop:
                        break
                    print(f"  等待中... {5-i} 秒")
                    time.sleep(1)
            
            # 阶段2：清理关卡
            if not should_stop:
                level_success = clear_level()
                if not level_success:
                    print("关卡清理失败，跳过本轮循环")
                    continue
            
            # 阶段3：返回城镇
            if not should_stop:
                return_to_town()
            
            # 每轮循环完成后在城镇的行为
            if not should_stop and cycle_count < MAX_CYCLES:
                post_loop_town_behavior()
            
            # 循环间隔
            if not should_stop and cycle_count < MAX_CYCLES:
                print(f"\n本轮循环完成，准备下一轮...")
                random_action_delay()

        if cycle_count >= MAX_CYCLES:
            print(f"\n已完成 {MAX_CYCLES} 轮循环，脚本自动结束。")

    except Exception as e:
        print(f"\n脚本运行出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 确保鼠标释放
        pyautogui.mouseUp()
        
        # 显示最终的颜色时间线摘要
        display_color_timeline_summary()
        save_color_timeline()
        
    print("\n脚本已完全停止。")

if __name__ == "__main__":
    # 设置pyautogui安全选项
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    
    main()