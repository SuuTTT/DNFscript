import pyautogui
import time
import signal
import sys
import random
import threading
from PIL import Image, ImageDraw
import numpy as np

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
MAX_CYCLES = 500              # 最大循环次数（防止无限运行）

# 人性化参数
COORD_VARIATION = 3           # 坐标随机偏移范围（像素）
MIN_CLICK_DELAY = 0.08        # 两次点击之间的最小间隔（秒）
MAX_CLICK_DELAY = 0.25        # 两次点击之间的最大间隔（秒）
MIN_ACTION_DELAY = 0.3        # 动作之间的最小间隔（秒）
MAX_ACTION_DELAY = 0.8        # 动作之间的最大间隔（秒）

# 鼠标控制参数
MOUSE_CONTROL_ENABLED = True    # 启用鼠标控制
EDGE_TRIGGER_SIZE = 10         # 触发边缘的大小（像素）
EDGE_HOLD_TIME = 0.5            # 在边缘停留的时间（秒）

# TOP EDGE MODE 参数 (3秒攻击 + 随机技能)
TOP_ATTACK_DURATION = 3.0       # 顶部模式攻击持续时间
SKILL_COORDS = [                # 技能按钮坐标列表 (技能1-7)
    (1590, 400),               # 技能1
    (1665, 400),               # 技能2  
    (1620, 350),               # 技能3
    (1685, 350),               # 技能4
    (1750, 350),               # 技能5
    (1718, 300),               # 技能6
    (1780, 300)                # 技能7
]

# TOP ATTACK 技能选择配置
TOP_SKILL_ENABLED = [True, True, True, True, True, True, True]  # 启用的技能 (1-7)
TOP_DRAG_PROBABILITY = 0.3      # 选择拖拽技能的概率 (0.0-1.0, 0.3 = 30%概率)
TOP_DRAG_ENABLED = [True, True, True, True]  # 启用的拖拽方向 (上/下/左/右)

# JITAN模式技能坐标 (技能8-11)
JITAN_SKILL_COORDS = [          # JITAN模式使用的技能坐标列表
    (1660, 250),               # 技能8
    (1700, 250),               # 技能9
    (1750, 250),               # 技能10
    (1785, 250)                # 技能11
]

# JITAN 技能选择配置
JITAN_SKILL_ENABLED = [True, True, True, True]  # 启用的技能 (8-11)

# 拖拽技能坐标 (技能1-4)
DRAG_SKILL_START = (1660, 300)  # 拖拽技能起始位置
DRAG_DIRECTIONS = [             # 拖拽方向: 上-1, 下-2, 左-3, 右-4
    (1660, 250),               # 向上拖拽
    (1660, 350),               # 向下拖拽
    (1610, 300),               # 向左拖拽
    (1710, 300)                # 向右拖拽
]

# CATCARD MODE 参数 (下边缘模式)
# 游戏状态检测相关
LEVEL_CLEAR_CHECK_COORD = (1470, 410)  # 检测关卡完成的坐标
LEVEL_CLEAR_COLOR = (255, 255, 255)    # 关卡完成时的目标颜色
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
ATTACK_HOLD_DURATION = 0.7             # 单次攻击持续时间（秒）
FINAL_ATTACK_DURATION = 0.4            # 最后一次攻击持续时间（秒）
MAX_ATTACK_DURATION = 100               # 最大攻击时间（秒）
ACTION_DELAY_MIN = 0.5                 # 动作间最小延迟
ACTION_DELAY_MAX = 1.5                 # 动作间最大延迟
POST_LOOP_WAIT_TIME = 3.0             # 每轮循环完成后在城镇的等待时间（秒）

# 全局变量来控制脚本
should_stop = False
script_enabled = False
is_running = False
current_mode = "jitan"  # 当前模式: "jitan", "pause", "top_attack", "catcard"
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

def random_action_delay():
    """动作之间的随机延迟"""
    delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
    time.sleep(delay)

def get_pixel_color(x, y):
    """获取指定坐标的像素颜色"""
    try:
        screenshot = pyautogui.screenshot()
        color = screenshot.getpixel((x, y))
        return color
    except Exception as e:
        return None

