import json
import os
from typing import Dict, Any
from enum import Enum
import logging
from ollama import Client

from config.settings import LLM_SERVER, MODEL_CONFIG, PROJECT_ROOT

class FeedbackType(Enum):
    """用户反馈类型"""
    NEGATIVE = "NEGATIVE"      # 否定
    UNCERTAIN = "UNCERTAIN"    # 不确定
    NEED_TIME = "NEED_TIME"   # 需要时间验证
    POSITIVE = "POSITIVE"      # 肯定
    LOST_CONFIDENCE = "LOST_CONFIDENCE"  # 失去信心

class FeedbackAnalysisError(Exception):
    pass

class FeedbackAnalyzer:
    """分析用户对解决方案的反馈并生成回应"""

    def __init__(self):
        """初始化反馈分析器"""
        self.client = Client(
            host=f"http://{LLM_SERVER['host']}:{LLM_SERVER['port']}"
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # 读取提示词
        prompt_path = os.path.join(PROJECT_ROOT, "config", "prompts", "feedback_analyzer_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt = f.read()

    def analyze(self, feedback: str, solution: str) -> Dict[str, str]:
        """
        分析用户反馈并生成回应

        Args:
            feedback: 用户的反馈内容
            solution: 系统提供的解决方案

        Returns:
            Dict[str, str]: 包含反馈类型和回应内容的字典
            {
                "type": "反馈类型",
                "response": "回应内容"
            }
        """
        try:
            # 验证输入
            self._validate_input(feedback, solution)
            print('-> ', solution)
            print('-> ', feedback)
            # 检查反馈长度
            if len(feedback) > 5000:  # 设置一个合理的长度限制
                raise FeedbackAnalysisError("Feedback is too long")
            
            # 准备提示词
            messages = [
                {
                    "role": "system",
                    "content": self.prompt
                },
                {
                    "role": "user",
                    "content": f"用户反馈: {feedback}\n解决方案: {solution}"
                }
            ]
            
            # 调用LLM
            response = self.client.chat(
                model=MODEL_CONFIG['model'],
                messages=messages,
                stream=False
            )
            content = response['message']['content']
            print(content)
            # 解析响应
            result = self._parse_llm_response(content)
            print(result)
            # 验证结果
            self._validate_result(result)
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to analyze feedback: {str(e)}")
            raise

    def _validate_input(self, feedback: str, solution: str) -> None:
        """
        验证输入数据的有效性

        Args:
            feedback: 用户的反馈内容
            solution: 系统提供的解决方案

        Raises:
            FeedbackAnalysisError: 当输入数据无效时抛出
        """
        if not isinstance(feedback, str) or not feedback.strip():
            raise FeedbackAnalysisError("Feedback cannot be empty")
        if not isinstance(solution, str) or not solution.strip():
            raise FeedbackAnalysisError("Solution cannot be empty")
            
        # 检查特殊字符，允许常见的空白字符
        allowed_control_chars = {ord('\n'), ord('\r'), ord('\t')}
        if any(ord(c) < 32 and ord(c) not in allowed_control_chars for c in feedback):
            raise FeedbackAnalysisError("Feedback contains invalid characters")
        if any(ord(c) < 32 and ord(c) not in allowed_control_chars for c in solution):
            raise FeedbackAnalysisError("Solution contains invalid characters")

    def _validate_result(self, result: Dict[str, Any]) -> None:
        """
        验证分析结果的有效性

        Args:
            result: LLM返回的分析结果

        Raises:
            FeedbackAnalysisError: 当结果格式无效时抛出
        """
        if not isinstance(result, dict):
            raise FeedbackAnalysisError("Invalid result format: not a dictionary")
        
        required_fields = ['type', 'response']
        for field in required_fields:
            if field not in result:
                raise FeedbackAnalysisError(f"Missing required field: {field}")
            
        if not isinstance(result['type'], str):
            raise FeedbackAnalysisError("Invalid type format: not a string")
            
        if not isinstance(result['response'], str):
            raise FeedbackAnalysisError("Invalid response format: not a string")
            
        valid_types = [member.value for member in FeedbackType]
        if result['type'] not in valid_types:
            raise FeedbackAnalysisError(f"Invalid feedback type: {result['type']}")

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        解析LLM响应内容，处理可能的markdown代码块

        Args:
            content (str): LLM响应内容

        Returns:
            Dict[str, Any]: 解析后的JSON对象

        Raises:
            FeedbackAnalysisError: JSON解析失败时抛出
        """
        # 如果响应被包裹在markdown代码块中，提取实际的JSON内容
        if content.startswith('```json\n'):
            content = content.split('```json\n')[1].split('```')[0]
        elif content.startswith('```\n'):
            content = content.split('```\n')[1].split('```')[0]
        
        try:
            result = json.loads(content)
            
            # 清理可能的额外字符，但保留下划线
            if isinstance(result.get('type'), str):
                # 只保留字母和下划线字符
                result['type'] = ''.join(c for c in result['type'] if c.isalpha() or c == '_')
                result['type'] = result['type'].upper()  # 确保全大写
                
            return result
        except json.JSONDecodeError as e:
            # 尝试从普通文本中提取类型和回应
            if 'type' in content and 'response' in content:
                lines = content.split('\n')
                type_line = next((line for line in lines if 'type' in line.lower()), None)
                response_line = next((line for line in lines if 'response' in line.lower()), None)
                
                if type_line and response_line:
                    # 只保留字母和下划线字符
                    type_value = ''.join(c for c in type_line.split(':')[1] if c.isalpha() or c == '_')
                    type_value = type_value.upper()  # 确保全大写
                    response_value = response_line.split(':')[1].strip().strip('"')
                    return {
                        'type': type_value,
                        'response': response_value
                    }
            
            raise FeedbackAnalysisError(f"Failed to parse LLM response: {str(e)}")
