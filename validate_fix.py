#!/usr/bin/env python3
"""
诊断和修复工具 - 解决代理问题后的验证
"""
import sys
import time
from proxy_manager import ProxyManager
from read_cookie import ReadCookie

def main():
    """运行诊断测试"""
    print("🔍 微信公众号爬虫代理问题修复工具")
    print("=" * 50)
    
    # 初始化代理管理器
    pm = ProxyManager()
    
    # 检查初始状态
    print("\n📊 当前系统状态检查:")
    initial_proxy_config = pm.get_system_proxy_config()
    print(f"   代理配置: {initial_proxy_config}")
    
    proxy_enabled = pm.is_system_proxy_enabled()
    proxy_working = pm.is_proxy_working() if proxy_enabled else False
    print(f"   代理状态: {'启用' if proxy_enabled else '禁用'}")
    print(f"   代理可用: {'是' if proxy_working else '否'}")
    
    network_ok = pm.validate_and_fix_network()
    print(f"   网络连接: {'正常' if network_ok else '异常'}")
    
    # 如果需要清理
    if proxy_enabled or not network_ok:
        print("\n🧹 发现代理问题，开始清理...")
        if pm.reset_network_state():
            print("✅ 网络重置完成")
        else:
            print("❌ 重置失败")
            return False
    
    # 运行测试抓取
    print("\n🔄 测试Cookie抓取功能...")
    cookie_reader = ReadCookie()
    
    print("✅ 代理问题诊断工具完成")
    print("\n🔧 建议：")
    print("   1. 运行: python main_enhanced.py --auto")
    print("   2. 如仍有问题，检查系统代理设置")
    print("   3. 确认 mitmproxy 已正确安装")

if __name__ == '__main__':
    main()