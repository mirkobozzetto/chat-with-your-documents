# src/rag_system/ai_service_manager.py
from langchain_openai import OpenAIEmbeddings, ChatOpenAI


class AIServiceManager:
    """
    Manages AI service connections (LLM and embeddings)
    """

    def __init__(self, openai_api_key: str, embedding_model: str,
                 chat_model: str, chat_temperature: float):
        self.openai_api_key = openai_api_key
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self.chat_temperature = chat_temperature

        self.embeddings = None
        self.llm = None

        self._initialize_services()

    def _initialize_services(self) -> None:
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            api_key=self.openai_api_key
        )

        self.llm = ChatOpenAI(
            model=self.chat_model,
            temperature=self.chat_temperature,
            api_key=self.openai_api_key
        )

    def get_embeddings(self) -> OpenAIEmbeddings:
        return self.embeddings

    def get_llm(self) -> ChatOpenAI:
        return self.llm

    def get_service_info(self) -> dict:
        return {
            "embedding_model": self.embedding_model,
            "chat_model": self.chat_model,
            "chat_temperature": self.chat_temperature
        }
