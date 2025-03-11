# AI心理咨询助手

这是一个基于Python实现的AI心理咨询助手系统，能够提供自动化的心理咨询服务。

## 功能特点

- 智能对话管理
- 动态问卷生成
- 个性化解决方案
- 专业知识库支持
- 自动报告生成

## 系统架构

系统由以下核心模块组成：

- `DialogueManager`: 对话管理器，负责管理对话流程
- `StateTracker`: 状态追踪器，负责追踪会话状态
- `KnowledgeBase`: 知识库，提供专业知识支持
- `QuestionnaireGenerator`: 问卷生成器，生成个性化问卷
- `SolutionGenerator`: 解决方案生成器，提供个性化解决方案
- `ReportGenerator`: 报告生成器，生成咨询报告

## 安装说明

1. 克隆项目：
```bash
git clone [项目地址]
cd zServer
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 启动服务器：
```bash
python app.py
```

2. API接口：
- `/chat`: 处理用户对话请求
- `/generate_report`: 生成咨询报告

## 开发指南

### 目录结构
```
zServer/
├── app.py              # 主应用程序
├── requirements.txt    # 项目依赖
├── README.md          # 项目文档
├── modules/           # 核心模块
│   ├── dialogue_manager.py
│   ├── state_tracker.py
│   ├── knowledge_base.py
│   ├── questionnaire_generator.py
│   ├── solution_generator.py
│   └── report_generator.py
├── config/            # 配置文件
│   └── config.py
├── utils/            # 工具函数
│   └── helpers.py
└── tests/            # 测试文件
```

### 开发规范

- 使用 Python 3.8 或以上版本
- 遵循 PEP 8 编码规范
- 使用 type hints 进行类型注解
- 编写单元测试确保代码质量

## 测试

运行测试：
```bash
pytest tests/
```

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 许可证

[GNU General Public License v3.0](LICENSE)
