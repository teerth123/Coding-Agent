import os
from langchain.tools import tool
import subprocess
from pathlib import Path


@tool
def WriteFile(fileName:str, content:str) -> str:
    """
    Create or overwrite a file with the provided content.
    """
    try:
        with open(fileName, "w") as f:
            f.write(content)
        
        return f"{fileName} is written"
    except Exception as e:
        return f"found error {str(e)}"
    #this creates file if doesnt exist and reads directly if its already present
        
@tool 
def ReadFile(fileName:str)->str:
    """Read and return the complete contents of a file."""
    try:
        with open(fileName, "r") as f:
            content = f.read()  

        return content
    except Exception as e:
        return f"found error {str(e)}"
    
@tool
def SearchContent(
    query:str,
    path:str = ".",
    caseSensitivity:bool = True,
    filePattern : str | None = None
) -> str:
    """search content across filesystem using ripgrep"""
    try:
        cmd = ["rg", query,path, "--line-number"]

        if not caseSensitivity:
            cmd.append("-i")
        
        if filePattern is not None:
            cmd.extend(["--glob", filePattern])

        result = subprocess.run(
            cmd, 
            text=True,
            capture_output=True
        )
        return f"searche results are - {result}"
    except Exception as e:
        return f"found error {str(e)}"

MAX_OUTPUT_CHARS = 10000

def trimOutput(text:str) -> str:
    # keep the head and tail, errors usually show up at the end (pip, pytest, compilers)
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    half = MAX_OUTPUT_CHARS // 2
    return f"{text[:half]}\n\n... {len(text) - MAX_OUTPUT_CHARS} characters trimmed ...\n\n{text[-half:]}"

def projectEnv() -> dict:
    # drop the agent's own venv, otherwise `python` / `pip` in commands resolve to the agent's interpreter
    env = os.environ.copy()
    agentVenv = env.pop("VIRTUAL_ENV", None)
    if agentVenv:
        env["PATH"] = os.pathsep.join(
            entry for entry in env.get("PATH", "").split(os.pathsep)
            if not entry.startswith(agentVenv)
        )
    return env

@tool
def TerminalAccess(command: str, workingDirectory: str | None = None, timeoutSeconds: int = 120) -> str:
    """
    Execute a bash command and return its stdout, stderr and return code.
    Shell syntax works: pipes, &&, redirects, cd, environment variables.

    :param command: the bash command to run
    :param workingDirectory: directory to run the command in, use the project's root
    :param timeoutSeconds: kill the command after this many seconds, don't start servers or other commands that never exit
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            executable="/bin/bash",
            cwd=workingDirectory,
            env=projectEnv(),
            text=True,
            capture_output=True,
            timeout=timeoutSeconds
        )

        return (
            f"stdout:\n{trimOutput(result.stdout)}\n"
            f"stderr:\n{trimOutput(result.stderr)}\n"
            f"return code: {result.returncode}"
        )

    except subprocess.TimeoutExpired:
        return f"TerminalAccess tool error: command timed out after {timeoutSeconds} seconds"
    except Exception as e:
        return f"TerminalAccess tool error: {e}"


@tool
def EditTool(filePath:str, oldText:str, newText:str) -> str:
    """
    Replace an exact piece of text in a file with new text.
    oldText must match the file exactly, including indentation and whitespace, and must appear exactly once.
    If it appears more than once, include more surrounding lines to make it unique.
    Pass an empty newText to delete oldText. Use WriteFile to create new files.

    :param filePath: path of the file to edit
    :param oldText: exact text currently in the file
    :param newText: text to put in its place
    """
    try:
        file = Path(filePath)
        content = file.read_text()

        if not oldText:
            return "EditTool error: oldText is empty, use WriteFile to create or overwrite a file"

        count = content.count(oldText)
        if count == 0:
            return f"EditTool error: oldText not found in {filePath}, read the file again and copy the text exactly"
        if count > 1:
            return f"EditTool error: oldText appears {count} times in {filePath}, include more surrounding lines so it matches only once"

        file.write_text(content.replace(oldText, newText, 1))
        return f"edited {filePath} successfully"
    except Exception as e:
        return f"EditTool error: {e}"
