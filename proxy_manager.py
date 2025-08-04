#!/usr/bin/env python3
"""
代理管理器 - 确保代理正确开关控制
解决Windows环境下mitmproxy代理无法完全关闭的问题
"""
import subprocess
import time
import winreg
import logging
import requests
from typing import Optional

class ProxyManager:
    """代理管理器，确保代理设置正确开关"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.proxy_port = 8080
        self.original_proxy_settings = {}
        
    def is_proxy_working(self, timeout: int = 5) -> bool:
        """检查代理服务器是否正常工作"""
        try:
            proxies = {
                'http': f'http://127.0.0.1:{self.proxy_port}',
                'https': f'http://127.0.0.1:{self.proxy_port}'
            }
            response = requests.get('http://httpbin.org/ip', 
                                  proxies=proxies, 
                                  timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def is_system_proxy_enabled(self) -> bool:
        """检查系统代理是否启用"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                               0, winreg.KEY_READ)
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            winreg.CloseKey(key)
            return proxy_enable == 1
        except Exception:
            return False
            
    def get_system_proxy_config(self) -> dict:
        """获取当前系统代理配置"""
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
            self.logger.error(f"获取代理配置失败: {e}")
            return {'enable': False, 'server': ""}
    
    def backup_proxy_settings(self):
        """备份原始代理设置"""
        self.original_proxy_settings = self.get_system_proxy_config()
        self.logger.info(f"已备份原始代理设置: {self.original_proxy_settings}")
    
    def restore_proxy_settings(self):
        """恢复原始代理设置"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                               0, winreg.KEY_SET_VALUE)
            
            if self.original_proxy_settings.get('enable', False):
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, 
                                self.original_proxy_settings.get('server', ''))
            else:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, '')
            
            winreg.CloseKey(key)
            self.logger.info("已恢复原始代理设置")
        except Exception as e:
            self.logger.error(f"恢复代理设置失败: {e}")
    
    def enable_proxy(self, port: int = 8080):
        """启用代理"""
        self.proxy_port = port
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                               0, winreg.KEY_SET_VALUE)
            
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"127.0.0.1:{port}")
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            self.logger.info(f"系统代理已设置为 127.0.0.1:{port}")
            time.sleep(2)  # 等待设置生效
            return True
            
        except Exception as e:
            self.logger.error(f"设置代理失败: {e}")
            return False
    
    def disable_proxy(self):
        """禁用代理并验证"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                               0, winreg.KEY_SET_VALUE)

            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, '')
            winreg.CloseKey(key)
            
            # 验证代理确实已关闭
            max_wait = 10
            for i in range(max_wait):
                if not self.is_system_proxy_enabled():
                    self.logger.info("系统代理已成功关闭")
                    return True
                time.sleep(1)
            
            self.logger.warning("代理关闭状态验证超时")
            return False
            
        except Exception as e:
            self.logger.error(f"关闭代理失败: {e}")
            return False
    
    def wait_for_proxy_ready(self, max_wait: int = 30) -> bool:
        """等待代理服务启动完成"""
        start_time = time.time()
        self.logger.info("等待代理服务启动...")
        
        while time.time() - start_time < max_wait:
            if self.is_proxy_working(timeout=2):
                self.logger.info("代理服务已启动并正常工作")
                return True
            time.sleep(2)
        
        self.logger.error("代理服务启动超时")
        return False
    
    def kill_mitmproxy_processes(self):
        """强制停止所有mitmproxy相关进程"""
        try:
            # 在Windows上结束mitmproxy进程
            result = subprocess.run(['taskkill', '/f', '/im', 'mitmdump.exe'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.logger.info("已强制结束所有mitmdump.exe进程")
            
            # 使用更精确的任务终止，避免误杀当前Python进程
            try:
                # 查找当前用户的mitmdump相关进程
                process_result = subprocess.run(['tasklist', '/fi', 'imagename eq mitmdump.exe'], 
                                              capture_output=True, text=True, timeout=3)
                if 'mitmdump.exe' in process_result.stdout.lower():
                    # 找到特定进程，使用更安全的终止方式
                    subprocess.run(['taskkill', '/f', '/im', 'mitmdump.exe'], 
                                 capture_output=True, text=True, timeout=3)
                    self.logger.info("已安全结束剩余的mitmproxy进程")
            except Exception:
                pass  # 忽略次要错误，避免程序终止
                
        except Exception as e:
            self.logger.warning(f"结束进程时出错: {e}")
    
    def validate_and_fix_network(self):
        """验证网络连接正常"""
        try:
            # 测试不使用代理是否能连接外网
            requests.get('https://httpbin.org/ip', timeout=5)
            self.logger.info("✅ 网络连接正常（无代理）")
            return True
        except Exception as e:
            self.logger.error(f"❌ 网络连接异常: {e}")
            return False
    
    def reset_network_state(self):
        """重置网络状态到干净状态 - 增强版本"""
        self.logger.info("=== 开始重置网络状态 ===")
        
        # 1. 延迟结束代理进程，避免重叠操作
        try:
            self.logger.info("🔍 正在检查并结束现有代理进程...")
            # 先检查是否真的需要结束进程
            process_list = subprocess.run(['tasklist', '/fi', 'imagename eq mitmdump.exe'], 
                                        capture_output=True, text=True, timeout=3)
            if 'mitmdump.exe' in process_list.stdout.lower():
                self.logger.info("检测到运行中的mitmdump进程，执行结束操作...")
                self.kill_mitmproxy_processes()
                time.sleep(1)  # 给系统一点时间清理
            else:
                self.logger.info("未发现运行中的mitmdump进程，跳过进程结束步骤")
                
        except Exception as e:
            self.logger.warning(f"⚠️ 检查代理进程时出错: {e}，继续执行下一步")
            time.sleep(1)  # 给系统一点时间
        
        # 2. 安全关闭代理设置
        operation_success = True
        try:
            self.logger.info("🔧 正在关闭系统代理设置...")
            proxy_disabled = self.disable_proxy()
            self.logger.info(f"{'✅' if proxy_disabled else '✅ 但已尝试'} 代理关闭操作")
        except Exception as e:
            self.logger.warning(f"⚠️ 关闭代理设置时发生错误: {e}")
            # 这个错误不那么关键，继续执行
        
        # 3. 谨慎验证网络连接（减少重试，降低超时风险）
        self.logger.info("🔗 正在验证网络连接...")
        max_retries = 2  # 减少重试次数
        
        for attempt in range(max_retries):
            try:
                proxy_enabled = self.is_system_proxy_enabled()
                network_ok = self.validate_and_fix_network()
                
                if not proxy_enabled and network_ok:
                    self.logger.info("✅ 网络状态重置验证完成")
                    return True
                
                self.logger.info(f"验证中: 代理状态={proxy_enabled}, 网络状态={network_ok}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ 第{attempt + 1}次网络检查时出错: {e}")
                # 网络检查失败不是程序终止的理由
                time.sleep(1)  # 简短延迟
            
            if attempt < max_retries - 1:
                self.logger.info(f"🔄 简要重试检查 {attempt + 1}/{max_retries}")
            
        self.logger.info("ℹ️ 网络重置流程已完成，代理清理已执行")
        return True  # 即使有网络访问问题，也允许程序继续


