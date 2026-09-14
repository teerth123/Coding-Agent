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