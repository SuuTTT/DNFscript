#!/usr/bin/env python3
# -*- coding:
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
import pytesseract
import os
import sys

def preprocess_image_for_ocr(image_path, method='basic'):
    """
    预处理图片以提高OCR识别率
    
    Args:
        image_path: 图片路径
        method: 预处理方法 ('basic', 'enhanced', 'contrast')
    
    Returns:
        处理后的图片
    """
    # 读取图片
    if isinstance(image_path, str):
        image = cv2.imread(image_path)
        if image is None:
            print(f"错误：无法读取图片 {image_path}")
            return None
    else:
        image = image_path
    
    if method == 'basic':
        # 基础处理：转灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray
    
    elif method == 'enhanced':
        # 增强处理：去噪、锐化、二值化
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 高斯模糊去噪
        denoised = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 自适应阈值二值化
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    elif method == 'contrast':
        # 对比度增强处理
        # 转换为PIL图片进行增强
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # 增强对比度
        enhancer = ImageEnhance.Contrast(pil_image)
        enhanced = enhancer.enhance(2.0)  # 增强对比度
        
        # 增强亮度
        enhancer = ImageEnhance.Brightness(enhanced)
        enhanced = enhancer.enhance(1.2)  # 稍微增加亮度
        
        # 转回OpenCV格式
        enhanced_cv = cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(enhanced_cv, cv2.COLOR_BGR2GRAY)
        
        return gray
    
    return image

def detect_chinese_text_ocr(image_path, target_text="疲劳值不足", save_debug=True):
    """
    使用OCR检测中文文字
    
    Args:
        image_path: 图片路径
        target_text: 目标文字
        save_debug: 是否保存调试图片
    
    Returns:
        dict: 检测结果
    """
    print(f"开始OCR检测图片: {image_path}")
    print(f"目标文字: {target_text}")
    
    results = {}
    
    # 尝试不同的预处理方法
    methods = ['basic', 'enhanced', 'contrast']
    
    for method in methods:
        print(f"\n--- 使用预处理方法: {method} ---")
        
        # 预处理图片
        processed_image = preprocess_image_for_ocr(image_path, method)
        if processed_image is None:
            continue
        
        # 保存调试图片
        if save_debug:
            debug_filename = f"debug_{method}_{os.path.basename(image_path)}"
            cv2.imwrite(debug_filename, processed_image)
            print(f"调试图片已保存: {debug_filename}")
        
        try:
            # 配置tesseract参数
            custom_config = r'--oem 3 --psm 6 -l chi_sim'
            
            # 进行OCR识别
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            print(f"识别到的文字: '{text.strip()}'")
            
            # 检查是否包含目标文字
            if target_text in text:
                print(f"✅ 成功检测到目标文字: {target_text}")
                results[method] = {
                    'success': True,
                    'text': text.strip(),
                    'method': method
                }
            else:
                print(f"❌ 未检测到目标文字")
                results[method] = {
                    'success': False,
                    'text': text.strip(),
                    'method': method
                }
        
        except Exception as e:
            print(f"OCR识别出错: {e}")
            results[method] = {
                'success': False,
                'error': str(e),
                'method': method
            }
    
    return results

def detect_chinese_text_template(image_path, target_text="疲劳值不足"):
    """
    使用模板匹配检测中文文字（需要预先准备模板图片）
    
    Args:
        image_path: 图片路径
        target_text: 目标文字
    
    Returns:
        dict: 检测结果
    """
    print(f"\n--- 模板匹配方法 ---")
    print("注意：此方法需要预先准备目标文字的模板图片")
    
    # 这里可以添加模板匹配的代码
    # 由于需要预先准备模板，暂时返回未实现状态
    return {
        'template': {
            'success': False,
            'message': '模板匹配需要预先准备目标文字模板图片',
            'method': 'template'
        }
    }

def analyze_image_properties(image_path):
    """
    分析图片属性
    """
    print(f"\n--- 图片属性分析 ---")
    
    image = cv2.imread(image_path)
    if image is None:
        print("无法读取图片")
        return
    
    height, width, channels = image.shape
    print(f"图片尺寸: {width} x {height}")
    print(f"颜色通道: {channels}")
    
    # 转换为灰度图分析亮度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    print(f"平均亮度: {mean_brightness:.1f}")
    
    # 分析对比度
    contrast = np.std(gray)
    print(f"对比度: {contrast:.1f}")

def main():
    """主函数"""
    print("中文文字识别工具")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # 默认图片路径
        image_path = "截屏2025-06-24 13.56.11.png"
    
    # 检查图片是否存在
    if not os.path.exists(image_path):
        print(f"错误：图片文件不存在 - {image_path}")
        print("请确保图片文件在当前目录中")
        return
    
    print(f"目标图片: {image_path}")
    
    # 分析图片属性
    analyze_image_properties(image_path)
    
    # 使用OCR检测
    target_text = "疲劳值不足"
    ocr_results = detect_chinese_text_ocr(image_path, target_text)
    
    # 使用模板匹配检测
    template_results = detect_chinese_text_template(image_path, target_text)
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("检测结果汇总")
    print(f"{'='*50}")
    
    all_results = {**ocr_results, **template_results}
    
    success_count = 0
    for method, result in all_results.items():
        if result.get('success', False):
            success_count += 1
            print(f"✅ {method}: 成功检测到 '{target_text}'")
        else:
            print(f"❌ {method}: 未检测到目标文字")
            if 'text' in result and result['text']:
                print(f"   识别到: '{result['text']}'")
    
    print(f"\n成功率: {success_count}/{len(all_results)} 种方法")
    
    if success_count > 0:
        print(f"\n🎉 检测成功！图片中包含文字: {target_text}")
    else:
        print(f"\n❌ 检测失败！未能在图片中找到文字: {target_text}")
        print("\n建议：")
        print("1. 检查图片清晰度")
        print("2. 确认文字颜色对比度")
        print("3. 尝试裁剪图片只保留文字区域")
        print("4. 检查tesseract中文语言包是否已安装")

if __name__ == "__main__":
    # 检查依赖
    try:
        import pytesseract
        import cv2
        from PIL import Image, ImageEnhance
    except ImportError as e:
        print(f"缺少必要的依赖库: {e}")
        print("请安装以下依赖:")
        print("pip install pytesseract opencv-python pillow")
        print("并确保已安装tesseract-ocr程序")
        sys.exit(1)
    
    main() 