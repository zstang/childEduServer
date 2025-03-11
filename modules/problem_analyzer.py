import os
import json
import logging
from typing import Dict, List, Any, Optional

from ollama import Client
from config.settings import LLM_SERVER, MODEL_CONFIG, PROJECT_ROOT

class ProblemAnalyzer:
    """分析用户问题并提取相关信息的模块"""

    def __init__(self):
        """初始化ProblemAnalyzer"""
        self.client = Client(host=f"http://{LLM_SERVER['host']}:{LLM_SERVER['port']}")
        self.prompt_path = os.path.join(PROJECT_ROOT, "config", "prompts", "problem_analyzer_prompt.txt")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def analyze(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """分析用户的咨询内容，提取问题相关信息。

        Args:
            messages: 用户的咨询对话历史

        Returns:
            Dict[str, Any]: 包含分析结果的字典，格式如下：
            {
                "problem": str,
                "provided_info": {
                    "age": str,
                    "occupation": str,
                    "duration": str,
                    "frequency": str,
                    "symptoms": List[str],
                    "context": List[str]
                },
                "coping_history": {
                    "attempts": List[str],
                    "effectiveness": List[str],
                    "current_status": List[str]
                },
                "user_expectation": {
                    "solution_type": str,
                    "improvement_goal": str,
                    "timeline": str
                },
                "missing_info": {
                    "critical": List[str],
                    "optional": List[str]
                }
            }

        Raises:
            ValueError: 如果LLM返回的结果格式不正确
        """
        # 格式化对话历史
        conversation_text = self._format_conversation(messages)
        
        # 读取提示词
        with open(self.prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            
        # 调用LLM进行分析
        response = self.client.chat(
            model=MODEL_CONFIG['model'],
            messages=[
                {
                    "role": "system",
                    "content": prompt_template
                },
                {
                    "role": "user",
                    "content": f"对话历史:\n{conversation_text}\n\n请分析用户问题并提取相关信息。"
                }
            ],
            stream=False
        )
        
        if not response or not response.get("message", {}).get("content"):
            raise ValueError("Empty response from LLM")
            
        content = response["message"]["content"]
        self.logger.debug(f"Problem analysis response: {content}")
        
        # 解析JSON响应
        try:
            # 找到JSON内容的开始和结束
            start = content.find('{')
            end = content.rfind('}') + 1
            if start == -1 or end == 0:
                raise ValueError("No valid JSON found in response")
            
            json_str = content[start:end]
            result = json.loads(json_str)
            
            # 验证结果格式
            self._validate_result(result)
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Response content: {content}")
            raise ValueError("Invalid JSON format in LLM response")
            
    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """格式化对话历史。

        Args:
            messages: 对话历史消息列表

        Returns:
            str: 格式化后的对话文本
        """
        formatted_conversation = []
        for message in messages:
            role = "用户" if message["role"] == "user" else "咨询师"
            content = message["content"]
            formatted_conversation.append(f"{role}: {content}")
        return "\n".join(formatted_conversation)
        
    def _validate_result(self, result: Dict[str, Any]) -> None:
        """验证分析结果的格式是否正确。

        Args:
            result: 待验证的分析结果

        Raises:
            ValueError: 如果结果格式不正确
        """
        required_fields = {
            "problem": str,
            "provided_info": dict,
            "coping_history": dict,
            "user_expectation": dict,
            "missing_info": dict
        }
        
        provided_info_fields = {
            "age": (str, type(None)),
            "occupation": (str, type(None)),
            "duration": (str, type(None)),
            "frequency": (str, type(None)),
            "symptoms": list,
            "context": list
        }
        
        coping_history_fields = {
            "attempts": list,
            "effectiveness": list,
            "current_status": list
        }
        
        user_expectation_fields = {
            "solution_type": (str, type(None)),
            "improvement_goal": (str, type(None)),
            "timeline": (str, type(None))
        }
        
        missing_info_fields = {
            "critical": list,
            "optional": list
        }
        
        # 验证顶层字段
        for field, field_type in required_fields.items():
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(result[field], field_type):
                raise ValueError(f"Invalid type for field {field}")
                
        # 验证provided_info字段
        for field, field_type in provided_info_fields.items():
            if field not in result["provided_info"]:
                raise ValueError(f"Missing field in provided_info: {field}")
            if isinstance(field_type, tuple):
                if not any(isinstance(result["provided_info"][field], t) for t in field_type):
                    raise ValueError(f"Invalid type for provided_info.{field}")
            elif not isinstance(result["provided_info"][field], field_type):
                raise ValueError(f"Invalid type for provided_info.{field}")
                
        # 验证coping_history字段
        for field, field_type in coping_history_fields.items():
            if field not in result["coping_history"]:
                raise ValueError(f"Missing field in coping_history: {field}")
            if not isinstance(result["coping_history"][field], field_type):
                raise ValueError(f"Invalid type for coping_history.{field}")
                
        # 验证user_expectation字段
        for field, field_type in user_expectation_fields.items():
            if field not in result["user_expectation"]:
                raise ValueError(f"Missing field in user_expectation: {field}")
            if isinstance(field_type, tuple):
                if not any(isinstance(result["user_expectation"][field], t) for t in field_type):
                    raise ValueError(f"Invalid type for user_expectation.{field}")
            elif not isinstance(result["user_expectation"][field], field_type):
                raise ValueError(f"Invalid type for user_expectation.{field}")
                
        # 验证solution_type的值
        solution_type = result["user_expectation"]["solution_type"]
        if solution_type is not None and solution_type not in ["long_term", "immediate"]:
            raise ValueError("solution_type must be 'long_term', 'immediate' or null")
                
        # 验证missing_info字段
        for field, field_type in missing_info_fields.items():
            if field not in result["missing_info"]:
                raise ValueError(f"Missing field in missing_info: {field}")
            if not isinstance(result["missing_info"][field], field_type):
                raise ValueError(f"Invalid type for missing_info.{field}")
