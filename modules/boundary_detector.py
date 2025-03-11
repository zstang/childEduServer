"""
用户边界检测器模块

这个模块负责检测和管理用户在对话中设定的各种边界，包括：
1. 目标边界（客观边界）
2. 主观边界（个人偏好）
3. 解决方案边界（可接受的方案范围）

主要功能：
- 从对话中提取用户边界
- 验证解决方案是否符合边界
- 管理和更新边界信息
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from ollama import Client

from config.settings import LLM_SERVER, MODEL_CONFIG, PROJECT_ROOT
from modules.exceptions import BoundaryExtractionError

class BoundaryDetector:
    def __init__(self):
        """初始化边界检测器"""
        self.client = Client(
            host=f"http://{LLM_SERVER['host']}:{LLM_SERVER['port']}"
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """
        格式化对话历史记录

        参数:
            history (List[Dict[str, str]]): 对话历史记录

        返回:
            str: 格式化后的对话历史字符串
        """
        return "\n".join([
            f"{'用户' if msg['role'] == 'user' else '助手'}: {msg['content']}"
            for msg in history
        ])

    def _validate_boundary_structure(self, boundary: Dict[str, Any]) -> bool:
        """
        验证边界结构是否完整

        参数:
            boundary (Dict[str, Any]): 边界字典

        返回:
            bool: 结构是否有效
        """
        required_fields = ["category", "type", "content", "flexibility", "source"]
        return all(field in boundary for field in required_fields)

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        解析LLM响应内容，处理可能的markdown代码块

        参数:
            content (str): LLM响应内容

        返回:
            Dict[str, Any]: 解析后的JSON对象

        异常:
            json.JSONDecodeError: JSON解析失败时抛出
        """
        # 如果响应被包裹在markdown代码块中，提取实际的JSON内容
        if content.startswith('```json\n'):
            content = content.split('```json\n')[1].split('```')[0]
        elif content.startswith('```\n'):
            content = content.split('```\n')[1].split('```')[0]
            
        return json.loads(content)

    def extract_boundaries(self, history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        从对话历史中提取用户边界

        参数:
            history (List[Dict[str, str]]): 对话历史记录

        返回:
            List[Dict[str, Any]]: 提取出的用户边界列表

        异常:
            BoundaryExtractionError: 边界提取失败时抛出
        """
        try:
            # 读取边界提取提示词
            prompt_path = os.path.join(PROJECT_ROOT, "config", "prompts", "boundary_detector_prompt.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()

            # 格式化对话历史
            formatted_history = self._format_conversation_history(history)

            # 调用LLM提取边界
            response = self.client.chat(
                model=MODEL_CONFIG['model'],
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": f"对话历史:\n{formatted_history}\n\n请提取用户边界。"
                    }
                ],
                stream=False
            )

            try:
                # 解析LLM响应
                result = self._parse_llm_response(response['message']['content'])
                
                # 提取所有边界
                boundaries = []
                if "boundaries" in result:
                    for category in ["objective_boundaries", "subjective_boundaries", "solution_boundaries"]:
                        if category in result["boundaries"]:
                            for boundary in result["boundaries"][category]:
                                boundary_obj = {
                                    "category": category,
                                    "type": boundary["type"],
                                    "content": boundary["content"],
                                    "flexibility": boundary["flexibility"],
                                    "source": boundary["source"]
                                }
                                if self._validate_boundary_structure(boundary_obj):
                                    boundaries.append(boundary_obj)
                                else:
                                    self.logger.warning("跳过结构不完整的边界: %s", json.dumps(boundary_obj))
                
                if not boundaries:
                    self.logger.warning("未能提取到任何有效边界")
                else:
                    self.logger.info("成功提取用户边界，共 %d 个", len(boundaries))
                    
                    # 验证是否提取到了不同类型的边界
                    boundary_categories = set(b["category"] for b in boundaries)
                    if len(boundary_categories) >= 2:
                        self.logger.info("成功提取到多个类别的边界: %s", boundary_categories)
                    else:
                        self.logger.warning("仅提取到单一类别的边界: %s", boundary_categories)
                
                return boundaries
                
            except json.JSONDecodeError as e:
                self.logger.error("JSON解析错误: %s", str(e))
                self.logger.error("原始响应: %s", response['message']['content'])
                raise BoundaryExtractionError(f"边界提取失败：JSON解析错误 - {str(e)}")
                
        except Exception as e:
            self.logger.error("边界提取失败: %s", str(e))
            raise BoundaryExtractionError(f"边界提取失败：{str(e)}")

    def validate_solution(self, solution: str, boundaries: List[Dict[str, Any]]) -> bool:
        """
        验证解决方案是否符合用户边界

        参数:
            solution (str): 生成的解决方案
            boundaries (List[Dict[str, Any]]): 用户设定的边界

        返回:
            bool: 是否符合用户边界
        """
        try:
            # 读取验证提示词
            prompt_path = os.path.join(PROJECT_ROOT, "config", "prompts", "boundary_validation_prompt.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()

            # 调用LLM验证解决方案
            response = self.client.chat(
                model=MODEL_CONFIG['model'],
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": f"解决方案:\n{solution}\n\n用户边界:\n{json.dumps(boundaries, ensure_ascii=False, indent=2)}\n\n请验证解决方案是否符合用户边界。"
                    }
                ],
                stream=False
            )

            try:
                result = json.loads(response['message']['content'])
                return result.get("is_valid", False)
            except json.JSONDecodeError:
                self.logger.error("验证结果解析失败")
                return False

        except Exception as e:
            self.logger.error("边界验证失败: %s", str(e))
            return False
