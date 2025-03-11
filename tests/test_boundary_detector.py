"""
边界提取测试模块

测试BoundaryDetector的边界提取功能，包括：
1. 基本边界提取
2. 复杂场景边界提取
3. 边界分类和灵活度评估
"""

import unittest
import json
import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.boundary_detector import BoundaryDetector

class TestBoundaryExtraction(unittest.TestCase):
    """测试边界提取功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类的初始化工作"""
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
        
    def setUp(self):
        """每个测试用例的初始化工作"""
        self.detector = BoundaryDetector()

    def test_conversation_history_formatting(self):
        """测试对话历史格式化"""
        history = [
            {"role": "user", "content": "问题1"},
            {"role": "assistant", "content": "回答1"},
            {"role": "user", "content": "问题2"}
        ]
        formatted = self.detector._format_conversation_history(history)
        expected = "用户: 问题1\n助手: 回答1\n用户: 问题2"
        self.assertEqual(formatted, expected)
        self.logger.info("对话历史格式化测试通过")

    def test_boundary_extraction_basic(self):
        """测试基本的边界提取功能"""
        history = [
            {"role": "user", "content": "我是一名单亲妈妈，平时要工作到很晚。"},
            {"role": "assistant", "content": "我理解您的情况，作为单亲妈妈确实不容易。"},
            {"role": "user", "content": "我觉得孩子的教育最重要的是培养兴趣，不想给他太大压力。"},
            {"role": "assistant", "content": "您说得对，保持适度的学习压力很重要。"},
            {"role": "user", "content": "之前试过请家教，但效果不好，以后不想再尝试了。"}
        ]
        
        boundaries = self.detector.extract_boundaries(history)
        self.assertIsInstance(boundaries, list)
        self.assertTrue(len(boundaries) > 0)
        
        # 验证边界结构
        for boundary in boundaries:
            self.assertTrue(self.detector._validate_boundary_structure(boundary))
            
        self.logger.info(f"提取到的边界: {json.dumps(boundaries, ensure_ascii=False, indent=2)}")

    def test_boundary_extraction_complex(self):
        """测试复杂场景的边界提取"""
        history = [
            {"role": "user", "content": "我每天都要工作12个小时，根本没时间陪孩子。"},
            {"role": "assistant", "content": "这确实是个很大的挑战。"},
            {"role": "user", "content": "我不想用惩罚的方式教育孩子，觉得这样不好。"},
            {"role": "assistant", "content": "您说得对，正面引导更有效。"},
            {"role": "user", "content": "我们家住在乡下，周围没有什么教育资源。"},
            {"role": "assistant", "content": "了解，这确实会带来一些限制。"},
            {"role": "user", "content": "而且现在家里经济条件不太好，请不起补习老师。"}
        ]
        
        boundaries = self.detector.extract_boundaries(history)
        self.assertTrue(len(boundaries) > 0)
        
        # 验证是否提取到了不同类型的边界
        boundary_categories = set(b["category"] for b in boundaries)
        self.assertTrue(len(boundary_categories) >= 2)
        
        # 验证边界结构
        for boundary in boundaries:
            self.assertTrue(self.detector._validate_boundary_structure(boundary))
        
        self.logger.info(f"复杂场景提取到的边界: {json.dumps(boundaries, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    unittest.main()
