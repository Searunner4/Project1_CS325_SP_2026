TTRPG Explainer AI assistance:

Start by downloading/installing the dependencies from the requirements.txt.
Check to see if there is an environment named "Project1_CS325," and if present, switch to it using the command "conda activate Project1_CS325"
Sometimes you will need to run the code twice in order to start it properly, so if it fails once try it once more.
For this file, it passes in a few ttrpg rulebooks and tries to chunk and embed the files, then it will store the embedded chunks into a vector, these vectors will be stored on the computer for later use.
    To avoid hiting rate limits for free tier users, there is a dely between the embeddings, storing the vectors on the computers prvents the need to wait on this again.
Once it's done chunking and embedding the files, it will then ask you for a query based on the passed in rulebooks.
Once it takes in the query, it embeds the query and stores it in another vector.
The query is then compares the user query to each of the embedded chunks in the main vector, takes the three closest results, makes sure an answer is based only on the provided context, then provides the answer.
