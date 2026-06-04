"""
文件B：接收数据并保存到本地MySQL数据库
"""
import pymysql
import json
import socket
from datetime import datetime
import sys
import os

def load_config(config_file='config_B.json'):
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_table_structure(structure_file='../table_structure.json'):
    """加载表结构JSON文件"""
    # 尝试多个可能的路径
    possible_paths = [
        os.path.join(os.path.dirname(__file__), structure_file),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'table_structure.json'),
        structure_file
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    raise FileNotFoundError(f"找不到表结构文件 table_structure.json")

def convert_sql_type_to_mysql(col_info):
    """将SQL Server数据类型转换为MySQL数据类型"""
    data_type = col_info['data_type'].upper()
    max_length = col_info.get('max_length')
    precision = col_info.get('precision')
    scale = col_info.get('scale')
    
    # MySQL类型映射
    type_mapping = {
        'FLOAT': 'DOUBLE',
        'INT': 'INT',
        'DATETIME': 'DATETIME',
        'VARCHAR': 'VARCHAR',
        'NVARCHAR': 'VARCHAR',
        'CHAR': 'CHAR',
        'NCHAR': 'CHAR',
        'TEXT': 'TEXT',
        'NTEXT': 'TEXT'
    }
    
    mysql_type = type_mapping.get(data_type, data_type)
    
    # 处理长度和精度
    if data_type in ['FLOAT', 'DOUBLE', 'REAL']:
        if precision:
            if precision == 53:
                return 'DOUBLE'
            else:
                return f'FLOAT({precision})'
        return 'DOUBLE'
    elif data_type in ['INT', 'BIGINT', 'SMALLINT', 'TINYINT']:
        # INT类型不需要精度参数
        return 'INT' if data_type == 'INT' else mysql_type
    elif data_type == 'DATETIME':
        return 'DATETIME'
    elif data_type in ['VARCHAR', 'NVARCHAR', 'CHAR', 'NCHAR']:
        if max_length == -1 or max_length is None:
            return 'TEXT'
        elif max_length:
            return f'{mysql_type}({max_length})'
        else:
            return mysql_type
    else:
        return mysql_type

def generate_mysql_create_table(structure_data):
    """根据表结构生成MySQL CREATE TABLE语句"""
    table_name = structure_data['table_name']
    columns = structure_data['columns']
    
    sql_parts = [f"CREATE TABLE IF NOT EXISTS `{table_name}` ("]
    
    col_definitions = []
    for col in columns:
        col_name = col['name']
        mysql_type = convert_sql_type_to_mysql(col)
        nullable = "" if col['is_nullable'] == "NO" else "NULL"
        not_null = "NOT NULL" if col['is_nullable'] == "NO" else ""
        
        # 处理默认值
        default = ""
        if col.get('default') and col['default'] != 'None' and col['default']:
            default_value = col['default']
            if isinstance(default_value, str):
                # 如果是函数调用（如GETDATE()），转换为MySQL的NOW()
                if 'GETDATE()' in default_value.upper() or 'NOW()' in default_value.upper():
                    default = " DEFAULT CURRENT_TIMESTAMP"
                elif not default_value.startswith('('):
                    default = f" DEFAULT '{default_value}'"
            else:
                default = f" DEFAULT {default_value}"
        
        # 组合列定义
        parts = [f"`{col_name}`", mysql_type]
        if not_null:
            parts.append(not_null)
        if nullable and not not_null:
            parts.append(nullable)
        if default:
            parts.append(default)
        
        col_definitions.append(" ".join(parts))
    
    sql_parts.append(",\n  ".join(col_definitions))
    sql_parts.append("\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
    
    return "\n".join(sql_parts)

def connect_database(host, port, user, password, database):
    """连接MySQL数据库，如果数据库不存在则自动创建"""
    try:
        # 先尝试连接指定数据库
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print(f"✓ MySQL数据库连接成功")
        return conn
    except pymysql.Error as e:
        error_code = e.args[0] if e.args else None
        # 1049 是数据库不存在的错误码
        if error_code == 1049:
            print(f"数据库 `{database}` 不存在，正在创建...")
            try:
                # 连接MySQL服务器（不指定数据库）
                temp_conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    charset='utf8mb4'
                )
                cursor = temp_conn.cursor()
                
                # 创建数据库
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                temp_conn.commit()
                cursor.close()
                temp_conn.close()
                
                print(f"✓ 数据库 `{database}` 创建成功")
                
                # 重新连接指定数据库
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                print(f"✓ MySQL数据库连接成功")
                return conn
            except pymysql.Error as create_error:
                raise Exception(f"创建数据库失败: {create_error}")
        else:
            raise Exception(f"无法连接到MySQL数据库: {e}")

