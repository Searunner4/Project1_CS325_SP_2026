from google import genai
import fitz # PyMuPDF library for PDF handling
import chromadb #Stored locally on the computer.
import time

embed_model = "gemini-embedding-001"
generate_model = "gemini-2.5-flash"
max_retries = 5
retry_delay = 20  # seconds
sleep_time = 12

#This class delas with the SRP
class PDFReader:
    def read(self, file_name):
        try:
            doc = fitz.open(file_name)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
        
            #text.strip() removes any leading or trailing whitespace from the text, and then checks if the resulting string is empty. If it is empty, it means that no text was extracted from the PDF, which could be due to the PDF containing only images or non-selectable text. In such cases, a warning message is printed to alert the user about the issue.
            if not text.strip():
                print(f"Warning: No text extracted from {file_name}. Check if the PDF contains selectable text.")
            return text
        except Exception as e:
            print(f"Error opening {file_name}: {e}")
            return ""


#This function takes in the text, splits it into words, and then creates the chunks of the specifiec size chunk_size, and
#having the overlap between the chunks be of size overlap.
#This class delas with the SRP
class TextChunker:
    def fixed_chunking(self, text, chunk_size = 500, overlap = 75):
        """Splits the input text into fixed-size chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return chunks


#This class delas with the OCP
class AIModel:
    def embed(self, text):
        raise NotImplementedError
    def generate(self, prompt):
        raise NotImplementedError

#This class delas with the OCP
class GeminiModel(AIModel):
    def __init__(self, client, embed_model, generate_model):
        self.client = client
        self.embed_model = embed_model
        self.generate_model = generate_model
    def embed(self, text):
        result = self.client.models.embed_content(model = self.embed_model, contents = text)
        return result.embeddings[0].values
    def embed_batch(self, batch_chunks):
        result = self.client.models.embed_content(model = self.embed_model, contents = batch_chunks)
        return [e.values for e in result.embeddings]
    def generate(self, prompt):
        response = self.client.models.generate_content(model = self.generate_model, contents = prompt)
        return response.text
    
#This class delas with the SRP
class EmbeddingService:
    def __init__(self, model: GeminiModel, max_retries, retry_delay):
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    def embed_chunks(self, chunks, batch_size = 30):
        all_embeddings = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            print (f"Processing batch {i // batch_size + 1}...")
            retries = 0
            success = False
            while not success and retries < self.max_retries:
                try:
                    embeddings = self.model.embed_batch(batch)
                    all_embeddings.extend(embeddings)
                    success = True
                    if i + batch_size < len(chunks):
                        print("Warning to avoid rate limits...")
                        time.sleep(sleep_time)
                except Exception as e:
                    error_message = str(e).upper()
                    if any(x in error_message for x in ["429", "503", "UNAVAILABLE"]):
                        wait_time = self.retry_delay * (retries + 1)
                        print(f"Retrying in {wait_time} seconds...")
                        self.retry_delay
                        retries += 1
                    else:
                        raise e
            if not success:
                raise Exception("Failed embeddding after retires")
        return all_embeddings

#This class delas with the SRP
class VectorDB:
    def __init__(self, path = "./my_vector_database"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name = "pdf_chunks")
    def is_empty(self):
        return self.collection.count() == 0
    def add(self, embeddings, documents, ids):
        self.collection.add(embeddings = embeddings, documents = documents, ids = ids)
    def query(self, query_vector, n_results = 5):
        return self.collection.query(query_embeddings = [query_vector], n_results= n_results)

#This class delas with the SRP
class QASystem:
    def __init__(self, model:AIModel, db:VectorDB):
        self.model = model
        self.db = db
    def answer(self, user_query):
        query_vector = self.model.embed(user_query)
        results = self.db.query(query_vector)
        docs = results["documents"][0]
        context = "\n".join(docs)
        prompt = f"""
        Answer the question using ONLY the provided context.
        Context:
        {context}
        Question: {user_query}
        """
        return self.model.generate(prompt), results

def main():             
    client = genai.Client()
    reader = PDFReader()
    chunker = TextChunker()
    model = GeminiModel(client, embed_model, generate_model)
    embedder = EmbeddingService(model, max_retries, retry_delay)
    db = VectorDB()



    #file_1 is approximately tripple the length of file_2 and file_3, in terms of page number, and causes problems with the embedding process, so I am taking it out currently, and can try to add it back in later.
    #as of the current moment, the system works with files 2 and 3, but adding in file 1 causes the embedding process to fail,
    #most likely due to hitting the daily rate limit for the free tier of the embedding model.
    #file_1 = "The_Crooked_Moon_Digital_PDF_-_2024_v1.1.pdf"  
    file_2 = "moonshine core and chicago guide pre-release.pdf"
    file_3 = "PR_Core_Book_Second-Print_Digital_Low-Res.pdf"


    combined_text = reader.read(file_2) + reader.read(file_3)#file_reader(file_2) + file_reader(file_3) + file_reader(file_1)



    all_chunks = chunker.fixed_chunking(combined_text)
    if not all_chunks:
        print("Error: No text chunks were created. Please check if the PDF contains selectable text or if the file path is correct.")
        return
    all_ids = [f"chunk_{i}" for i in range(len(all_chunks))]

#This section checks if there isn't a collection already on the computer, if there isn't, it starts the embedding process, then allows the user to query the document.
#If there is already a collection, the embedding process doesn't need to be run again, and just allows the user to query the documents.
    if db.is_empty():
        
        print("Collection is empty. Starting embedding process...")
        all_embeddings = embedder.embed_chunks(all_chunks)
        if len(all_embeddings) != len(all_chunks):
            raise ValueError(f"Warning: Number of chunks ({len(all_chunks)}) does not match number of embeddings ({len(all_embeddings)}). Check for errors in the embedding process.")
        db.add(all_embeddings, all_chunks, all_ids)
        print("Embeddings stored successfully!")
    else:
        print(f"Using existing DB with {db.collection.count()} entries.")
    qa = QASystem(model, db)
    print("\nPDF QA System ready!\n")
    user_query = input("Enter your query (or 'finish query' to quit): ")
    try:
        answer, results = qa.answer(user_query)
        print("\nResponse:\n", answer)
        print("\nChunks Used:\n", results)
    except Exception as e:
        print("Error: ", e)
if __name__ == "__main__":
    main()
