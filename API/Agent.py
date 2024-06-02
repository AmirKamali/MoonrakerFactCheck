import os
import getpass
OPENAI_API_KEY = 'sk-proj-KbwQ4mxSf3QoOFg0CCw5T3BlbkFJitl4EtxAdt6dIo2MQn3a'
TAVILY_API_KEY = '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'
LANGCHAIN_API_KEY = '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'
# os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API Key:")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY



from uuid import uuid4

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = f"AIE2 - LangGraph - {uuid4().hex[0:8]}"
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY


#from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults

tool_belt = [
#    DuckDuckGoSearchRun(),
    TavilySearchResults(), # TavilyRun() replaced duckduckgo-search because of rate limiting
    ArxivQueryRun() # Maybe use a different tool here for sentiment and all
]


from langgraph.prebuilt import ToolExecutor

tool_executor = ToolExecutor(tool_belt)


from langchain_openai import ChatOpenAI

model = ChatOpenAI(temperature=0)


from langchain_core.utils.function_calling import convert_to_openai_function

functions = [convert_to_openai_function(t) for t in tool_belt]
model = model.bind_functions(functions)


from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
  messages: Annotated[list, add_messages]
  
  
from langgraph.prebuilt import ToolInvocation
import json
from langchain_core.messages import FunctionMessage

def call_model(state):
  messages = state["messages"]
  response = model.invoke(messages)
  return {"messages" : [response]}

def call_tool(state):
  last_message = state["messages"][-1]

  action = ToolInvocation(
      tool=last_message.additional_kwargs["function_call"]["name"],
      tool_input=json.loads(
          last_message.additional_kwargs["function_call"]["arguments"]
      )
  )

  response = tool_executor.invoke(action)

  function_message = FunctionMessage(content=str(response), name=action.tool)

  return {"messages" : [function_message]}


# AI MAKERSPACE PREPR 
# Date: 2024-5-16

# Basic Imports & Setup
# import os
# from openai import AsyncOpenAI

from langchain.agents import Tool

# Using Chainlit for our UI
# import chainlit as cl
# from chainlit.prompt import Prompt, PromptMessage
# from chainlit.playground.providers import ChatOpenAI

# Getting the API key from the .env file
from dotenv import load_dotenv
load_dotenv()

# RAG pipeline imports and setup code
# Get the DeveloperWeek PDF file (future implementation: direct download from URL)
from langchain.document_loaders import PyMuPDFLoader

# Adjust the URL to the direct download format
file_id = "1JeA-w4kvbI3GHk9Dh_j19_Q0JUDE7hse"
direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"

# Now load the document using the direct URL
docs = PyMuPDFLoader(direct_url).load()

import tiktoken
def tiktoken_len(text):
    tokens = tiktoken.encoding_for_model("gpt-3.5-turbo").encode(
        text,
    )
    return len(tokens)

# Split the document into chunks
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 500,           # 500 tokens per chunk, experiment with this value
    chunk_overlap = 50,        # 50 tokens overlap between chunks, experiment with this value
    length_function = tiktoken_len,
)

split_chunks = text_splitter.split_documents(docs)

# Load the embeddings model
from langchain_openai.embeddings import OpenAIEmbeddings

embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

# Load the vector store and retriever from Qdrant
from langchain_community.vectorstores import Qdrant

qdrant_vectorstore = Qdrant.from_documents(
    split_chunks,
    embedding_model,
    location=":memory:",
    collection_name="Prepr",
)

qdrant_retriever = qdrant_vectorstore.as_retriever()

from langchain_openai import ChatOpenAI
openai_chat_model = ChatOpenAI(model="gpt-3.5-turbo")

