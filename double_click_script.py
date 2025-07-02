#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Human-like Double Click Script
Performs 500 double clicks at specified coordinates with human-like variations
"""

import pyautogui
import time
import random
import signal
import sys

# 禁用PyAutoGUI的fail-safe功能
pyautogui.FAILSAFE = False

# --- 配置参数 ---
TARGET_X, TARGET_Y = 1721, 374     # 目标坐标
TOTAL_CLICKS = 500                 # 总点击次数
COORD_VARIATION = 2                # 坐标随机偏移范围（像素）
MIN_CLICK_INTERVAL = 0.1           # 两次双击之间的最小间隔（秒）
MAX_CLICK_INTERVAL = 0.4           # 两次双击之间的最大间隔（秒）
MIN_DOUBLE_CLICK_DELAY = 0.05      # 双击内部延迟最小值（秒）
MAX_DOUBLE_CLICK_DELAY = 0.15      # 双击内部延迟最大值（秒）

# 全局控制变量
should_stop = False

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    global should_stop
    print("\n检测到 Ctrl+C，正在安全退出...")
    should_stop = True

def add_human_variation(x, y, variation=COORD_VARIATION):
    """为坐标添加随机偏移，模拟人类点击的不精确性"""
    new_x = x + random.randint(-variation, variation)
    new_y = y + random.randint(-variation, variation)
    return new_x, new_y

def human_double_click(x, y, click_number):
    """执行人性化的双击操作"""
    if should_stop:
        return False
    
    # 添加坐标变化
    click_x, click_y = add_human_variation(x, y)
    
    # 随机移动速度
    move_duration = random.uniform(0.1, 0.3)
    
    print(f"双击 #{click_number:3d}: 移动到 ({click_x}, {click_y})")
    
    # 移动到目标位置
    pyautogui.moveTo(click_x, click_y, duration=move_duration)
    
    # 添加短暂停顿，模拟人类反应时间
    time.sleep(random.uniform(0.05, 0.15))
    
    if should_stop:
        return False
    
    # 执行第一次点击
    pyautogui.click()
    
    # 双击之间的延迟
    double_click_delay = random.uniform(MIN_DOUBLE_CLICK_DELAY, MAX_DOUBLE_CLICK_DELAY)
    time.sleep(double_click_delay)
    
    if should_stop:
        return False
    
    # 执行第二次点击
    pyautogui.click()
    
    print(f"双击 #{click_number:3d}: 完成 (延迟: {double_click_delay:.3f}s)")
    
    return True

def main():
    """主函数"""
    print("🖱️  Human-like Double Click Script")
    print("=" * 50)
    print(f"目标坐标: ({TARGET_X}, {TARGET_Y})")
    print(f"总点击次数: {TOTAL_CLICKS}")
    print(f"坐标变化范围: ±{COORD_VARIATION} 像素")
    print(f"点击间隔: {MIN_CLICK_INTERVAL}-{MAX_CLICK_INTERVAL} 秒")
    print("=" * 50)
    print("\n按 Ctrl+C 可随时停止脚本")
    
    # 3秒倒计时
    print("\n开始倒计时:")
    for i in range(3, 0, -1):
        if should_stop:
            return
        print(f"  {i} 秒后开始...")
        time.sleep(1)
    
    if should_stop:
        return
    
    print("\n🚀 开始执行双击操作!")
    print("-" * 30)
    
    successful_clicks = 0
    start_time = time.time()
    
    try:
        for click_num in range(1, TOTAL_CLICKS + 1):
            if should_stop:
                break
            
            # 执行双击
            success = human_double_click(TARGET_X, TARGET_Y, click_num)
            
            if success:
                successful_clicks += 1
            else:
                break
            
            # 进度显示
            if click_num % 50 == 0:
                elapsed_time = time.time() - start_time
                avg_time_per_click = elapsed_time / click_num
                remaining_clicks = TOTAL_CLICKS - click_num
                estimated_remaining_time = avg_time_per_click * remaining_clicks
                
                print(f"\n📊 进度报告:")
                print(f"   已完成: {click_num}/{TOTAL_CLICKS} ({click_num/TOTAL_CLICKS*100:.1f}%)")
                print(f"   已用时: {elapsed_time:.1f} 秒")
                print(f"   预计剩余: {estimated_remaining_time:.1f} 秒")
                print("-" * 30)
            
            # 检查是否需要停止
            if should_stop:
                break
            
            # 双击之间的随机间隔
            if click_num < TOTAL_CLICKS:
                interval = random.uniform(MIN_CLICK_INTERVAL, MAX_CLICK_INTERVAL)
                
                # 分割睡眠时间以便及时响应停止信号
                sleep_chunks = max(1, int(interval / 0.1))
                chunk_time = interval / sleep_chunks
                
                for _ in range(sleep_chunks):
                    if should_stop:
                        break
                    time.sleep(chunk_time)
    
    except Exception as e:
        print(f"\n❌ 执行过程中出现错误: {e}")
    
    finally:
        # 最终统计
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n🏁 脚本执行完成!")
        print("=" * 50)
        print(f"成功双击次数: {successful_clicks}/{TOTAL_CLICKS}")
        print(f"成功率: {successful_clicks/TOTAL_CLICKS*100:.1f}%")
        print(f"总用时: {total_time:.2f} 秒")
        if successful_clicks > 0:
            print(f"平均每次双击用时: {total_time/successful_clicks:.3f} 秒")
        
        if should_stop:
            print("\n⚠️  脚本被用户中断")
        elif successful_clicks == TOTAL_CLICKS:
            print("\n🎉 所有双击操作成功完成!")
        else:
            print(f"\n⚠️  提前结束，剩余 {TOTAL_CLICKS - successful_clicks} 次双击未完成")

if __name__ == "__main__":
    # 检查依赖
    try:
        import pyautogui
    except ImportError:
        print("❌ 缺少 pyautogui 库")
        print("请安装: pip install pyautogui")
        sys.exit(1)
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    # 运行主程序
    main()
    
    print("\n👋 脚本已退出") 