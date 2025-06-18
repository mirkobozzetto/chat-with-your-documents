# src/qa_manager.py
import re
from typing import Optional, List, Dict, Any
from langchain.chains import RetrievalQA
from src.vector_stores.base_vector_store import BaseVectorStoreManager
from src.document_selector import DocumentSelector
from src.agents import AgentManager


class QAManager:

    def __init__(self, llm, vector_store_manager: BaseVectorStoreManager,
                 document_selector: DocumentSelector, retrieval_k: int,
                 retrieval_fetch_k: int, retrieval_lambda_mult: float):
        self.llm = llm
        self.vector_store_manager = vector_store_manager
        self.document_selector = document_selector
        self.retrieval_k = retrieval_k
        self.retrieval_fetch_k = retrieval_fetch_k
        self.retrieval_lambda_mult = retrieval_lambda_mult
        self.qa_chain = None
        self.agent_manager = AgentManager()

    def create_qa_chain(self) -> None:
        print("🔗 Creating optimized QA chain...")

        vector_store = self.vector_store_manager.get_vector_store()
        if not vector_store:
            raise ValueError("Vector store not available")

        search_kwargs = {
            "k": self.retrieval_k,
            "fetch_k": self.retrieval_fetch_k,
            "lambda_mult": self.retrieval_lambda_mult
        }

        document_filter = self.document_selector.get_document_filter()
        if document_filter:
            search_kwargs["filter"] = document_filter
            print(f"🎯 Filtering results to document: {self.document_selector.get_selected_document()}")

        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )

        from langchain.prompts import PromptTemplate

        prompt_template = """Use the following context to answer the question accurately and comprehensively. 
Respond in the same language as the question.

Context:
{context}

Question: {question}

Instructions:
- Analyze the full context to understand relationships between different sections
- Cite specific passages when they support your answer
- If the context lacks sufficient information, state this clearly
- Provide thorough explanations for complex topics
- Maintain accuracy to the source material

Answer:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=False,
            chain_type_kwargs={"prompt": PROMPT}
        )

        print("✅ QA chain ready")

    def ask_question(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Process a document first.")

        print(f"\n❓ Question: {question}")

        selected_document = self.document_selector.get_selected_document()
        if self.document_selector.has_selected_document():
            print(f"📖 Querying document: {selected_document}")

            agent_config = self.agent_manager.get_agent_for_document(selected_document)
            if agent_config and agent_config.is_active:
                print(f"🤖 Using {agent_config.agent_type.value} agent")

        print("🤔 Thinking...")

        enhanced_query = self._build_enhanced_query_with_agent(question, chat_history, selected_document)

        # Check if question mentions specific chapter and apply additional filtering
        chapter_filter = self._extract_chapter_filter(question)
        if chapter_filter:
            print(f"🔍 Detected chapter query: {chapter_filter}")
            result = self._query_with_chapter_filter(enhanced_query, chapter_filter)
        else:
            result = self.qa_chain.invoke({"query": enhanced_query})

        if result["source_documents"]:
            expanded_docs = self._expand_context_with_adjacent_chunks(result["source_documents"])
            if len(expanded_docs) > len(result["source_documents"]):
                print(f"🧠 Context expansion: {len(result['source_documents'])} → {len(expanded_docs)} chunks")
                result["source_documents"] = expanded_docs

        # Debug: Print metadata of retrieved documents
        print("🔍 DEBUG: Retrieved documents metadata:")
        for i, doc in enumerate(result["source_documents"]):
            metadata_summary = {k: v for k, v in doc.metadata.items() if k in ['chapter_number', 'section_number', 'chapter_title', 'source_filename', 'chunk_index']}
            print(f"   Doc {i+1}: {metadata_summary}")

        print(f"\n💡 Answer: {result['result']}")
        print(f"\n📚 Sources used: {len(result['source_documents'])} chunks")

        return result

    def _expand_context_with_adjacent_chunks(self, source_documents: List) -> List:
        """Add adjacent chunks to improve context continuity."""
        if not source_documents:
            return source_documents

        docs_by_file = {}
        for doc in source_documents:
            filename = doc.metadata.get('source_filename', 'unknown')
            if filename not in docs_by_file:
                docs_by_file[filename] = []
            docs_by_file[filename].append(doc)

        expanded_docs = []

        for filename, docs in docs_by_file.items():
            docs_with_index = [(doc, doc.metadata.get('chunk_index', 0)) for doc in docs]
            docs_with_index.sort(key=lambda x: x[1])

            expanded_file_docs = []

            for doc, chunk_index in docs_with_index:
                expanded_file_docs.append(doc)
                adjacent_chunks = self._get_adjacent_chunks(filename, chunk_index)
                expanded_file_docs.extend(adjacent_chunks)

            seen_content = set()
            for doc in expanded_file_docs:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    expanded_docs.append(doc)

        return expanded_docs[:12]

    def _get_adjacent_chunks(self, filename: str, target_index: int) -> List:
        """Retrieve chunks adjacent to a given index for context continuity."""
        try:
            vector_store = self.vector_store_manager.get_vector_store()
            if not vector_store:
                return []

            search_kwargs = {
                "k": 6,
                "fetch_k": 15,
                "filter": {
                    "source_filename": filename
                }
            }

            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            )

            nearby_docs = retriever.get_relevant_documents("the and of")

            adjacent = []
            for doc in nearby_docs:
                doc_index = doc.metadata.get('chunk_index', 0)
                if abs(doc_index - target_index) <= 2 and doc_index != target_index:
                    adjacent.append(doc)

            return adjacent[:3]

        except Exception as e:
            print(f"⚠️ Error retrieving adjacent chunks: {e}")
            return []

    def _build_enhanced_query_with_agent(self, question: str, chat_history: Optional[List[Dict]],
                                       selected_document: Optional[str]) -> str:
        context_query = self._build_context_from_history(question, chat_history)

        agent_config = self.agent_manager.get_agent_for_document(selected_document)
        if agent_config and agent_config.is_active:
            return self.agent_manager.build_enhanced_prompt(
                question=context_query,
                context="{context}",
                document_name=selected_document
            )

        return context_query

    def _build_context_from_history(self, question: str, chat_history: Optional[List[Dict]]) -> str:
        if chat_history and len(chat_history) > 0:
            context_messages = []
            for msg in chat_history[-6:]:
                role = "Human" if msg["role"] == "user" else "Assistant"
                context_messages.append(f"{role}: {msg['content']}")

            conversation_context = "\n".join(context_messages)
            enhanced_query = f"""Previous conversation:
{conversation_context}

