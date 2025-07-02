import pyautogui
import time
import signal
import sys
import random
import threading

# 禁用PyAutoGUI的fail-safe功能
pyautogui.FAILSAFE = False

# --- 1. 参数配置 ---
# 你可以根据需要修改这些值
CLICK_X, CLICK_Y = 1779, 125  # 单击坐标  再次挑战
CLICK_X2, CLICK_Y2 = 1738, 400  # 单击坐标 后跳
HOLD_X, HOLD_Y = 1779, 400    # 长按坐标 攻击
HOLD_DURATION = 1.4             # 长按的持续时间（秒）
HOLD_REPEATS = 4             # 长按重复次数
CYCLE_DELAY = 0.3               # 每个大循环之间的间隔时间（秒）
MAX_CYCLES = 100              # 最大循环次数（防止无限运行）

# 人性化参数
COORD_VARIATION = 3           # 坐标随机偏移范围（像素）
MIN_CLICK_DELAY = 0.08        # 两次点击之间的最小间隔（秒）
MAX_CLICK_DELAY = 0.25        # 两次点击之间的最大间隔（秒）
MIN_ACTION_DELAY = 0.3        # 动作之间的最小间隔（秒）
MAX_ACTION_DELAY = 0.8        # 动作之间的最大间隔（秒）

# 鼠标控制参数
MOUSE_CONTROL_ENABLED = True    # 启用鼠标控制
EDGE_TRIGGER_SIZE = 100         # 触发边缘的大小（像素）
EDGE_HOLD_TIME = 1            # 在边缘停留的时间（秒）

# 全局变量来控制脚本
should_stop = False
script_enabled = False
is_running = False
last_mouse_check = 0
mouse_edge_start_time = 0
current_edge = None

def get_screen_size():
    """获取屏幕尺寸"""
    return pyautogui.size()

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

def random_action_delay():
    """动作之间的随机延迟"""
    delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
    time.sleep(delay)

def human_hold(x, y, hold_duration=2.0):
    """执行人性化的长按操作"""
    # 添加坐标变化和随机移动时间
    hold_x, hold_y = add_human_variation(x, y)
    move_duration = random.uniform(0.2, 0.5)
    pyautogui.moveTo(hold_x, hold_y, duration=move_duration)
    
    # 添加短暂停顿再按下
    time.sleep(random.uniform(0.1, 0.3))
    pyautogui.mouseDown()
    print(f"  鼠标已按下，坐标: ({hold_x}, {hold_y})")
    
    # 保持期间添加随机变化
    actual_hold_duration = hold_duration + random.uniform(-0.2, 0.3)
    hold_start_time = time.time()
    while time.time() - hold_start_time < actual_hold_duration and not should_stop:
        # 检查是否被暂停
        if not is_running:
            pyautogui.mouseUp()
            print(f"  鼠标已松开 (暂停)")
            # 等待恢复
            while not is_running and not should_stop:
                time.sleep(0.1)
            # 如果恢复了，重新按下
            if not should_stop and is_running:
                pyautogui.moveTo(hold_x, hold_y, duration=0.1)
                pyautogui.mouseDown()
                print(f"  鼠标重新按下 (恢复)")
                hold_start_time = time.time()  # 重置计时
        time.sleep(0.05)
    
    if should_stop:
        pyautogui.mouseUp()
        return False
    
    pyautogui.mouseUp()
    print(f"  鼠标已松开，持续了 {actual_hold_duration:.2f} 秒")
    return True

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global should_stop
    print("\n检测到 Ctrl+C，正在安全退出...")
    should_stop = True

def on_start_pressed():
    """启动/恢复脚本的通用处理"""
    global is_running, script_enabled, should_stop
    if not script_enabled:
        script_enabled = True
        print("\n🟢 脚本已启用！")
    elif not is_running:
        is_running = True
        should_stop = False  # 重置停止标志
        print("\n▶️  脚本开始/恢复运行...")
    else:
        print("\n⚠️  脚本已在运行中")

def on_pause_pressed():
    """暂停脚本的通用处理"""
    global is_running
    if is_running:
        is_running = False
        print("\n⏸️  脚本已暂停 (可用左边缘恢复)")
    else:
        print("\n⚠️  脚本未运行")

