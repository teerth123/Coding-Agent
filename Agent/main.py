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
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from uuid import uuid4
import os
import asyncio

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

from Tools.standardTools.index import WriteFile, ReadFile, SearchContent, TerminalAccess, EditLineChange
from Tools.WebTools.index import readContent, searchOnline
from Tools.GitTools.index import pullRepo
from Tools.PlannerTools.index import plannerTool, request_plan



Builder = ChatOpenRouter(
    model="openrouter/free",
    temperature=0
)

Tools = [WriteFile, ReadFile, SearchContent, TerminalAccess, EditLineChange, readContent, searchOnline, pullRepo]
tools_by_name = {tool.name:tool for tool in Tools}
# request_plan is bound to the llm but kept out of tools_by_name, tool_node never runs it
Builder = Builder.bind_tools(Tools + [request_plan])

class AgentState(TypedDict):
    plan:list[str]
    currentStep:int
    acceptance_criteria:list[str]
    allowedPath:str 
    messages:Annotated[list[AnyMessage], operator.add]
    llm_call:int

async def llm_call(state:dict)->str:
    
    plan = state.get("plan", [])
    currentStep = state.get("currentStep", 0)
    acceptance_criteria = state.get("acceptance_criteria", [])

    return {
        "messages" : [
            await Builder.ainvoke(
                [
                    SystemMessage(
                        content=f"you are coding agent, follow the {plan}, your current goal is to work on {plan[currentStep]}, acceptance criteria is strictly {acceptance_criteria}" if len(plan) else "you are coding agent, if the task is small (changes 3 files or less) implement it directly. if its bigger, do not call request_plan until you have grasp or knowledge about the project architecture, so first understand the project files, architecture, using other tools then call request_plan with what you learned, then work on implementation"
                    )
                ]
                + state["messages"]
            )      
        ],
        "llm_call" : state.get('llm_call', 0)+1
    }

async def tool_node(state:dict):
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = await tool.ainvoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id = tool_call["id"]))
    return {"messages":result} 

async def should_continue(state:AgentState) -> str:
    """
    Docstring for should_continue
    
    :param state: Description
    :type state: MessageState
    :return: Description
    :rtype: Any | Literal['tool_node']
    """
    last_message = state["messages"][-1]

    if state.get("llm_call", 0) > 30:
        print("======AGENT IS TRAPPED IN LOOP======")
        return END

    # checked before the generic tool check, request_plan is also a tool call
    if any(tool_call["name"] == request_plan.name for tool_call in last_message.tool_calls):
        return "planner_node"

    if last_message.tool_calls:
        return "tool_node"

    if state.get("currentStep", 0) < len(state.get("plan", [])) - 1:
        return "advance_step_node"

    return END

async def planner_node(state:AgentState) -> str:
    """
        planner node is kept as node and not a tool call becasue its changing the state of the graph
        I researched about it, tool calls should never do that
    """
    print("inside planner node now")

    # every tool call needs a matching ToolMessage, or the next llm call gets rejected by the api
    toolMessages = []
    context = ""
    for tool_call in state["messages"][-1].tool_calls:
        if tool_call["name"] == request_plan.name:
            planCallId = tool_call["id"]
            context = tool_call["args"].get("context", "")
        else:
            toolMessages.append(ToolMessage(content="skipped, call request_plan alone and wait for the plan first", tool_call_id=tool_call["id"]))

    task = next(message for message in reversed(state["messages"]) if isinstance(message, HumanMessage))

    result = await plannerTool.ainvoke({"messages":[task, HumanMessage(content=context)]})
    if result["plan_needed"] is True:
        steps = "\n".join(f"{index+1}. {step}" for index, step in enumerate(result["steps"]))
        criteria = "\n".join(f"- {rule}" for rule in result["acceptance_criteria"])
        toolMessages.append(ToolMessage(content=f"plan:\n{steps}\n\nacceptance criteria:\n{criteria}", tool_call_id=planCallId))
        return {
            "plan" : result["steps"],
            "acceptance_criteria":result["acceptance_criteria"],
            "currentStep":0,
            "messages":toolMessages
        }
    toolMessages.append(ToolMessage(content="no plan needed for this task, implement it directly", tool_call_id=planCallId))
    return {
        "plan": [],
        "acceptance_criteria": [],
        "currentStep": 0,
        "messages":toolMessages
    }

async def advance_step_node(state:AgentState):
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

agent_builder.add_edge(START, "llm_call")
agent_builder.add_edge("tool_node", "llm_call")
agent_builder.add_edge("planner_node", "llm_call")
agent_builder.add_edge("advance_step_node", "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue , 
    ["tool_node", "advance_step_node","planner_node", END] 
)


async def main():
    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        
        agent = agent_builder.compile(
            checkpointer=checkpointer
        )

        while True:
            msg = input("type your message here - ")

            if msg=="STOP DADDY":
                break

            msg = [HumanMessage(content=msg)]
            allowedPath = input("enter allowed path here - ")
            threadID = input("enter threadid, or leave blank")
            if not threadID:
                threadID = uuid4()

            config={
                        "configurable":{
                            "thread_id":str(threadID)
                        }
                    }

            print("thread id is - ", threadID)

            async for chunks in agent.astream(
                {
                    "messages":msg,
                    "plan":[],
                    "acceptance_criteria":[],
                    "allowedPath":allowedPath,
                    "currentStep":0,
                    "llm_call":0
                },
                config=config,
                stream_mode="messages"
            ):
                print(chunks)


