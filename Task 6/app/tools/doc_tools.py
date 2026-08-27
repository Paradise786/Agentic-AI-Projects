import os
from pydantic import BaseModel, Field
from app.tools.registry import BaseTool, tool_registry
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service

class DocReaderSchema(BaseModel):
    file_path: str = Field(description="Absolute path to the document file (e.g. 'c:/documents/guide.pdf')")

class PDFReaderTool(BaseTool):
    name = "pdf_reader"
    description = "Extracts plaintext contents from a PDF file."
    input_schema = DocReaderSchema

    def _execute(self, args: DocReaderSchema, context: dict) -> str:
        if not os.path.exists(args.file_path):
            raise FileNotFoundError(f"File not found: {args.file_path}")
        return rag_service.read_pdf(args.file_path)

class DOCXReaderTool(BaseTool):
    name = "docx_reader"
    description = "Extracts plaintext contents from a DOCX file."
    input_schema = DocReaderSchema

    def _execute(self, args: DocReaderSchema, context: dict) -> str:
        if not os.path.exists(args.file_path):
            raise FileNotFoundError(f"File not found: {args.file_path}")
        return rag_service.read_docx(args.file_path)

class TXTReaderTool(BaseTool):
    name = "txt_reader"
    description = "Extracts plaintext contents from a TXT file."
    input_schema = DocReaderSchema

    def _execute(self, args: DocReaderSchema, context: dict) -> str:
        if not os.path.exists(args.file_path):
            raise FileNotFoundError(f"File not found: {args.file_path}")
        return rag_service.read_txt(args.file_path)

class SummarizationSchema(BaseModel):
    text: str = Field(description="Long text block or document content to summarize.")

class SummarizationTool(BaseTool):
    name = "summarizer"
    description = "Summarize text segments, paragraphs, or full files."
    input_schema = SummarizationSchema

    def _execute(self, args: SummarizationSchema, context: dict) -> str:
        prompt = f"Please provide a concise summary of the following text:\n\n{args.text}"
        system_prompt = "You are a professional writing and summarization assistant. Extract key action points."
        return llm_service.query(prompt, system_prompt=system_prompt)

# Register all tools
tool_registry.register(PDFReaderTool())
tool_registry.register(DOCXReaderTool())
tool_registry.register(TXTReaderTool())
tool_registry.register(SummarizationTool())
