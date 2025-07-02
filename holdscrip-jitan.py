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
# 基本坐标配置
ATTACK_COORD = (1797, 404)            # 攻击坐标
CHALLENGE_AGAIN_COORD = (1779, 125)   # 再次挑战按钮
BACK_JUMP_COORD = (1738, 400)         # 后跳坐标
RETURN_TO_TOWN_COORD = (1777, 164)    # 返回城镇按钮

# 黑暗大地关卡进入坐标
DARK_LAND_COORDS = [
    (1127, 85),    # 第一步
    (1404, 327),   # 第二步  
    (1800, 412)    # 第三步
]

# 检测坐标
PL_EXHAUSTED_CHECK_COORD = (1462, 192)  # PL不足检测坐标
LEVEL_COMPLETE_CHECK_COORD = (1666, 61) # 关卡完成检测坐标（再次挑战按钮）

# 时间配置
ATTACK_HOLD_DURATION = 1.4            # 攻击持续时间
ATTACK_REPEATS = 4                    # 攻击重复次数
ITEM_PICKUP_HOLD_DURATION = 1.0       # 拾取物品持续时间
ITEM_PICKUP_REPEATS = 4               # 拾取物品重复次数
CHECK_INTERVAL = 0.5                  # 检测间隔
MAX_FIGHT_DURATION = 60               # 最大战斗时间（秒）
CYCLE_DELAY = 0.3                     # 循环间隔
MAX_CYCLES = 100                      # 最大循环次数

# 人性化参数
COORD_VARIATION = 3                   # 坐标随机偏移范围
MIN_ACTION_DELAY = 0.3               # 动作间最小延迟
MAX_ACTION_DELAY = 0.8               # 动作间最大延迟

# 调试和控制参数
VERBOSE_MODE = True                 # 详细输出模式（默认关闭）

# 全局变量
should_stop = False
current_level = "jitan"              # 当前关卡类型：jitan 或 dark_land

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
    
    if VERBOSE_MODE:
        print(f"  {description}坐标: ({click_x}, {click_y})")
    pyautogui.moveTo(click_x, click_y, duration=move_duration)
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.click()

def human_hold(x, y, hold_duration=1.0, description="长按"):
    """执行人性化的长按操作"""
    if should_stop:
        return False
    
    hold_x, hold_y = add_human_variation(x, y)
    move_duration = random.uniform(0.2, 0.4)
    pyautogui.moveTo(hold_x, hold_y, duration=move_duration)
    
    time.sleep(random.uniform(0.1, 0.2))
    pyautogui.mouseDown()
    
    if VERBOSE_MODE:
        print(f"  {description}开始，坐标: ({hold_x}, {hold_y})，持续 {hold_duration} 秒")
    
    # 保持期间添加随机变化
    actual_hold_duration = hold_duration + random.uniform(-0.1, 0.2)
    hold_start_time = time.time()
    while time.time() - hold_start_time < actual_hold_duration and not should_stop:
        time.sleep(0.05)
    
    pyautogui.mouseUp()
    if VERBOSE_MODE:
        print(f"  {description}完成")
    return not should_stop

def get_pixel_color(x, y):
    """获取指定坐标的像素颜色"""
    try:
        screenshot = pyautogui.screenshot()
        color = screenshot.getpixel((x, y))
        return color
    except Exception as e:
        if VERBOSE_MODE:
            print(f"获取像素颜色时出错: {e}")
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
    """检查颜色是否不是灰色（按钮出现）- 模糊检测"""
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

def is_bright_color(color, brightness_threshold=150):
    """检查颜色是否足够亮（按钮出现）- 专门用于按钮检测"""
    if color is None:
        return False
    
    # 标准化颜色格式
    rgb_color = normalize_color(color)
    if rgb_color is None:
        return False
    
    r, g, b = rgb_color
    brightness = (r + g + b) / 3
    
    # 判断是否为亮色（按钮通常是亮色）
    return brightness > brightness_threshold

def check_pl_exhausted():
    """检查PL是否耗尽"""
    color = get_pixel_color(PL_EXHAUSTED_CHECK_COORD[0], PL_EXHAUSTED_CHECK_COORD[1])
    
    # 使用多种检测方法
    is_colorful_detected = is_colorful(color)
    is_bright_detected = is_bright_color(color)
    
    # PL耗尽时通常显示明亮或彩色的警告
    is_exhausted = is_colorful_detected or is_bright_detected
    
    if VERBOSE_MODE:
        color_analysis = analyze_color_properties(color)
        print(f"  PL检测 - 坐标: {PL_EXHAUSTED_CHECK_COORD}, 颜色: {color}")
        print(f"  分析: {color_analysis}")
        print(f"  彩色检测: {is_colorful_detected}, 亮色检测: {is_bright_detected}")
        if is_exhausted:
            print(f"  → PL耗尽！")
    
    return is_exhausted

def check_level_complete():
    """检查关卡是否完成（再次挑战按钮是否出现）"""
    color = get_pixel_color(LEVEL_COMPLETE_CHECK_COORD[0], LEVEL_COMPLETE_CHECK_COORD[1])
    
    # 使用多种检测方法
    is_colorful_detected = is_colorful(color)
    is_bright_detected = is_bright_color(color)
    
    # 按钮出现时通常是明亮或彩色的
    is_complete = is_colorful_detected or is_bright_detected
    
    if VERBOSE_MODE:
        color_analysis = analyze_color_properties(color)
        print(f"  关卡完成检测 - 坐标: {LEVEL_COMPLETE_CHECK_COORD}, 颜色: {color}")
        print(f"  分析: {color_analysis}")
        print(f"  彩色检测: {is_colorful_detected}, 亮色检测: {is_bright_detected}")
        if is_complete:
            print(f"  → 关卡完成！")
    
    return is_complete

