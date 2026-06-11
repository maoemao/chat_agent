import os
import re
import json
import httpx
from pathlib import Path
from typing import List, Optional, Dict
from app.config.settings import settings
from app.utils.logger import rag_logger

class RAGService:
    def __init__(self):
        rag_logger.info("Initializing RAGService")
        self.documents: List[Dict[str, str]] = []
        self.embeddings: Dict[str, List[float]] = {}
        self.api_key = settings.VOLC_API_KEY
        self.base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
        self.embedding_model = "doubao-embedding-vision"
        self.chat_model = "ark-code-latest"
        self._load_documents()
        rag_logger.info("RAGService initialized")
    
    async def _get_embedding(self, text: str) -> List[float]:
        """使用火山引擎Embedding API获取文本向量"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.embedding_model,
                "input": text
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("data") and len(result["data"]) > 0:
                    return result["data"][0]["embedding"]
                else:
                    rag_logger.error(f"Embedding API returned empty data: {result}")
                    return []
            else:
                rag_logger.error(f"Embedding API error: {response.status_code} - {response.text[:200]}")
                return []
        except Exception as e:
            rag_logger.error(f"Failed to get embedding: {str(e)}", exc_info=True)
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _load_documents(self):
        docs_path = settings.rag_docs_path
        rag_logger.debug(f"Loading documents from: {docs_path}")
        
        if not docs_path.exists():
            rag_logger.info(f"Documents path not found, creating: {docs_path}")
            docs_path.mkdir(parents=True, exist_ok=True)
        
        try:
            md_files = list(docs_path.glob("*.md"))
            rag_logger.info(f"Found {len(md_files)} markdown file(s)")
            
            for file_path in md_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    self.documents.append({
                        'title': file_path.stem,
                        'content': content,
                        'path': str(file_path)
                    })
                    rag_logger.debug(f"Loaded document: {file_path.name}")
                except Exception as e:
                    rag_logger.error(f"Failed to read {file_path}: {str(e)}")
            
            # 预计算文档embedding (使用同步方式，避免在__init__中使用asyncio.run)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在事件循环中，创建新任务
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, self._precompute_embeddings())
                else:
                    asyncio.run(self._precompute_embeddings())
            except Exception as e:
                rag_logger.error(f"Failed to precompute embeddings: {str(e)}")
            
            rag_logger.info(f"Successfully loaded {len(self.documents)} document(s)")
            
        except Exception as e:
            rag_logger.error(f"Failed to load documents: {str(e)}", exc_info=True)
    
    def _split_by_headers(self, content: str) -> List[str]:
        """按Markdown标题分块，保留完整章节"""
        import re
        # 按 ## 或 ### 标题分割
        pattern = r'(?=\n##\s+)'
        chunks = re.split(pattern, content)
        
        result = []
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) >= 10:
                result.append(chunk)

        return result
    
    async def _precompute_embeddings(self):
        """预计算所有文档的embedding"""
        if not self.api_key:
            rag_logger.warning("No API key available, skipping embedding precomputation")
            return
        
        rag_logger.info("Precomputing document embeddings...")
        
        for doc in self.documents:
            # 按Markdown标题分块
            chunks = self._split_by_headers(doc['content'])
            doc_embeddings = []
            
            for chunk in chunks:
                if len(chunk.strip()) < 10:
                    continue
                
                embedding = await self._get_embedding(chunk.strip())
                if embedding:
                    doc_embeddings.append({
                        'text': chunk.strip(),
                        'embedding': embedding
                    })
            
            doc['embeddings'] = doc_embeddings
            rag_logger.debug(f"Computed {len(doc_embeddings)} embeddings for {doc['title']}")
        
        rag_logger.info("Document embeddings precomputation completed")
    
    async def _find_relevant_chunks(self, query: str, top_k: int = 5) -> List[str]:
        if not self.documents:
            return []
        
        # 获取查询的embedding
        query_embedding = await self._get_embedding(query)
        
        if query_embedding:
            # 使用向量相似度搜索
            scored_chunks = []
            
            for doc in self.documents:
                if 'embeddings' in doc:
                    for chunk in doc['embeddings']:
                        similarity = self._cosine_similarity(query_embedding, chunk['embedding'])
                        scored_chunks.append((similarity, chunk['text']))
            
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            
            # 如果最高相似度太低，降级到关键词匹配
            if not scored_chunks or scored_chunks[0][0] < 0.3:
                rag_logger.warning(f"Embedding similarity too low ({scored_chunks[0][0] if scored_chunks else 0}), falling back to keyword matching")
                return self._keyword_match(query, top_k)
            
            # 返回相似度大于0.3的chunk，至少返回1个
            result = [chunk for score, chunk in scored_chunks if score > 0.3][:top_k]
            if not result and scored_chunks:
                result = [scored_chunks[0][1]]
            return result
        else:
            # 降级到关键词匹配
            rag_logger.warning("Embedding not available, falling back to keyword matching")
            return self._keyword_match(query, top_k)
    
    def _keyword_match(self, query: str, top_k: int = 5) -> List[str]:
        """关键词匹配（降级方案）"""
        query_words = set(re.findall(r'\w+', query.lower()))
        scored_chunks = []
        
        for doc in self.documents:
            chunks = self._split_by_headers(doc['content'])
            for chunk in chunks:
                if len(chunk.strip()) < 10:
                    continue
                
                content_words = set(re.findall(r'\w+', chunk.lower()))
                if not query_words:
                    continue
                
                matching_words = query_words & content_words
                score = len(matching_words) / len(query_words)
                
                if score > 0:
                    scored_chunks.append((score, chunk.strip()))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:top_k]]
    
    async def _generate_answer(self, question: str, context_chunks: List[str]) -> str:
        """使用火山引擎Chat API基于检索内容生成回答"""
        if not self.api_key:
            # 没有API Key，直接返回拼接的上下文
            context = "\n\n".join(context_chunks)
            return f"基于文档内容：\n\n{context}"
        
        try:
            context = "\n\n".join(context_chunks)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            system_prompt = """你是一个基于文档的问答助手。请根据提供的文档内容，回答用户的问题。
