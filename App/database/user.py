"""
用户数据库管理
"""
import sqlite3
import hashlib
from datetime import datetime
from App.code.config import DB_PATH, DEFAULT_ADMIN

class UserDatabase:
    """用户数据库管理类"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
        
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0
            )
        ''')
        
        # 检查并添加 is_admin 字段（如果不存在）
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # 字段已存在
        
        # 创建检测记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                detection_type TEXT,
                result TEXT,
                confidence REAL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建默认管理员账户
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, ?)',
                (DEFAULT_ADMIN['username'], 
                 self._hash_password(DEFAULT_ADMIN['password']), 
                 'admin@system.com',
                 1)
            )
            print(f"✅ 创建默认管理员：{DEFAULT_ADMIN['username']}")
        except sqlite3.IntegrityError:
            # 如果管理员已存在，确保其 is_admin 字段为 1
            cursor.execute(
                'UPDATE users SET is_admin = 1 WHERE username = ?',
                (DEFAULT_ADMIN['username'],)
            )
            pass  # 已存在
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password):
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password, email=None):
        """注册用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                (username, password_hash, email)
            )
            
            conn.commit()
            conn.close()
            return True, "注册成功"
        except sqlite3.IntegrityError:
            return False, "用户名已存在"
        except Exception as e:
            return False, f"注册失败：{e}"
    
    def login_user(self, username, password):
        """用户登录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            cursor.execute(
                'SELECT id, username, email, created_at, is_admin FROM users WHERE username = ? AND password_hash = ? AND is_active = 1',
                (username, password_hash)
            )
            
            user = cursor.fetchone()
            
            if user:
                # 更新最后登录时间
                cursor.execute(
                    'UPDATE users SET last_login = ? WHERE username = ?',
                    (datetime.now(), username)
                )
                conn.commit()
                
                user_data = {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'created_at': user[3],
                    'is_admin': bool(user[4])
                }
                
                conn.close()
                return True, "登录成功", user_data
            else:
                conn.close()
                return False, "用户名或密码错误", None
                
        except Exception as e:
            return False, f"登录失败：{e}", None
    
    def get_user_by_id(self, user_id):
        """根据 ID 获取用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, created_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3]
            }
        return None
    
    def get_all_users(self):
        """获取所有用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, username, email, created_at, last_login, is_active, is_admin FROM users')
            users = cursor.fetchall()
            
            conn.close()
            
            user_list = []
            for user in users:
                user_list.append({
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'created_at': user[3],
                    'last_login': user[4],
                    'is_active': bool(user[5]),
                    'is_admin': bool(user[6])
                })
            return user_list
        except Exception as e:
            print(f"获取用户列表失败：{e}")
            return []
    
    def add_user(self, username, password, email=None, is_admin=False):
        """添加用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, ?)',
                (username, password_hash, email, is_admin)
            )
            
            conn.commit()
            conn.close()
            return True, "添加用户成功"
        except sqlite3.IntegrityError:
            return False, "用户名已存在"
        except Exception as e:
            return False, f"添加用户失败：{e}"
    
    def delete_user(self, user_id):
        """删除用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 不能删除管理员账户
            cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if user and user[0]:
                conn.close()
                return False, "不能删除管理员账户"
            
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return True, "删除用户成功"
        except Exception as e:
            return False, f"删除用户失败：{e}"
    
    def update_user(self, user_id, username=None, password=None, email=None, is_active=None, is_admin=None):
        """更新用户信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            if username:
                update_fields.append('username = ?')
                params.append(username)
            if password:
                update_fields.append('password_hash = ?')
                params.append(self._hash_password(password))
            if email is not None:
                update_fields.append('email = ?')
                params.append(email)
            if is_active is not None:
                update_fields.append('is_active = ?')
                params.append(is_active)
            if is_admin is not None:
                update_fields.append('is_admin = ?')
                params.append(is_admin)
            
            if update_fields:
                params.append(user_id)
                query = f'UPDATE users SET {", ".join(update_fields)} WHERE id = ?'
                cursor.execute(query, params)
                conn.commit()
            
            conn.close()
            return True, "更新用户成功"
        except sqlite3.IntegrityError:
            return False, "用户名已存在"
        except Exception as e:
            return False, f"更新用户失败：{e}"
    
    def add_detection_log(self, user_id, detection_type, result, confidence, image_path=None):
        """添加检测记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO detection_logs (user_id, detection_type, result, confidence, image_path) VALUES (?, ?, ?, ?, ?)',
                (user_id, detection_type, result, confidence, image_path)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加日志失败：{e}")
            return False
    
    def get_user_logs(self, user_id, limit=100):
        """获取用户检测记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, detection_type, result, confidence, image_path, created_at 
               FROM detection_logs 
               WHERE user_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?''',
            (user_id, limit)
        )
        
        logs = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': log[0],
                'type': log[1],
                'result': log[2],
                'confidence': log[3],
                'image_path': log[4],
                'time': log[5]
            }
            for log in logs
        ]
