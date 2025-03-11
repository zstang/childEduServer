import gradio as gr
import requests
import json
from datetime import datetime

# API endpoint configuration
API_BASE_URL = "http://localhost:15003"

class ConsultationTester:
    def __init__(self):
        self.session_id = None
        self.chat_history = []
    
    def send_message(self, message):
        """Send a message to the consultation system"""
        payload = {
            "message": message,
        }
        
        # 如果已有会话ID，添加到请求中
        if self.session_id:
            payload["session_id"] = self.session_id
        
        response = requests.post(f"{API_BASE_URL}/api/chat", json=payload)
        data = response.json()
        
        # 如果是新会话，保存会话ID
        if not self.session_id and 'session_id' in data:
            self.session_id = data['session_id']
            self.chat_history = [("系统", "您好，我是知蒙教育AI咨询师。请描述您遇到的问题。")]
        
        # Update chat history
        self.chat_history.append(("用户", message))
        if 'response' in data:
            self.chat_history.append(("系统", data['response']))
        
        # Format chat history for display
        formatted_history = "\n".join([f"{role}: {msg}" for role, msg in self.chat_history])
        
        # Get session status for display
        status_info = []
        if self.session_id:
            status = self.get_session_status()
            try:
                status_data = json.loads(status)
                status_info.extend([
                    f"会话ID: {self.session_id}",
                    f"当前状态: {status_data.get('state', 'unknown')}",
                    f"当前主题: {status_data.get('current_topic', 'unknown')}"
                ])
                
                # 显示用户边界信息
                if 'boundaries' in status_data:
                    status_info.append("\n用户边界:")
                    for boundary in status_data['boundaries']:
                        status_info.append(
                            f"- {boundary['category']}: {boundary['content']}"
                        )
            except json.JSONDecodeError:
                status_info = [f"会话ID: {self.session_id}", "状态获取失败"]
        else:
            status_info = ["等待开始新对话..."]
        
        return formatted_history, "\n".join(status_info)
    
    def get_session_status(self):
        """Get current session status"""
        if not self.session_id:
            return "未开始对话"
        
        response = requests.get(f"{API_BASE_URL}/api/session/status",
                              params={"session_id": self.session_id})
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    
    def get_session_history(self):
        """Get session chat history"""
        if not self.session_id:
            return "未开始对话"
        
        response = requests.get(f"{API_BASE_URL}/api/session/history",
                              params={"session_id": self.session_id})
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    
    def generate_report(self):
        """Generate session report"""
        if not self.session_id:
            return "未开始对话，无法生成报告"
        
        response = requests.post(f"{API_BASE_URL}/api/session/generate_report",
                               json={"session_id": self.session_id})
        print(response.json())
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    
    def end_session(self):
        """End current session"""
        if not self.session_id:
            return "没有活跃的会话"
        
        response = requests.post(f"{API_BASE_URL}/api/session/end",
                               json={"session_id": self.session_id})
        self.session_id = None
        self.chat_history = []
        return "会话已结束"

def create_interface():
    """Create the Gradio interface"""
    tester = ConsultationTester()
    
    with gr.Blocks(title="心理咨询系统测试界面") as interface:
        gr.Markdown("# 心理咨询系统测试界面")
        
        with gr.Row():
            with gr.Column(scale=2):
                chat_history = gr.Textbox(label="对话历史", lines=10)
                message_box = gr.Textbox(label="输入消息", lines=2)
                send_btn = gr.Button("发送")
            
            with gr.Column(scale=1):
                session_info = gr.Textbox(label="会话信息", lines=10)
                status_btn = gr.Button("刷新状态")
                history_btn = gr.Button("查看历史")
                report_btn = gr.Button("生成报告")
                end_btn = gr.Button("结束会话")
        
        # Event handlers
        send_btn.click(
            fn=tester.send_message,
            inputs=message_box,
            outputs=[chat_history, session_info]
        )
        status_btn.click(
            fn=tester.get_session_status,
            inputs=[],
            outputs=session_info
        )
        history_btn.click(
            fn=tester.get_session_history,
            inputs=[],
            outputs=session_info
        )
        report_btn.click(
            fn=tester.generate_report,
            inputs=[],
            outputs=session_info
        )
        end_btn.click(
            fn=tester.end_session,
            inputs=[],
            outputs=session_info
        )
    
    return interface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(share=True, server_port=7893)
