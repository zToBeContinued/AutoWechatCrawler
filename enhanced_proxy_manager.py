#!/usr/bin/env python3
"""
增强代理管理器 - 专门解决微信公众号访问的代理问题
包含SSL证书安装、代理绕过设置、微信特定配置等
"""

import subprocess
import time
import winreg
import logging
import requests
import os
import shutil
from pathlib import Path
from typing import Optional, List

class EnhancedProxyManager:
    """增强代理管理器，专门处理微信公众号访问问题"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.proxy_port = 8080
        self.original_proxy_settings = {}
        self.mitmproxy_cert_path = None
        
    def setup_wechat_proxy_config(self) -> bool:
        """设置专门针对微信的代理配置"""
        try:
            self.logger.info("🔧 开始设置微信专用代理配置...")
            
            # 1. 安装mitmproxy证书
            if not self.install_mitmproxy_certificate():
                self.logger.warning("⚠️ mitmproxy证书安装失败，可能影响HTTPS访问")
            
            # 2. 设置代理绕过列表
            self.setup_proxy_bypass()
            
            # 3. 配置系统代理
            self.setup_system_proxy_with_bypass()
            
            self.logger.info("✅ 微信专用代理配置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 设置微信代理配置失败: {e}")
            return False
    
    def install_mitmproxy_certificate(self) -> bool:
        """安装mitmproxy的SSL证书到系统信任存储"""
        try:
            # 查找mitmproxy证书文件
            possible_cert_paths = [
                os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.crt"),
                os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.pem"),
                "./mitmproxy-ca-cert.crt",
                "./mitmproxy-ca-cert.pem"
            ]
            
            cert_path = None
            for path in possible_cert_paths:
                if os.path.exists(path):
                    cert_path = path
                    break
            
            if not cert_path:
                self.logger.warning("未找到mitmproxy证书文件，尝试生成...")
                # 尝试启动mitmproxy生成证书
                self.generate_mitmproxy_certificate()
                
                # 再次查找
                for path in possible_cert_paths:
                    if os.path.exists(path):
                        cert_path = path
                        break
            
            if not cert_path:
                self.logger.error("无法找到或生成mitmproxy证书")
                return False
            
            self.mitmproxy_cert_path = cert_path
            self.logger.info(f"找到mitmproxy证书: {cert_path}")
            
            # 安装证书到Windows证书存储
            return self.install_certificate_to_windows_store(cert_path)
            
        except Exception as e:
            self.logger.error(f"安装mitmproxy证书失败: {e}")
            return False
    
    def generate_mitmproxy_certificate(self):
        """生成mitmproxy证书"""
        try:
            self.logger.info("正在生成mitmproxy证书...")
            # 启动mitmdump一小段时间来生成证书
            process = subprocess.Popen(
                ['mitmdump', '--listen-port', '8081'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 等待2秒让证书生成
            time.sleep(2)
            process.terminate()
            process.wait(timeout=5)
            
            self.logger.info("mitmproxy证书生成完成")
            
        except Exception as e:
            self.logger.warning(f"生成mitmproxy证书时出错: {e}")
    
    def install_certificate_to_windows_store(self, cert_path: str) -> bool:
        """将证书安装到Windows证书存储"""
        try:
            self.logger.info("正在安装证书到Windows证书存储...")
            
            # 使用certlm.msc或certutil命令安装证书
            cmd = [
                'certutil', '-addstore', '-user', 'Root', cert_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info("✅ 证书已成功安装到系统信任存储")
                return True
            else:
                self.logger.warning(f"证书安装可能失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"安装证书到Windows存储失败: {e}")
            return False
    
    def setup_proxy_bypass(self):
        """设置代理绕过列表，避免某些域名走代理"""
        try:
            # 设置不走代理的域名列表
            bypass_list = [
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
                # 添加一些可能导致问题的域名
                "*.microsoft.com",
                "*.windows.com",
                "*.msftconnecttest.com"
            ]
            
            bypass_string = ";".join(bypass_list)
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, bypass_string)
            winreg.CloseKey(key)
            
            self.logger.info("✅ 代理绕过列表已设置")
            
        except Exception as e:
            self.logger.error(f"设置代理绕过列表失败: {e}")
    
    def setup_system_proxy_with_bypass(self):
        """设置系统代理，包含绕过配置"""
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
            
            self.logger.info(f"✅ 系统代理已设置为 127.0.0.1:{self.proxy_port}")
            
        except Exception as e:
            self.logger.error(f"设置系统代理失败: {e}")
    
    def start_enhanced_mitmproxy(self) -> subprocess.Popen:
        """启动增强配置的mitmproxy"""
        try:
            # 构建mitmproxy启动命令，添加更多兼容性选项
            cmd = [
                'mitmdump',
                '-s', 'cookie_extractor.py',
                '--listen-port', str(self.proxy_port),
                '--ssl-insecure',  # 忽略上游SSL错误
                '--set', 'confdir=~/.mitmproxy',  # 指定配置目录
                '--set', 'ssl_insecure=true',  # 允许不安全的SSL连接
                '--set', 'upstream_cert=false',  # 不验证上游证书
                '--anticache',  # 禁用缓存，确保获取最新内容
                '--anticomp'   # 禁用压缩，便于内容分析
            ]
            
            self.logger.info(f"启动增强mitmproxy: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            return process
            
        except Exception as e:
            self.logger.error(f"启动增强mitmproxy失败: {e}")
            raise
    
    def test_wechat_connectivity(self) -> bool:
        """测试微信公众号连接性"""
        try:
            test_urls = [
                "https://mp.weixin.qq.com",
                "https://mp.weixin.qq.com/mp/profile_ext?action=home"
            ]
            
            proxies = {
                'http': f'http://127.0.0.1:{self.proxy_port}',
                'https': f'http://127.0.0.1:{self.proxy_port}'
            }
            
            for url in test_urls:
                try:
                    self.logger.info(f"测试连接: {url}")
                    response = requests.get(
                        url, 
                        proxies=proxies, 
                        timeout=10,
                        verify=False  # 忽略SSL验证
                    )
                    
                    if response.status_code == 200:
                        self.logger.info(f"✅ {url} 连接成功")
                        return True
                    else:
                        self.logger.warning(f"⚠️ {url} 返回状态码: {response.status_code}")
                        
                except Exception as e:
                    self.logger.warning(f"❌ {url} 连接失败: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"测试微信连接性失败: {e}")
            return False
    
    def cleanup_enhanced_proxy(self):
        """清理增强代理设置"""
        try:
            self.logger.info("🧹 开始清理增强代理设置...")
            
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
            
            self.logger.info("✅ 增强代理设置已清理")
            
        except Exception as e:
            self.logger.error(f"清理增强代理设置失败: {e}")