def table_exists(cursor, table_name):
    """检查表是否存在"""
    try:
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        print(f"检查表存在性时出错: {e}")
        return False

def create_table_if_not_exists(cursor, conn, structure_data):
    """如果表不存在则创建表"""
    table_name = structure_data['table_name']
    
    if table_exists(cursor, table_name):
        print(f"✓ 表 `{table_name}` 已存在")
        return True
    
    print(f"表 `{table_name}` 不存在，正在创建...")
    
    try:
        create_sql = generate_mysql_create_table(structure_data)
        print("\n生成的 CREATE TABLE SQL:")
        print("-" * 80)
        print(create_sql)
        print("-" * 80)
        
        cursor.execute(create_sql)
        conn.commit()
        print(f"✓ 表 `{table_name}` 创建成功！")
        return True
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_table_columns_info(cursor, table_name):
    """获取表的列信息，包括是否允许NULL和默认值"""
    query = f"""
    SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = '{table_name}'
    """
    cursor.execute(query)
    columns_info = {}
    for row in cursor.fetchall():
        columns_info[row['COLUMN_NAME']] = {
            'nullable': row['IS_NULLABLE'] == 'YES',
            'default': row['COLUMN_DEFAULT'],
            'data_type': row['DATA_TYPE']
        }
    return columns_info

def insert_record(cursor, conn, table_name, record):
    """插入记录到数据库，允许值为空（NULL），但NOT NULL字段必须有值"""
    # 获取表的列信息
    try:
        columns_info = get_table_columns_info(cursor, table_name)
    except:
        columns_info = {}
    
    # 处理列和值
    columns = []
    values = []
    
    # 先处理record中存在的字段
    for col_name, col_value in record.items():
        col_info = columns_info.get(col_name, {})
        is_nullable = col_info.get('nullable', True)
        
        # 如果值为None
        if col_value is None:
            if not is_nullable:
                # NOT NULL字段，提供默认值
                default_value = col_info.get('default')
                data_type = col_info.get('data_type', '').upper()
                
                if default_value is not None:
                    col_value = default_value
                else:
                    # 根据数据类型提供默认值
                    if 'INT' in data_type:
                        col_value = 0
                    elif 'FLOAT' in data_type or 'DOUBLE' in data_type or 'DECIMAL' in data_type:
                        col_value = 0.0
                    elif 'VARCHAR' in data_type or 'CHAR' in data_type or 'TEXT' in data_type:
                        col_value = ''
                    elif 'DATETIME' in data_type or 'DATE' in data_type or 'TIME' in data_type:
                        col_value = datetime.now()
                    else:
                        col_value = ''
        # 如果值不为None，直接使用
        
        columns.append(col_name)
        values.append(col_value)
    
    # 检查是否有NOT NULL字段在record中不存在，需要补充默认值
    for col_name, col_info in columns_info.items():
        if col_name not in columns:  # 字段不在record中
            is_nullable = col_info.get('nullable', True)
            if not is_nullable:  # NOT NULL字段必须提供值
                default_value = col_info.get('default')
                data_type = col_info.get('data_type', '').upper()
                
                if default_value is not None:
                    col_value = default_value
                else:
                    # 根据数据类型提供默认值
                    if 'INT' in data_type:
                        col_value = 0
                    elif 'FLOAT' in data_type or 'DOUBLE' in data_type or 'DECIMAL' in data_type:
                        col_value = 0.0
                    elif 'VARCHAR' in data_type or 'CHAR' in data_type or 'TEXT' in data_type:
                        col_value = ''
                    elif 'DATETIME' in data_type or 'DATE' in data_type or 'TIME' in data_type:
                        col_value = datetime.now()
                    else:
                        col_value = ''
                
                columns.append(col_name)
                values.append(col_value)
    
    if not columns:
        print("  警告: 没有可插入的字段")
        return False
    
    # 构建INSERT语句（MySQL使用反引号）
    placeholders = ', '.join(['%s' for _ in columns])
    column_names = ', '.join([f'`{col}`' for col in columns])
    
    insert_sql = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
    
    # 处理datetime类型
    processed_values = []
    for val in values:
        if isinstance(val, str):
            # 尝试解析ISO格式的datetime字符串
            try:
                # 先尝试带时区的格式
                dt = datetime.fromisoformat(val.replace('Z', '+00:00'))
                processed_values.append(dt)
            except:
                try:
                    # 再尝试不带时区的格式
                    dt = datetime.fromisoformat(val)
                    processed_values.append(dt)
                except:
                    # 如果解析失败，保持原值
                    processed_values.append(val)
        else:
            processed_values.append(val)
    
    cursor.execute(insert_sql, processed_values)
    conn.commit()
    
    return cursor.rowcount > 0

