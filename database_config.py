# coding:utf-8
# database_config.py
"""
数据库配置文件
用于管理数据库连接参数和相关配置
"""

# 数据库连接配置
DATABASE_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'faxuan'
}

# 数据库表配置
TABLE_CONFIG = {
    'table_name': 'fx_article_records',
    'crawl_channel_default': '微信公众号'
}

# 文章ID生成配置
ARTICLE_ID_CONFIG = {
    'time_format': '%Y%m%d%H%M',  # 前12位时间格式
    'random_digits': 4           # 后4位随机数位数
}

# 数据库操作配置
DB_OPERATION_CONFIG = {
    'auto_reconnect': True,      # 自动重连
    'connection_timeout': 30,    # 连接超时时间(秒)
    'batch_insert_delay': 0.1,   # 批量插入间隔(秒)
    'max_retry_times': 3         # 最大重试次数
}

def get_database_config():
    """获取数据库配置"""
    return DATABASE_CONFIG.copy()

def get_table_config():
    """获取表配置"""
    return TABLE_CONFIG.copy()

def get_article_id_config():
    """获取文章ID配置"""
    return ARTICLE_ID_CONFIG.copy()

def get_db_operation_config():
    """获取数据库操作配置"""
    return DB_OPERATION_CONFIG.copy()

def validate_database_config(config):
    """
    验证数据库配置
    
    Args:
        config: 数据库配置字典
        
    Returns:
        tuple: (is_valid, error_message)
    """
    required_keys = ['host', 'port', 'user', 'password', 'database']
    
    for key in required_keys:
        if key not in config:
            return False, f"缺少必需的配置项: {key}"
        
        if not config[key]:
            return False, f"配置项 {key} 不能为空"
    
    # 验证端口号
    try:
        port = int(config['port'])
        if port <= 0 or port > 65535:
            return False, "端口号必须在1-65535之间"
    except (ValueError, TypeError):
        return False, "端口号必须是有效的数字"
    
    return True, "配置验证通过"

# 示例：如何使用配置
if __name__ == "__main__":
    print("数据库配置示例:")
    print("=" * 40)
    
    # 获取配置
    db_config = get_database_config()
    table_config = get_table_config()
    
    print("数据库连接配置:")
    for key, value in db_config.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")
    
    print("\n表配置:")
    for key, value in table_config.items():
        print(f"  {key}: {value}")
    
    # 验证配置
    is_valid, message = validate_database_config(db_config)
    print(f"\n配置验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    print(f"验证信息: {message}")