Current question: {question}

Please answer the current question considering the conversation context above."""

            print("🧠 Using conversation context...")
            return enhanced_query
        else:
            return question

    def is_ready(self) -> bool:
        return self.qa_chain is not None

    def update_document_selection(self) -> None:
        if self.is_ready():
            self.create_qa_chain()

    def get_agent_manager(self) -> AgentManager:
        return self.agent_manager

    def sync_agents_with_documents(self, available_documents: List[str]) -> None:
        self.agent_manager.sync_with_available_documents(available_documents)

    def _extract_chapter_filter(self, question: str) -> Optional[Dict[str, str]]:
        """Extract chapter information from the user's question."""
        chapter_patterns = [
            r'chapitre\s+(\d+|[ivxlc]+)',
            r'chapter\s+(\d+|[ivxlc]+)',
            r'section\s+(\d+|[ivxlc]+)',
            r'partie\s+(\d+|[ivxlc]+)',
            r'(\d+)\.(\d+)',
        ]

        question_lower = question.lower()

        for pattern in chapter_patterns:
            match = re.search(pattern, question_lower)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[0] and groups[1]:  # Section numbering like "1.2"
                    return {
                        "section_number": groups[0],
                        "subsection_number": groups[1]
                    }
                elif groups and len(groups) > 0 and groups[0]:
                    chapter_num = self._normalize_chapter_number(groups[0])
                    if chapter_num:  # Only return if we have a valid chapter number
                        if 'chapitre' in pattern or 'chapter' in pattern:
                            return {"chapter_number": chapter_num}
                        else:
                            return {"section_number": chapter_num}

        return None

    def _normalize_chapter_number(self, chapter_str: str) -> str:
        """Normalize chapter numbers (convert roman to arabic if needed)."""
        if not chapter_str:  # Check for None or empty string
            return ""

        roman_to_arabic = {
            'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
            'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10',
            'xi': '11', 'xii': '12', 'xiii': '13', 'xiv': '14', 'xv': '15',
            'xvi': '16', 'xvii': '17', 'xviii': '18', 'xix': '19', 'xx': '20'
        }

        chapter_lower = chapter_str.lower().strip()
        if chapter_lower in roman_to_arabic:
            return roman_to_arabic[chapter_lower]

        return chapter_str.strip()

    def _query_with_chapter_filter(self, query: str, chapter_filter: Dict[str, str]) -> Dict[str, Any]:
        """Query with specific chapter filtering."""
        vector_store = self.vector_store_manager.get_vector_store()

        # Build filter for chapter-specific metadata
        metadata_filter = {}
        document_filter = self.document_selector.get_document_filter()
        if document_filter:
            metadata_filter.update(document_filter)

        # Add chapter-specific filters
        for key, value in chapter_filter.items():
            metadata_filter[key] = value

        # Create a new retriever with chapter-specific filtering
        search_kwargs = {
            "k": self.retrieval_k * 2,  # Get more results for better chapter matching
            "fetch_k": self.retrieval_fetch_k * 2,
            "lambda_mult": self.retrieval_lambda_mult,
            "filter": metadata_filter
        }

        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )

        # Create temporary QA chain for this specific query
        chapter_qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=False
        )

        result = chapter_qa_chain.invoke({"query": query})

        # Filter results to ensure they match the requested chapter
        filtered_docs = []
        for doc in result["source_documents"]:
            doc_matches = False
            for key, value in chapter_filter.items():
                if doc.metadata.get(key) == value:
                    doc_matches = True
                    break
            if doc_matches:
                filtered_docs.append(doc)

        # If we have filtered docs, use them; otherwise fallback to original results
        if filtered_docs:
            result["source_documents"] = filtered_docs
            print(f"📊 Found {len(filtered_docs)} chapter-specific documents")
        else:
            print("⚠️ No chapter-specific documents found, using general results")

        return result