def random_action_delay():
    """动作之间的随机延迟"""
    delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
    time.sleep(delay)

def pickup_items():
    """拾取物品：攻击坐标长按1秒，重复4次"""
    print("开始拾取物品...")
    
    for i in range(ITEM_PICKUP_REPEATS):
        if should_stop:
            break
        
        print(f"  拾取物品 {i+1}/{ITEM_PICKUP_REPEATS}")
        success = human_hold(ATTACK_COORD[0], ATTACK_COORD[1], 
                           ITEM_PICKUP_HOLD_DURATION, f"拾取物品{i+1}")
        
        if not success:
            break
        
        # 拾取间隔
        if i < ITEM_PICKUP_REPEATS - 1:
            time.sleep(random.uniform(0.2, 0.5))
    
    print("物品拾取完成")

def enter_dark_land():
    """进入黑暗大地关卡"""
    global current_level
    print("\n=== 进入黑暗大地关卡 ===")
    
    for i, (x, y) in enumerate(DARK_LAND_COORDS):
        if should_stop:
            break
        print(f"  黑暗大地进入步骤 {i+1}/3")
        human_click(x, y, f"黑暗大地步骤{i+1}")
        random_action_delay()
    
    current_level = "dark_land"
    print("✓ 已进入黑暗大地关卡")

def return_to_town():
    """返回城镇"""
    print("返回城镇...")
    human_click(RETURN_TO_TOWN_COORD[0], RETURN_TO_TOWN_COORD[1], "返回城镇")
    time.sleep(2.0)  # 等待返回城镇

def fight_until_complete():
    """战斗直到关卡完成"""
    print(f"开始战斗（{current_level}模式）...")
    
    start_time = time.time()
    attack_count = 0
    
    while time.time() - start_time < MAX_FIGHT_DURATION and not should_stop:
        # 检查PL是否耗尽
        if check_pl_exhausted():
            print("检测到PL耗尽！")
            return "pl_exhausted"
        
        # 检查关卡是否完成
        if check_level_complete():
            print("检测到关卡完成！")
            return "level_complete"
        
        # 执行攻击
        attack_count += 1
        if VERBOSE_MODE:
            print(f"  执行第 {attack_count} 次攻击")
        elif attack_count == 1:
            print("  开始攻击循环...")
        
        success = human_hold(ATTACK_COORD[0], ATTACK_COORD[1], 
                           ATTACK_HOLD_DURATION, f"攻击{attack_count}")
        
        if not success:
            break
        
        # 攻击间隔
        time.sleep(random.uniform(0.2, 0.5))
    
    print("战斗超时或被中断")
    return "timeout"

def challenge_again():
    """再次挑战"""
    print("点击再次挑战...")
    human_click(CHALLENGE_AGAIN_COORD[0], CHALLENGE_AGAIN_COORD[1], "再次挑战")

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global should_stop
    print("\n检测到 Ctrl+C，正在安全退出...")
    should_stop = True

# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)

def main():
    """主程序循环"""
    global current_level
    
    print("智能极团自动化脚本已启动...")
    print(f"PL检测坐标: {PL_EXHAUSTED_CHECK_COORD}")
    print(f"关卡完成检测坐标: {LEVEL_COMPLETE_CHECK_COORD}")
    print(f"最大循环次数: {MAX_CYCLES}")
    print(f"详细输出模式: {'开启' if VERBOSE_MODE else '关闭'}")
    print("按 Ctrl+C 可以随时停止脚本。")
    
    # 倒计时
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print("开始执行！")
    
    try:
        cycle_count = 0
        
        while cycle_count < MAX_CYCLES and not should_stop:
            cycle_count += 1
            print(f"\n{'='*50}")
            print(f"第 {cycle_count} 轮循环 - 当前关卡: {current_level}")
            print(f"{'='*50}")
            
            # 战斗阶段
            fight_result = fight_until_complete()
            
            if should_stop:
                break
            
            if fight_result == "pl_exhausted":
                print("\nPL耗尽，切换到黑暗大地关卡")
                return_to_town()
                if not should_stop:
                    enter_dark_land()
                    # 继续下一轮循环，但现在在黑暗大地
                    continue
                    
            elif fight_result == "level_complete":
                print("\n关卡完成，开始拾取物品")
                pickup_items()
                
                if not should_stop:
                    print("准备再次挑战...")
                    challenge_again()
                    # 等待关卡加载
                    time.sleep(2.0)
                    
            elif fight_result == "timeout":
                print("\n战斗超时，尝试再次挑战")
                challenge_again()
                time.sleep(2.0)
            
            # 循环间隔
            if not should_stop and cycle_count < MAX_CYCLES:
                if VERBOSE_MODE:
                    print(f"等待 {CYCLE_DELAY} 秒后开始下一轮...")
                time.sleep(CYCLE_DELAY)
        
        if cycle_count >= MAX_CYCLES:
            print(f"\n已完成 {MAX_CYCLES} 轮循环，脚本自动结束。")
            
    except Exception as e:
        print(f"\n脚本运行出错: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 确保鼠标释放
        pyautogui.mouseUp()
        print("\n脚本已完全停止。")

if __name__ == "__main__":
    # 设置pyautogui安全选项
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    
    main()