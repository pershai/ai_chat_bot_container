import asyncio
from src.core.database import SessionLocal
from src.services.ingestion_service import ingest_pdf
from src.models.user import User


class MockUploadFile:
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content

    async def read(self):
        return self.content


async def test_ingestion():
    db = SessionLocal()
    try:
        # Get user
        user = db.query(User).filter(User.username == "test_script_user").first()
        if not user:
            print("❌ User not found")
            return

        print(f"Ingesting document for user: {user.username}")

        # Minimal PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello World from Gemini!) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000157 00000 n \n0000000302 00000 n \n0000000389 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n483\n%%EOF\n"

        mock_file = MockUploadFile("test_doc.pdf", pdf_content)

        # Ingest
        result = await ingest_pdf(mock_file, user.id, db)
        print(f"✅ {result}")

    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_ingestion())
