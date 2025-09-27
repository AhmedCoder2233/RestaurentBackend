from agents import OpenAIChatCompletionsModel, AsyncOpenAI, Runner, Agent, function_tool, RunContextWrapper
from dotenv import load_dotenv
from dataclasses import dataclass
import os
import httpx
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from google import genai
from google.genai.types import EmbedContentConfig
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

router = APIRouter(
    prefix="/agent",      
    tags=["Agent"],    
)


file_path = "restaurent.pdf"
loader = PyPDFLoader(file_path=file_path)
pages = loader.load_and_split()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chroma_client = chromadb.Client()

pdf_documents_text = [page.page_content for page in pages]
pdf_doc_ids = [f"pdf_page_{i+1}" for i in range(len(pages))]

embed_model = "gemini-embedding-exp-03-07"

pdf_embeddings_response = client.models.embed_content(
    model=embed_model,
    contents=pdf_documents_text,
    config=EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
)
pdf_doc_embeddings = [emb.values for emb in pdf_embeddings_response.embeddings]

collection = chroma_client.get_or_create_collection(name="knowledge_base1")

try:
    collection.add(
        documents=pdf_documents_text,
        embeddings=pdf_doc_embeddings,
        ids=pdf_doc_ids
    )
    print(f"Added {len(pages)} PDF pages to the knowledge base.")
except Exception as e:
    print(f"Could not add PDF documents to collection, potentially they already exist: {e}")

print("Total documents in collection:", collection.count())


@dataclass
class Token:
    token: str

# ---------------- TOOLS ---------------- #

