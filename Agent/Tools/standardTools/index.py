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
    
@tool
def TerminalAccess(cmd:str)->str:
    """Execute a terminal command and return its output."""
    try:
        result = subprocess.run(cmd, text=True, capture_output=True)

        return f"TerminalAccess tool call results are - {result}"

    except Exception as e:
        return f"found error on TerminalAccess tool - {str(e)}"
    
@tool 
def EditLineChange(lineNum:int, fileLoc:str, content:str)->str:
    """line specific changes across files"""
    try:
        file = Path(fileLoc)
        originalContent = file.read_text().splitlines()
        originalContent[lineNum] = content

        result = file.write_text("\n".join(originalContent) + "\n")
        print(result)
        
        return f"changed the line succesfully"
    except Exception as e:
        return f"found error on EditLineChange tool - {str(e)}"