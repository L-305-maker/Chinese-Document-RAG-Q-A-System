# Project Structure

本文档说明当前项目的目录结构、核心模块职责，以及中文文档 RAG 问答系统的主要数据流。

## 目录总览

```text
Chinese Document RAG Q&A System/
|-- config/
|   |-- setting.py
|
|-- data/
|   |-- raw_rag/
|   |   |-- 01_RAG基础...20_LongRAG与RankRAG...md
|   |
|   |-- vector_db/
|       |-- chroma.sqlite3
|       |-- <chroma-collection-id>/
|
|-- docs/
|   |-- OPERATION.md
|   |-- PROJECT_STRUCTURE.md
|
|-- src/
|   |-- build_answer/
|   |   |-- answer_builder.py
|   |
|   |-- embedding/
|   |   |-- embedding_model.py
|   |
|   |-- ingestion/
|   |   |-- cleaner.py
|   |   |-- deduplicator.py
|   |   |-- file_ingestor.py
|   |   |-- file_type.py
|   |   |-- ingest_main.py
|   |   |-- loaders.py
|   |   |-- metadata_builder.py
|   |   |-- splitter.py
|   |
|   |-- llm/
|   |   |-- __init__.py
|   |   |-- llm_client.py
|   |
|   |-- query_processing/
|   |   |-- QA_main.py
|   |   |-- base_query.py
|   |   |-- normalize.py
|   |   |-- process_query.py
|   |   |-- query_rewriter.py
|   |   |-- query_router.py
|   |
|   |-- rerank/
|   |   |-- __init__.py
|   |   |-- reranker.py
|   |
|   |-- retrieval/
|   |   |-- retriever.py
|   |
|   |-- validation/
|   |   |-- prompt_validator.py
|   |
|   |-- vectorstore/
|   |   |-- chroma_store.py
|   |
|   |-- document.py
|
|-- utils/
|-- .env
|-- .gitignore
|-- README.md
|-- requirements.txt
```

说明：

- `__pycache__/` 是 Python 运行时生成的缓存目录，不属于源码结构说明重点。
- `data/vector_db/` 是 Chroma 向量库持久化目录，属于运行产物。

## 顶层文件与目录

| 路径 | 作用 |
| --- | --- |
| `config/` | 项目配置读取入口，当前负责从 `.env` 加载大模型相关配置。 |
| `data/raw_rag/` | 原始知识文档目录，当前存放 20 篇 RAG 主题 Markdown 文档。 |
| `data/vector_db/` | Chroma 本地向量数据库目录，保存已入库的 chunk、索引和元数据。 |
| `docs/` | 项目文档目录。 |
| `src/` | 核心业务代码，包含文档入库、向量检索、问题处理、答案构建和 LLM 调用。 |
| `utils/` | 通用工具目录，目前为空。 |
| `.env` | 本地环境变量文件，存放 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 等敏感配置。 |
| `requirements.txt` | Python 依赖列表。 |

## 核心模块

### `config/`

- `setting.py`：使用 `python-dotenv` 加载 `.env`，并通过 `settings` 暴露：
  - `LLM_API_KEY`
  - `LLM_BASE_URL`
  - `LLM_MODEL`，默认值为 `deepseek-chat`
  - `VECTOR_DB_PATH`
  - `COLLECTION_NAME`
  - `EMBEDDING_MODEL`
  - `RERANK_ENABLED`
  - `RERANK_ALLOW_DOWNLOAD`
  - `RERANK_MODEL`
  - `RERANK_CANDIDATE_MULTIPLIER`
  - `RERANK_MAX_CANDIDATES`
  - `MULTI_QUERY_MAX_QUERIES`

### `src/document.py`

定义项目内部统一使用的 `Document` 数据结构：

- `page_content`：文档正文或切分后的 chunk 内容。
- `metadata`：来源、文件路径、页码、chunk 编号、hash 等元数据。

该结构在入库、向量存储、检索前的数据转换中反复使用。

### `src/ingestion/`

文档入库流水线模块，负责把本地文件转换为可检索的向量数据。

