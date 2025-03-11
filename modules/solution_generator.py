"""
解决方案生成器模块

这个模块负责生成个性化的心理咨询解决方案，包括：
1. 基于问题分析生成解决方案
2. 根据用户特点定制方案
3. 生成具体的执行步骤
4. 提供辅助资源
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from ollama import Client

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from config.settings import LLM_SERVER, MODEL_CONFIG
from modules.exceptions import SolutionGeneratorError, PromptFileError, ResponseGenerationError
from modules.boundary_detector import BoundaryDetector

class SolutionGenerator:
    def __init__(self):
        """初始化解决方案生成器"""
        self.client = Client(
            host=f"http://{LLM_SERVER['host']}:{LLM_SERVER['port']}"
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.boundary_detector = BoundaryDetector()

    def _read_prompt_file(self, file_name: str) -> str:
        """
        读取提示词文件

        参数:
            file_name (str): 提示词文件名

        返回:
            str: 提示词内容
        """
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise PromptFileError(f"读取提示词文件失败：{str(e)}")

    def generate_response(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成回答

        参数:
            question (str): 当前问题
            context (Optional[Dict[str, Any]]): 上下文信息，包含主题和状态等

        返回:
            Dict[str, Any]: 包含响应内容和元数据的字典
        """
        try:
            # 提取用户边界
            boundaries = []
            #try:
            #    boundaries = self.boundary_detector.extract_boundaries(history)
            #except Exception as e:
            #    self.logger.warning("边界提取失败，将继续生成响应: %s", str(e))
            #    boundaries = []

            # 读取咨询提示词
            prompt = self._read_prompt_file("config/prompts/counseling_prompt.txt")
            # 构建对话历史
            history = [{
                        "role": "system",
                        "content": prompt
                    }]
            print('context-> ', context)
            # 处理上下文历史记录
            if context is not None and 'history' in context:
                try:
                    # 验证历史记录格式
                    for entry in context['history']:
                        if not isinstance(entry, dict) or 'role' not in entry or 'content' not in entry:
                            raise ValueError("无效的历史记录格式")
                    history.extend(context['history'])
                except (TypeError, ValueError) as e:
                    self.logger.error("处理历史记录失败: %s", str(e))
                    raise ResponseGenerationError(f"处理历史记录失败：{str(e)}")

            # 调用LLM生成响应
            response = self.client.chat(
                model=MODEL_CONFIG['model'],
                messages=history +
                    [{
                        "role": "user",
                        "content": f"问题：{question}\n\n"
                    }
                ],
                stream=False
            )
            
            # 验证响应是否符合用户边界
            solution = response['message']['content']
            #if boundaries and not self.boundary_detector.validate_solution(solution, boundaries):
            #    self.logger.warning("生成的响应不符合用户边界，将重新生成")
            #    # TODO: 实现重新生成逻辑
            
            return {
                'message': {
                    'content': solution
                },
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'model': MODEL_CONFIG['model']
                }
            }

        except Exception as e:
            self.logger.error("生成响应失败: %s", str(e))
            raise ResponseGenerationError(f"生成响应失败：{str(e)}")