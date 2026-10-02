import uuid
import asyncio
from datetime import datetime
from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from sidekick_tools import playwright_tools, other_tools

class State(TypedDict):
  messages: Annotated[List[Any], add_messages]
  success_criteria: str
  plan: Optional[str]
  feedback_on_work: Optional[str]
  success_criteria_met: bool
  user_input_needed: bool

class EvaluatorOutput(BaseModel):
  feedback: str = Field(description="Feedback on assistant's work or question asked")
  success_criteria_met: bool = Field(description="Whether the success criteria fully met")
  user_input_needed: bool = Field(description="If clarifying questions or user inputs needed for the tasks")

class Sidekick:
  def __init__(self, username: str = "default_user"):
    self.username = username
    self.worker_llm_with_tools = None
    self.evaluator_llm_with_output = None
    self.planner_llm = None
    self.tools = None
    self.graph = None
    self.browser = None
    self.playwright = None
    self._saver_cm = None

  async def setup(self):
    self.tools, self.browser, self.playwright = await playwright_tools()
    self.tools += await other_tools()

    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

    self.planner_llm = llm
    self.worker_llm_with_tools = llm.bind_tools(self.tools)
    self.evaluator_llm_with_output = llm.with_structured_output(EvaluatorOutput)

    self._saver_cm = AsyncSqliteSaver.from_conn_string("sidekick_memory.sqlite")
    checkpointer = await self._saver_cm.__aenter__()
        
    await self.build_graph(checkpointer)

  def planner(self, state: State) -> Dict[str, Any]:
    """ Creates the plan and ask clarifying questions from the user """
    planner_prompt = f"""You are an expert Planner Agent. Analyze the user's request and success criteria user provided.
    Success Criteria: {state['success_criteria']}

    Rules:
    1. If the user's request need some clarifications, ask 3 clarifications questions from the user.
    2. If the request is clear and you think you do not need clarifications, create the step by step execution plan for the worker agent.
    """  
    messages = [SystemMessage(content=planner_prompt)] + state["messages"]
    response = self.planner_llm.invoke(messages)
    return {"plan": response.content}

  def worker(self, state: State) -> Dict[str, Any]:
    system_message = f"""You are an Autonomous Worker Assistant executing tasks based on a plan. 
    Current Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    Success Criteria: {state['success_criteria']}
    Execution Plan: {state.get('plan', 'No plan generated yet.')}

    Rules:
    1. Follow the execution plan step by step using available tools.
    2. If you need any clarification from the user before proceeding, state your questions clearly starting with 'Question: '. 
    """

    if state.get("feedback_on_work"):
      system_message += f"\nPrevoius Evaluator Feedback: {state['feedback_on_work']}\nFix any errors mentioned."

    messages = [SystemMessage(content=system_message)] + state["messages"]
    response = self.worker_llm_with_tools.invoke(messages)
    return {"messages": [response]}

  def worker_router(self, state: State) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
      return "tools"
    return "evaluator"

  def format_conversation(self, messages: List[Any]) -> str:
    conversation = "Conversation History:\n"
    for message in messages:
      if isinstance(message, HumanMessage):
        conversation += f"User: {message.content}\n"
      elif isinstance(message, AIMessage):
        text = message.content or "[Tool Execution]"
        conversation += f"Assistant: {text}\n"
    return conversation

  def evaluator(self, state: State) -> Dict[str, Any]:
    system_message = "You are an Evaluator checking if task success criteria are met or user input is needed."
    user_message = f"""
    Full Conversation:
    {self.format_conversation(state['messages'])}

    Success Criteria: {state['success_criteria']}
    Latest Response: {state['messages'][-1].content}

    Determine if criteria are met or if the Assistant is asking clarifying questions.
    """
    eval_result = self.evaluator_llm_with_output.invoke([SystemMessage(content=system_message), HumanMessage(content=user_message)])
        
    return {
      "feedback_on_work": eval_result.feedback,
      "success_criteria_met": eval_result.success_criteria_met,
      "user_input_needed": eval_result.user_input_needed
    }

  def route_based_on_evaluation(self, state: State) -> str:
    if state["success_criteria_met"] or state["user_input_needed"]:
      return "END"
    return "worker"

  async def build_graph(self, checkpointer):
    graph_builder = StateGraph(State)

    graph_builder.add_node("planner", self.planner)
    graph_builder.add_node("worker", self.worker)
    graph_builder.add_node("tools", ToolNode(tools=self.tools))
    graph_builder.add_node("evaluator", self.evaluator)

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "worker")
    graph_builder.add_conditional_edges("worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"})
    graph_builder.add_edge("tools", "worker")
    graph_builder.add_conditional_edges("evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END})

    self.graph = graph_builder.compile(checkpointer=checkpointer)

  async def run_superstep(self, message: str, success_criteria: str, history: list):
    config = {"configurable": {"thread_id": self.username}}
        
    state = {
      "messages": [HumanMessage(content=message)],
      "success_criteria": success_criteria or "Provide a clear and accurate answer.",
      "feedback_on_work": None,
      "success_criteria_met": False,
      "user_input_needed": False
    }
        
    result = await self.graph.ainvoke(state, config=config)
        
    reply = result["messages"][-1].content
    return history + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]  

  async def cleanup(self):
    if self.browser:
      await self.browser.close()
    if self.playwright:
      await self.playwright.stop()
    if self._saver_cm:
      await self._saver_cm.__aexit__(None, None, None)