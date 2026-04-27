# For the refactoring of this code I decided to implement the Single Responsibility Principle (SRP) and the Open-Closed Principle (OCP)
# I decided to implement these principles because I wanted to ensure that if I wanted to build on this code, or do something similar in the future I had a strong base, to ensure that any future edits would be easy to make, and to ensure I have a better understanding of which part of the code does what.
# I made sure to split my previous code into different classes and just use objects of and calls to those classes instead of having one long main function with calls to other functions.
# An example of what I had before would be:
# if collection.count() == 0:
#   print("Collection is empty. Starting embedding process...")
#   batch_size = 30  # Adjust batch size as needed
#   batch_size = 30  # Adjust batch size as needed
#   for i in range(0, len(all_chunks), batch_size):
#       batch_chunks = all_chunks[i:i + batch_size]
#       print (f"Processing batch {i // batch_size + 1} with {len(batch_chunks)} chunks...")
#       success = False
#       retries = 0
#       while not success and retries < max_retries:
#           try:
#               result = client.models.embed_content(model=embed_model, contents=batch_chunks)
#               batch_embeddings = [e.values for e in result.embeddings]
#               all_embeddings.extend(batch_embeddings)
#               success = True
#               if i + batch_size < len(all_chunks):
#                   print(f"Batch processed successfully. Waiting {sleep_time} seconds before processing the next batch to avoid rate limits...")
#                   time.sleep(sleep_time)  # Sleep to avoid hitting rate limits
#           except Exception as e:
#               error_message = str(e).upper()
#               if any(x in error_message for x in ["429", "RESOURCE EXHAUSTED", "503", "UNAVAILABLE"]):
#                   print(f"Rate limit hit, Waiting {retry_delay + (retry_delay * retries)} seconds before retrying...")
#                   time.sleep(retry_delay + (retry_delay * retries))  # Wait before retrying
#                   retries += 1
#               else:
#                   print(f"Error embedding batch {i // batch_size + 1}: {e}")
#                   raise e
# Compared to what I have now:
# if db.is_empty():
#        print("Collection is empty. Starting embedding process...")
#        all_embeddings = embedder.embed_chunks(all_chunks)
#        if len(all_embeddings) != len(all_chunks):
#            raise ValueError(f"Warning: Number of chunks ({len(all_chunks)}) does not match number of embeddings ({len(all_embeddings)}). Check for errors in the embedding process.")
#         db.add(all_embeddings, all_chunks, all_ids)
#        print("Embeddings stored successfully!")
#    else:
#        print(f"Using existing DB with {db.collection.count()} entries.")

