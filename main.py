from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage

#Define a function that passes the project details to the AI model and returns the caption
def generate_caption(project_name, description, designer):
    print("Generating caption...")
    llm = ChatOllama(
    model="llama3.1",
    temperature=1)
    # Define the input messages
    print("Model loaded...")
    messages = [
        ("system", "You are a skilled Social Media Manager responsible for crafting engaging captions for a design blog. For each post, you receive text with details about the author, the project name, the project, and relevant information. Your task is to write clear, compelling captions in the third person, tailored to Instagram, ensuring they resonate with the audience and highlight the design elements effectively. Do not add any comments to the captions that need to be filled out and always mention the Instagram Tag in the caption."),
        ("human", f"This is {project_name}] by {designer}. {description}"),
    ]
    
    # Pass the messages to the AI model
    print("Passing messages to the model...")
    ai_msg = llm.invoke(messages)
    print("Caption generated...")
    # Return the caption
    caption = ai_msg.content
    return caption 
