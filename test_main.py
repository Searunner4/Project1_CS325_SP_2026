import pytest
from unittest.mock import Mock, MagicMock, patch
from main import PDFReader, TextChunker, AIModel, GeminiModel, EmbeddingService, VectorDB, QASystem
import main

class TestPDFReader:
    def test_read_returns_text(self):
        test_page1 = Mock()
        test_page1.get_text.return_value = "Hello"
        test_page2 = Mock()
        test_page2.get_text.return_value = " world"
        test_doc = MagicMock()
        test_doc.__iter__.return_value = iter([test_page1, test_page2])
        with patch.object(main.fitz, "open", return_value=test_doc):
            reader = main.PDFReader()
            result = reader.read("file.pdf")
        assert result == "Hello world"
        test_doc.close.assert_called_once()
    def test_read_warns_on_empty_text(self, capsys):
        test_page = Mock()
        test_page.get_text.return_value = "   "
        test_doc = MagicMock()
        test_doc.__iter__.return_value = iter([test_page])
        with patch.object(main.fitz, "open", return_value=test_doc):
            reader = main.PDFReader()
            result = reader.read("empty.pdf")
        assert result == "   "
        captured = capsys.readouterr()
        assert "Warning: No text extracted from empty.pdf" in captured.out
    def test_read_returns_empty_string_on_exception(self, capsys):
        with patch.object(main.fitz, "open", side_effect = Exception("bad pdf")):
            reader = main.PDFReader()
            result = reader.read("broken.pdf")
        assert result == ""
        captured = capsys.readouterr()
        assert "Error opening broken.pdf" in captured.out
class TestTextChunker:
    def text_fixed_chunking_basic(self):
        chunker = main.TextChunker()
        text = "one two three four five six seven eight"
        chunks = chunker.fixed_chunking(text, chunk_size = 3, overlap = 1)
        assert chunks == ["one two three", "four five six", "seven eight"]
        def test_fixed_chunking_empty_text(self):
            chunker = main.TextChunker()
            assert chunker.fixed_chunking("") == []
    
class MockAIModel(AIModel):
    def embed(self, text):
        return [0.9, 0.8, 0.5]
    def generate(self, prompt):
        return "dummyAnswer"
    
class TestGeminiModel:
    def test_embed_calls_embed_content(self):
        test_result = Mock()
        test_result.embeddings = [Mock(values=[1, 2, 3])]
        test_client = Mock()
        test_client.models.embed_content.return_value = test_result
        model = main.GeminiModel(test_client, "embed-model1", "gen-model1")
        result = model.embed("hello")
        assert result == [1, 2, 3]
        test_client.models.embed_content.assert_called_once_with(model = "embed-model1", contents="hello",)
    def test_generate_calls_generate_content(self):
        test_response = Mock(text = "answer")
        test_client = Mock()
        test_client.models.generate_content.return_value = test_response
        model = main.GeminiModel(test_client, "embed-model", "gen-model")
        result = model.generate("prompt")
        assert result == "answer"
        test_client.models.generate_content.assert_called_once_with(model = "gen-model", contents = "prompt",)
    # def test_embed_batch_has_typo_bug(self):
    #     test_client = Mock()
    #     model = main.GeminiModel(test_client, "embed-model", "gen-model")
    #     with pytest.raises(AttributeError):
    #         model.embed_batch(["chunk1", "chunk2"])
class TestEmbeddingService:
    def text_embed_chunks_single_batch(self):
        model = Mock()
        model.embed_batch.return_value = [[1.0], [2.0]]
        service = main.EmbeddingService(model, max_retries=2, retry_delay=0)
        chunks = ["a", "b"]
        with patch.object(main.time, "sleep") as sleep_mock:
            result = service.embed_chunks(chunks, batch_size=10)
        assert result == [[1.0], [2.0]]
        model.embed_batch.assert_called_once_with(["a", "b"])
        sleep_mock.assert_not_called()
    def test_embed_chunks_retires_on_429(self):
        model = Mock()
        model.embed_batch.side_effect = [Exception("429 Too Many Requests"), [[1.0]]]
        service = main.EmbeddingService(model, max_retries = 2, retry_delay=0)
        chunks = ["a"]
        with patch.object(main.time, "sleep") as sleep_mock:
            result = service.embed_chunks(chunks, batch_size=1)
        assert result == [[1.0]]
        assert model.embed_batch.call_count == 2
        #assert sleep_mock.called
    def test_embed_chunks_raises_on_non_retryable_error(self):
        model = Mock()
        model.embed_batch.side_effect = Exception("bad request")
        service = main.EmbeddingService(model, max_retries = 2, retry_delay = 0)
        with pytest.raises(Exception, match = "bad request"):
            service.embed_chunks(["a"], batch_size = 1)
            
class MockVectorDB:
    def query(self, query_vector, n_results = 5):
        return {"documents":[["doc1 text", "doc2 text"]]}
# class TestQASystem:
#     def test_answer_builds_prompt_and_returns_result(self):
#         model = Mock()
#         model.embed.return_value = [0.1, 0.2]
#         model.generate.return_value = "final answer"
#         db = Mock()
#         db.query.return_value = {"documents": [["doc one", "doc two"]]}
def test_qa_mock():
    model = MockAIModel()
    db = MockVectorDB()
    qa = QASystem(model, db)
    answer, results = qa.answer("What is this?")
    assert answer == "dummyAnswer"
    assert "documents" in results
    print("I worked!")