from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = """
SYSTEM:
You are a fact-check examiner.
Your job is to verify the accuracy of statements and statistics provided in an array of JSON strings.
Use your own knowledge to check these statements and determine their accuracy.
Provide the results in an array of objects in JSON format, each containing the following parameters:
- Status: [ACCURATE, NOT ACCURATE, PARTIALLY ACCURATE]
- summary: A brief summary of the verification process and findings
- OriginalDetails: An object containing:
  - chunk_id: An identifier for the chunk of text
  - text: The original statement being verified
  - from: The starting position of the statement
  - to: The ending position of the statement
- Citation: An object containing:
  - Source: The source of the information
  - Summary: A brief summary of the information from the source
  - Link: The URL to the original source

Here is an example of a transactional conversation:
User: Is the statement about the conference accurate?
You: Let me check the statement. [Process the input]
     Output: 
     [
       {
         Status: ACCURATE,
         summary: "The conference date is confirmed.",
         OriginalDetails: 
         {
           chunk_id: 1,
           text: "The conference is on June 1st, 2024.",
           from: 0,
           to: 39
         },
         Citation:
         {
           Source: "Conference Website",
           Summary: "Date confirmation on the official website.",
           Link: "https://www.conference-website.com/june-1st-2024"
         }
       }
     ]

It can also be a chain of questions and answers where you and the user continue the chain until they say "Got it".
Here is an example of a transactional conversation:
User: Can you verify this statement?
You: Sure, let me verify that for you. [Process the input]
     Output: 
     [
       {
         Status: ACCURATE,
         summary: "The keynote speaker is confirmed.",
         OriginalDetails:
         {
           chunk_id: 1,
           text: "The keynote speaker is Bono.",
           from: 0,
           to: 29
         },
         Citation:
         {
           Source: "Conference Website",
           Summary: "Keynote speaker details.",
           Link: "https://www.conference-website.com/keynote-speaker-bono"
         }
       }
     ]
User: Got it.

If asked a question about a statement or statistic, you can provide detailed information about the verification process.

The format of verification replies is:
Output: 
[
 {
   Status: [ACCURATE, NOT ACCURATE, PARTIALLY ACCURATE],
   summary: A brief summary of the verification process and findings
   OriginalDetails:
   {
     chunk_id: An identifier for the chunk of text,
     text: The original statement being verified,
     from: The starting position of the statement,
     to: The ending position of the statement
   },
   Citation:
   {
     Source: The source of the information,
     Summary: A brief summary of the information from the source,
     Link: The URL to the original source
   }
 }
]

CONTEXT:
{context}

QUERY:
{question}
You are capable of looking up information and providing detailed responses.
When asked a question about the accuracy of a statement, you should provide a detailed response.
After completing your response, you should ask the user if they would like more verifications by asking "Hope that helps. Would you like to verify another statement?".
If the user says "yes", you should proceed with the next statement. If the user says "no", you should say "Goodbye!" or ask if they would like to provide feedback.
If you cannot verify the information, you should say "I am sorry, I do not have that information, but I am always here to help you with any other questions you may have.".
"""


rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT)

from operator import itemgetter
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

retrieval_augmented_qa_chain = (
        {"context": itemgetter("question") | qdrant_retriever, "question": itemgetter("question")}
        | RunnablePassthrough.assign(context=itemgetter("context"))
        | {"response": rag_prompt | openai_chat_model, "context": itemgetter("context")}
)

retrieval_augmented_qa_chain.invoke({"question": 'whens the event coming?'})

rag_tool = Tool(
    name="RAGTool",
    func=lambda inputs: retrieval_augmented_qa_chain.invoke(inputs),
    description="Use this tool to answer questions using the RAG approach."
)

from langgraph.graph import StateGraph, END

# Define a state schema
state_schema = {
    "start": "agent",
    "states": {
        "agent": {
            "next": "action",
            "type": "function",
            "function": lambda context: {"input": context["input"]}
        },
        "action": {
            "next": END,
            "type": "tool",
            "tool": rag_tool
        }
    }
}


from langgraph.graph import StateGraph, END

workflow = StateGraph(state_schema=state_schema)

workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)


workflow.set_entry_point("agent")


def should_continue(state):
  last_message = state["messages"][-1]

  if "function_call" not in last_message.additional_kwargs:
    return "end"

  return "continue"

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue" : "action",
        "end" : END
    }
)


workflow.add_edge("action", "agent")


app = workflow.compile()


def print_messages(messages):
  next_is_tool = False
  initial_query = True
  for message in messages["messages"]:
    if "function_call" in message.additional_kwargs:
      print()
      print(f'Tool Call - Name: {message.additional_kwargs["function_call"]["name"]} + Query: {message.additional_kwargs["function_call"]["arguments"]}')
      next_is_tool = True
      continue
    if next_is_tool:
      print(f"Tool Response: {message.content}")
      next_is_tool = False
      continue
    if initial_query:
      print(f"Initial Query: {message.content}")
      print()
      initial_query = False
      continue
    print()
    print(f"Agent Response: {message.content}")



from langchain_core.messages import HumanMessage

inputs = {"messages" : [HumanMessage(content="When is DeveloperWeek conference scheduled?")]}
#inputs = {"messages" : [HumanMessage(content="What is RAG?")]}
messages = app.invoke(inputs)

print_messages(messages)


inputs = {"messages" : [HumanMessage(content="When did Al Gore created the Internet.  What year did Trump go to jail?")]}

messages = app.invoke(inputs)

print_messages(messages)


def convert_inputs(input_object):
  return {"messages" : [HumanMessage(content=input_object["question"])]}

def parse_output(input_state):
  return input_state["messages"][-1].content

agent_chain = convert_inputs | app | parse_output


agent_chain.invoke({"question" : "What is RAG for LLM Applications"})

def agent_factcheck(input):
    return agent_chain.invoke({"text" : input})