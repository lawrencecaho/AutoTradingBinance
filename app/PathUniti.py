"""
通用路径管理模块
用于统一管理项目中的所有路径配置
"""
import os
import sys
from pathlib import Path

class PathManager:
    """路径管理器"""
    
    def __init__(self):
        # 基础路径
        self.current_file = Path(__file__)
        self.app_dir = self.current_file.parent  # app目录 (当前文件在app目录中)
        self.project_root = self.app_dir.parent  # 项目根目录
        
        # 常用目录
        self.data_dir = self.app_dir / "data"  # Docker环境下，数据目录在app内
        self.logs_dir = self.app_dir / "logs"  # Docker环境下，日志目录在app内
        self.docs_dir = self.project_root / "docs"
        self.secret_dir = self.project_root / "Secret"
        
        # app内部目录
        self.config_dir = self.app_dir  # config.py在app根目录
        self.database_dir = self.app_dir / "DatabaseOperator"
        self.fetcher_dir = self.app_dir / "ExchangeFetcher"
        self.calculator_dir = self.app_dir / "DataProcessingCalculator"
        self.fastapi_dir = self.app_dir / "myfastapi"
        self.program_manager_dir = self.app_dir / "ProgramManager"
        self.exchange_bill_dir = self.app_dir / "ExchangeBill"
        
    def setup_python_path(self):
        """设置Python路径"""
        paths_to_add = [
            str(self.project_root),
            str(self.app_dir),
        ]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
                
        return True
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            self.logs_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_secret_file_path(self, filename: str) -> Path:
        """获取Secret目录下的文件路径"""
        return self.secret_dir / filename
    
    def get_config_file_path(self) -> Path:
        """获取config.py文件路径"""
        return self.app_dir / "config.py"
    
    def get_log_file_path(self, log_name: str = "app.log") -> Path:
        """获取日志文件路径"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        return self.logs_dir / log_name
            
    def get_relative_path(self, target_path: str) -> Path:
        """获取相对于项目根目录的路径"""
        return self.project_root / target_path
    
    def get_app_relative_path(self, target_path: str) -> Path:
        """获取相对于app目录的路径"""
        return self.app_dir / target_path

# 创建全局路径管理器实例
path_manager = PathManager()

# 自动设置Python路径
path_manager.setup_python_path()
path_manager.ensure_directories()

# 导出常用路径变量
PROJECT_ROOT = path_manager.project_root
APP_DIR = path_manager.app_dir
DATA_DIR = path_manager.data_dir
LOGS_DIR = path_manager.logs_dir
DOCS_DIR = path_manager.docs_dir
SECRET_DIR = path_manager.secret_dir

# 导出app内部目录
DATABASE_DIR = path_manager.database_dir
FETCHER_DIR = path_manager.fetcher_dir
CALCULATOR_DIR = path_manager.calculator_dir
FASTAPI_DIR = path_manager.fastapi_dir
PROGRAM_MANAGER_DIR = path_manager.program_manager_dir
EXCHANGE_BILL_DIR = path_manager.exchange_bill_dir

# 导出实用函数
get_secret_file = path_manager.get_secret_file_path
get_config_file = path_manager.get_config_file_path
get_log_file = path_manager.get_log_file_path