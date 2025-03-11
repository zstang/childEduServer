"""
异常类定义模块

这个模块定义了所有自定义异常类，包括：
1. 基础异常类
2. 解决方案生成相关异常
3. 问题验证相关异常
4. 对话管理相关异常
"""

from typing import Dict, Any, Optional


class BaseError(Exception):
    """基础异常类"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class PromptFileError(BaseError):
    """提示词文件相关错误"""
    pass


class BoundaryExtractionError(BaseError):
    """边界提取错误"""
    pass


class ResponseGenerationError(BaseError):
    """回答生成错误"""
    pass


class QuestionValidatorError(BaseError):
    """问题验证器异常基类"""
    pass


class ValidationError(QuestionValidatorError):
    """问题验证错误"""
    pass


class PrivacyCheckError(QuestionValidatorError):
    """隐私检查错误"""
    pass


class DialogueManagerError(BaseError):
    """对话管理器异常基类"""
    pass


class StateTrackingError(DialogueManagerError):
    """状态跟踪错误"""
    pass


class ContextManagementError(DialogueManagerError):
    """上下文管理错误"""
    pass


class SolutionGeneratorError(DialogueManagerError):
    """解决方案生成器错误"""
    pass


class UnitTestError(BaseError):
    """单元测试错误"""
    pass


class FeedbackAnalysisError(UnitTestError):
    """反馈分析测试错误"""
    pass