@function_tool
def answer_from_knowledge_base(query: str) -> str:
    """
    Tool: Given a user query, this tool searches the knowledge base and returns an answer using retrieved documents.
    """
    print(f"[Debug] RAG function call with query {query}")
    q_resp = client.models.embed_content(
        model=embed_model,
        contents=[query],
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    q_vector = q_resp.embeddings[0].values
    res = collection.query(query_embeddings=[q_vector], n_results=1, include=["documents"])
    print(f"[Debug] RAG vector db output {res}")
    if res and res.get("documents") and res["documents"][0]:
        top_doc = res["documents"][0][0]  
        return top_doc
    else:
        return "Could not find relevant information in the knowledge base."


@function_tool
async def getMenu(ctx: RunContextWrapper[Token]):
    """
    Use this tool to show Menu to user.
    Always returns structured JSON.
    """
    try:
        async with httpx.AsyncClient() as client:
            data = await client.get(
            "http://localhost:8000/users/getmenu/foragent",
            headers={"Authorization": f"Bearer {ctx.context.token}"})

            print(f"getMenu Call huwa with data: {data.json()}")


            if data.status_code != 200:
                return {"menu": [], "email": None, "error": "Invalid or expired token"}

            return data.json()
    except Exception as e:
        print(f"Menu Tool ma error aya: {e}")


@function_tool
async def getPreviousOrders(ctx: RunContextWrapper[Token], email: str):
    """
    Use this tool to show Previous orders of users.
    Always returns structured JSON.
    """
    try:
        async with httpx.AsyncClient() as client:
            data = await client.get(
            f"http://localhost:8000/users/getorderbyemail/{email}",
            headers={"Authorization": f"Bearer {ctx.context.token}"}
            )

            print(f"getPreviousOrder Call huwa with data: {data.json()}")

            if data.status_code != 200:
                return {"orders": [], "error": "Failed to fetch orders"}

            return data.json()
    except Exception as e:
        print(f"Previous Tool ma error aya: {e}")


informationAgent = Agent(
    name="informationAgent",
    instructions="""
    # You are the Information Agent

    ## Tasks
    1. If the user asks any Customer Support / Restaurant related query → create a clean query and call the `answer_from_knowledge_base` tool.
    2. If tool returns relevant info → summarize it in clear numbered points (1. 2. 3. ...).
    3. If tool cannot find answer → reply:
       "Sorry, i don't have information about it.  
        For further assistance please contact: ahmedpubgking3388@gmail.com"
    4. If user question is totally irrelevant (not customer support related) → handoff back to MainAgent.
    """,
    model=model, 
    tools=[answer_from_knowledge_base]
)

# ---------------- AGENTS ---------------- #
menuAgent = Agent(
    name="menuAgent",
    instructions="""
    # You are the **Menu Agent**

    ## HARD RULES (must follow strictly)
    1. If user asks about:
       - Menu
       - Previous Orders
       - Food Suggestions
       → You MUST ALWAYS call the `getMenu` tool FIRST.

    2. After calling `getMenu`:
       - If response has `"error"` OR `"email": null` → immediately reply:
         ⚠️ Please login to continue.
       - If valid email exists → then call `getPreviousOrders(email)`.

    3. Never, ever ask the user for their email.  
       The email must only come from `getMenu`.

    4. If user query is not about Menu/Orders/Suggestions → handoff to MainAgent.

    ## Reply Style
    - Do NOT use markdown bold (**), italics, or lists with dashes.
    - Always use plain text with numbering like:
      1. 🍔 Cheeseburger — Juicy beef patty with cheddar cheese, lettuce, tomato and pickles. — $7.49
      2. 🍕 Margherita Pizza — Classic Neapolitan pizza topped with tomatoes, mozzarella, fresh basil and olive oil. — $8.99

    - Structure must be:

    Sure! Here's our menu:

    🍽️ APPETIZERS
    1. 🥟 Samosa — Deep-fried pastry filled with spiced potatoes and peas. — $1.25
    2. 🥗 Caesar Salad — Crisp romaine lettuce tossed with Caesar dressing, croutons and parmesan cheese. — $6.99

    🍕 MAIN COURSES
    3. 🍔 Cheeseburger — Juicy beef patty with cheddar cheese, lettuce, tomato and pickles. — $7.49
    4. 🍕 Margherita Pizza — Classic Neapolitan pizza topped with tomatoes, mozzarella, fresh basil and olive oil. — $8.99
    5. 🍗 Butter Chicken — Creamy tomato-based curry with tender chicken pieces. — $13.00

    🍰 DESSERTS
    6. 🍫 Chocolate Brownie — Rich and fudgy chocolate brownie with walnuts. — $3.50
    7. 🥞 Pancakes with Maple Syrup — Fluffy pancakes drizzled with real maple syrup and served with butter. — $4.75

    🥤 DRINKS
    8. 🍹 Fruit Smoothie Bowl — Smoothie made with blended fruits, topped with fresh fruits, nuts and seeds. — $6.50

    If previous orders exist:
    Also, here are your previous orders:
    1. 🥗 Caesar Salad
    2. 🍕 Margherita Pizza
    3. 🍟 French Fries
    """,
    model=model,
    tools=[getMenu, getPreviousOrders]
)


mainAgent = Agent(
    name="MainAgent",
    instructions="""
    # You are the Main Orchestrator Agent

    ## Tasks
    1. If query is about Menu, Previous Orders, or Food Suggestions → handoff to menuAgent.
    2. If query is about Restaurant / Customer Support (like complaints, issues, timings, contact info, general info) → handoff to informationAgent.
    3. If user greets (e.g., "hello", "hi") → greet politely.
    4. If irrelevant or unrelated question → politely say you cannot proceed with this request.
    NEVER Reply on your own!
    """,
    model=model,
    handoffs=[menuAgent, informationAgent]
)

menuAgent.handoffs.append(mainAgent)
informationAgent.handoffs.append(mainAgent)

# ---------------- MEMORY ---------------- #

memory = []

# ---------------- ROUTE ---------------- #

@router.post("/callAgent/{usermessage}/{token}")
async def main(usermessage: str, token: str):
    try:
        data = Token(token=token)
        memory.append({"role": "user", "content": usermessage})
        result = await Runner.run(mainAgent, memory, context=data)
        memory.append({"role": "assistant", "content": result.final_output})

        print(f"✅ Agent Reply: {result.final_output}")
        return {"message": result.final_output}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"message": "⚠️ Internal error aya, please try again later."}
