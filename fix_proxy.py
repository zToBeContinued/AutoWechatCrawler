#!/usr/bin/env python3
"""
代理修复工具 - 手动清理系统代理设置
解决网络连接异常问题：HTTPSConnectionPool proxy error
"""

import winreg
import requests
import time
import logging

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_current_proxy_settings():
    """获取当前代理设置"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                           0, winreg.KEY_READ)
        try:
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
        except WindowsError:
            proxy_enable = 0
        try:
            proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
        except WindowsError:
            proxy_server = ""
        winreg.CloseKey(key)
        return {
            'enable': proxy_enable == 1,
            'server': proxy_server
        }
    except Exception as e:
        print(f"获取代理设置失败: {e}")
        return {'enable': False, 'server': ""}

def disable_system_proxy():
    """强制禁用系统代理"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                           0, winreg.KEY_WRITE)
        
        # 禁用代理
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        # 清空代理服务器设置
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, '')
        winreg.CloseKey(key)
        
        print("✅ 系统代理已禁用")
        return True
        
    except Exception as e:
        print(f"❌ 禁用代理失败: {e}")
        return False

def test_network_connection():
    """测试网络连接"""
    test_urls = [
        'https://www.baidu.com',
        'https://httpbin.org/ip',
        'https://www.google.com'
    ]
    
    for url in test_urls:
        try:
            print(f"测试连接: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {url} 连接成功")
                return True
        except Exception as e:
            print(f"❌ {url} 连接失败: {e}")
    
    return False

def kill_proxy_processes():
    """结束可能的代理进程"""
    import subprocess
    import psutil
    
    proxy_processes = ['mitmdump', 'mitmproxy', 'mitmweb']
    killed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() in proxy_processes:
                print(f"发现代理进程: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.kill()
                killed_count += 1
                print(f"✅ 已结束进程: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed_count > 0:
        print(f"✅ 共结束了 {killed_count} 个代理进程")
        time.sleep(2)  # 等待进程完全结束
    else:
        print("ℹ️ 未发现运行中的代理进程")

def main():
    """主修复流程"""
    logger = setup_logging()
    
    print("🔧 代理修复工具启动")
    print("=" * 50)
    
    # 1. 检查当前代理状态
    print("\n📊 检查当前代理状态...")
    current_settings = get_current_proxy_settings()
    print(f"代理启用: {current_settings['enable']}")
    print(f"代理服务器: {current_settings['server']}")
    
    # 2. 结束代理进程
    print("\n🔄 结束代理进程...")
    kill_proxy_processes()
    
    # 3. 禁用系统代理
    print("\n🚫 禁用系统代理...")
    if disable_system_proxy():
        print("✅ 代理禁用成功")
    else:
        print("❌ 代理禁用失败")
        return False
    
    # 4. 等待设置生效
    print("\n⏳ 等待设置生效...")
    time.sleep(3)
    
    # 5. 验证代理状态
    print("\n🔍 验证代理状态...")
    new_settings = get_current_proxy_settings()
    print(f"代理启用: {new_settings['enable']}")
    print(f"代理服务器: {new_settings['server']}")
    
    if not new_settings['enable']:
        print("✅ 代理已成功禁用")
    else:
        print("❌ 代理仍然启用，可能需要手动设置")
        return False
    
    # 6. 测试网络连接
    print("\n🌐 测试网络连接...")
    if test_network_connection():
        print("✅ 网络连接正常")
        return True
    else:
        print("❌ 网络连接仍有问题")
        return False

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n🎉 代理修复完成！现在可以正常运行爬虫程序了。")
        else:
            print("\n❌ 代理修复失败，请手动检查网络设置。")
            print("\n💡 手动修复步骤：")
            print("1. 打开 Internet 选项 -> 连接 -> 局域网设置")
            print("2. 取消勾选 '为LAN使用代理服务器'")
            print("3. 点击确定保存设置")
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 修复过程出错: {e}")
