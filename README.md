# Project1_CS325_SP_2026
# TTRPG Explainer AI assistance:
# Start by downloading/installing the dependencies from the requirements.txt.
# Before running, ensure that the pdfs are in the same directory as the code (i.e., if you have a folder named Project1, ensure that the PDFs and code are all in that folder, even if the code is in another folder inside Project1)
# Check to see if there is an environment named "Project1_CS325," and if present, switch to it using the command "conda activate Project1_CS325"
# Sometimes you will need to run the code twice in order to start it properly, so if it fails once try it once more.
# For this file, it passes in a few ttrpg rulebooks and tries to chunk and embed the files, then it will store the embedded chunks into a vector, these vectors will be stored on the computer for later use.
# To avoid hiting rate limits for free tier users, there is a dely between the embeddings, storing the vectors on the computers prvents the need to wait on this again.
# While cunking and embedding, please ensure that the computer doesn't shut down.
# Once it's done chunking and embedding the files, it will then ask you for a query based on the passed in rulebooks.
# Once it takes in the query, it embeds the query and stores it in another vector.
# The query is then compares the user query to each of the embedded chunks in the main vector, takes the three closest results, makes sure an answer is based only on the provided context, then provides the answer.

# Design decisions
# I decided to go with Google's Gemini because it has good for searching through and querying PDFs, as well as having a free tier, allowing it to be able to be accessed by anyone.
# I used gemini-2.5-flash specifically because it provides good speed,built in tool use, and it can naturally take in text and images, which is useful.
# gemini-embedding-001 was also used for its increased documentation, while also improving LLM accuracy
# chromaDB was used be able to store the embedded vector(s) on the computer, to prevent the user having to wait on the embedding process each time.
# for chunk size, when doing research, I found that the optimal chunk size for embedding ranges from as low as 128 tokens (milvus.io) and as high as 1024 (pinecone.io) tokens, withboth sites recommending (128-256) being on the smaller end.
# Geeks for Geeks recommends using a chunk size of 300-500 tokens as a nice middle ground.
# 500 tokens (unit of splitting text, in this case words) is the size I decided on.
# this size allows to keep a good amount of context in each chunk, whilst ensureing the chunks don't get too cluttered.
# for overlap, I found that an overlap between a 10-20% of the chunk size is recommended (unstruct.com) to make sure a good amout of context is preserved between chunks.
# 15% is a the middle ground between the two ends of the recommended range, so it keeps a good amout of context between the cunks, while not overlapping so much that the chunks are all the same text.
# Both chunk size and overlap size help ensure that everything is covered in a way that can be parsed through in a meaningful way, while not not having too much redudancy, but still keeping enough context so that nothing gets lost.
# For the retry_delay, max retires, and sleep statements, they help enesure that the free tier users, like myself, don't hit their rate limits per minute, but still ensuring that if the daily rate limit or the rate limit per minute are hit, the user doesn't endlessly wait for the chunks to be embedded.

# Use Case
# This system is a software that takes in, chunks, embeds, and stores PDFs, allowing users to later query the PDFs.
# The primary actors in this use case will be individuals or small groups of people, who's prime goal will be to get answers about the Power Rangers (PR) TTRPG Core Rulebook, or the Moonshine TTRPG Core Rulebook.
# A couple of scenarios include the users wanting to ask about specific rulings for the PR and Moonshine TTRPGs. EX1: The users run the code through, allowing the chunks and embeddings to be made and stored. After that process is complete, User_1 asks "What is the Green Ranger role's level 7 ability in Power Rangers, and what does it do?" The AI assistant then pulls the ability Sidestep from the PR book, and gives the description. EX2: After User_1 is done, User_2 asks "What are the 4 primary attributes in Moonshine?" The AI assistant then pulls grit, stealth, focusm and charm from the Moonshine book.
# Some alternate flows can include the differences between the TTRPG systems. EX1: Moonshine doesn't have classes or roles like most other TTRPG systems, so if you ask for the classes in Moonshine, it may provide you with the different NPC jobs (like the milkman). Another example of an alternate flow is inputting too vague of a query, which also ties into the last point of there being differences between systems.