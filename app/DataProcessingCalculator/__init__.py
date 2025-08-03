# DataProcessingCalculator Initialization

# 延迟导入，避免在包级别导入时出现依赖错误
def get_calculator():
    from . import calculator
    return calculator

def get_data_analyze():
    from . import DataAnalyze
    return DataAnalyze

def get_data_modification_module():
    from . import DataModificationModule
    return DataModificationModule

def get_time_dispersion_tool():
    from . import TimeDispersionAmzTool
    return TimeDispersionAmzTool

__all__ = ['get_calculator', 'get_data_analyze', 'get_data_modification_module', 'get_time_dispersion_tool']