def check_mouse_edges():
    """检查鼠标是否在屏幕边缘"""
    global current_edge, mouse_edge_start_time, last_mouse_check
    
    current_time = time.time()
    if current_time - last_mouse_check < 0.2:  # 每200ms检查一次
        return
    last_mouse_check = current_time
    
    try:
        mouse_x, mouse_y = pyautogui.position()
        screen_width, screen_height = get_screen_size()
        
        # 检查屏幕边缘（避开角落）
        edge = None
        if mouse_x <= EDGE_TRIGGER_SIZE and EDGE_TRIGGER_SIZE < mouse_y < screen_height - EDGE_TRIGGER_SIZE:
            edge = "left"  # 左边缘 - 启动/恢复
        elif mouse_x >= screen_width - EDGE_TRIGGER_SIZE and EDGE_TRIGGER_SIZE < mouse_y < screen_height - EDGE_TRIGGER_SIZE:
            edge = "right"  # 右边缘 - 暂停
        
        if edge != current_edge:
            current_edge = edge
            mouse_edge_start_time = current_time
        elif edge and current_time - mouse_edge_start_time >= EDGE_HOLD_TIME:
            # 在边缘停留足够时间
            if edge == "left":
                on_start_pressed()
                print("🖱️  鼠标左边缘触发 - 启动/恢复脚本")
            elif edge == "right":
                on_pause_pressed()
                print("🖱️  鼠标右边缘触发 - 暂停脚本")
            
            # 重置以避免重复触发
            mouse_edge_start_time = current_time + 3.0
            
    except Exception as e:
        pass  # 忽略鼠标检查错误

