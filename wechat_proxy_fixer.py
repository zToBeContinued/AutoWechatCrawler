#!/usr/bin/env python3
"""
微信代理问题修复工具
专门解决"代理服务器出现问题，或者地址有误"的错误
"""

import subprocess
import time
import winreg
import logging
import requests
import os
import sys
from pathlib import Path

class WeChatProxyFixer:
    """微信代理问题修复工具"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('wechat_proxy_fix.log', encoding='utf-8')
            ]
        )
    
    def diagnose_proxy_issues(self):
        """诊断代理相关问题"""
        print("🔍 开始诊断微信代理问题...")
        print("=" * 60)
        
        issues = []
        
        # 1. 检查系统代理状态
        proxy_config = self.get_system_proxy_config()
        print(f"📊 系统代理状态:")
        print(f"   启用: {proxy_config['enable']}")
        print(f"   服务器: {proxy_config['server']}")
        print(f"   绕过列表: {proxy_config.get('bypass', '无')}")
        
        if proxy_config['enable'] and not proxy_config['server']:
            issues.append("代理已启用但服务器地址为空")
        
        # 2. 检查代理服务器连通性
        if proxy_config['enable'] and proxy_config['server']:
            if not self.test_proxy_connectivity(proxy_config['server']):
                issues.append(f"代理服务器 {proxy_config['server']} 无法连接")
        
        # 3. 检查mitmproxy进程
        mitm_processes = self.find_mitmproxy_processes()
        print(f"🔄 mitmproxy进程: {len(mitm_processes)} 个")
        for proc in mitm_processes:
            print(f"   PID: {proc['pid']}, 命令: {proc['cmd']}")
        
        if proxy_config['enable'] and len(mitm_processes) == 0:
            issues.append("代理已启用但未找到mitmproxy进程")
        
        # 4. 检查端口占用
        if self.is_port_in_use(8080):
            print("🔌 端口8080已被占用")
        else:
            print("🔌 端口8080空闲")
            if proxy_config['enable'] and '8080' in proxy_config['server']:
                issues.append("代理指向8080端口但该端口未被占用")
        
        # 5. 检查证书问题
        cert_issues = self.check_certificate_issues()
        if cert_issues:
            issues.extend(cert_issues)
        
        # 输出诊断结果
        print("\n📋 诊断结果:")
        if issues:
            print("❌ 发现以下问题:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("✅ 未发现明显问题")
        
        return issues
    
    def get_system_proxy_config(self):
        """获取系统代理配置"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_READ
            )
            
            config = {}
            
            try:
                proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                config['enable'] = proxy_enable == 1
            except WindowsError:
                config['enable'] = False
            
            try:
                proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                config['server'] = proxy_server
            except WindowsError:
                config['server'] = ""
            
            try:
                proxy_override, _ = winreg.QueryValueEx(key, "ProxyOverride")
                config['bypass'] = proxy_override
            except WindowsError:
                config['bypass'] = ""
            
            winreg.CloseKey(key)
            return config
            
        except Exception as e:
            self.logger.error(f"获取代理配置失败: {e}")
            return {'enable': False, 'server': '', 'bypass': ''}
    
    def test_proxy_connectivity(self, proxy_server):
        """测试代理服务器连通性"""
        try:
            proxies = {
                'http': f'http://{proxy_server}',
                'https': f'http://{proxy_server}'
            }
            
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def find_mitmproxy_processes(self):
        """查找mitmproxy相关进程"""
        try:
            result = subprocess.run(
                ['tasklist', '/fo', 'csv'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            processes = []
            for line in result.stdout.split('\n')[1:]:  # 跳过标题行
                if 'mitmdump' in line.lower() or 'mitmproxy' in line.lower():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        processes.append({
                            'name': parts[0].strip('"'),
                            'pid': parts[1].strip('"'),
                            'cmd': line
                        })
            
            return processes
            
        except Exception as e:
            self.logger.error(f"查找mitmproxy进程失败: {e}")
            return []
    
    def is_port_in_use(self, port):
        """检查端口是否被占用"""
        try:
            result = subprocess.run(
                ['netstat', '-an'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return f":{port}" in result.stdout
            
        except Exception:
            return False
    
    def check_certificate_issues(self):
        """检查证书相关问题"""
        issues = []
        
        # 检查mitmproxy证书是否存在
        cert_paths = [
            os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.crt"),
            os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.pem")
        ]
        
        cert_found = False
        for path in cert_paths:
            if os.path.exists(path):
                cert_found = True
                print(f"📜 找到证书文件: {path}")
                break
        
        if not cert_found:
            issues.append("未找到mitmproxy证书文件")
        
        return issues
    
    def fix_common_issues(self):
        """修复常见问题"""
        print("\n🔧 开始修复常见问题...")
        print("=" * 60)
        
        # 1. 清理残留的代理设置
        print("1️⃣ 清理残留的代理设置...")
        self.clean_proxy_settings()
        
        # 2. 终止残留的mitmproxy进程
        print("2️⃣ 终止残留的mitmproxy进程...")
        self.kill_mitmproxy_processes()
        
        # 3. 重置网络配置
        print("3️⃣ 重置网络配置...")
        self.reset_network_config()
        
        # 4. 测试网络连接
        print("4️⃣ 测试网络连接...")
        if self.test_network_connectivity():
            print("✅ 网络连接正常")
        else:
            print("❌ 网络连接异常")
        
        print("\n✅ 常见问题修复完成")
    
    def clean_proxy_settings(self):
        """清理代理设置"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_SET_VALUE
            )
            
            # 禁用代理
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            
            # 清空代理服务器
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
            
            # 清空代理绕过列表
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "")
            
            winreg.CloseKey(key)
            
            print("   ✅ 代理设置已清理")
            
        except Exception as e:
            print(f"   ❌ 清理代理设置失败: {e}")
    
    def kill_mitmproxy_processes(self):
        """终止mitmproxy进程"""
        try:
            processes = self.find_mitmproxy_processes()
            
            if not processes:
                print("   ℹ️ 未发现mitmproxy进程")
                return
            
            for proc in processes:
                try:
                    subprocess.run(
                        ['taskkill', '/f', '/pid', proc['pid']],
                        capture_output=True,
                        timeout=5
                    )
                    print(f"   ✅ 已终止进程 PID: {proc['pid']}")
                except Exception as e:
                    print(f"   ❌ 终止进程失败 PID: {proc['pid']}, 错误: {e}")
            
            time.sleep(2)  # 等待进程完全终止
            
        except Exception as e:
            print(f"   ❌ 终止mitmproxy进程失败: {e}")
    
    def reset_network_config(self):
        """重置网络配置"""
        try:
            # 刷新DNS
            subprocess.run(['ipconfig', '/flushdns'], capture_output=True, timeout=10)
            print("   ✅ DNS缓存已刷新")
            
            # 重置Winsock
            subprocess.run(['netsh', 'winsock', 'reset'], capture_output=True, timeout=10)
            print("   ✅ Winsock已重置")
            
        except Exception as e:
            print(f"   ❌ 重置网络配置失败: {e}")
    
    def test_network_connectivity(self):
        """测试网络连接"""
        test_urls = [
            "https://www.baidu.com",
            "https://mp.weixin.qq.com"
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ {url} 连接成功")
                    return True
            except Exception:
                print(f"   ❌ {url} 连接失败")
        
        return False
    
    def provide_manual_solutions(self):
        """提供手动解决方案"""
        print("\n💡 手动解决方案:")
        print("=" * 60)
        print("如果自动修复无效，请尝试以下手动操作：")
        print()
        print("1. 重启微信客户端:")
        print("   - 完全退出微信")
        print("   - 等待10秒后重新启动")
        print()
        print("2. 清除微信缓存:")
        print("   - 微信设置 -> 通用 -> 存储空间 -> 清理缓存")
        print()
        print("3. 检查Internet选项:")
        print("   - 控制面板 -> Internet选项 -> 连接 -> 局域网设置")
        print("   - 确保'为LAN使用代理服务器'未勾选")
        print()
        print("4. 重启网络适配器:")
        print("   - 设备管理器 -> 网络适配器")
        print("   - 禁用后重新启用网络适配器")
        print()
        print("5. 以管理员权限运行:")
        print("   - 右键点击程序 -> 以管理员身份运行")


def main():
    """主函数"""
    print("🔧 微信代理问题修复工具")
    print("=" * 60)
    
    fixer = WeChatProxyFixer()
    
    # 诊断问题
    issues = fixer.diagnose_proxy_issues()
    
    if issues:
        print(f"\n发现 {len(issues)} 个问题，开始自动修复...")
        fixer.fix_common_issues()
        
        # 重新诊断
        print("\n🔍 重新诊断...")
        remaining_issues = fixer.diagnose_proxy_issues()
        
        if remaining_issues:
            print(f"\n仍有 {len(remaining_issues)} 个问题未解决")
            fixer.provide_manual_solutions()
        else:
            print("\n🎉 所有问题已修复！")
    else:
        print("\n✅ 未发现问题，系统状态正常")
    
    print("\n" + "=" * 60)
    print("修复完成！请重新尝试运行微信爬虫程序。")


if __name__ == '__main__':
    main()