| 文件 | 作用 |
| --- | --- |
| `file_type.py` | 根据文件后缀识别文件类型，支持 `.pdf`、`.txt`、`.md`、`.docx`、`.doc`。 |
| `loaders.py` | 定义不同文件格式的 Loader，将 PDF、Word、TXT、Markdown 读取为 `Document`。 |
| `cleaner.py` | 清洗文本，统一换行和空格，并过滤过短内容。 |
| `splitter.py` | 使用 `RecursiveCharacterTextSplitter` 将文档切分为 chunk。 |
| `metadata_builder.py` | 为 chunk 补充 `chunk_index`、`file_type`、`ingested_at`、`file_path` 等元数据。 |
| `deduplicator.py` | 基于正文 hash 去重，并写入 `content_hash`、`chunk_id`。 |
| `file_ingestor.py` | 入库编排器，串联文件类型识别、加载、清洗、切分、元数据构建、去重和写入向量库。 |
| `ingest_main.py` | 入库脚本入口，默认将 `./data/raw_rag` 写入 `./data/vector_db` 的 `rag_docs` 集合。 |

入库主流程：

```text
原始文件
  -> detect_file_type()
  -> LoaderFactory.get_loader().load()
  -> DocumentCleaner.clean()
  -> DocumentSplitter.split_documents()
  -> MetadataBuilder.add_metadata()
  -> DocumentDeduplicator.deduplicator()
  -> ChromaVectorStore.add_documents()
```

### `src/embedding/`

- `embedding_model.py`：创建 HuggingFace Embedding 模型。
  - 当前模型：`BAAI/bge-small-zh-v1.5`
  - 如果检测到 CUDA，则使用 GPU，否则使用 CPU。
  - `normalize_embeddings=True`，便于向量相似度检索。

### `src/vectorstore/`

- `chroma_store.py`：封装 Chroma 向量数据库。
  - 默认持久化目录：`./data/vector_db`
  - 默认集合名：`rag_docs`
  - 提供 `add_documents()`、`similarity_search()`、`similarity_search_with_score()`。

该模块是入库链路和检索链路之间的桥梁。

### `src/validation/`

- `prompt_validator.py`：查询文本校验器。
  - 检查空输入。
  - 检查最大长度。
  - 粗略识别乱码、不可打印字符、高比例符号、异常重复字符等情况。
  - 输出标准化后的 `normalized_prompt`。

### `src/retrieval/`

- `retriever.py`：向量检索模块。
  - `VectorRetriever.retrieve()`：执行 dense 单查询检索。
  - `VectorRetriever.multi_retrieve()`：执行多 query 检索、合并结果并基于 chunk id 去重。
  - `VectorRetriever.retrieve_with_route()`：读取 `query_router` 的路由结果，决定使用 dense、multi-query 或 fallback 检索。
  - 返回结构包含 `status`、`query`、`documents`。
  - 每个检索结果包含 `content`、`metadata`、`score`。
  - 当 `need_rerank=True` 时，会先召回更多候选 chunk，再调用 rerank 模块重排。

### `src/rerank/`

- `reranker.py`：重排模块。
  - 默认使用 `sentence-transformers` 的 `CrossEncoder`。
  - 默认模型由 `RERANK_MODEL` 控制，当前默认值为 `BAAI/bge-reranker-base`。
  - 如果 rerank 模型不可用或推理失败，会降级返回原始 dense 排序结果，避免整条问答链路失败。
  - 重排后会为文档补充 `original_score` 和 `rerank_score`。

### `src/query_processing/`

查询预处理与路由模块，负责把用户问题变成更适合检索和回答的结构化信息。

| 文件 | 作用 |
| --- | --- |
| `base_query.py` | 定义 `QueryState`，用于表达查询处理过程中的状态字段。 |
| `normalize.py` | 查询标准化和质量检查，包括全角转半角、中英文间加空格、删除噪声符号、语言检测、长度检查等。 |
| `query_rewriter.py` | 使用 LLM 将用户问题改写为更适合检索的查询，并抽取 `search_queries`、`keywords`、`sub_questions`。失败时使用 fallback。 |
| `query_router.py` | 根据查询内容和改写结果判断问题类型，并决定是否检索、检索模式、`top_k`、是否重排、是否使用子问题。 |
| `process_query.py` | 查询处理总入口，串联标准化、改写和路由。 |
| `QA_main.py` | 问答总入口，串联查询处理、检索、答案 Prompt 构建和 LLM 调用。 |