要求：
1. 只基于提供的文档内容回答，不要添加文档外的信息
2. 回答要简洁、准确、有条理
3. 如果文档中没有相关信息，明确告知用户
4. 使用中文回答"""
            
            user_prompt = f"""文档内容：
{context}

用户问题：{question}

请根据以上文档内容回答问题。"""
            
            data = {
                "model": self.chat_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 2048,
                "temperature": 0.3
            }
            
            rag_logger.debug(f"Sending RAG generation request to {self.base_url}/chat/completions")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("choices") and len(result["choices"]) > 0:
                    answer = result["choices"][0]["message"]["content"]
                    rag_logger.info("RAG answer generated successfully")
                    return answer
                else:
                    rag_logger.error(f"Chat API returned empty choices: {result}")
                    # 降级返回上下文
                    return f"基于文档内容：\n\n{context}"
            else:
                rag_logger.error(f"Chat API error: {response.status_code} - {response.text[:200]}")
                # 降级返回上下文
                return f"基于文档内容：\n\n{context}"
                
        except Exception as e:
            rag_logger.error(f"Failed to generate answer: {str(e)}", exc_info=True)
            # 降级返回上下文
            context = "\n\n".join(context_chunks)
            return f"基于文档内容：\n\n{context}"
    
    async def query(self, question: str) -> Optional[str]:
        rag_logger.info(f"Processing RAG query: {question[:100]}")
        
        if not self.documents:
            rag_logger.warning("No documents loaded")
            return "RAG服务尚未初始化，请确保已添加文档到 data/documents 目录"
        
        try:
            # 1. 检索相关文档片段
            relevant_chunks = await self._find_relevant_chunks(question)
            
            if not relevant_chunks:
                rag_logger.info("No relevant chunks found")
                return f"抱歉，我在文档中没有找到与\"{question}\"相关的内容。\n\n当前加载了 {len(self.documents)} 个文档，你可以尝试用其他关键词提问。"
            
            rag_logger.info(f"Found {len(relevant_chunks)} relevant chunks")
            
            # 2. 使用LLM生成回答
            answer = await self._generate_answer(question, relevant_chunks)
            
            return answer
            
        except Exception as e:
            rag_logger.error(f"RAG query failed: {str(e)}", exc_info=True)
            return f"查询失败: {str(e)}"
    
    async def add_document(self, file_path: str) -> bool:
        rag_logger.info(f"Adding document: {file_path}")
        
        try:
            path = Path(file_path)
            if not path.exists():
                rag_logger.error(f"File not found: {file_path}")
                return False
            
            content = path.read_text(encoding='utf-8')
            doc = {
                'title': path.stem,
                'content': content,
                'path': str(path)
            }
            
            # 计算新文档的embedding
            if self.api_key:
                paragraphs = content.split('\n\n')
                doc_embeddings = []
                
                for paragraph in paragraphs:
                    if len(paragraph.strip()) < 10:
                        continue
                    
                    embedding = await self._get_embedding(paragraph.strip())
                    if embedding:
                        doc_embeddings.append({
                            'text': paragraph.strip(),
                            'embedding': embedding
                        })
                
                doc['embeddings'] = doc_embeddings
            
            self.documents.append(doc)
            
            rag_logger.info(f"Document added successfully: {file_path}")
            return True
        except Exception as e:
            rag_logger.error(f"Failed to add document {file_path}: {str(e)}", exc_info=True)
            return False
