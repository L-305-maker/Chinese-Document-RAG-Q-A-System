# Chinese Document Q&A RAG System
面向中文文档的模块化知识问答系统，支持PDF、Word、TXT、Markdown等多种文件格式

## 1、项目简介：
本项目旨在构建一个面向中文文档的RAG问答系统

传统大语言模型在回答用户问题时易出现以下问题：
- 无法访问用户的个人文档或本地文件
- 回答缺少依据
- 幻觉问题高发
- 对长文本问题、多文档问题的解决能力偏弱
而本项目通过Retrieval-Augmented Generation技术。将外部的知识库与大语言模型结合起来，是系统能够从本地文档中检索得到相关内容，再基于相关内容进行生成，大大提高生成的可靠程度

## 2、当前功能：
目前已经实现了以下功能：
- PDF、Word、TXT、Markdown等多种文件的加载
- 文档清洗，文档递归切分，并构建相应的metadata
- 支持Chroma向量数据库存储
- 支持mebedding模型封装
- query router、query normalize、基于LLM的query rewrite
- dense retrieval和multi-query retrieval
- CrossEncoder rerank的实现
- 构建更加专业的prompt
- 调用LLM进行回答
- 返回检索的信息来源

## 3、项目结构以及核心模块说明
详细项目结构以及相关文件细节已经存储在`docs/`下的`PROJECT_STRUCTURE.md`文件里

## 4、安装环境：
4.1 克隆项目
```bash
 git clone https://github.com/L-305-maker/Chinese-Document-RAG-Q-A-System.git
cd Chinese-Document-Q-A-System
```
4.2 创建虚拟环境
```bash
conda create -n rag-system python=3.10
conda activate rag-system
```
4.3 安装依赖
```bash
pip install requirement.txt
```

## 5、配置环境变量：
建议在根目录下创建.env文件：
```text
LLM_API_KEY = your_api_key
LLM_BASE_URL = https://api.deepseek.com
LLM_MODEL = deepseek-chat

EMBEDDING_MODEL = your_embedding_model_name
RERANK_MODEL = your_rerank_model_name

CHROMA_PERSIST_DIR = ./data/chorma_ab
CHROMA_COLLECTION_NAME = chinese_document_rag
```

## 6、使用指南：
相关使用指南存储在`docs/`下的`OPERATION.md`文件里

## 7、后续计划：
### 7.1 检索增强：
- 实现 BM25 Retriever
- 实现 Dense + BM25 Hybrid Retrieval
- 实现 score normalization
- 实现 weighted score fusion
- 比较 Dense、BM25、Hybrid、Hybrid+Rerank

### 7.2 评估体系的实现：
计划新增`evaluation/`模块：
```text
evaluation/
├── eval_dataset.json
├── evaluate_retrieval.py
├── evaluate_generation.py
├── run_eval.py
└── eval_report.md
```
支持下列指标：`Hit@K`、`Recall@K`、`MRR`、`Keyword Recall`、`Answer Relavance`、`Faithfulness`、`Context Precision`、`Latency`、`Token Cost`

### 7.3 应用层封装：
计划新增FastAPI接口：
```text
POST /ingest
POST /chat
GET /health
```
计划新增Streamlit前端：
- 文档上传
- 知识库构建
- 问答交互
- 检索结果展示
- 引用来源展示
- rerank score 展示

### 7.4 Agentic RAG:
后续还计划探索Agentic RAG。