from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import settings

client = QdrantClient(
    url=settings.RAG.QDRANT_URL,
    api_key=settings.RAG.QDRANT_API_KEY
)

# Opsional: Buat index jika belum ada (aman dijalankan berulang)
try:
    client.create_payload_index(
        collection_name="my_pdf_collection",
        field_name="text",
        field_schema=models.TextIndexParams(
            type="text",
            tokenizer=models.TokenizerType.WORD,
            lowercase=True
        )
    )
    print("Text index created for 'text' field.")
except Exception as e:
    if "already exists" not in str(e):
        print("Index already exists or error:", e)

# Sekarang lakukan scroll dengan key="text"
search_result = client.scroll(
    collection_name="my_pdf_collection",
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="text",
                match=models.MatchText(text="Rektor")
            )
        ]
    ),
    limit=5
)

for point in search_result[0]:
    print("=== FOUND ===")
    print(point.payload["text"])
    print("-" * 50)