# README-PostgreSQL-Security.md

# PostgreSQL兼容的安全模块

本文档描述了使用SQLAlchemy Core重构的安全模块，以确保与PostgreSQL的兼容性。

## 重构的主要内容

1. 使用SQLAlchemy Core代替SQLAlchemy ORM
2. 改进事务管理和连接处理
3. 增强错误处理和日志记录
4. 优化前端与后端的加密通信

## 关键改进

### 1. 数据库连接和事务处理

使用显式事务和连接管理，确保在PostgreSQL环境下正确处理：

```python
conn = engine.connect()
trans = conn.begin()  # 显式开始事务
try:
    # 数据库操作
    trans.commit()  # 提交事务
except Exception as e:
    trans.rollback()  # 回滚事务
    logger.error(f"操作失败: {str(e)}")
    raise
finally:
    if conn:
        conn.close()  # 确保连接关闭
```

### 2. 表定义和查询

使用SQLAlchemy Core的表定义和查询语法：

```python
# 表定义
global_options = Table(
    "global_options", 
    metadata,
    Column("id", String, primary_key=True),
    Column("varb", String, unique=True, nullable=False),
    Column("options", Text, nullable=True),
    Column("reserve", String, nullable=True),
    Column("reserve1", Text, nullable=True),
    Column("fixed_time", TIMESTAMP, nullable=True)
)

# 查询示例
query = select(global_options).where(global_options.c.varb == "private_key")
result = conn.execute(query).fetchone()

# 更新示例
update_stmt = update(global_options).where(
    global_options.c.varb == "private_key"
).values(
    options="新值",
    fixed_time=datetime.now()
)
conn.execute(update_stmt)

# 插入示例
insert_stmt = insert(global_options).values(
    id=str(uuid.uuid4()),
    varb="key_name",
    options="值",
    fixed_time=datetime.now()
)
conn.execute(insert_stmt)
```

### 3. 前端改进

增强了前端的错误处理和安全通信：

```typescript
try {
  // 使用服务器公钥加密数据
  const encryptedData = await encryptData(data, serverPublicKey);
  
  const response = await fetch(endpoint, {
    // 请求配置
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('API请求失败:', response.status, errorText);
    throw new Error(`服务器响应错误: ${response.status} - ${errorText || '未知错误'}`);
  }
  
  return await response.json() as T;
} catch (error) {
  console.error('加密请求失败:', error);
  // 错误处理
}
```

## 测试方法

系统提供了多个测试脚本用于验证功能：

1. **数据库连接测试**: `test_database_connection.py`
   测试PostgreSQL连接和表操作是否正常

2. **安全模块测试**: `test_security.py`
   测试加密、解密、签名验证等功能

3. **集成测试**: `integration_test.py`
   测试前后端通信是否正常工作

运行测试：

```bash
# 测试数据库连接
python myfastapi/test_database_connection.py

# 测试安全模块
python myfastapi/test_security.py

# 集成测试
python myfastapi/integration_test.py
```

## 前端测试

在开发环境中测试前端：

```bash
# 启动开发服务器
cd $Frontend
npm run dev
```

在浏览器中访问 `http://localhost:3000/login` 并使用测试账号登录。

## 潜在问题和解决方案

1. **密钥同步问题**:
   如果数据库和本地文件中的密钥不同步，系统会自动从数据库更新本地文件。

2. **事务管理**:
   使用显式事务管理确保数据一致性，避免部分操作提交。

3. **错误处理**:
   增强了错误日志记录，确保能够定位问题。

4. **加密通信**:
   前端增加了更好的错误处理，提高了用户体验。

## 未来改进

1. 实现响应解密功能以提高安全性
2. 增加更多单元测试和集成测试
3. 提高错误处理的用户友好性
4. 添加监控和警报系统
