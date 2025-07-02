import pyautogui
import time
import signal
import sys
import random

# --- 1. 参数配置 ---
# 你可以根据需要修改这些值
CLICK_X, CLICK_Y = 1779, 400  # 目标坐标
DOUBLE_CLICK_X, DOUBLE_CLICK_Y = 1779, 125  # 双击坐标
HOLD_DURATION = 8             # 长按的持续时间（秒）
CYCLE_DELAY = 2               # 每个大循环之间的间隔时间（秒）
MAX_CYCLES = 100              # 最大循环次数（防止无限运行）

# 人性化参数
COORD_VARIATION = 3           # 坐标随机偏移范围（像素）
MIN_CLICK_DELAY = 0.08        # 两次点击之间的最小间隔（秒）
MAX_CLICK_DELAY = 0.25        # 两次点击之间的最大间隔（秒）
MIN_ACTION_DELAY = 0.3        # 动作之间的最小间隔（秒）
MAX_ACTION_DELAY = 0.8        # 动作之间的最大间隔（秒）

# 全局变量来控制脚本停止
should_stop = False

def add_human_variation(x, y, variation=COORD_VARIATION):
    """为坐标添加随机偏移，模拟人类点击的不精确性"""
    new_x = x + random.randint(-variation, variation)
    new_y = y + random.randint(-variation, variation)
    return new_x, new_y

def human_click(x, y, description="点击"):
    """执行更人性化的点击"""
    # 添加坐标变化
    click_x, click_y = add_human_variation(x, y)
    
    # 随机移动速度
    move_duration = random.uniform(0.1, 0.3)
    
    print(f"  {description}坐标: ({click_x}, {click_y})")
    pyautogui.moveTo(click_x, click_y, duration=move_duration)
    
    # 添加短暂停顿，模拟人类反应时间
    time.sleep(random.uniform(0.05, 0.15))
    
    pyautogui.click()

def human_double_click(x, y):
    """执行更人性化的双击（两次单击）"""
    print(f"  执行第一次点击...")
    human_click(x, y, "第一次点击")
    
    # 两次点击之间的随机间隔
    delay = random.uniform(MIN_CLICK_DELAY, MAX_CLICK_DELAY)
    time.sleep(delay)
    
    print(f"  执行第二次点击...")
    human_click(x, y, "第二次点击")

def random_action_delay():
    """动作之间的随机延迟"""
    delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
    time.sleep(delay)

def human_click_hold_click(x, y, hold_duration=1.0):
    """执行点击-保持-点击序列"""
    print(f"  执行第一次点击...")
    
    # 第一次点击
    click_x1, click_y1 = add_human_variation(x, y)
    move_duration = random.uniform(0.1, 0.3)
    pyautogui.moveTo(click_x1, click_y1, duration=move_duration)
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.click()
    print(f"    第一次点击完成，坐标: ({click_x1}, {click_y1})")
    
    # 短暂间隔
    time.sleep(random.uniform(0.05, 0.2))
    
    # 保持按下
    click_x2, click_y2 = add_human_variation(x, y)
    move_duration = random.uniform(0.1, 0.25)
    pyautogui.moveTo(click_x2, click_y2, duration=move_duration)
    time.sleep(random.uniform(0.05, 0.15))
    
    print(f"  开始保持按下，持续约 {hold_duration} 秒...")
    pyautogui.mouseDown()
    
    # 保持期间添加随机变化
    actual_hold_duration = hold_duration + random.uniform(-0.1, 0.2)
    hold_start_time = time.time()
    while time.time() - hold_start_time < actual_hold_duration and not should_stop:
        time.sleep(0.05)
    
    if should_stop:
        pyautogui.mouseUp()
        return
    
    pyautogui.mouseUp()
    print(f"    保持完成，坐标: ({click_x2}, {click_y2})")
    
    # 短暂间隔
    time.sleep(random.uniform(0.05, 0.2))
    
    # 第二次点击
    print(f"  执行第二次点击...")
    click_x3, click_y3 = add_human_variation(x, y)
    move_duration = random.uniform(0.1, 0.3)
    pyautogui.moveTo(click_x3, click_y3, duration=move_duration)
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.click()
    print(f"    第二次点击完成，坐标: ({click_x3}, {click_y3})")

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global should_stop
    print("\n检测到 Ctrl+C，正在安全退出...")
    should_stop = True

# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)

# --- 2. 主程序 ---
print("自动化脚本已启动...")
print(f"目标坐标: ({CLICK_X}, {CLICK_Y})")
print(f"最大循环次数: {MAX_CYCLES}")
print("按 Ctrl+C 可以随时停止脚本。")

# 倒计时3秒，给你时间切换窗口
for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)
print("开始执行！")

try:
    cycle_count = 0
    # 循环执行，直到达到最大次数或手动停止
    while cycle_count < MAX_CYCLES and not should_stop:
        cycle_count += 1
        print(f"\n=== 第 {cycle_count} 轮循环 ===")

        # --- 动作一：长按并释放 ---
        print(f"正在执行长按操作，持续 {HOLD_DURATION} 秒...")
        
        # 添加坐标变化和随机移动时间
        hold_x, hold_y = add_human_variation(CLICK_X, CLICK_Y)
        move_duration = random.uniform(0.2, 0.5)
        pyautogui.moveTo(hold_x, hold_y, duration=move_duration)
        
        # 添加短暂停顿再按下
        time.sleep(random.uniform(0.1, 0.3))
        pyautogui.mouseDown()
        print(f"  鼠标已按下，坐标: ({hold_x}, {hold_y})")
        
        # 在按住期间，分段检查是否需要停止
        hold_start_time = time.time()
        while time.time() - hold_start_time < HOLD_DURATION and not should_stop:
            time.sleep(0.1) # 短暂休眠，避免CPU占用过高
        
        pyautogui.mouseUp()
        if should_stop:
            print("  检测到停止信号，鼠标已松开")
            break
        
        print("  鼠标已松开。长按完成。")
        
        # 动作间随机延迟
        random_action_delay()

        # --- 动作二：单击 ---
        if not should_stop:
            print("正在执行点击-保持-点击操作...")
            human_click_hold_click(CLICK_X, CLICK_Y, 1.0)
            print("  点击-保持-点击完成。")

        # 动作间随机延迟
        random_action_delay()

        # --- 动作三：双击 ---
        if not should_stop:
            print(f"正在执行双击操作，坐标: ({DOUBLE_CLICK_X}, {DOUBLE_CLICK_Y})...")
            human_double_click(DOUBLE_CLICK_X, DOUBLE_CLICK_Y)
            print("  双击完成。")

        # --- 等待下一次循环 ---
        if not should_stop and cycle_count < MAX_CYCLES:
            print(f"本轮循环结束，等待 {CYCLE_DELAY} 秒后开始下一轮...")
            sleep_start = time.time()
            while time.time() - sleep_start < CYCLE_DELAY and not should_stop:
                time.sleep(0.1)

    if cycle_count >= MAX_CYCLES:
        print(f"\n已完成 {MAX_CYCLES} 轮循环，脚本自动结束。")

except Exception as e:
    print(f"\n脚本运行出错: {e}")

finally:
    # 确保无论脚本如何退出（正常停止或出错），鼠标都会被松开
    pyautogui.mouseUp()
    print("\n脚本已完全停止。")