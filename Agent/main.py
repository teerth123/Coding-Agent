from langchain_openrouter import ChatOpenRouter
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, AnyMessage, ToolMessage
import operator
from typing_extensions import TypedDict, Annotated
from typing import Literal
from langgraph.graph import StateGraph, END, START 
from IPython.display import Image, display
from dotenv import load_dotenv

from Tools.standardTools.index import WriteFile, ReadFile, SearchContent, TerminalAccess, EditLineChange
from Tools.WebTools.index import readContent, searchOnline
from Tools.GitTools.index import pullRepo

load_dotenv()


Builder = ChatOpenRouter(
    model="nvidia/nemotron-3.5-lightning:free",
    temperature=0
)

Tools = [WriteFile, ReadFile, SearchContent, TerminalAccess, EditLineChange, readContent, searchOnline, pullRepo]
tools_by_name = {tool.name:tool for tool in Tools}
Builder = Builder.bind_tools(Tools)

#defined state
class MessageState(TypedDict):
    messages:Annotated[list[AnyMessage], operator.add]
    llm_call:int

#defined llm_call --> will be used as llm brain
def llm_call(state:dict)->str:
    return {
        "messages" : [
            Builder.invoke(
                [
                    SystemMessage(
                        content="you are coding agent"
                    )
                ]
                + state["messages"]
            )      
        ],
        "llm_calls" : state.get('llm_calls', 0)+1
    }

def tool_node(state:dict):
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id = tool_call["id"]))
    return {"messages":result} 

def should_continue(state:MessageState) -> str:
    """
    Docstring for should_continue
    
    :param state: Description
    :type state: MessageState
    :return: Description
    :rtype: Any | Literal['tool_node']
    """
    message = state["messages"]
    last_message = message[-1]

    if last_message.tool_calls:
        return "tool_node"
    
    return END

agent_builder = StateGraph(MessageState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue , 
    ["tool_node", END] 
)
agent_builder.add_edge("tool_node", "llm_call")
agent = agent_builder.compile()

graph_png = agent.get_graph(xray=True).draw_mermaid_png()

with open("agent_graph.png", "wb") as f:
    f.write(graph_png)

print("Graph saved to agent_graph.png")