def is_colorful(color, gray_threshold=40):
    """判断颜色是否为彩色（非灰色）"""
    if not color or len(color) < 3:
        return False
    
    r, g, b = color[:3]
    
    # 计算RGB差异
    max_diff = max(abs(r-g), abs(r-b), abs(g-b))
    
    return max_diff > gray_threshold

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
    global is_running, script_enabled, should_stop, current_mode
    if not script_enabled:
        script_enabled = True
        print("\n🟢 脚本已启用！")
    elif not is_running:
        current_mode = "jitan"
        is_running = True
        should_stop = False  # 重置停止标志
        print("\n▶️  切换到 JITAN 模式...")
    else:
        print("\n⚠️  脚本已在运行中")

def on_pause_pressed():
    """暂停脚本的通用处理"""
    global is_running, current_mode
    if is_running:
        is_running = False
        current_mode = "pause"
        print("\n⏸️  脚本已暂停 (可用其他边缘切换模式)")
    else:
        print("\n⚠️  脚本未运行")

def on_top_edge_pressed():
    """顶部边缘：3秒攻击 + 随机技能模式"""
    global is_running, script_enabled, should_stop, current_mode
    if not script_enabled:
        script_enabled = True
        print("\n🟢 脚本已启用！")
    current_mode = "top_attack"
    is_running = True
    should_stop = False
    print("\n🔥 切换到 TOP ATTACK 模式 (3秒攻击 + 随机技能)...")

def on_bottom_edge_pressed():
    """底部边缘：猫卡模式"""
    global is_running, script_enabled, should_stop, current_mode
    if not script_enabled:
        script_enabled = True
        print("\n🟢 脚本已启用！")
    current_mode = "catcard"
    is_running = True
    should_stop = False
    print("\n🐱 切换到 CATCARD 模式 (智能关卡清理)...")

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
        
        # 检查屏幕边缘
        edge = None
        if mouse_x <= EDGE_TRIGGER_SIZE and EDGE_TRIGGER_SIZE < mouse_y < screen_height - EDGE_TRIGGER_SIZE:
            edge = "left"  # 左边缘 - Jitan模式
        elif mouse_x >= screen_width - EDGE_TRIGGER_SIZE and EDGE_TRIGGER_SIZE < mouse_y < screen_height - EDGE_TRIGGER_SIZE:
            edge = "right"  # 右边缘 - 暂停
        elif mouse_y <= EDGE_TRIGGER_SIZE and EDGE_TRIGGER_SIZE < mouse_x < screen_width - EDGE_TRIGGER_SIZE:
            edge = "top"  # 顶部边缘 - 3秒攻击模式
        elif mouse_y >= screen_height - EDGE_TRIGGER_SIZE and EDGE_TRIGGER_SIZE < mouse_x < screen_width - EDGE_TRIGGER_SIZE:
            edge = "bottom"  # 底部边缘 - 猫卡模式
        
        if edge != current_edge:
            current_edge = edge
            mouse_edge_start_time = current_time
        elif edge and current_time - mouse_edge_start_time >= EDGE_HOLD_TIME:
            # 在边缘停留足够时间
            if edge == "left":
                on_start_pressed()
                print("🖱️  鼠标左边缘触发 - JITAN模式")
            elif edge == "right":
                on_pause_pressed()
                print("🖱️  鼠标右边缘触发 - 暂停模式")
            elif edge == "top":
                on_top_edge_pressed()
                print("🖱️  鼠标顶部边缘触发 - TOP ATTACK模式")
            elif edge == "bottom":
                on_bottom_edge_pressed()
                print("🖱️  鼠标底部边缘触发 - CATCARD模式")
            
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
    print("   移动鼠标到屏幕边缘停留1秒选择模式:")
    print("   左边缘 = JITAN模式 | 右边缘 = 暂停")
    print("   顶部边缘 = TOP ATTACK模式 | 底部边缘 = CATCARD模式")
    print("   按 Ctrl+C 退出程序")
    
    while not script_enabled and not should_stop:
        time.sleep(0.1)
    
    if should_stop:
        return False
    
    # 等待运行命令
    print("\n📋 脚本已启用，再次触发边缘命令开始运行")
    while not is_running and not should_stop:
        time.sleep(0.1)
    
    return not should_stop

