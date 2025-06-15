# AutoTradingBinance 项目管理器 Shell 界面

## 🎯 概述

AutoTradingBinance 项目管理器是一个专业的交互式命令行工具，提供了完整的项目管理、安全配置、系统监控等功能。

## 🚀 快速启动

### 方法 1: 使用启动脚本
```bash
./start_shell.sh
```

### 方法 2: 直接运行 Python 脚本
```bash
python3 ProgramManager/shell.py
```

### 方法 3: 使用根目录管理脚本
```bash
python3 manage.py
```

## 🔧 主要功能

### 1. 项目设置 (`setup`)
- 完整的环境设置
- 依赖安装
- 权限配置
- 安全检查

### 2. 依赖管理 (`deps`)
- 安装Python依赖
- 更新过期包
- 检查依赖状态

### 3. 安全管理 (`security`)
- 系统安全检查
- 文件权限设置
- 环境变量验证

### 4. 密钥管理 (`keys`)
- 密钥状态检查
- 自动密钥轮换
- 密钥生成

### 5. Redis管理 (`redis`)
- Redis连接测试
- Redis配置查看
- 实时监控Redis状态
- Token黑名单管理
- 会话管理测试
- CSRF Token管理
- 性能统计和清理

### 6. 服务器管理 (`server`)
- 启动/停止 FastAPI 服务器
- 服务器状态监控
- 服务器重启

### 7. 系统监控 (`monitor`)
- 系统资源使用情况
- 内存、CPU、磁盘监控
- 网络状态检查

### 8. 项目状态 (`status`)
- 检查所有组件状态
- 配置验证
- 服务健康检查

### 9. 日志查看 (`logs`)
- 查看系统日志
- 错误日志分析
- 实时日志监控

## 🎨 界面特性

### 彩色输出
- 🟢 绿色：成功操作
- 🟡 黄色：警告信息
- 🔴 红色：错误信息
- 🔵 蓝色：信息提示
- 🟣 紫色：特殊功能

### 交互式菜单
- 数字选择 (1-8)
- 命令别名 (setup, deps, security, etc.)
- 快捷命令 (help, clear, history, exit)

### 命令历史
- 自动记录执行的命令
- 时间戳标记
- 历史命令查看

## 📋 使用示例

### 基本使用流程

1. **首次设置**
   ```
   [AutoTrading]➤ setup
   ```

2. **检查项目状态**
   ```
   [AutoTrading]➤ status
   ```

3. **启动服务器**
   ```
   [AutoTrading]➤ server
   ```

4. **监控系统**
   ```
   [AutoTrading]➤ monitor
   ```

### 高级功能

1. **密钥轮换**
   ```
   [AutoTrading]➤ keys
   选择: 2 (轮换密钥)
   ```

2. **安全检查**
   ```
   [AutoTrading]➤ security
   选择: 1 (安全检查)
   ```

3. **依赖更新**
   ```
   [AutoTrading]➤ deps
   选择: 2 (更新依赖)
   ```

## 🔧 快捷命令

| 命令 | 功能 |
|------|------|
| `help` / `h` / `?` | 显示帮助菜单 |
| `clear` / `cls` | 清屏 |
| `history` | 显示命令历史 |
| `exit` / `quit` / `q` | 退出程序 |

## 🛡️ 安全特性

- 密钥操作需要确认
- 文件权限自动设置
- 安全检查自动化
- 进程监控和管理

## 📁 文件结构

```
AutoTradingBinance/
├── ProgramManager/          # 🔧 项目管理工具
│   ├── shell.py            # 交互式 Shell 界面
│   ├── manage.py           # 命令行管理工具  
│   ├── setup.py            # 项目设置
│   └── *.sh                # Shell 脚本
├── start_shell.sh          # 快速启动脚本
├── manage.py               # 根目录启动入口
└── ...
```

## 🐛 故障排除

### 常见问题

1. **Python 环境问题**
   - 确保安装了 Python 3.8+
   - 检查虚拟环境是否激活

2. **权限问题**
   - 运行权限设置：`chmod +x start_shell.sh`
   - 密钥文件权限自动管理

3. **依赖问题**
   - 运行依赖安装：在 shell 中选择 `deps` → `1`
   - 更新过期依赖：在 shell 中选择 `deps` → `2`

### 日志调试

使用 shell 界面的日志查看功能：
```
[AutoTrading]➤ logs
```

## 🔄 更新和维护

Shell 界面会自动检查项目状态并提供维护建议。定期运行：

1. `status` - 检查项目健康状态
2. `security` - 运行安全检查
3. `deps` - 更新依赖包
4. `keys` - 检查密钥状态

---

## 💡 提示

- 使用 Tab 键可以在某些系统上自动补全
- 输入错误命令时会显示建议
- 支持 Ctrl+C 安全退出
- 所有操作都有详细的状态反馈

享受使用 AutoTradingBinance 项目管理器！🚀

## 🔗 Redis管理详细说明

Redis管理功能提供了完整的Redis连接、监控和测试工具：

### Redis管理子菜单
```
[AutoTrading]➤ redis
🔗 Redis管理
1. 查看Redis配置    - 显示当前Redis连接配置
2. 测试Redis连接    - 验证Redis服务器连接状态
3. 运行完整测试    - 执行所有Redis功能测试
4. Redis统计信息   - 显示Redis性能和使用统计
5. 实时监控Redis   - 实时监控Redis状态
6. 清理过期数据    - 清理过期的缓存数据
7. 返回主菜单
```

### 独立Redis管理工具

除了集成到shell中，还可以直接使用Redis管理工具：

```bash
# 查看Redis配置
python3 ProgramManager/redis_manager.py config

# 运行连接测试
python3 ProgramManager/redis_manager.py test

# 查看统计信息
python3 ProgramManager/redis_manager.py stats

# 实时监控(间隔5秒，监控20次)
python3 ProgramManager/redis_manager.py monitor --interval 5 --count 20

# 运行所有测试和检查
python3 ProgramManager/redis_manager.py all
```

### Redis功能测试包括
1. **连接测试** - 验证Redis服务器连接
2. **Token黑名单** - 测试JWT Token撤销功能
3. **会话管理** - 测试用户会话存储和管理
4. **CSRF Token** - 测试CSRF防护Token生成和验证

### 环境变量配置
在`.env`文件中配置Redis连接：
```bash
REDIS_URL=redis://testserver.lan:6379/0
REDIS_PASSWORD="your_redis_password"
REDIS_DB=0
```
