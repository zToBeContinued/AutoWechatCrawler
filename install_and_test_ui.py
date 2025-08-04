# coding:utf-8
# install_and_test_ui.py
"""
安装和测试uiautomation库
"""

import subprocess
import sys
import os

def install_uiautomation():
    """安装uiautomation库"""
    print("🔧 正在安装uiautomation库...")
    
    try:
        # 使用pip安装uiautomation
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'uiautomation'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ uiautomation库安装成功")
            print(result.stdout)
            return True
        else:
            print("❌ uiautomation库安装失败")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 安装超时")
        return False
    except Exception as e:
        print(f"❌ 安装过程出错: {e}")
        return False

def test_uiautomation():
    """测试uiautomation库"""
    print("\n🧪 测试uiautomation库...")
    
    try:
        import uiautomation as auto
        print("✅ uiautomation库导入成功")
        
        # 测试基本功能
        print("📋 测试基本功能:")
        
        # 获取桌面
        desktop = auto.GetRootControl()
        print(f"   ✅ 获取桌面成功: {desktop}")
        
        # 获取当前鼠标位置
        cursor_pos = auto.GetCursorPos()
        print(f"   ✅ 获取鼠标位置: {cursor_pos}")
        
        # 测试查找窗口功能
        print("🔍 测试查找浏览器窗口:")
        
        # Chrome
        try:
            chrome_win = auto.WindowControl(searchDepth=1, ClassName='Chrome_WidgetWin_1')
            if chrome_win.Exists(1):
                print("   ✅ 找到Chrome浏览器")
            else:
                print("   ⚠️ 未找到Chrome浏览器")
        except Exception as e:
            print(f"   ❌ Chrome测试失败: {e}")
        
        # Edge
        try:
            edge_win = auto.WindowControl(searchDepth=1, ClassName='Chrome_WidgetWin_1', SubName='Edge')
            if edge_win.Exists(1):
                print("   ✅ 找到Edge浏览器")
            else:
                print("   ⚠️ 未找到Edge浏览器")
        except Exception as e:
            print(f"   ❌ Edge测试失败: {e}")
        
        # Firefox
        try:
            firefox_win = auto.WindowControl(searchDepth=1, ClassName='MozillaWindowClass')
            if firefox_win.Exists(1):
                print("   ✅ 找到Firefox浏览器")
            else:
                print("   ⚠️ 未找到Firefox浏览器")
        except Exception as e:
            print(f"   ❌ Firefox测试失败: {e}")
        
        print("\n✅ uiautomation库测试完成")
        return True
        
    except ImportError as e:
        print(f"❌ uiautomation库导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ uiautomation库测试失败: {e}")
        return False

def test_browser_automation():
    """测试浏览器自动化功能"""
    print("\n🌐 测试浏览器自动化功能...")
    
    try:
        import uiautomation as auto
        import webbrowser
        import time
        
        # 打开一个测试页面
        test_url = "https://www.baidu.com"
        print(f"🔗 打开测试页面: {test_url}")
        webbrowser.open(test_url)
        
        # 等待浏览器加载
        print("⏳ 等待5秒让浏览器加载...")
        time.sleep(5)
        
        # 尝试找到浏览器窗口
        browser_found = False
        browsers_to_try = [
            {'ClassName': 'Chrome_WidgetWin_1', 'Name': 'Chrome'},
            {'ClassName': 'Chrome_WidgetWin_1', 'Name': 'Edge'},
            {'ClassName': 'MozillaWindowClass', 'Name': 'Firefox'},
        ]
        
        for browser_config in browsers_to_try:
            try:
                window = auto.WindowControl(searchDepth=1, ClassName=browser_config['ClassName'])
                if window.Exists(2):
                    print(f"✅ 找到{browser_config['Name']}浏览器窗口")
                    
                    # 激活窗口
                    window.SetActive()
                    time.sleep(1)
                    
                    # 测试发送按键
                    print("🔄 测试发送F5刷新...")
                    auto.SendKeys('{F5}')
                    
                    print("✅ 浏览器自动化测试成功")
                    browser_found = True
                    break
                    
            except Exception as e:
                continue
        
        if not browser_found:
            print("⚠️ 未找到浏览器窗口，但这可能是正常的")
            print("💡 请确保有浏览器打开并重试")
        
        return True
        
    except Exception as e:
        print(f"❌ 浏览器自动化测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 uiautomation库安装和测试工具")
    print("="*50)
    
    # 检查是否已安装
    try:
        import uiautomation
        print("✅ uiautomation库已安装")
        skip_install = True
    except ImportError:
        print("⚠️ uiautomation库未安装")
        skip_install = False
    
    # 安装库
    if not skip_install:
        if not install_uiautomation():
            print("❌ 安装失败，无法继续测试")
            return
    
    # 测试库
    if test_uiautomation():
        print("\n🎉 uiautomation库可以正常使用")
        
        # 询问是否测试浏览器自动化
        choice = input("\n是否测试浏览器自动化功能？(y/N): ").strip().lower()
        if choice == 'y':
            test_browser_automation()
    else:
        print("\n❌ uiautomation库测试失败")
    
    print("\n" + "="*50)
    print("测试完成")

if __name__ == "__main__":
    main()
