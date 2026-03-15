from google import genai
import fitz # PyMuPDF library for PDF handling
import chromadb #Stored locally on the computer.
import time

embed_model = "gemini-embedding-001"
generate_model = "gemini-2.5-flash"
max_retries = 5
retry_delay = 20  # seconds

#This funcitn reads in the file file_name, opens it, gets the text out of it, and returns the text.
#If the PDF contains only images or non-selectable text, it shows an error message.
def file_reader(file_name):
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

#This function isn't being used currently, but it can potentially be used in the future to potentially help determine
#optimal chunk size and overlap size by giving the amout of words in the text.
def word_count(text):
    """Counts the number of words in the given text."""
    words = text.split()
    return len(words)

#This function takes in the text, splits it into words, and then creates the chunks of the specifiec size chunk_size, and
#having the overlap between the chunks be of size overlap.
def fixed_chunking(text, chunk_size = 1000, overlap = 150):
    """Splits the input text into fixed-size chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

client = genai.Client()



#file_1 is approximately tripple the length of file_2 and file_3, in terms of page number, and causes problems with the embedding process, so I am taking it out currently, and can try to add it back in later.
#as of the current moment, the system works with files 2 and 3, but adding in file 1 causes the embedding process to fail,
#most likely due to hitting the daily rate limit for the free tier of the embedding model.
#file_1 = "The_Crooked_Moon_Digital_PDF_-_2024_v1.1.pdf"  
file_2 = "moonshine core and chicago guide pre-release.pdf"
file_3 = "PR_Core_Book_Second-Print_Digital_Low-Res.pdf"


combined_text = file_reader(file_2) + file_reader(file_3) #+ file_reader(file_1)



all_chunks = fixed_chunking(combined_text, chunk_size = 500, overlap = 75)
if not all_chunks:
    print("Error: No text chunks were created. Please check if the PDF contains selectable text or if the file path is correct.")
    exit()

#Create a collection, and then add the vectors to the collection, and then we can query the collection later on.
dbClient = chromadb.PersistentClient(path = "./my_vector_database")
collection = dbClient.get_or_create_collection(name ="pdf_chunks")

all_ids = [f"chunk_{i}" for i in range(len(all_chunks))]
all_embeddings = []

#This section checks if there isn't a collection already on the computer, if there isn't, it starts the embedding process, then allows the user to query the document.
#If there is already a collection, the embedding process doesn't need to be run again, and just allows the user to query the documents.
if collection.count() == 0:
    print("Collection is empty. Starting embedding process...")
    batch_size = 30  # Adjust batch size as needed
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i + batch_size]
        print (f"Processing batch {i // batch_size + 1} with {len(batch_chunks)} chunks...")
        success = False
        retries = 0
        #This loop makes sure the program doesn't crash if the embedding process the first few times due to hitting the rate limit.
        #Want to make sure the program works for free tier users.
        while not success and retries < max_retries:
            try:
                result = client.models.embed_content(model=embed_model, contents=batch_chunks)
                batch_embeddings = [e.values for e in result.embeddings]
                all_embeddings.extend(batch_embeddings)
                success = True
                if i + batch_size < len(all_chunks):
                    print("Batch processed successfully. Waiting 12 seconds before processing the next batch to avoid rate limits...")
                    time.sleep(12)  # Sleep to avoid hitting rate limits
            except Exception as e:
                error_message = str(e).upper()
                if any(x in error_message for x in ["429", "RESOURCE EXHAUSTED", "503", "UNAVAILABLE"]):
                    print(f"Rate limit hit, Waiting {retry_delay + (retry_delay * retries)} seconds before retrying...")
                    time.sleep(retry_delay + (retry_delay * retries))  # Wait before retrying
                    retries += 1
                else:
                    print(f"Error embedding batch {i // batch_size + 1}: {e}")
                    raise e
    #Ensures the embedding process was successful.
    if not success:
        print(f"Failed to generate embeddings after multiple retries for batch {i // batch_size + 1}.")
        exit()
    #Makes sure there wer actually chunks created.
    if not all_chunks:
        raise ValueError("No chunks were created from the PDFs; check file paths and chunking.")
    #makes sure there were actually embeddings created.
    if not all_embeddings:
        raise ValueError("No embeddings were generated; check embedding process.")
    #Makes sure no chunks were lost during the embedding process.
    if len(all_chunks) != len(all_embeddings):
        raise ValueError(f"Warning: Number of chunks ({len(all_chunks)}) does not match number of embeddings ({len(all_embeddings)}). Check for errors in the embedding process.")

#all_chunks = the unembedded chunks, all_embeddings is the embedded chunks.
    if len(all_embeddings) == len(all_chunks):
        print(f"All chunks embedded successfully after processing batch {i // batch_size + 1}.")
        collection.add(embeddings = all_embeddings,documents = all_chunks, ids = all_ids)
    else: 
        print(f"Warning: Number of embeddings ({len(all_embeddings)}) does not match number of chunks ({len(all_chunks)}) after processing batch {i // batch_size + 1}. Check for errors in the embedding process.")
        exit()
else:
    print(f"Collection already contains {collection.count()} chunks. Skipping addition of new chunks.")

#embidding is the numerical representation, documents is the original text chunks, ids is the Unique IDs, which are required.

#These lines prompts the user to ask a question about the content of the books.
print("Hello, welcome to the PDF Questioning Answering System! This allows you to ask questions about the content of 2 TTRPG books, 'Moonshine Core and Chicago Guide', the Core Rulebook for the Moonshine TTRPG and guide to Chicago, and 'Power Rangers Core Book', the Power Rangers TTRPG Core Rulebook. You can ask any question about the content of these books, and the system will answer your question based on the content of the books. Please note that the system may not be able to answer all questions, but it will attempt to provide accurate and relevant information based on the content of the books. It's recommended to specify which book you are curious about in the question. Let's get started!")
user_query = input("Enter your query: ")

#This statement embeds the user query using the same embedding model as used before, and then it returns the vector representation of the user query.
embedded_query = client.models.embed_content(model = embed_model, contents = user_query)

#This staement gets the numerical value of the first element in the embeddded_query vector.
#If this statement didn't have the .values at the end, it would return everything about the first element of the array, not just the numerical value.
query_vector = embedded_query.embeddings[0].values

#this function call finds the top n_results most similar chunks in query_vector, and then it returns the similar chunks in a list and sets comparison_results to the list for the time being.
comparison_results = collection.query(query_embeddings = [query_vector], n_results =  3)

database_results = comparison_results['documents'][0]

final_result_text = "\n".join(database_results)
prompt = "Answer the question using ONLY the provided context."
final_prompt = f"{prompt}\n\nContext:\n{final_result_text}\n\nQuestion: {user_query}"

#This section generates the response to the user query using the filal results text and the user query, throwing an exception if there is an error.
response = None
for i in range(max_retries):
    try:
         response = client.models.generate_content(model = generate_model, contents = final_prompt)
         print(f"Response: {response.text}")
         break
    except Exception as e:
        error_message = str(e).upper()
        if any(x in error_message for x in ["503", "UNAVAILABLE"]):
            print(f"Model is currently overloaded (503), Waiting {retry_delay} seconds before retrying...")
            time.sleep(retry_delay)  # Wait before retrying
        else:
            print(f"Error generating response: {e}")
            raise e

#This statement prints out the response to the user query.
print(f"Response: {response.text}")
print(f"Chunks pulled from: {comparison_results}")
