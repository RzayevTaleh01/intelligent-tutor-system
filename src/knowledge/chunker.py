import uuid
import pypdf
import io
from typing import List, Dict, Any
from src.knowledge.models import SourceResponse

class Chunker:
    def __init__(self, chunk_size=1000, overlap=150):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        text = ""
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_content))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            except Exception as e:
                print(f"PDF Error: {e}")
                return {"text": "", "count": 0}
        else:
            # Assume text
            try:
                text = file_content.decode('utf-8', errors='ignore')
            except:
                text = str(file_content)

        # Create Chunks
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_text = text[start:end]
            
            # Adjust to nearest space to avoid cutting words
            if end < text_len:
                last_space = chunk_text.rfind(' ')
                if last_space != -1:
                    end = start + last_space
                    chunk_text = text[start:end]
            
            chunks.append({
                "id": str(uuid.uuid4()),
                "position": start,
                "text": chunk_text.strip(),
                "meta": {"source": filename}
            })
            
            start += (len(chunk_text) - self.overlap)
            
        return {
            "text_len": text_len,
            "chunks": chunks
        }
