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
        ("system", "You are a skilled Social Media Manager crafting Instagram captions for a design-focused account. For each post, you will receive details about the project, including the designer, project name, description, and relevant information. Your task is to write an engaging, well-structured caption in the third person that: (1) opens with a clever wordplay or hook related to the design, (2) mentions the designer’s Instagram handle (e.g., '@designer_handle'), (3) accurately describes the project’s core elements, and (4) avoids excessive adjectives, keeping the tone sophisticated and compelling. You may expand the caption up to 3–4 short paragraphs if it enhances the description, but keep each part direct and relevant to the project. End with 3–5 relevant hashtags that suit the project’s aesthetic and focus. Avoid adding any placeholder text or additional comments."),
        ("human", f"This is {project_name} by {designer}. {description}"),
    ]
    
    # Pass the messages to the AI model
    print("Passing messages to the model...")
    ai_msg = llm.invoke(messages)
    print("Caption generated...")
    # Return the caption
    caption = ai_msg.content
    return caption 
