import os
import json
import logging
from typing import Dict, List, Any, Optional

from ollama import Client
from config.settings import LLM_SERVER, MODEL_CONFIG, PROJECT_ROOT

class QuestionGenerator:
    """基于问题分析结果生成后续提问的模块"""

    def __init__(self):
        """初始化QuestionGenerator"""
        self.client = Client(host=f"http://{LLM_SERVER['host']}:{LLM_SERVER['port']}")
        self.prompt_path = os.path.join(PROJECT_ROOT, "config", "prompts", "question_generator_prompt.txt")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def generate(self, analysis_result: Dict[str, Any]) -> str:
        """基于问题分析结果生成后续提问。

        Args:
            analysis_result: 问题分析结果，包含problem和missing_info字段

        Returns:
            str: 生成的提问内容，包含开场白、问题和结束语

        Raises:
            ValueError: 如果输入格式不正确或LLM返回的结果格式不正确
        """
        # 验证输入
        self._validate_input(analysis_result)
        
        # 读取提示词
        with open(self.prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            
        # 准备输入数据
        total_questions = len(analysis_result["missing_info"]["critical"]) + len(analysis_result["missing_info"]["optional"])
        input_data = {
            "problem": analysis_result["problem"],
            "missing_info": analysis_result["missing_info"],
            "total_questions": total_questions
        }
            
        # 调用LLM生成提问
        response = self.client.chat(
            model=MODEL_CONFIG['model'],
            messages=[
                {
                    "role": "system",
                    "content": prompt_template
                },
                {
                    "role": "user",
                    "content": f"基于以下问题分析结果生成提问：\n{json.dumps(input_data, ensure_ascii=False, indent=2)}"
                }
            ],
            stream=False
        )
        
        if not response or not response.get("message", {}).get("content"):
            raise ValueError("Empty response from LLM")
            
        content = response["message"]["content"]
        self.logger.debug(f"Question generation response: {content}")
        print(content)
        return content.strip()


    def _validate_input(self, analysis_result: Dict[str, Any]) -> None:
        """验证输入数据的格式是否正确。

        Args:
            analysis_result: 问题分析结果

        Raises:
            ValueError: 如果输入格式不正确
        """
        required_fields = ["problem", "missing_info"]
        for field in required_fields:
            if field not in analysis_result:
                raise ValueError(f"Missing required field in analysis_result: {field}")
                
        missing_info = analysis_result["missing_info"]
        if not isinstance(missing_info, dict):
            raise ValueError("missing_info must be a dictionary")
            
        required_missing_info_fields = ["critical", "optional"]
        for field in required_missing_info_fields:
            if field not in missing_info:
                raise ValueError(f"Missing required field in missing_info: {field}")
            if not isinstance(missing_info[field], list):
                raise ValueError(f"Field {field} in missing_info must be a list")

    def _validate_result(self, result: Dict[str, Any]) -> None:
        """验证生成的提问结果格式是否正确。

        Args:
            result: 生成的提问结果

        Raises:
            ValueError: 如果结果格式不正确
        """
        # 验证顶层字段
        required_fields = {
            "introduction": str,
            "questions": dict,
            "closing": str
        }
        
        for field, field_type in required_fields.items():
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(result[field], field_type):
                raise ValueError(f"Invalid type for field {field}")
                
        # 验证questions字段
        questions = result["questions"]
        required_questions_fields = {
            "format": str,
            "content": list,
            "priority": list
        }
        
        for field, field_type in required_questions_fields.items():
            if field not in questions:
                raise ValueError(f"Missing required field in questions: {field}")
            if not isinstance(questions[field], field_type):
                raise ValueError(f"Invalid type for questions.{field}")
                
        # 验证format的值
        if questions["format"] not in ["list", "direct"]:
            raise ValueError("questions.format must be 'list' or 'direct'")
            
        # 验证content和priority的长度匹配
        if len(questions["content"]) != len(questions["priority"]):
            raise ValueError("questions.content and questions.priority must have the same length")
            
        # 验证priority的值
        valid_priorities = ["high", "medium"]
        for priority in questions["priority"]:
            if priority not in valid_priorities:
                raise ValueError(f"Invalid priority value: {priority}")
                
        # 验证format与问题数量的匹配
        if questions["format"] == "direct" and len(questions["content"]) > 3:
            raise ValueError("Format 'direct' can only be used when there are 3 or fewer questions")
        if questions["format"] == "list" and len(questions["content"]) <= 3:
            raise ValueError("Format 'list' should be used when there are more than 3 questions")
