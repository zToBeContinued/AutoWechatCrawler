#!/usr/bin/env python3
"""
微信浏览器代理配置工具
专门解决微信内置浏览器的代理访问问题
"""

import subprocess
import time
import winreg
import logging
import requests
import os
import json
from pathlib import Path

class WeChatBrowserProxyConfig:
    """微信浏览器代理配置器"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.proxy_port = 8080
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def configure_wechat_browser_proxy(self):
        """配置微信浏览器专用代理设置"""
        print("🔧 配置微信浏览器专用代理设置...")
        print("=" * 60)
        
        try:
            # 1. 设置更宽松的代理绕过规则
            self.setup_wechat_proxy_bypass()
            
            # 2. 配置系统代理
            self.setup_system_proxy()
            
            # 3. 安装并信任mitmproxy证书
            self.install_mitmproxy_certificate()
            
            # 4. 配置mitmproxy启动参数
            self.create_mitmproxy_config()
            
            # 5. 测试配置
            self.test_wechat_proxy_config()
            
            print("✅ 微信浏览器代理配置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"配置失败: {e}")
            return False
    
    def setup_wechat_proxy_bypass(self):
        """设置微信专用的代理绕过规则"""
        try:
            # 微信可能需要直连的域名
            bypass_domains = [
                "localhost",
                "127.0.0.1",
                "*.local",
                "10.*",
                "172.16.*",
                "172.17.*",
                "172.18.*",
                "172.19.*",
                "172.20.*",
                "172.21.*",
                "172.22.*",
                "172.23.*",
                "172.24.*",
                "172.25.*",
                "172.26.*",
                "172.27.*",
                "172.28.*",
                "172.29.*",
                "172.30.*",
                "172.31.*",
                "192.168.*",
                "<local>",
                # 微信相关域名（某些情况下可能需要直连）
                "*.qq.com",
                "*.gtimg.cn",
                "*.qpic.cn",
                # Windows系统域名
                "*.microsoft.com",
                "*.windows.com",
                "*.msftconnecttest.com",
                "*.windowsupdate.com"
            ]
            
            bypass_string = ";".join(bypass_domains)
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, bypass_string)
            winreg.CloseKey(key)
            
            print("✅ 代理绕过规则已设置")
            self.logger.info(f"代理绕过规则: {bypass_string}")
            
        except Exception as e:
            self.logger.error(f"设置代理绕过规则失败: {e}")
            raise
    
    def setup_system_proxy(self):
        """设置系统代理"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_SET_VALUE
            )
            
            # 设置代理服务器
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"127.0.0.1:{self.proxy_port}")
            
            # 启用代理
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            
            winreg.CloseKey(key)
            
            print(f"✅ 系统代理已设置: 127.0.0.1:{self.proxy_port}")
            
        except Exception as e:
            self.logger.error(f"设置系统代理失败: {e}")
            raise
    
    def install_mitmproxy_certificate(self):
        """安装mitmproxy证书到系统信任存储"""
        try:
            # 查找证书文件
            cert_paths = [
                os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.crt"),
                os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.pem")
            ]
            
            cert_path = None
            for path in cert_paths:
                if os.path.exists(path):
                    cert_path = path
                    break
            
            if not cert_path:
                print("⚠️ 未找到mitmproxy证书，尝试生成...")
                self.generate_mitmproxy_certificate()
                
                # 再次查找
                for path in cert_paths:
                    if os.path.exists(path):
                        cert_path = path
                        break
            
            if cert_path:
                print(f"📜 找到证书: {cert_path}")
                
                # 尝试安装证书
                try:
                    result = subprocess.run([
                        'certutil', '-addstore', '-user', 'Root', cert_path
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        print("✅ 证书已安装到系统信任存储")
                    else:
                        print(f"⚠️ 证书安装可能失败: {result.stderr}")
                        
                except Exception as e:
                    print(f"⚠️ 证书安装失败: {e}")
            else:
                print("❌ 无法找到或生成mitmproxy证书")
                
        except Exception as e:
            self.logger.error(f"安装证书失败: {e}")
    
    def generate_mitmproxy_certificate(self):
        """生成mitmproxy证书"""
        try:
            print("正在生成mitmproxy证书...")
            
            # 启动mitmdump生成证书
            process = subprocess.Popen([
                'mitmdump', '--listen-port', '8081'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待证书生成
            time.sleep(3)
            process.terminate()
            process.wait(timeout=5)
            
            print("证书生成完成")
            
        except Exception as e:
            self.logger.warning(f"生成证书失败: {e}")
    
    def create_mitmproxy_config(self):
        """创建mitmproxy配置文件"""
        try:
            config_dir = os.path.expanduser("~/.mitmproxy")
            os.makedirs(config_dir, exist_ok=True)
            
            # 创建配置文件
            config = {
                "listen_port": self.proxy_port,
                "ssl_insecure": True,
                "upstream_cert": False,
                "anticache": True,
                "anticomp": True,
                "confdir": config_dir
            }
            
            config_file = os.path.join(config_dir, "config.yaml")
            
            # 写入YAML格式配置
            with open(config_file, 'w', encoding='utf-8') as f:
                for key, value in config.items():
                    if isinstance(value, bool):
                        f.write(f"{key}: {str(value).lower()}\n")
                    else:
                        f.write(f"{key}: {value}\n")
            
            print(f"✅ mitmproxy配置文件已创建: {config_file}")
            
        except Exception as e:
            self.logger.error(f"创建mitmproxy配置失败: {e}")
    
    def test_wechat_proxy_config(self):
        """测试微信代理配置"""
        try:
            print("🧪 测试代理配置...")
            
            # 测试代理连接
            proxies = {
                'http': f'http://127.0.0.1:{self.proxy_port}',
                'https': f'http://127.0.0.1:{self.proxy_port}'
            }
            
            test_urls = [
                "http://httpbin.org/ip",
                "https://httpbin.org/ip"
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(
                        url, 
                        proxies=proxies, 
                        timeout=10,
                        verify=False
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ {url} 代理测试成功")
                        return True
                    else:
                        print(f"⚠️ {url} 返回状态码: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ {url} 代理测试失败: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"测试代理配置失败: {e}")
            return False
    
    def start_optimized_mitmproxy(self):
        """启动优化的mitmproxy"""
        try:
            print("🚀 启动优化的mitmproxy...")
            
            cmd = [
                'mitmdump',
                '-s', 'cookie_extractor.py',
                '--listen-port', str(self.proxy_port),
                '--ssl-insecure',
                '--set', 'upstream_cert=false',
                '--set', 'ssl_insecure=true',
                '--anticache',
                '--anticomp',
                '--set', f'confdir={os.path.expanduser("~/.mitmproxy")}',
                # 添加更多兼容性选项
                '--set', 'http2=false',  # 禁用HTTP/2，提高兼容性
                '--set', 'websocket=false',  # 禁用WebSocket代理
                '--set', 'rawtcp=false'  # 禁用原始TCP代理
            ]
            
            print(f"启动命令: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return process
            
        except Exception as e:
            self.logger.error(f"启动mitmproxy失败: {e}")
            raise
    
    def cleanup_proxy_config(self):
        """清理代理配置"""
        try:
            print("🧹 清理代理配置...")
            
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
            
            print("✅ 代理配置已清理")
            
        except Exception as e:
            self.logger.error(f"清理代理配置失败: {e}")
    
    def provide_troubleshooting_tips(self):
        """提供故障排除建议"""
        print("\n💡 微信浏览器代理故障排除建议:")
        print("=" * 60)
        print("如果仍然遇到'代理服务器出现问题'错误，请尝试：")
        print()
        print("1. 重启微信客户端:")
        print("   - 完全退出微信（包括系统托盘）")
        print("   - 等待10秒后重新启动微信")
        print()
        print("2. 清除微信缓存:")
        print("   - 微信设置 -> 通用 -> 存储空间 -> 清理缓存")
        print("   - 重启微信")
        print()
        print("3. 检查防火墙设置:")
        print("   - 确保防火墙允许mitmdump.exe通过")
        print("   - 临时关闭防火墙测试")
        print()
        print("4. 尝试不同的端口:")
        print("   - 修改代理端口为8081或8082")
        print("   - 重新启动mitmproxy")
        print()
        print("5. 手动信任证书:")
        print("   - 打开 certmgr.msc")
        print("   - 导入mitmproxy证书到'受信任的根证书颁发机构'")


def main():
    """主函数"""
    print("🔧 微信浏览器代理配置工具")
    print("=" * 60)
    
    config = WeChatBrowserProxyConfig()
    
    try:
        # 配置微信浏览器代理
        if config.configure_wechat_browser_proxy():
            print("\n🎉 配置成功！")
            print("现在可以尝试运行微信爬虫程序。")
            
            # 询问是否启动优化的mitmproxy
            print("\n是否启动优化的mitmproxy？(y/n): ", end="")
            choice = input().lower().strip()
            
            if choice == 'y':
                try:
                    process = config.start_optimized_mitmproxy()
                    print("✅ mitmproxy已启动")
                    print("按Ctrl+C停止...")
                    
                    # 等待用户中断
                    process.wait()
                    
                except KeyboardInterrupt:
                    print("\n正在停止mitmproxy...")
                    process.terminate()
                    process.wait(timeout=5)
                    
                finally:
                    config.cleanup_proxy_config()
            
        else:
            print("\n❌ 配置失败")
            config.provide_troubleshooting_tips()
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
        config.cleanup_proxy_config()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        config.cleanup_proxy_config()


if __name__ == '__main__':
    main()