def start_mouse_monitor():
    """启动鼠标监控线程"""
    def mouse_monitor():
        while not should_stop:
            if MOUSE_CONTROL_ENABLED:
                check_mouse_edges()
            time.sleep(0.2)
    
    monitor_thread = threading.Thread(target=mouse_monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread

def wait_for_start():
    """等待用户启动脚本"""
    global script_enabled, is_running, should_stop
    print("\n⏳ 等待启动命令...")
    print("   移动鼠标到屏幕左边缘停留1.5秒 或 创建start.txt文件")
    print("   按 Ctrl+C 退出程序")
    
    while not script_enabled and not should_stop:
        time.sleep(0.1)
    
    if should_stop:
        return False
    
    # 等待运行命令
    print("\n📋 脚本已启用，再次触发启动命令开始运行")
    while not is_running and not should_stop:
        time.sleep(0.1)
    
    return not should_stop

# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)

# --- 2. 主程序 ---
print("🎮 jitan自动化脚本 v3.0 - 暂停/恢复控制")
print("=" * 60)
print(f"目标坐标1: ({CLICK_X}, {CLICK_Y})")
print(f"目标坐标2: ({CLICK_X2}, {CLICK_Y2})")
print(f"长按坐标: ({HOLD_X}, {HOLD_Y})")
print(f"最大循环次数: {MAX_CYCLES}")
print("=" * 60)

print("\n🎯 控制方式:")
print("\n1️⃣  【鼠标控制】- 推荐游戏时使用")
print("   🖱️  鼠标移动到屏幕左边缘停留1.5秒 = 启动/恢复脚本")
print("   🖱️  鼠标移动到屏幕右边缘停留1.5秒 = 暂停脚本")
print("   ✅ 避开了屏幕角落，不会触发系统fail-safe")
print("   ✅ 暂停后可以用左边缘恢复，无需重启")

print("\n2️⃣  【文件控制】- 最稳定")
print("   📁 创建文件 'start.txt' = 启动/恢复脚本")
print("   📁 创建文件 'stop.txt' = 暂停脚本")
print("   📁 删除对应文件可重复使用")

print("\n3️⃣  【完全退出】")
print("   🛑 Ctrl+C = 完全退出程序")

print("\n" + "=" * 60)
print("💡 建议: 游戏时使用鼠标边缘控制，左启动右暂停！")
print("=" * 60)

# 启动鼠标监控
if MOUSE_CONTROL_ENABLED:
    start_mouse_monitor()
    print("\n🖱️  鼠标边缘控制已激活")

# 启动文件监控
def start_file_monitor():
    """启动文件监控线程"""
    def file_monitor():
        while not should_stop:
            try:
                import os
                if os.path.exists('start.txt'):
                    on_start_pressed()
                    print("📁 检测到 start.txt - 启动/恢复脚本")
                    try:
                        os.remove('start.txt')
                    except:
                        pass
                
                if os.path.exists('stop.txt'):
                    on_pause_pressed()
                    print("📁 检测到 stop.txt - 暂停脚本")
                    try:
                        os.remove('stop.txt')
                    except:
                        pass
                        
            except Exception as e:
                pass
            time.sleep(0.5)  # 每500ms检查一次文件
    
    monitor_thread = threading.Thread(target=file_monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread

start_file_monitor()
print("📁 文件控制已激活")

# 直接启动脚本
script_enabled = True
is_running = True
print("\n🚀 脚本自动启动中...")

try:
    cycle_count = 0
    
    # 主循环 - 永远不会因为暂停而退出
    while not should_stop:
        # 如果脚本被暂停，等待恢复
        while not is_running and not should_stop:
            time.sleep(0.1)
        
        if should_stop:
            break
        
        # 检查是否还有循环次数
        if cycle_count >= MAX_CYCLES:
            print(f"\n🎯 已完成 {MAX_CYCLES} 轮循环！脚本将继续等待...")
            # 不退出，继续等待暂停/恢复控制
            while not should_stop:
                time.sleep(1)
            break
            
        cycle_count += 1
        print(f"\n--- 第 {cycle_count} 轮循环 ---")

        # --- 动作组一：长按重复 ---
        for hold_count in range(HOLD_REPEATS):
            # 检查暂停状态
            while not is_running and not should_stop:
                time.sleep(0.1)
            
            if should_stop:
                break
            
            print(f"正在执行第 {hold_count + 1} 次长按操作，持续 {HOLD_DURATION} 秒...")
            success = human_hold(HOLD_X, HOLD_Y, HOLD_DURATION)
            
            if not success:  # 如果被中断
                break
            
            print(f"  第 {hold_count + 1} 次长按完成。")
            
            # 长按之间的间隔（除了最后一次）
            if hold_count < HOLD_REPEATS - 1:
                # 在延迟期间也检查暂停状态
                delay_start = time.time()
                target_delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
                while time.time() - delay_start < target_delay and not should_stop:
                    if not is_running:
                        # 暂停期间等待
                        while not is_running and not should_stop:
                            time.sleep(0.1)
                        # 恢复后重新计算延迟时间
                        delay_start = time.time()
                    time.sleep(0.1)

        # 检查暂停状态
        while not is_running and not should_stop:
            time.sleep(0.1)
        
        if should_stop:
            break

        # 长按组完成后的延迟
        delay_start = time.time()
        target_delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
        while time.time() - delay_start < target_delay and not should_stop:
            if not is_running:
                # 暂停期间等待
                while not is_running and not should_stop:
                    time.sleep(0.1)
                # 恢复后重新计算延迟时间
                delay_start = time.time()
            time.sleep(0.1)

        # --- 动作组二：第一次点击 ---
        # 检查暂停状态
        while not is_running and not should_stop:
            time.sleep(0.1)
            
        if is_running and not should_stop:
            print("正在执行第一次单击操作...")
            human_click(CLICK_X, CLICK_Y, "第一次单击")
            print("  第一次单击完成。")
        
        # --- 动作组三：第二次点击 ---
        # 检查暂停状态
        while not is_running and not should_stop:
            time.sleep(0.1)
            
        if is_running and not should_stop:
            print("正在执行第二次单击操作...")
            human_click(CLICK_X2, CLICK_Y2, "第二次单击")
            print("  第二次单击完成。")

        # --- 等待下一次循环 ---
        if not should_stop:
            print(f"本轮循环结束，等待 {CYCLE_DELAY} 秒后开始下一轮...")
            sleep_start = time.time()
            while time.time() - sleep_start < CYCLE_DELAY and not should_stop:
                if not is_running:
                    # 暂停期间等待
                    while not is_running and not should_stop:
                        time.sleep(0.1)
                    # 恢复后重新计算等待时间
                    sleep_start = time.time()
                time.sleep(0.1)

    # 只有 Ctrl+C 才会到达这里
    print(f"\n🛑 脚本已完全停止（已完成 {cycle_count} 轮）")

except Exception as e:
    print(f"\n❌ 脚本运行出错: {e}")

finally:
    # 确保无论脚本如何退出，鼠标都会被松开
    pyautogui.mouseUp()
    print("\n👋 脚本已完全停止。")