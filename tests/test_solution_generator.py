"""
测试解决方案生成器模块

这个模块包含了对 SolutionGenerator 类的全面测试，包括：
1. 基本功能测试
2. 边界条件测试
3. 用户边界处理测试
4. 多轮对话测试
"""

import os
import sys
import unittest
import json
from datetime import datetime
import logging

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from modules.solution_generator import SolutionGenerator
from config.settings import MODEL_CONFIG, UserRole


class TestSolutionGenerator(unittest.TestCase):
    """测试解决方案生成器"""
    
    @classmethod
    def setUpClass(cls):
        """测试类的初始化工作"""
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        cls.logger = logging.getLogger(__name__)
        
    def setUp(self):
        """每个测试用例的初始化工作"""
        self.generator = SolutionGenerator()
        
    def test_generate_response_basic(self):
        """测试基本的解决方案生成"""
        question = "我最近感到很焦虑，该怎么办？"
        context = {
            'history': [
                {"role": "user", "content": "我最近感到很焦虑"},
                {"role": "assistant", "content": "能具体说说是什么情况让你感到焦虑吗？"}
            ],
            'topic': '焦虑情绪',
            'state': 'solution_generation'
        }
        
        response = self.generator.generate_response(question, context)
        
        # 验证响应格式
        self.assertIsInstance(response, dict)
        self.assertIn('message', response)
        self.assertIn('content', response['message'])
        self.assertTrue(response['message']['content'])
        
    def test_generate_response_no_context(self):
        """测试没有上下文的解决方案生成"""
        question = "我该如何改善睡眠质量？"
        
        response = self.generator.generate_response(question)
        
        # 验证响应格式
        self.assertIsInstance(response, dict)
        self.assertIn('message', response)
        self.assertIn('content', response['message'])
        self.assertTrue(response['message']['content'])
        
    def test_generate_response_with_empty_history(self):
        """测试空历史记录的解决方案生成"""
        question = "如何控制情绪？"
        context = {
            'history': [],
            'topic': '情绪管理',
            'state': 'solution_generation'
        }
        
        response = self.generator.generate_response(question, context)
        
        # 验证响应格式
        self.assertIsInstance(response, dict)
        self.assertIn('message', response)
        self.assertIn('content', response['message'])
        self.assertTrue(response['message']['content'])
        
    def test_generate_response_error_handling(self):
        """测试错误处理"""
        question = "test_error"
        context = {
            'history': [{"invalid_format": "this should cause an error"}],
            'topic': 'test',
            'state': 'error'
        }
        
        with self.assertRaises(Exception):
            self.generator.generate_response(question, context)
            
    def test_read_prompt_file(self):
        """测试提示词文件读取"""
        try:
            prompt = self.generator._read_prompt_file("config/prompts/counseling_prompt.txt")
            self.assertIsInstance(prompt, str)
            self.assertTrue(prompt)
        except PromptFileError:
            self.fail("提示词文件读取失败")


def main():
    unittest.main(verbosity=2)


if __name__ == "__main__":
    main()
