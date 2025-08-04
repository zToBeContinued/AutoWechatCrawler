#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理代理设置
"""

import winreg
import subprocess

def cleanup_proxy():
    """清理系统代理设置"""
    try:
        # 打开注册表项
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                           0, winreg.KEY_SET_VALUE)
        
        # 禁用代理
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        
        # 清空代理服务器设置
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
        
        # 关闭注册表项
        winreg.CloseKey(key)
        
        print("✅ 系统代理已关闭")
        
    except Exception as e:
        print(f"❌ 关闭系统代理失败: {e}")

def kill_mitmproxy():
    """强制停止所有mitmproxy进程"""
    try:
        result = subprocess.run(['taskkill', '/f', '/im', 'mitmdump.exe'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ 已强制结束所有mitmdump.exe进程")
        else:
            print("ℹ️ 没有找到运行中的mitmdump.exe进程")
    except Exception as e:
        print(f"❌ 结束进程时出错: {e}")

def main():
    print("🧹 清理代理设置和mitmproxy进程")
    print("="*40)
    
    kill_mitmproxy()
    cleanup_proxy()
    
    print("\n✅ 清理完成")

if __name__ == "__main__":
    main()
