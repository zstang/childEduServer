"""
问题验证器模块

这个模块整合了问题验证的所有功能，包括：
1. 隐私和安全检查
2. 问题范围验证
3. 新问题判断
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, Tuple

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from config.settings import UserRole
from modules.privacy_checker import PrivacyChecker
from modules.scope_validator import ScopeValidator
from modules.exceptions import ValidationError


class QuestionValidator:
    def __init__(self):
        """初始化问题验证器"""
        self.privacy_checker = PrivacyChecker()
        self.scope_validator = ScopeValidator()

    def validate_question(self, question: str, role: UserRole = UserRole.STUDENT) -> Dict[str, Any]:
        """
        验证问题的合法性

        参数:
            question (str): 用户问题
            role (UserRole): 用户角色，默认为学生

        返回:
            Dict[str, Any]: 验证结果
        """
        try:
            # 1. 检查隐私和安全问题
            privacy_result = self.privacy_checker.check_privacy(question)
            if not privacy_result.is_safe:
                return {
                    'is_valid': False,
                    'error_message': privacy_result.suggestion or '包含隐私信息',
                    'topic': None
                }

            # 2. 验证问题范围
            scope_result = self.scope_validator.validate_question(question, role)
            if not scope_result.get('is_valid', False):
                return {
                    'is_valid': False,
                    'error_message': scope_result.get('reason', '问题超出咨询范围'),
                    'topic': None
                }

            return {
                'is_valid': True,
                'topic': scope_result.get('topic', '未分类'),
                'error_message': None
            }

        except Exception as e:
            logging.error(f"验证问题时发生错误: {str(e)}")
            return {
                'is_valid': False,
                'error_message': '验证过程发生错误',
                'topic': None
            }