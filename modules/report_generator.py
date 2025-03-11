"""
报告生成器模块

这个模块负责生成咨询报告，包括：
1. 收集会话信息
2. 整理分析结果
3. 生成解决方案总结
4. 输出报告文件

主要功能：
- 信息收集
- 报告生成
- 报告存储
"""

import json
import logging
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from ollama import Client

from config.settings import LLM_SERVER, MODEL_CONFIG, PROJECT_ROOT

class ReportGenerator:
    def __init__(self):
        """初始化报告生成器"""
        self.client = Client(
            host=f"http://{LLM_SERVER['host']}:{LLM_SERVER['port']}"
        )
        self.output_dir = Path("reports")  # 报告输出目录
        self.prompt_path = os.path.join(PROJECT_ROOT, "config", "prompts", "report_generation_prompt.txt")
        self.step_prompts = {
            "user_complaint": os.path.join(PROJECT_ROOT, "config", "prompts", "report_steps", "1_user_complaint.txt"),
            "problem_analysis": os.path.join(PROJECT_ROOT, "config", "prompts", "report_steps", "2_problem_analysis.txt"),
            "solution": os.path.join(PROJECT_ROOT, "config", "prompts", "report_steps", "3_solution.txt"),
            #"complete_report": os.path.join(PROJECT_ROOT, "config", "prompts", "report_steps", "complete_report.txt")
        }
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self._ensure_output_dir()
        self._load_prompts()
        self.last_llm_response = None
    
    def _load_prompts(self) -> None:
        """加载所有提示词"""
        # 加载主提示词
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"Report generation prompt not found at {self.prompt_path}")
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            self.report_prompt = f.read()
        
        # 加载步骤提示词
        self.step_prompts_content = {}
        for step, path in self.step_prompts.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Step prompt not found at {path}")
            with open(path, "r", encoding="utf-8") as f:
                self.step_prompts_content[step] = f.read()

    def _ensure_output_dir(self) -> None:
        """确保输出目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, session_id: str, session_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        生成咨询报告。该方法会分三步生成报告内容，然后整合成最终报告。
        
        参数：
            session_id (str): 会话ID
            session_history (List[Dict[str, str]]): 会话历史记录
            
        返回：
            Dict[str, Any]: 生成的报告
        """
        try:
            # 格式化会话历史
            consultation_text = self._format_conversation(session_history)
            
            # 分步生成内容
            self.logger.info("Step 1: Generating user complaint section...")
            user_complaint = self.generate_user_complaint(consultation_text)
            
            self.logger.info("Step 2: Generating problem analysis section...")
            problem_analysis = self.generate_problem_analysis(consultation_text)
            
            self.logger.info("Step 3: Generating solution section...")
            solution = self.generate_solution(consultation_text)
            
            # 整合所有部分
            sections = {
                "用户主诉": "\n".join(user_complaint['main_issues']),
                "用户问题与诉求": "\n".join(user_complaint['requests']),
                "问题分析": "\n".join(problem_analysis['problem_nature']),
                "权威解释": "\n".join(problem_analysis['explanations']),
                "解决方案": "\n".join(solution['recommendations']),
                "结语": solution['conclusion']
            }
            
            # 使用提示词优化整合后的内容
            prompt_path = os.path.join(PROJECT_ROOT, "config", "prompts", "report_generation_prompt.txt")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_sys = f.read()
            
            # 准备优化提示
            sections_text = "\n\n".join([f"{k}：\n{v}" for k, v in sections.items()])
            print(sections_text)
            
            
            # 调用LLM优化内容
            response = self.client.chat(
                model=MODEL_CONFIG['model'],
                messages=[
                    {
                        "role": "system",
                        "content": prompt_sys
                    },
                    {
                        "role": "user",
                        "content": sections_text
                    }
                ],
                stream=False
            )
            
            if not response:
                raise ValueError("Empty response from LLM")
                
            print(type(response))
            print(response)
            content = response['message']["content"]
            
            # 解析优化后的内容
            optimized_sections = {}
            current_section = None
            current_content = []
            
            content = content.replace('###', '')
            print('---->')
            print(content)
            '''
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.endswith('：') and line[:-1] in sections.keys():
                    if current_section:
                        optimized_sections[current_section] = '\n'.join(current_content)
                        current_content = []
                    current_section = line[:-1]
                    self.logger.debug(f"Found new section: {line[:-1]}")
                else:
                    current_content.append(line)
                    
            if current_section and current_content:
                optimized_sections[current_section] = '\n'.join(current_content)
            '''
            [part1, part2] = content.split(' 结语')
            optimized_sections['结语'] = part2
            [part1, part2] = part1.split(' 解决方案')
            optimized_sections['解决方案'] = part2
            [part1, part2] = part1.split(' 权威解释')
            optimized_sections['权威解释'] = part2
            [part1, part2] = part1.split(' 问题分析')
            optimized_sections['问题分析'] = part2
            [part1, part2] = part1.split(' 用户问题与诉求')
            optimized_sections['用户问题与诉求'] = part2
            [part1, part2] = part1.split(' 用户主诉')
            optimized_sections['用户主诉'] = part2

            
            final_report = [
                {'用户主诉': optimized_sections['用户主诉']},
                {'用户问题与诉求': optimized_sections['用户问题与诉求']},
                {'问题分析': optimized_sections['问题分析']},
                {'权威解释': optimized_sections['权威解释']},
                {'解决方案': optimized_sections['解决方案']},
                {'结语': optimized_sections['结语']},
            ]
            # 构建最终报告
            report = {
                "report_id": f"report_{session_id}",
                "generated_at": datetime.now().isoformat(),
                "sections": final_report
            }
            
            print(json.dumps(report, indent=4, ensure_ascii=False))
            # 保存报告
            self._save_report(session_id, report)
            
            self.logger.info(f"Successfully generated report: report_{session_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            raise
    
    def _format_conversation(self, session_history: List[Dict[str, str]]) -> str:
        """格式化会话历史"""
        formatted_conversation = []
        for message in session_history:
            role = "用户" if message.get("role") == "user" else "系统"
            content = message.get("content", "")
            formatted_conversation.append(f"{role}: {content}")
        return "\n".join(formatted_conversation)
    

    def _save_report(self, session_id: str, report: Dict[str, Any]) -> None:
        """
        保存报告到文件系统
        
        参数：
            session_id (str): 会话ID
            report (Dict[str, Any]): 报告内容
        """
        report_path = self.output_dir / f"report_{session_id}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        self.logger.info(f"报告已保存到: {report_path}")
    
    def generate_user_complaint(self, consultation_text: str) -> dict:
        """Generate the user complaint section of the report.
        
        Args:
            consultation_text: The consultation text to analyze
            
        Returns:
            A dictionary containing the parsed user complaint section
        """
        with open(self.step_prompts["user_complaint"], 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            
        response = self.client.chat(
            model=MODEL_CONFIG['model'],
            messages=[
                {
                    "role": "system",
                    "content": prompt_template
                },
                {
                    "role": "user",
                    "content": f"对话历史:\n{consultation_text}\n\n请总结用户的主要问题和诉求，并以分点形式列出。每个要点请单独成行，以'-'或'*'开头。请特别注意是否存在睡眠相关的问题。"
                }
            ],
            stream=False
        )
        
        if not response or not response.get("message", {}).get("content"):
            raise ValueError("Empty response from LLM")
            
        content = response["message"]["content"]
        self.logger.debug(f"User complaint response: {content}")
        
        # Parse the response
        sections = {
            'main_issues': [],
            'requests': []
        }
        current_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            self.logger.debug(f"Processing line: '{line}'")
                
            if any(header in line for header in ['主要问题：', '用户主诉：']):
                current_section = 'main_issues'
                self.logger.debug("Found main issues section")
            elif any(header in line for header in ['诉求：', '用户问题与诉求：']):
                current_section = 'requests'
                self.logger.debug("Found requests section")
            elif current_section and (line.startswith('-') or line.startswith('*')):
                # Remove the bullet point and clean the line
                cleaned_line = line[1:].strip()
                if cleaned_line:
                    sections[current_section].append(cleaned_line)
                    self.logger.debug(f"Added to {current_section}: {cleaned_line}")
        
        # Log the final sections
        self.logger.debug(f"Final sections: {sections}")
        
        # Validate sections
        if not sections['main_issues'] or not sections['requests']:
            self.logger.error(f"Failed to parse sections. Content: {content}")
            raise ValueError("Failed to parse user complaint sections")
            
        return sections
    
    def generate_problem_analysis(self, consultation_text: str) -> dict:
        """Generate the problem analysis section of the report.
        
        Args:
            consultation_text: The consultation text to analyze
            
        Returns:
            A dictionary containing the parsed problem analysis section
        """
        with open(self.step_prompts["problem_analysis"], 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            
        response = self.client.chat(
            model=MODEL_CONFIG['model'],
            messages=[
                {
                    "role": "system",
                    "content": prompt_template
                },
                {
                    "role": "user",
                    "content": f"对话历史:\n{consultation_text}\n\n请分析问题性质和提供专业解释，并以分点形式列出。每个要点请单独成行，以'-'或'*'开头。"
                }
            ],
            stream=False
        )
        
        if not response or not response.get("message", {}).get("content"):
            raise ValueError("Empty response from LLM")
            
        content = response["message"]["content"]
        self.logger.debug(f"Problem analysis response: {content}")
        
        # Parse the response
        sections = {
            'problem_nature': [],
            'explanations': []
        }
        current_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            self.logger.debug(f"Processing line: '{line}'")
                
            if '问题性质：' in line:
                current_section = 'problem_nature'
                self.logger.debug("Found problem nature section")
            elif '专业解释：' in line:
                current_section = 'explanations'
                self.logger.debug("Found explanations section")
            elif current_section and (line.startswith('-') or line.startswith('*')):
                # Remove the bullet point and clean the line
                cleaned_line = line[1:].strip()
                if cleaned_line:
                    sections[current_section].append(cleaned_line)
                    self.logger.debug(f"Added to {current_section}: {cleaned_line}")
        
        # Log the final sections
        self.logger.debug(f"Final sections: {sections}")
        
        # Validate sections
        if not sections['problem_nature'] or not sections['explanations']:
            self.logger.error(f"Failed to parse sections. Content: {content}")
            raise ValueError("Failed to parse problem analysis sections")
            
        return sections
    
    def generate_solution(self, consultation_text: str) -> dict:
        """Generate the solution section of the report.
        
        Args:
            consultation_text: The consultation text to analyze
            
        Returns:
            A dictionary containing the parsed solution section
        """
        with open(self.step_prompts["solution"], 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            
        response = self.client.chat(
            model=MODEL_CONFIG['model'],
            messages=[
                {
                    "role": "system",
                    "content": prompt_template
                },
                {
                    "role": "user",
                    "content": f"对话历史:\n{consultation_text}\n\n请提供具体的建议措施和总结，并以分点形式列出。每个要点请单独成行，以'-'或'*'开头。建议措施中请务必包含改善睡眠的建议。"
                }
            ],
            stream=False
        )
        
        if not response or not response.get("message", {}).get("content"):
            raise ValueError("Empty response from LLM")
            
        content = response["message"]["content"]
        self.logger.debug(f"Solution response: {content}")
        
        # Parse the response
        sections = {
            'recommendations': [],
            'conclusion': None
        }
        current_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            self.logger.debug(f"Processing line: '{line}'")
                
            if '建议措施：' in line:
                current_section = 'recommendations'
                self.logger.debug("Found recommendations section")
            elif '总结：' in line:
                current_section = 'conclusion'
                self.logger.debug("Found conclusion section")
            elif current_section == 'recommendations' and (line.startswith('-') or line.startswith('*')):
                # Remove the bullet point and clean the line
                cleaned_line = line[1:].strip()
                if cleaned_line:
                    sections['recommendations'].append(cleaned_line)
                    self.logger.debug(f"Added recommendation: {cleaned_line}")
            elif current_section == 'conclusion':
                if sections['conclusion'] is None:
                    sections['conclusion'] = line
                else:
                    sections['conclusion'] += '\n' + line
                self.logger.debug(f"Added to conclusion: {line}")
        
        # Log the final sections
        self.logger.debug(f"Final sections: {sections}")
        
        # Validate sections
        if not sections['recommendations'] or not sections['conclusion']:
            self.logger.error(f"Failed to parse sections. Content: {content}")
            raise ValueError("Failed to parse solution sections")
              
        return sections
    