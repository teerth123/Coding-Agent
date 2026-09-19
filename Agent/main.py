# region Learning
# endregion

from langchain_openrouter import ChatOpenRouter
from langchain.messages import SystemMessage, AnyMessage, ToolMessage, HumanMessage
import operator
from typing_extensions import TypedDict, Annotated
from typing import Literal
from langgraph.graph import StateGraph, END, START 
from IPython.display import Image, display
from dotenv import load_dotenv
load_dotenv()


from Tools.standardTools.index import WriteFile, ReadFile, SearchContent, TerminalAccess, EditLineChange
from Tools.WebTools.index import readContent, searchOnline
from Tools.GitTools.index import pullRepo
from Tools.PlannerTools.index import plannerTool



Builder = ChatOpenRouter(
    model="openrouter/free",
    temperature=0
)

Tools = [WriteFile, ReadFile, SearchContent, TerminalAccess, EditLineChange, readContent, searchOnline, pullRepo]
tools_by_name = {tool.name:tool for tool in Tools}
Builder = Builder.bind_tools(Tools)

class AgentState(TypedDict):
    plan:list[str]
    currentStep:int
    acceptance_criteria:list[str]
    allowedPath:str 
    messages:Annotated[list[AnyMessage], operator.add]
    llm_call:int

def llm_call(state:dict)->str:
    
    plan = state.get("plan", [])
    currentStep = state.get("currentStep", 0)
    acceptance_criteria = state.get("acceptance_criteria", [])

    return {
        "messages" : [
            Builder.invoke(
                [
                    SystemMessage(
                        content=f"you are coding agent, follow the {plan}, your current goal is to work on {plan[currentStep]}, acceptance criteria is strictly {acceptance_criteria}" if len(plan) else "you are coding agent"
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

def should_continue(state:AgentState) -> str:
    """
    Docstring for should_continue
    
    :param state: Description
    :type state: MessageState
    :return: Description
    :rtype: Any | Literal['tool_node']
    """
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tool_node"
    
    if state["currentStep"] < len(state["plan"]) - 1:
        return "advance_step_node"

    return END

def planner_node(state:AgentState) -> str:
    """
        planner node is kept as node and not a tool call becasue its changing the state of the graph
        I researched about it, tool calls should never do that
    """
    print("inside planner node now")

    result = plannerTool.invoke({"messages":state["messages"]})
    if result["plan_needed"] is True:
        return {
            "plan" : result["steps"],
            "acceptance_criteria":result["acceptance_criteria"],
            "currentStep":0
        }
    return {
        "plan": [],
        "acceptance_criteria": [],
        "currentStep": 0
    }

def advance_step_node(state:AgentState):
    """
    Docstring for advance_step_node
    
    :param state: Description
    :type state: AgentState
    """
    advancedStep = state["currentStep"]+1
    return {
        "currentStep":advancedStep
    }


agent_builder = StateGraph(AgentState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("planner_node", planner_node)
agent_builder.add_node("advance_step_node", advance_step_node)

agent_builder.add_edge(START, "planner_node")
agent_builder.add_edge("tool_node", "llm_call")
agent_builder.add_edge("planner_node", "llm_call")
agent_builder.add_edge("advance_step_node", "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue , 
    ["tool_node", "advance_step_node", END] 
)

agent = agent_builder.compile()

# graph_png = agent.get_graph(xray=True).draw_mermaid_png()
# with open("agent_graph.png", "wb") as f:
#     f.write(graph_png)
# print("Graph saved to agent_graph.png")

print("program will ask for inputs now")

msg = input("type your message here - ")
msg = [HumanMessage(content=msg)]
allowedPath = input("enter allowed path here - ")

print("program should start with streaming now")

for chunks in agent.stream(
    {
        "messages":msg,
        "allowedPath":allowedPath,
        "currentStep":0
    },
    stream_mode="messages"
):
    print(chunks)
    
#region Learning
# basic agent is done now, 
# need to start with how to make it better, what other things we can add to this
#  
#endregion