from ddgs import DDGS
import requests
from langchain.tools import tool

#tool1 = read the actual content of the site
#tool2 = online search (brave, serpAI, tavily)

@tool
def readContent(url:str)->str:
    """read exact website content"""
    try:
        res = requests.get(
            f"https://r.jina.ai/{url}",
            timeout=30
        )
        res.raise_for_status()
        
        return res.text()
    except Exception as e:
        return f"found error on readContent tool call - {str(e)}"
    
@tool
def searchOnline(query:str)->str:
    """search online for queries"""
    try:
        res = DDGS().text(query, max_results = 5)
        return res
    
    except Exception as e:
        return f"found error in searchOnline tool call - f{str(e)}"