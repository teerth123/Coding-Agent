from langchain.messages import HumanMessage, AnyMessage
from langchain_openrouter import ChatOpenRouter
from pydantic import BaseModel, Field
from langchain.tools import tool

class Planner_schema(BaseModel):
    plan_needed :bool = Field(
        description="whether this task require plan or not"
    )
    steps:list[str] = Field(
        description="maximum upto 5 steps and an additional step for testing"
    )
    acceptance_criteria:list[str] = Field(
        description="list of rules to follow to check once code is done, build can pass but end to end completed task is different thing"
    )

PlannerAgent = ChatOpenRouter(
    model="openrouter/free",
    temperature=0,
    max_tokens=1500
).with_structured_output(Planner_schema)
    
@tool
def plannerTool(messages:list[AnyMessage]):
    """
    Docstring for plannerTool
    
    :param messages: Description
    :type messages: list[AnyMessage]
    """

    print("inside plannerTool now")
    Instructions = """
        if the task is really easy, and does not change more than 3 files then go ahead and start implementing directly, you don't really need planner for this
        If its important and heavy change, then make maximum upto 5 steps plan, other than all the steps from this plan the last step of the plan should always be about testing the application end to end, not just feature. 
        Always follow 2 stages of testing - first one by building or compiling the entire application or whatever project it is, second one by writing thorough tests if it consists of logical operations, maybe backend apis or c++ problems. 
    """

    print("invoking the planner agent")

    result = PlannerAgent.invoke([
        HumanMessage(content=f"{Instructions}\n\n{messages[-1]}")
    ])

    print(f"planner agent's output is - {result}")
    return result.model_dump()


    
