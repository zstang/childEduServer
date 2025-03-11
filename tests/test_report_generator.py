"""
测试报告生成器模块
"""

import unittest
import os
import json
from datetime import datetime

from modules.report_generator import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        self.report_generator = ReportGenerator()
        self.test_session_id = "test_session_123"
        self.test_session_history = [
            {"role": "user", "content": "我最近总是感到焦虑"},
            {"role": "assistant", "content": "能具体描述一下你的焦虑表现吗？"},
            {"role": "user", "content": "工作压力大，晚上睡不着，容易紧张。最近项目deadline快到了，总是担心完不成任务，晚上躺在床上也会想工作的事情。白天注意力也不太集中，效率反而更低了。"}
        ]
    '''
    def test_format_conversation(self):
        """测试对话历史格式化功能"""
        result = self.report_generator._format_conversation(self.test_session_history)
        self.assertIsInstance(result, str)
        self.assertTrue(result)
        
        # 验证格式化后的内容包含所有对话
        for message in self.test_session_history:
            self.assertIn(message['content'], result)
            
        #print("\n对话历史格式化测试结果: ===============")
        #print(result)
    
    def test_generate_user_complaint(self):
        print("\n分步测试1：用户主诉测试结果: Begin")
        """测试用户主诉和问题诉求生成功能"""
        consultation_text = self.report_generator._format_conversation(self.test_session_history)
        result = self.report_generator.generate_user_complaint(consultation_text)
        
        # 检查返回值格式
        self.assertIsInstance(result, dict)
        self.assertIn('main_issues', result)
        self.assertIn('requests', result)
        
        main_issues = result['main_issues']
        requests = result['requests']
        
        # 检查主要问题
        self.assertTrue(len(main_issues) > 0, "应该至少有一个主要问题")
        self.assertTrue(any(
            any(sleep_word in issue for sleep_word in ["睡眠", "睡不着", "入睡"])
            for issue in main_issues
        ), "应该识别出睡眠相关问题")
        self.assertTrue(any("焦虑" in issue for issue in main_issues), "应该识别出焦虑问题")
        
        # 检查诉求
        self.assertTrue(len(requests) > 0, "应该至少有一个诉求")
        self.assertTrue(any(
            any(sleep_word in request for sleep_word in ["睡眠", "睡不着", "入睡"])
            for request in requests
        ), "应该包含改善睡眠相关的诉求")
        
        print("\n分步测试1：用户主诉测试结果:")
        print(f"用户主诉: {main_issues}")
        print(f"用户诉求: {requests}")
        print("\n分步测试1：用户主诉测试结果: End")
    
    def test_generate_problem_analysis(self):
        print("\n分步测试2：问题分析测试结果: Begin")
        """测试问题分析和专业解释生成功能"""
        consultation_text = self.report_generator._format_conversation(self.test_session_history)
        result = self.report_generator.generate_problem_analysis(consultation_text)
        
        # 验证结果结构
        self.assertIsInstance(result, dict)
        self.assertIn('problem_nature', result)
        self.assertIn('explanations', result)
        
        # 验证内容质量
        problem_nature = result['problem_nature']
        self.assertTrue(len(problem_nature) >= 2, "应该提供至少两个问题性质分析")
        
        explanations = result['explanations']
        self.assertTrue(len(explanations) >= 2, "应该提供至少两个专业解释")
        self.assertTrue(
            any("压力" in exp or "焦虑" in exp for exp in explanations),
            "专业解释应该涉及压力或焦虑相关内容"
        )
        
        print("\n分步测试2：问题分析测试结果:")
        print(f"问题分析: {problem_nature}")
        print(f"权威解释: {explanations}")
        print("\n分步测试2：问题分析测试结果: End")
    
    def test_generate_solution(self):
        print("\n分步测试3：解决方案测试结果: Begin")
        """测试解决方案和总结生成功能"""
        consultation_text = self.report_generator._format_conversation(self.test_session_history)
        result = self.report_generator.generate_solution(consultation_text)
        
        # 验证结果结构
        self.assertIsInstance(result, dict)
        self.assertIn('recommendations', result)
        self.assertIn('conclusion', result)
        
        # 验证内容质量
        recommendations = result['recommendations']
        self.assertTrue(len(recommendations) >= 3, "应该提供至少三个建议措施")
        self.assertTrue(
            any("睡眠" in rec or "休息" in rec for rec in recommendations),
            "建议措施应该包含睡眠或休息相关建议"
        )
        
        conclusion = result['conclusion']
        self.assertTrue(len(conclusion) >= 50, "总结内容应该足够详细")
        self.assertTrue(
            "压力" in conclusion or "焦虑" in conclusion,
            "总结应该提及压力或焦虑管理"
        )
        
        print("\n分步测试3：解决方案测试结果:")
        print(f"解决方案: {recommendations}")
        print(f"结语: {conclusion}")
        print("\n分步测试3：解决方案测试结果: End")
    '''

    def test_generate_complete_report(self):
        print("\n完整报告测试结果: Begin")
        """测试完整报告生成功能"""
        result = self.report_generator.generate(self.test_session_id, self.test_session_history)
        
        # 验证报告基本结构
        self.assertIsInstance(result, dict)
        self.assertIn('report_id', result)
        self.assertIn('generated_at', result)
        self.assertIn('sections', result)
        
        # 验证报告各部分内容
        sections = {} # {k:v for k,v in j.items() for j in result['sections']}
        for sec in result['sections']:
            for k,v in sec.items():
                sections[k] = v
        expected_sections = ['用户主诉', '用户问题与诉求', '问题分析', '权威解释', '解决方案', '结语']
        for section in expected_sections:
            self.assertIn(section, sections)
            self.assertTrue(sections[section], f"{section} 不应为空")
            self.assertTrue(len(sections[section]) >= 20, f"{section} 内容应该足够详细")
        
        # 验证报告ID格式
        self.assertEqual(result['report_id'], f'report_{self.test_session_id}')
        
        # 验证生成时间格式
        try:
            datetime.fromisoformat(result['generated_at'])
        except ValueError:
            self.fail("generated_at 格式不正确")
            
        print("\n完整报告测试结果: Begin")
        for section, content in sections.items():
            print(f"\n{section}:")
            print(content)
        print("\n完整报告测试结果: End")
            
 
        
if __name__ == '__main__':
    unittest.main()
