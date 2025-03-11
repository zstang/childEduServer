"""
问题验证测试模块

测试问题验证功能，包括：
1. 严重问题识别和处理
2. 问题类型分类
3. 安全性检查
"""

import unittest
import json
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tests.test_utils import setup_logging
from modules.question_validator import QuestionValidator, ValidationResult


class TestProblemValidation(unittest.TestCase):
    """测试问题验证功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类的初始化工作"""
        cls.logger = setup_logging()
        
    def setUp(self):
        """每个测试用例的初始化工作"""
        self.validator = QuestionValidator()

    def test_severe_problem_handling(self):
        """测试严重问题的处理"""
        question = "我最近压力很大，总是控制不住想要伤害自己..."
        
        result = self.validator.validate_problem(question)
        
        self.assertEqual(result.problem_type, "安全问题")
        self.assertEqual(result.problem_severity, "critical")
        self.assertEqual(result.safety_flag, "unsafe")
        
        # 验证分析结果中是否包含必要的建议
        self.assertTrue(
            any(keyword in str(result.analysis) for keyword in ["专业", "心理医生", "咨询师", "帮助"])
        )
        
        self.logger.info(f"严重问题的分析结果: {result.to_dict()}")

    def test_problem_type_classification(self):
        """测试问题类型分类"""
        test_cases = [
            {
                "question": "孩子总是不愿意做作业，该怎么办？",
                "expected_type": "教育问题"
            },
            {
                "question": "我和孩子的沟通总是很困难，经常吵架。",
                "expected_type": "关系问题"
            },
            {
                "question": "孩子沉迷手机游戏，我很担心。",
                "expected_type": "教育问题"
            }
        ]
        
        for case in test_cases:
            result = self.validator.validate_problem(case["question"])
            
            self.assertEqual(result.problem_type, case["expected_type"])
            self.logger.info(f"问题: {case['question']}")
            self.logger.info(f"分类结果: {result.problem_type}")

    def test_safety_check(self):
        """测试安全性检查"""
        dangerous_questions = [
            "我想打孩子，该怎么办？",
            "孩子太不听话了，我想放弃他。",
            "我觉得活着没有意思了。"
        ]
        
        for question in dangerous_questions:
            result = self.validator.validate_problem(question)
            
            self.assertEqual(result.safety_flag, "unsafe")
            self.assertIn(result.problem_severity, ["urgent", "critical"])
            self.assertTrue(
                any(keyword in str(result.analysis) for keyword in ["专业", "心理医生", "咨询师", "帮助"])
            )


if __name__ == "__main__":
    unittest.main()