if __name__ == "__main__":
    asyncio.run(main())



# graph_png = agent.get_graph(xray=True).draw_mermaid_png()
# with open("agent_graph.png", "wb") as f:
#     f.write(graph_png)
# print("Graph saved to agent_graph.png")


    
#region Learning
# basic agent is done now, 
# need to start with how to make it better, what other things we can add to this
#  
#endregion


# we have a buggy chess project inside /home/batman/Desktop/Projects/Agent/testingChess
# fix it - "plan": [
#         "Inspect repository",
#         "Implement chess logic",
#         "Run tests",
#         "Fix failures",
#         "Report results",
#     ],


# it worked
# perfect!!
# i changed the model from free -> specific structured output supporting llm, it failed at the end cuz openrouter got overloaded, 

# AIMessageChunk(content='', additional_kwargs={}, response_metadata={'model_provider': 'openrouter', 'cost': 0.0, 'cost_details': {'upstream_inference_completions_cost': 0.0, 'upstream_inference_prompt_cost': 0.0, 'upstream_inference_cost': 0.0}}, id='lc_run--01a0e17b-056c-72f3-8d1f-d1a0933b3219', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 18816, 'output_tokens': 240, 'total_tokens': 19056, 'input_token_details': {'cache_creation': 0, 'cache_read': 12672}, 'output_token_details': {'reasoning': 39}}, tool_call_chunks=[]), {'ls_integration': 'langchain_chat_model', 'langgraph_step': 58, 'langgraph_node': 'llm_call', 'langgraph_triggers': ('branch:to:llm_call',), 'langgraph_path': ('__pregel_pull', 'llm_call'), 'langgraph_checkpoint_ns': 'llm_call:8db79660-370d-2713-0204-b18183beac84', 'checkpoint_ns': 'llm_call:8db79660-370d-2713-0204-b18183beac84', 'ls_provider': 'openrouter', 'ls_model_name': 'nvidia/nemotron-3-super-120b-a12b:free', 'ls_model_type': 'chat', 'ls_temperature': 0.0, 'lc_versions': {'langchain-core': '1.6.1', 'langchain': '1.3.18', 'langchain-openrouter': '0.2.8'}})
# (AIMessageChunk(content='', additional_kwargs={}, response_metadata={}, id='lc_run--01a0e17b-056c-72f3-8d1f-d1a0933b3219', tool_calls=[], invalid_tool_calls=[], tool_call_chunks=[], chunk_position='last'), {'ls_integration': 'langchain_chat_model', 'langgraph_step': 58, 'langgraph_node': 'llm_call', 'langgraph_triggers': ('branch:to:llm_call',), 'langgraph_path': ('__pregel_pull', 'llm_call'), 'langgraph_checkpoint_ns': 'llm_call:8db79660-370d-2713-0204-b18183beac84', 'checkpoint_ns': 'llm_call:8db79660-370d-2713-0204-b18183beac84', 'ls_provider': 'openrouter', 'ls_model_name': 'nvidia/nemotron-3-super-120b-a12b:free', 'ls_model_type': 'chat', 'ls_temperature': 0.0, 'lc_versions': {'langchain-core': '1.6.1', 'langchain': '1.3.18', 'langchain-openrouter': '0.2.8'}})
# Traceback (most recent call last):
#   File "/home/batman/Desktop/Projects/Agent/Agent/main.py", line 156, in <module>
#     for chunks in agent.stream(
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2967, in stream
#     for _ in runner.tick(
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 344, in tick
#     _panic_or_proceed(
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 687, in _panic_or_proceed
#     raise exc
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langgraph/pregel/_executor.py", line 80, in done
#     task.result()
#   File "/usr/lib/python3.12/concurrent/futures/_base.py", line 449, in result
#     return self.__get_result()
#            ^^^^^^^^^^^^^^^^^^^
#   File "/usr/lib/python3.12/concurrent/futures/_base.py", line 401, in __get_result
#     raise self._exception
#   File "/usr/lib/python3.12/concurrent/futures/thread.py", line 58, in run
#     result = self.fn(*self.args, **self.kwargs)
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 617, in run_with_retry
#     return task.proc.invoke(task.input, config)
#            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 707, in invoke
#     input = context.run(step.invoke, input, config, **kwargs)
#             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 447, in invoke
#     ret = self.func(*args, **kwargs)
#           ^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/home/batman/Desktop/Projects/Agent/Agent/main.py", line 48, in llm_call
#     Builder.invoke(
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langchain_core/runnables/base.py", line 6014, in invoke
#     return self.bound.invoke(
#            ^^^^^^^^^^^^^^^^^^
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py", line 488, in invoke
#     self.generate_prompt(
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py", line 1877, in generate_prompt
#     return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)
#            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py", line 1684, in generate
#     self._generate_with_cache(
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py", line 1981, in _generate_with_cache
#     for chunk in self._stream(messages, stop=stop, **kwargs):
#   File "/home/batman/Desktop/Projects/Agent/Agent/.venv/lib/python3.12/site-packages/langchain_openrouter/chat_models.py", line 617, in _stream
#     raise ValueError(msg)
# ValueError: OpenRouter API returned an error during streaming: Upstream error from Nvidia: Service temporarily overloaded (code: 503)
# During task with name 'llm_call' and id 'dea7497a-94e2-21e1-0145-22efe564e6e6'

# i tested manully on the browser, it works perfectly fine
