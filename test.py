#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信爬虫错误诊断工具
专门诊断 ret: -6 错误
"""
import time
import requests
from datetime import datetime
import os
import re
from urllib.parse import urlparse, parse_qs

class WechatErrorDiagnostic:
    """微信错误诊断器"""
    
    def __init__(self, auth_info):
        self.auth_info = auth_info
        
    def diagnose_ret_minus_6(self):
        """诊断 ret: -6 错误"""
        print("=== 微信 ret: -6 错误诊断 ===")
        
        # 1. 检查认证信息完整性
        print("\n1. 检查认证信息:")
        required_fields = ['appmsg_token', 'biz', 'cookie_str']
        for field in required_fields:
            value = self.auth_info.get(field, '')
            status = "OK" if value else "缺失"
            print(f"   {field}: {status}")
            
        # 2. 检查token新鲜度
        print("\n2. 检查token时效性:")
        appmsg_token = self.auth_info.get('appmsg_token', '')
        if '_' in appmsg_token:
            timestamp_part = appmsg_token.split('_')[0]
            try:
                # 检查token是否包含时间戳信息
                print(f"   token前缀: {timestamp_part}")
            except:
                print("   无法解析token时间戳")
        
        # 3. 检查关键headers
        print("\n3. 检查关键Headers:")
        headers = self.auth_info.get('headers', {})
        critical_headers = [
            'x-wechat-key',
            'x-wechat-uin', 
            'exportkey',
            'user-agent',
            'referer'
        ]
        
        for header in critical_headers:
            if header in headers:
                value = headers[header][:50] + "..." if len(headers[header]) > 50 else headers[header]
                print(f"   {header}: 存在 ({value})")
            else:
                print(f"   {header}: 缺失 ❌")
                
        # 4. 测试基础连接
        print("\n4. 测试基础连接:")
        self.test_basic_connection()
        
        # 5. 建议解决方案
        print("\n5. 建议解决方案:")
        self.suggest_solutions()
        
    def test_basic_connection(self):
        """测试基础连接"""
        try:
            # 测试到微信服务器的连接
            response = requests.get(
                "https://mp.weixin.qq.com",
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            print(f"   连接状态: {response.status_code}")
        except Exception as e:
            print(f"   连接失败: {e}")
            
    def suggest_solutions(self):
        """建议解决方案"""
        suggestions = [
            "1. 重新抓包获取最新的认证信息",
            "2. 检查是否在微信中正常访问过文章",
            "3. 等待5-10分钟后重试（避免频率限制）",
            "4. 确保使用相同的浏览器环境",
            "5. 检查系统时间是否正确",
            "6. 尝试访问不同的公众号文章"
        ]
        
        for suggestion in suggestions:
            print(f"   {suggestion}")
            
    def test_with_minimal_request(self):
        """使用最简请求测试"""
        print("\n=== 最简请求测试 ===")
        
        url = "https://mp.weixin.qq.com/mp/profile_ext"
        
        # 构建最基础的请求参数
        params = {
            'action': 'home',
            '__biz': self.auth_info.get('biz'),
            'devicetype': 'Windows+10+x64',
            'version': '6309092a',
            'lang': 'zh_CN',
            'nettype': 'WIFI',
            'a8scene': '7',
            'pass_ticket': '',
            'wx_header': '3'
        }
        
        # 基础headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://mp.weixin.qq.com/'
        }
        
        # 添加cookie
        if self.auth_info.get('cookie_str'):
            headers['Cookie'] = self.auth_info['cookie_str']
            
        try:
            print("发送测试请求...")
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    ret_code = data.get('ret', 'unknown')
                    print(f"返回码: {ret_code}")
                    
                    if ret_code == -6:
                        print("仍然返回 -6 错误，建议重新抓包")
                    elif ret_code == 0:
                        print("测试成功！认证信息有效")
                    else:
                        print(f"其他错误码: {ret_code}")
                        
                except:
                    print("响应不是JSON格式")
                    print(f"响应内容: {response.text[:200]}...")
            else:
                print(f"HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"请求失败: {e}")
            
def load_auth_from_file(keys_file="wechat_keys.txt"):
    """从 wechat_keys.txt 文件加载认证信息"""
    print(f"📄 读取认证文件: {keys_file}")
    
    if not os.path.exists(keys_file):
        print(f"❌ 文件不存在: {keys_file}")
        return None
        
    try:
        with open(keys_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 提取最新记录
        records = content.split('============================================================')
        if len(records) < 2:
            print("❌ 文件格式不正确，未找到有效记录")
            return None
            
        latest_record = records[-1].strip()
        print("🔍 解析最新抓包记录...")
        
        # 解析URL
        url_match = re.search(r'allurl: (https://[^\n]+)', latest_record)
        if not url_match:
            print("❌ 未找到文章URL")
            return None
            
        article_url = url_match.group(1).strip()
        print(f"🔗 文章URL: {article_url[:80]}...")
        
        # 从URL解析参数
        parsed_url = urlparse(article_url)
        query_params = parse_qs(parsed_url.query)
        
        # 提取 __biz
        biz = query_params.get('__biz', [None])[0]
        if not biz:
            print("❌ 未找到 __biz 参数")
            return None
            
        # 解析Cookies
        cookies_match = re.search(r'Cookies: (.+?)(?=\nHeaders:|\n[A-Z]|\Z)', latest_record, re.DOTALL)
        if not cookies_match:
            print("❌ 未找到Cookies")
            return None
            
        cookie_str = cookies_match.group(1).strip()
        
        # 提取appmsg_token
        appmsg_token_match = re.search(r'appmsg_token=([^;]+)', cookie_str)
        if not appmsg_token_match:
            print("❌ 未找到appmsg_token")
            return None
            
        appmsg_token = appmsg_token_match.group(1).strip()
        
        # 解析Headers
        headers_section = re.search(r'Headers:\n(.*?)(?=\n\n|\Z)', latest_record, re.DOTALL)
        headers = {}
        
        if headers_section:
            headers_text = headers_section.group(1)
            for line in headers_text.split('\n'):
                line = line.strip()
                if line and ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
        
        auth_info = {
            'appmsg_token': appmsg_token,
            'biz': biz,
            'cookie_str': cookie_str,
            'headers': headers,
            'sample_url': article_url
        }
        
        print("✅ 认证信息解析成功")
        print(f"   __biz: {biz}")
        print(f"   appmsg_token: {appmsg_token[:30]}...")
        print(f"   cookie长度: {len(cookie_str)} 字符")
        print(f"   headers数量: {len(headers)}")
        
        return auth_info
        
    except Exception as e:
        print(f"❌ 解析认证信息失败: {e}")
        return None


def main():
    """主函数 - 测试微信认证信息"""
    print("🔧 微信爬虫认证测试工具")
    print("=" * 50)
    
    # 1. 加载认证信息
    auth_info = load_auth_from_file()
    if not auth_info:
        print("\n💡 解决建议:")
        print("   1. 确保 wechat_keys.txt 文件存在")
        print("   2. 检查文件是否包含完整的抓包记录")
        print("   3. 重新运行抓包程序获取新的认证信息")
        return
    
    # 2. 创建诊断器
    diagnostic = WechatErrorDiagnostic(auth_info)
    
    print("\n" + "=" * 50)
    
    # 3. 运行完整诊断
    print("🔍 开始完整诊断...")
    diagnostic.diagnose_ret_minus_6()
    
    print("\n" + "=" * 50)
    
    # 4. 运行实际API测试
    print("🚀 开始实际API测试...")
    diagnostic.test_with_minimal_request()
    
    print("\n" + "=" * 50)
    print("📋 测试完成！")
    
    # 5. 交互式选项
    while True:
        print("\n请选择后续操作:")
        print("1. 重新运行诊断")
        print("2. 仅运行API测试")
        print("3. 仅检查认证信息")
        print("4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            print("\n" + "=" * 50)
            diagnostic.diagnose_ret_minus_6()
        elif choice == '2':
            print("\n" + "=" * 50)
            diagnostic.test_with_minimal_request()
        elif choice == '3':
            print("\n" + "=" * 50)
            print("📊 当前认证信息:")
            print(f"   __biz: {auth_info['biz']}")
            print(f"   appmsg_token: {auth_info['appmsg_token']}")
            print(f"   cookie长度: {len(auth_info['cookie_str'])}")
            print(f"   headers: {list(auth_info['headers'].keys())}")
        elif choice == '4':
            print("👋 退出测试工具")
            break
        else:
            print("❌ 无效选项，请重新选择")


if __name__ == "__main__":
    main()