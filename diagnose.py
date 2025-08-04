#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号批量阅读量抓取器 - 诊断工具
帮助用户快速诊断和解决常见问题
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from read_cookie import ReadCookie

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境")
    print("-" * 40)
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("⚠️ 建议使用Python 3.7或更高版本")
    else:
        print("✅ Python版本符合要求")
    
    # 检查必要的包
    required_packages = ['requests', 'pandas', 'openpyxl', 'bs4']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 请安装缺失的包:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_cookie_file():
    """检查Cookie文件"""
    print("\n🔍 检查Cookie文件")
    print("-" * 40)
    
    if not os.path.exists('wechat_keys.txt'):
        print("❌ 未找到wechat_keys.txt文件")
        print("💡 解决方案:")
        print("   1. 运行: python main_enhanced.py")
        print("   2. 选择功能1进行Cookie抓取")
        return False
    
    # 检查文件大小
    file_size = os.path.getsize('wechat_keys.txt')
    print(f"📁 文件大小: {file_size} 字节")
    
    if file_size < 100:
        print("⚠️ 文件太小，可能没有有效数据")
        return False
    
    # 检查文件内容
    try:
        with open('wechat_keys.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'appmsg_token' in content and '__biz' in content:
            print("✅ 文件包含必要的认证信息")
            
            # 检查时间戳
            lines = content.split('\n')
            latest_time = None
            for line in lines:
                if line.startswith('time:'):
                    time_str = line.replace('time:', '').strip()
                    try:
                        latest_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                        break
                    except:
                        pass
            
            if latest_time:
                time_diff = datetime.now() - latest_time
                print(f"⏰ Cookie时间: {latest_time}")
                print(f"⏰ 距今: {time_diff}")
                
                if time_diff > timedelta(hours=24):
                    print("⚠️ Cookie可能已过期（超过24小时）")
                    print("💡 建议重新抓取Cookie")
                    return False
                else:
                    print("✅ Cookie时间较新")
            
            return True
        else:
            print("❌ 文件缺少必要的认证信息")
            return False
    
    except Exception as e:
        print(f"❌ 读取文件出错: {e}")
        return False

def test_cookie_parsing():
    """测试Cookie解析"""
    print("\n🔍 测试Cookie解析")
    print("-" * 40)
    
    try:
        cookie_reader = ReadCookie('wechat_keys.txt', delete_existing_file=False)
        result = cookie_reader.get_latest_cookies()
        
        if result:
            print("✅ Cookie解析成功")
            print(f"   __biz: {result['biz']}")
            print(f"   appmsg_token: {result['appmsg_token'][:30]}...")
            print(f"   cookie长度: {len(result['cookie_str'])} 字符")
            return result
        else:
            print("❌ Cookie解析失败")
            return None
    except Exception as e:
        print(f"❌ Cookie解析出错: {e}")
        return None

def test_network_connectivity(auth_info):
    """测试网络连接"""
    print("\n🔍 测试网络连接")
    print("-" * 40)
    
    if not auth_info:
        print("❌ 无有效认证信息，跳过网络测试")
        return False
    
    # 测试基本网络连接
    try:
        response = requests.get('https://www.baidu.com', timeout=10)
        print("✅ 基本网络连接正常")
    except Exception as e:
        print(f"❌ 基本网络连接失败: {e}")
        return False
    
    # 测试微信API连接
    try:
        url = "https://mp.weixin.qq.com/mp/profile_ext"
        params = {
            'action': 'getmsg',
            '__biz': auth_info['biz'],
            'f': 'json',
            'offset': 0,
            'count': 1,
            'is_ok': 1,
            'scene': 124,
            'uin': 777,
            'key': 777,
            'pass_ticket': 'test',
            'wxtoken': '',
            'appmsg_token': auth_info['appmsg_token'],
            'x5': 0,
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': auth_info['cookie_str'],
            'Referer': 'https://mp.weixin.qq.com/',
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            print("✅ 微信API连接成功")
            
            # 检查响应内容
            try:
                data = response.json()
                if 'general_msg_list' in data:
                    print("✅ API返回数据格式正确")
                    return True
                elif 'ret' in data:
                    ret_code = data.get('ret', 0)
                    if ret_code == -3:
                        print("❌ Cookie已过期或无效")
                    elif ret_code == -1:
                        print("❌ 请求频率过高")
                    else:
                        print(f"❌ API返回错误码: {ret_code}")
                    return False
                else:
                    print("⚠️ API返回格式异常")
                    return False
            except:
                print("⚠️ API返回非JSON格式")
                return False
        else:
            print(f"❌ 微信API连接失败，状态码: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 微信API连接出错: {e}")
        return False

def check_data_directory():
    """检查数据目录"""
    print("\n🔍 检查数据目录")
    print("-" * 40)
    
    data_dir = "./data/readnum_batch"
    
    try:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            print(f"✅ 创建数据目录: {data_dir}")
        else:
            print(f"✅ 数据目录存在: {data_dir}")
        
        # 检查写入权限
        test_file = os.path.join(data_dir, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ 数据目录可写")
        
        return True
    except Exception as e:
        print(f"❌ 数据目录检查失败: {e}")
        return False

def provide_solutions():
    """提供解决方案"""
    print("\n💡 常见问题解决方案")
    print("=" * 50)
    
    print("1. Cookie过期或无效:")
    print("   - 运行: python main_enhanced.py")
    print("   - 选择功能1重新抓取Cookie")
    print("   - 确保在抓取过程中访问了微信公众号文章")
    
    print("\n2. 网络连接问题:")
    print("   - 检查网络连接是否稳定")
    print("   - 如果使用代理，确保代理设置正确")
    print("   - 尝试关闭防火墙或杀毒软件")
    
    print("\n3. 依赖包缺失:")
    print("   - 运行: pip install -r requirements.txt")
    print("   - 或手动安装: pip install requests pandas openpyxl beautifulsoup4")
    
    print("\n4. 权限问题:")
    print("   - 确保程序有读写文件的权限")
    print("   - 尝试以管理员身份运行")
    
    print("\n5. 频率限制:")
    print("   - 等待30分钟后重试")
    print("   - 降低抓取频率参数")
    print("   - 使用更长的请求间隔")

def main():
    """主诊断函数"""
    print("🔧 微信公众号批量阅读量抓取器 - 诊断工具")
    print("=" * 60)
    
    # 诊断结果
    results = []
    
    # 1. 检查环境
    results.append(("运行环境", check_environment()))
    
    # 2. 检查Cookie文件
    results.append(("Cookie文件", check_cookie_file()))
    
    # 3. 测试Cookie解析
    auth_info = test_cookie_parsing()
    results.append(("Cookie解析", auth_info is not None))
    
    # 4. 测试网络连接
    if auth_info:
        results.append(("网络连接", test_network_connectivity(auth_info)))
    else:
        results.append(("网络连接", False))
    
    # 5. 检查数据目录
    results.append(("数据目录", check_data_directory()))
    
    # 输出诊断结果
    print("\n" + "=" * 60)
    print("📋 诊断结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ 正常" if result else "❌ 异常"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 诊断通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有检查通过！系统可以正常使用")
        print("💡 如果仍有问题，请运行: python test_batch_readnum.py")
    else:
        print("⚠️ 发现问题，请参考以下解决方案")
        provide_solutions()

if __name__ == "__main__":
    main()