# TOP ATTACK MODE 功能
def execute_top_attack_cycle():
    """执行顶部攻击模式：3秒攻击 + 随机技能"""
    if not is_running or should_stop or current_mode != "top_attack":
        return
    
    print("\n🔥 TOP ATTACK: 开始3秒攻击...")
    
    # 3秒攻击
    success = human_hold(HOLD_X, HOLD_Y, TOP_ATTACK_DURATION)
    if not success or not is_running:
        return
    
    print("🔥 TOP ATTACK: 攻击完成，选择随机技能...")
    
    # 创建可用技能列表（只包含启用的技能）
    available_skills = []
    for i, enabled in enumerate(TOP_SKILL_ENABLED):
        if enabled:
            available_skills.append(SKILL_COORDS[i])
    
    # 创建可用拖拽方向列表（只包含启用的方向）
    available_drags = []
    for i, enabled in enumerate(TOP_DRAG_ENABLED):
        if enabled:
            available_drags.append(DRAG_DIRECTIONS[i])
    
    # 根据概率决定使用拖拽技能还是点击技能
    use_drag = random.random() < TOP_DRAG_PROBABILITY and len(available_drags) > 0
    
    if use_drag:
        # 使用拖拽技能
        drag_direction = random.choice(available_drags)
        direction_names = ["向上", "向下", "向左", "向右"]
        direction_index = DRAG_DIRECTIONS.index(drag_direction)
        direction_name = direction_names[direction_index]
        
        print(f"🔥 TOP ATTACK: 执行拖拽技能 - {direction_name} (概率: {TOP_DRAG_PROBABILITY*100:.1f}%)")
        human_drag(DRAG_SKILL_START[0], DRAG_SKILL_START[1], 
                  drag_direction[0], drag_direction[1], 
                  0.3, f"拖拽技能{direction_name}")
        print(f"🔥 TOP ATTACK: 拖拽技能完成 - {direction_name}")
    else:
        # 使用点击技能
        if len(available_skills) > 0:
            skill_coord = random.choice(available_skills)
            skill_index = SKILL_COORDS.index(skill_coord) + 1  # 技能编号从1开始
            human_click(skill_coord[0], skill_coord[1], f"技能{skill_index}")
            print(f"🔥 TOP ATTACK: 点击技能{skill_index}完成 - 坐标{skill_coord}")
        else:
            print("🔥 TOP ATTACK: 警告 - 没有启用的点击技能！")
    
    # 短暂延迟
    time.sleep(random.uniform(0.5, 1.0))

# CATCARD MODE 功能
def enter_level():
    """阶段1：进入关卡"""
    if not is_running or should_stop or current_mode != "catcard":
        return False
    
    print("\n🐱 CATCARD: === 阶段1：进入关卡 ===")
    
    # 向右拖拽摇杆
    print("  向右拖拽摇杆...")
    right_end_x = JOYSTICK_START[0] + JOYSTICK_DRAG_DISTANCE
    right_end_y = JOYSTICK_START[1]
    human_drag(JOYSTICK_START[0], JOYSTICK_START[1], right_end_x, right_end_y, 
              JOYSTICK_HOLD_DURATION, "向右拖拽")
    
    # 地图选择序列
    for i, (x, y) in enumerate(MAP_SELECT_COORDS):
        if should_stop or not is_running:
            return False
        print(f"  地图选择步骤 {i+1}/3")
        human_click(x, y, f"地图选择{i+1}")
        time.sleep(random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX))
    
    print("🐱 CATCARD: ✓ 进入关卡完成")
    return True

def clear_level():
    """阶段2：清理关卡"""
    if not is_running or should_stop or current_mode != "catcard":
        return False
    
    print("\n🐱 CATCARD: === 阶段2：清理关卡 ===")
    
    print("开始攻击，同时监控关卡完成状态...")
    
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
    
    while time.time() - start_time < MAX_ATTACK_DURATION and not should_stop and is_running:
        if current_mode != "catcard":
            break
            
        attack_count += 1
        print(f"  第 {attack_count} 次攻击（持续 {ATTACK_HOLD_DURATION} 秒）...")
        
        # 开始攻击
        pyautogui.mouseDown()
        
        # 持续攻击，同时检查关卡是否完成
        hold_start_time = time.time()
        level_completed = False
        
        while time.time() - hold_start_time < ATTACK_HOLD_DURATION and not should_stop and is_running:
            if current_mode != "catcard":
                break
                
            # 每0.1秒检查一次关卡状态
            current_color = get_pixel_color(LEVEL_CLEAR_CHECK_COORD[0], LEVEL_CLEAR_CHECK_COORD[1])
            
            if current_color and is_colorful(current_color):
                level_completed = True
                print(f"    ✓ 检测到彩色，关卡完成！")
                break
            time.sleep(0.1)
        
        # 释放攻击
        pyautogui.mouseUp()
        
        # 如果关卡完成，执行额外的攻击
        if level_completed:
            print(f"  关卡已完成，执行最后一次攻击（{FINAL_ATTACK_DURATION} 秒）...")
            time.sleep(random.uniform(0.1, 0.3))  # 短暂间隔
            pyautogui.mouseDown()
            time.sleep(FINAL_ATTACK_DURATION)
            pyautogui.mouseUp()
            
            # 攻击完成后暂停2秒
            print("  攻击完成，暂停2秒后返回城镇...")
            time.sleep(2.0)
            
            print("🐱 CATCARD: ✓ 关卡清理完成！")
            return True
        
        # 如果关卡未完成，短暂休息后继续
        if not should_stop and is_running and current_mode == "catcard":
            rest_time = random.uniform(0.2, 0.5)
            time.sleep(rest_time)
    
    print("🐱 CATCARD: ✗ 关卡清理超时或被中断")
    return False