def check_record_exists(cursor, table_name, creation_date):
    """检查记录是否已存在（根据creation_date）"""
    if not creation_date:
        return False
    
    try:
        # 尝试解析datetime
        if isinstance(creation_date, str):
            try:
                dt = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
            except:
                dt = datetime.fromisoformat(creation_date)
        else:
            dt = creation_date
        
        query = f"""
        SELECT COUNT(*) as cnt
        FROM `{table_name}` 
        WHERE creation_date = %s
        """
        cursor.execute(query, (dt,))
        result = cursor.fetchone()
        return result['cnt'] > 0 if result else False
    except Exception as e:
        print(f"检查记录存在性时出错: {e}")
        return False

def receive_data(sock):
    """接收数据"""
    try:
        # 先接收数据长度（4字节）
        length_bytes = sock.recv(4)
        if len(length_bytes) < 4:
            return None
        
        length = int.from_bytes(length_bytes, byteorder='big')
        
        # 接收实际数据
        data = b''
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                return None
            data += chunk
        
        # 解析JSON
        json_data = data.decode('utf-8')
        record = json.loads(json_data)
        
        return record
    except Exception as e:
        print(f"接收数据错误: {e}")
        return None

def main():
    """主函数"""
    print("=" * 80)
    print("文件B：实时数据同步接收端 (MySQL)")
    print("=" * 80)
    print()
    
    try:
        # 加载配置
        config = load_config()
        db_config = config['local_database']
        server_config = config['server']
        
        print(f"MySQL数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        print(f"监听地址: {server_config['host']}:{server_config['port']}")
        print()
        
        # 连接数据库
        conn = connect_database(
            db_config['host'],
            db_config['port'],
            db_config['user'],
            db_config['password'],
            db_config['database']
        )
        cursor = conn.cursor()
        
        # 加载表结构并检查/创建表
        try:
            structure_data = load_table_structure()
            create_table_if_not_exists(cursor, conn, structure_data)
        except FileNotFoundError as e:
            print(f"⚠ 警告: {e}")
            print("将尝试使用现有表结构")
        
        # 创建socket服务器
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((server_config['host'], server_config['port']))
        server_socket.listen(5)
        
        print(f"\n✓ 服务器已启动，等待连接...")
        print("按 Ctrl+C 停止")
        print("-" * 80)
        
        while True:
            try:
                # 接受连接
                client_socket, client_address = server_socket.accept()
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 收到来自 {client_address[0]}:{client_address[1]} 的连接")
                
                # 接收数据
                record = receive_data(client_socket)
                
                if record:
                    creation_date = record.get('creation_date')
                    print(f"收到数据，creation_date: {creation_date}")
                    
                    # 检查记录是否已存在
                    if check_record_exists(cursor, db_config['table_name'], creation_date):
                        print("⚠ 记录已存在，跳过插入")
                        client_socket.sendall("OK".encode('utf-8'))
                    else:
                        # 插入记录
                        if insert_record(cursor, conn, db_config['table_name'], record):
                            print("✓ 数据保存成功")
                            client_socket.sendall("OK".encode('utf-8'))
                        else:
                            print("✗ 数据保存失败")
                            client_socket.sendall("FAIL".encode('utf-8'))
                else:
                    print("✗ 接收数据失败")
                    client_socket.sendall("FAIL".encode('utf-8'))
                
                client_socket.close()
                
            except KeyboardInterrupt:
                print("\n\n程序已停止")
                break
            except Exception as e:
                print(f"\n错误: {e}")
                import traceback
                traceback.print_exc()
        
        server_socket.close()
        cursor.close()
        conn.close()
        
    except FileNotFoundError:
        print(f"错误: 找不到配置文件 'config_B.json'")
        print("请运行 init_config.bat 进行初始化配置")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
