#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查当前系统代理状态
"""

import winreg
import subprocess

def check_system_proxy():
    """检查系统代理设置"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                           0, winreg.KEY_READ)
        
        try:
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
        except:
            proxy_enable = 0
            
        try:
            proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
        except:
            proxy_server = ""
            
        winreg.CloseKey(key)
        
        print(f"系统代理状态: {'启用' if proxy_enable == 1 else '禁用'}")
        print(f"代理服务器: {proxy_server}")
        
        return proxy_enable == 1, proxy_server
        
    except Exception as e:
        print(f"检查代理状态失败: {e}")
        return False, ""

def check_mitmproxy_process():
    """检查mitmproxy进程"""
    try:
        result = subprocess.run(['tasklist', '/fi', 'imagename eq mitmdump.exe'], 
                              capture_output=True, text=True, timeout=5)
        if 'mitmdump.exe' in result.stdout:
            print("✅ 发现mitmproxy进程正在运行")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'mitmdump.exe' in line:
                    print(f"进程信息: {line.strip()}")
        else:
            print("❌ 没有发现mitmproxy进程")
    except Exception as e:
        print(f"检查进程失败: {e}")

def check_port_8080():
    """检查8080端口是否被占用"""
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        port_8080_found = False
        for line in lines:
            if ':8080' in line and 'LISTENING' in line:
                print(f"✅ 端口8080正在监听: {line.strip()}")
                port_8080_found = True
        
        if not port_8080_found:
            print("❌ 端口8080没有在监听")
            
    except Exception as e:
        print(f"检查端口失败: {e}")

def main():
    print("🔍 系统代理和mitmproxy状态检查")
    print("="*50)
    
    print("\n1. 系统代理设置:")
    check_system_proxy()
    
    print("\n2. mitmproxy进程状态:")
    check_mitmproxy_process()
    
    print("\n3. 端口8080监听状态:")
    check_port_8080()

if __name__ == "__main__":
    main()