def return_to_town():
    """阶段3：返回城镇"""
    if not is_running or should_stop or current_mode != "catcard":
        return
    
    print("\n🐱 CATCARD: === 阶段3：返回城镇 ===")
    
    for i, (x, y) in enumerate(RETURN_TO_TOWN_COORDS):
        if should_stop or not is_running or current_mode != "catcard":
            break
        print(f"  返回城镇步骤 {i+1}/3")
        human_click(x, y, f"返回城镇{i+1}")
        time.sleep(random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX))
    
    print("🐱 CATCARD: ✓ 返回城镇完成")

def post_loop_town_behavior():
    """每轮循环完成后在城镇的行为：等待3秒，然后左右拖拽"""
    if not is_running or should_stop or current_mode != "catcard":
        return
    
    print(f"\n🐱 CATCARD: === 城镇等待和移动 ===")
    print(f"等待 {POST_LOOP_WAIT_TIME} 秒...")
    
    # 等待3秒，可被中断
    for i in range(int(POST_LOOP_WAIT_TIME)):
        if should_stop or not is_running or current_mode != "catcard":
            return
        print(f"  等待中... {int(POST_LOOP_WAIT_TIME)-i} 秒")
        time.sleep(1)
    
    if should_stop or not is_running or current_mode != "catcard":
        return
    
    print("开始城镇移动...")
    
    # 向左拖拽0.5秒
    print("  向左移动 0.5 秒...")
    left_end_x = JOYSTICK_START[0] - JOYSTICK_DRAG_DISTANCE
    left_end_y = JOYSTICK_START[1]
    human_drag(JOYSTICK_START[0], JOYSTICK_START[1], left_end_x, left_end_y, 
              0.5, "向左拖拽")
    
    if should_stop or not is_running or current_mode != "catcard":
        return
    
    # 短暂停顿
    time.sleep(random.uniform(0.2, 0.4))
    
    # 向右拖拽1.5秒
    print("  向右移动 1.5 秒...")
    right_end_x = JOYSTICK_START[0] + JOYSTICK_DRAG_DISTANCE
    right_end_y = JOYSTICK_START[1]
    human_drag(JOYSTICK_START[0], JOYSTICK_START[1], right_end_x, right_end_y, 
              1.5, "向右拖拽")
    
    print("🐱 CATCARD: ✓ 城镇移动完成")

def execute_catcard_cycle():
    """执行完整的猫卡循环"""
    if not is_running or should_stop or current_mode != "catcard":
        return
    
    print(f"\n🐱 CATCARD: 开始新的循环...")
    
    # 阶段1：进入关卡
    if not enter_level():
        return
    
    # 等待5秒让关卡加载完成
    print("\n等待关卡加载完成...")
    for i in range(5):
        if should_stop or not is_running or current_mode != "catcard":
            return
        print(f"  等待中... {5-i} 秒")
        time.sleep(1)
    
    # 阶段2：清理关卡
    level_success = clear_level()
    if not level_success:
        print("关卡清理失败，跳过本轮循环")
        return
    
    # 阶段3：返回城镇
    return_to_town()
    
    # 每轮循环完成后在城镇的行为
    post_loop_town_behavior()
    
    print(f"🐱 CATCARD: 本轮循环完成")

# 设置信号处理器
signal.signal(signal.SIGINT, signal_handler)

