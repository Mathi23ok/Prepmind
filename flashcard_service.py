from services.llm_service import generate_answer
from services.llm_service import generate_flashcards

def create_flashcards(chunks):
    context = "\n".join(chunks[:5])
    return generate_flashcards(context)

def generate_flashcards_from_chunks(chunks):
    context = "\n".join(chunks[:5])  # limit for now

    prompt = f"""
    From the following content, generate 5 flashcards.

    Format:
    Q: question
    A: answer

    Content:
    {context}
    """

    return generate_answer(prompt, "Generate flashcards")

def create_topic_flashcards(chunks, topic):
    filtered_chunks = [c for c in chunks if topic.lower() in c.lower()]

    if len(filtered_chunks) == 0:
        return "No relevant content found"

    context = "\n".join(filtered_chunks[:5])

    return generate_flashcards(context)