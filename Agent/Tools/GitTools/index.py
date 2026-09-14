from langchain.tools import tool
import subprocess

@tool 
def pullRepo(url:str)->str:
    """pull github repo locally and set it up"""
    try:
        res = subprocess.run(f"git clone {url}", capture_output=True, text=True)
        return res
    except Exception as e:
        return f"found error in pullRepo tool call - {str(e)}"
    
