## tools
# File tools
Read, write, edit(line specific change), globe(searching using file patterns), grep(searching file content), terminal access(for ls, mkdir, etc)

# Web
webFearch, webFetch

# Task 
todoWrite, todoList, todoUpdate

# Git
setting up projects locally, push changes, raise PR

# Futuristic, Ambitious Ideas
1. simultaneous spawning agents
2. A2A proto between multiple agents (PID can be used --> actually seems very easy as backend logic remains separate, agent's logic remains separate so now backend can spawn multiple agents by just doing python main.py , or actually making a orchestrator function that returns PID back every time an agent is spawned, now any random agent can be connected to any other agent)


## Imp things
1. how to prevent agent from touching its source code
2. 

## Story
1. I wanted to code the agentic part with NOOA(nvidia's new agentic framework like ADK, langgraph but oops heavy) , but Claude convinced me to go for langgraph
2. the best command line tool is rg(ripgrep), but cannot be isntalled using pip install, so have to put in dockerfile
3. 8th Sept, was writing the git tools and realised - every project should run inside separate docker container, every time a a dockerfile should run
4. model is still not an agent  
   need llm_call named def
        tool_call
        END
5. 15th Sept - i have good number of tools to test the agent on coding tasks(not pulling and setting up repos locally)
6. Other than tools, we can have checkpoints, better state(rich one, right now we only have messages and llm_calls), we can add files chagned, actionables(maybe json formatted - actionables = {"remaining":[1, 2, 3, ....] , "done":[1, 2, 3], "currently working on":[1, 2, 3]}, etc)
7. Most important thing i should be doing now is - streaming the response  --> turns out streaming in langgraph is really easy bro, now i understand why frameworks for building agents is better than doing everything manually, cuz i remember the syntax for straeming is really different to memorize or even get hold of
8. one more important thing here is checkpointing - and seems like making db calls inside every action(llm call, tool calls, etc) is not the best approach, the best approach is checkpointing with langgraph, and this first requires rich state first(so i have to first work with the messageState)
9. on 16th of sept, I ran it for the first time with stream mode on, and it worked unexpectably well, it build a tic tac toe game but its not working and there are syntacticle errors in files too. I will blantaly mention all the wrong things off my head so I won't forget them. 
 - it didnt test it itself, just coded out and handed over to me
 - as of now I'm just printing entire chunk, so need to make it show only the important part and not everything
 - I think these are the only things I care about as of now. 
10. Let's start with state, we need filesChanged to keep track of all the filesChanged in single session , tasks(this is more towards todolist, but I'm not really sure if state is shared with llms or not) , skills_currently_in_use - maybe this can be an array to tarck which skills users want right now to use , for this one i think I have to actually study how skills are attached to agents
11. on 18th sept, a very important thing i found out - tool calls are never meant to change the state of the graph, its always the nodes that must update the state. for planning tool call, I made a node instead of making a tool call because plan and current step is being added in the graph's state.
12. Testing is one thing, considering every task equally important and serious is different thing, half assed tic-tac-toe game can still gets compiled and built succesfully, but making it production level is completely different instinct. Hence I actually need "acceptance criteria" along with plan.

## Actionables
1. Rich state
2. checkpoint
3. 

------------------Then Taste against the stanford chess game-----------------
## Actionable
1. Backend in fastapi + dockerfile
2. git tool calls + github oauth etc
3. 