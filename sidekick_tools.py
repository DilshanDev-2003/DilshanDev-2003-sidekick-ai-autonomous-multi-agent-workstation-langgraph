import os
import requests
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from langchain_core.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit, PlayWrightBrowserToolkit
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper, SQLDatabase
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool

load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
  playwright = await async_playwright().start()
  async_browser = await playwright.chromium.launch(headless=False)
  playwright_toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
  return playwright_toolkit.get_tools(), async_browser, playwright

def push(text: str):
  """ Send a push notification to the user """
  requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user})
  return "success"

def get_file_tools():
  file_toolkit = FileManagementToolkit(root_dir="sandbox")
  return file_toolkit.get_tools()

async def other_tools():
  push_tool = Tool(
    name="send_push_notification",
    func=push,
    description="Use this tool if we want to send a push notification to the user's mobile phone"
  )

  file_tools = get_file_tools()
  
  tool_search = Tool(
    name="search",
    func=serper.run,
    description="Use this tool if we want to get results from the online web search"
  )

  wikipedia = WikipediaAPIWrapper()
  wikipedia_tool = WikipediaQueryRun(api_wrapper=wikipedia)

  python_repl_tool = PythonREPLTool()

  db = SQLDatabase.from_uri("sqlite:///sidekick_app.db")
  sql_tool = QuerySQLDataBaseTool(db=db)
  sql_agent_tool = Tool(
    name="sql_query_tool",
    func=sql_tool.invoke,
    description="Use this tool to run the sql queries in local sqlite database"
  )

  return file_tools + [push_tool, tool_search, python_repl_tool,wikipedia_tool, sql_agent_tool]