# --- 2. 主程序 ---
print("🎮 jitan自动化脚本 v4.0 - 4种攻击模式")
print("=" * 60)
print(f"目标坐标1: ({CLICK_X}, {CLICK_Y})")
print(f"目标坐标2: ({CLICK_X2}, {CLICK_Y2})")
print(f"长按坐标: ({HOLD_X}, {HOLD_Y})")
print(f"最大循环次数: {MAX_CYCLES}")
print("=" * 60)

print("\n🎯 4种攻击模式:")
print("\n1️⃣  【左边缘】- JITAN模式 (原始模式)")
print("   🖱️  4次长按攻击 + 2次点击")
print("   ✅ 经典jitan流程")

print("\n2️⃣  【右边缘】- 暂停模式")
print("   🖱️  暂停所有操作")
print("   ✅ 可以用其他边缘切换到不同模式")

print("\n3️⃣  【顶部边缘】- TOP ATTACK模式")
print("   🖱️  3秒长按攻击 + 随机技能")
print("   ✅ 无限循环，适合练级")

print("\n4️⃣  【底部边缘】- CATCARD模式") 
print("   🖱️  智能关卡清理")
print("   ✅ 自动进入关卡 → 清理 → 返回城镇")

print("\n" + "=" * 60)
print("💡 使用方法: 将鼠标移动到屏幕边缘停留1秒选择模式！")
print("💡 左=经典 | 右=暂停 | 上=连击 | 下=智能")
print("=" * 60)

# 启动鼠标监控
if MOUSE_CONTROL_ENABLED:
    start_mouse_monitor()
    print("\n🖱️  4边缘控制已激活")