查询处理主流程：

```text
用户问题
  -> normalized_query_quality()
  -> rewrite_query()
  -> route_query()
  -> query_info
```

当前路由支持的问题类型：

- `chitchat`：闲聊，不进入知识库检索。
- `fact_qa`：事实问答，默认使用向量检索。
- `summary`：总结类问题，提高 `top_k`。
- `compare`：对比类问题，倾向多查询检索。
- `how_to`：方法或步骤类问题，倾向多查询检索。
- `multi_hop`：多跳问题，使用子问题或多 query。
- `out_of_scope`：不适合基于知识库回答的问题。

### `src/build_answer/`

- `answer_builder.py`：根据用户问题和检索结果构建最终回答 Prompt。
  - 将每条资料组织为编号上下文。
  - 保留来源、页码和正文内容。
  - 要求 LLM 严格基于参考资料回答，并在资料不足时说明无法回答。

### `src/llm/`

- `llm_client.py`：封装 OpenAI 兼容接口的大模型调用。
  - 使用 `settings` 中的 API Key、Base URL 和模型名。
  - `LLMclient.generate()` 负责发送 Chat Completions 请求。
  - `call_llm()` 提供全局复用的简化调用入口。
- `__init__.py`：包初始化文件。

## 端到端问答流程

```text
QA(prompt)
  -> process_query(prompt)
     -> normalize
     -> rewrite
     -> route
  -> 如果不需要检索：直接返回路由说明
  -> ChromaVectorStore()
  -> VectorRetriever.retrieve_with_route(query_info)
     -> dense 或 multi_query 检索
     -> 可选 rerank
  -> build_answer_prompt(question, documents)
  -> call_llm(answer_prompt)
  -> 返回 answer、query_info、sources
```

返回结果主要字段：

| 字段 | 含义 |
| --- | --- |
| `status` | 本次问答状态，通常为 `success` 或 `error`。 |
| `answer` | LLM 生成的最终答案，或错误/无需检索说明。 |
| `query_info` | 标准化、改写、路由后的查询信息。 |
| `sources` | 检索命中的文档 chunk 列表。 |

## 数据目录说明

### `data/raw_rag/`

当前知识库原始文档目录，包含 RAG 相关 Markdown 文档，例如：

- `01_RAG基础：为什么大模型需要外部知识.md`
- `02_稠密检索DPR：从BM25到向量召回.md`
- `17_GraphRAG：从文本片段到知识图谱.md`
- `20_LongRAG与RankRAG：长上下文和排序生成一体化.md`

这些文件会被 `src/ingestion/ingest_main.py` 批量读取并写入向量库。

### `data/vector_db/`

Chroma 持久化目录，包含：

- `chroma.sqlite3`
- 向量索引二进制文件，如 `data_level0.bin`、`header.bin`、`length.bin`、`link_lists.bin`

该目录通常由入库脚本生成，不建议手动编辑其中内容。

## 依赖概览

项目依赖记录在 `requirements.txt`，主要包括：

- `torch`
- `pypdf`
- `chromadb`
- `langchain-text-splitters`
- `langchain-chroma`
- `langchain-huggingface`
- `sentence-transformers`
- `python-docx`
- `openai`
- `python-dotenv`

## 推荐开发入口

常用入口如下：

```text
入库入口：src/ingestion/ingest_main.py
问答入口：src/query_processing/QA_main.py
测试入口：test.py
配置入口：config/setting.py
```

当新增能力时，可以按下面的方向扩展：

- 新文件格式支持：扩展 `src/ingestion/file_type.py` 和 `src/ingestion/loaders.py`。
- 新检索策略：扩展 `src/retrieval/retriever.py` 和 `src/query_processing/query_router.py`。
- 新重排策略：扩展 `src/rerank/reranker.py`，或在 `VectorRetriever` 中注入新的 reranker。
- 新向量库实现：在 `src/vectorstore/` 下增加新的 store 封装。
- 新 LLM 提供商：扩展 `src/llm/llm_client.py` 或新增 provider 适配层。
- 答案格式优化：调整 `src/build_answer/answer_builder.py`。