# 启动文件监控
def start_file_monitor():
    """启动文件监控线程"""
    def file_monitor():
        while not should_stop:
            try:
                import os
                if os.path.exists('start.txt'):
                    on_start_pressed()
                    print("📁 检测到 start.txt - 启动JITAN模式")
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
                
                if os.path.exists('top.txt'):
                    on_top_edge_pressed()
                    print("📁 检测到 top.txt - 启动TOP ATTACK模式")
                    try:
                        os.remove('top.txt')
                    except:
                        pass
                
                if os.path.exists('catcard.txt'):
                    on_bottom_edge_pressed()
                    print("📁 检测到 catcard.txt - 启动CATCARD模式")
                    try:
                        os.remove('catcard.txt')
                    except:
                        pass
                        
            except Exception as e:
                pass
            time.sleep(0.5)  # 每500ms检查一次文件
    
    monitor_thread = threading.Thread(target=file_monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread

start_file_monitor()
print("📁 文件控制已激活 (start.txt/stop.txt/top.txt/catcard.txt)")

# 等待用户启动
if not wait_for_start():
    sys.exit(0)

try:
    cycle_count = 0
    
    # 主循环 - 永远不会因为暂停而退出
    while not should_stop:
        # 如果脚本被暂停，等待恢复
        while not is_running and not should_stop:
            time.sleep(0.1)
        
        if should_stop:
            break
        
        # 根据当前模式执行不同的逻辑
        if current_mode == "jitan":
            # 检查是否还有循环次数
            if cycle_count >= MAX_CYCLES:
                print(f"\n🎯 JITAN模式已完成 {MAX_CYCLES} 轮循环！等待模式切换...")
                # 不退出，继续等待模式切换
                while not should_stop and current_mode == "jitan":
                    time.sleep(1)
                continue
                
            cycle_count += 1
            print(f"\n--- 第 {cycle_count} 轮JITAN循环 ---")

            # --- 动作组一：长按重复 ---
            for hold_count in range(HOLD_REPEATS):
                # 检查暂停状态和模式切换
                while not is_running and not should_stop:
                    time.sleep(0.1)
                
                if should_stop or current_mode != "jitan":
                    break
                
                print(f"正在执行第 {hold_count + 1} 次长按操作，持续 {HOLD_DURATION} 秒...")
                success = human_hold(HOLD_X, HOLD_Y, HOLD_DURATION)
                
                if not success or current_mode != "jitan":  # 如果被中断或模式切换
                    break
                
                print(f"  第 {hold_count + 1} 次长按完成。")
                
                # 长按之间的间隔（除了最后一次）
                if hold_count < HOLD_REPEATS - 1:
                    # 在延迟期间也检查暂停状态
                    delay_start = time.time()
                    target_delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
                    while time.time() - delay_start < target_delay and not should_stop:
                        if not is_running or current_mode != "jitan":
                            # 暂停期间等待
                            while (not is_running or current_mode != "jitan") and not should_stop:
                                time.sleep(0.1)
                            # 恢复后重新计算延迟时间
                            delay_start = time.time()
                        time.sleep(0.1)

            # 检查暂停状态和模式
            while not is_running and not should_stop:
                time.sleep(0.1)
            
            if should_stop or current_mode != "jitan":
                continue

            # 长按组完成后的延迟
            delay_start = time.time()
            target_delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
            while time.time() - delay_start < target_delay and not should_stop:
                if not is_running or current_mode != "jitan":
                    # 暂停期间等待
                    while (not is_running or current_mode != "jitan") and not should_stop:
                        time.sleep(0.1)
                    # 恢复后重新计算延迟时间
                    delay_start = time.time()
                time.sleep(0.1)

            # --- 新增：随机点击技能8-11 ---
            # 检查暂停状态
            while not is_running and not should_stop:
                time.sleep(0.1)
                
            if is_running and not should_stop and current_mode == "jitan":
                print("正在执行随机技能点击...")
                
                # 创建可用技能列表（只包含启用的技能）
                available_jitan_skills = []
                for i, enabled in enumerate(JITAN_SKILL_ENABLED):
                    if enabled:
                        available_jitan_skills.append(JITAN_SKILL_COORDS[i])
                
                if len(available_jitan_skills) > 0:
                    skill_coord = random.choice(available_jitan_skills)
                    skill_index = JITAN_SKILL_COORDS.index(skill_coord) + 8  # 技能编号从8开始
                    human_click(skill_coord[0], skill_coord[1], f"JITAN技能{skill_index}")
                    print(f"  JITAN技能{skill_index}点击完成 - 坐标{skill_coord}")
                else:
                    print("  JITAN: 警告 - 没有启用的技能！跳过技能点击")
                
                # 技能点击后的短暂延迟
                delay_start = time.time()
                target_delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
                while time.time() - delay_start < target_delay and not should_stop:
                    if not is_running or current_mode != "jitan":
                        # 暂停期间等待
                        while (not is_running or current_mode != "jitan") and not should_stop:
                            time.sleep(0.1)
                        # 恢复后重新计算延迟时间
                        delay_start = time.time()
                    time.sleep(0.1)

            # --- 动作组二：第一次点击 ---
            # 检查暂停状态
            while not is_running and not should_stop:
                time.sleep(0.1)
                
            if is_running and not should_stop and current_mode == "jitan":
                print("正在执行第一次单击操作...")
                human_click(CLICK_X, CLICK_Y, "第一次单击")
                print("  第一次单击完成。")
            
            # --- 动作组三：第二次点击 ---
            # 检查暂停状态
            while not is_running and not should_stop:
                time.sleep(0.1)
                
            if is_running and not should_stop and current_mode == "jitan":
                print("正在执行第二次单击操作...")
                human_click(CLICK_X2, CLICK_Y2, "第二次单击")
                print("  第二次单击完成。")

            # --- 等待下一次循环 ---
            if not should_stop and current_mode == "jitan":
                print(f"本轮JITAN循环结束，等待 {CYCLE_DELAY} 秒后开始下一轮...")
                sleep_start = time.time()
                while time.time() - sleep_start < CYCLE_DELAY and not should_stop:
                    if not is_running or current_mode != "jitan":
                        # 暂停期间等待
                        while (not is_running or current_mode != "jitan") and not should_stop:
                            time.sleep(0.1)
                        # 恢复后重新计算等待时间
                        sleep_start = time.time()
                    time.sleep(0.1)
                    
        elif current_mode == "top_attack":
            # TOP ATTACK模式：无限循环
            execute_top_attack_cycle()
            
        elif current_mode == "catcard":
            # CATCARD模式：智能关卡清理
            execute_catcard_cycle()
            
        elif current_mode == "pause":
            # 暂停模式：什么都不做，等待模式切换
            time.sleep(0.1)

    # 只有 Ctrl+C 才会到达这里
    print(f"\n🛑 脚本已完全停止（已完成 {cycle_count} 轮JITAN循环）")

except Exception as e:
    print(f"\n❌ 脚本运行出错: {e}")

finally:
    # 确保无论脚本如何退出，鼠标都会被松开
    pyautogui.mouseUp()
    print("\n👋 脚本已完全停止。")