import gradio as gr
from sidekick import Sidekick
from langchain_core.messages import HumanMessage

async def setup(username):
    user_id = username if username.strip() else "default_user"
    sidekick = Sidekick(username=user_id)
    await sidekick.setup()
    return sidekick

def extract_text(content) -> str:
    """Extracts clean text from string, list of dicts, or structured message content."""
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        # Handle dict representation of messages or text blocks
        if "content" in content:
            return extract_text(content["content"])
        if "text" in content:
            return content["text"]
    elif isinstance(item := content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    text_parts.append(item["text"])
                elif "content" in item:
                    text_parts.append(extract_text(item["content"]))
            elif isinstance(item, str):
                text_parts.append(item)
            elif hasattr(item, "content"):
                text_parts.append(extract_text(item.content))
        return "\n".join(text_parts)
    elif hasattr(content, "content"):
        return extract_text(content.content)
    
    return str(content)

async def process_message(sidekick, message, success_criteria, history):
    config = {"configurable": {"thread_id": sidekick.username}}
    state = {
        "messages": [HumanMessage(content=message)],
        "success_criteria": success_criteria or "Provide a clear and accurate answer.",
        "feedback_on_work": None,
        "success_criteria_met": False,
        "user_input_needed": False
    }

    current_history = history + [{"role": "user", "content": message}]

    async for event in sidekick.graph.astream(state, config=config):
        for node, values in event.items():
            if "messages" in values and values["messages"]:
                last_msg = values["messages"][-1]
                
                # Safely get raw content regardless of object structure
                if hasattr(last_msg, "content"):
                    raw_content = last_msg.content
                elif isinstance(last_msg, dict) and "content" in last_msg:
                    raw_content = last_msg["content"]
                else:
                    raw_content = last_msg
                
                # Extract clean text string
                clean_text = extract_text(raw_content)
                
                formatted_response = f"[{node}]:\n{clean_text}" if clean_text else f"[{node}]: Executing..."
                
                yield current_history + [{"role": "assistant", "content": formatted_response}], current_history

async def reset(username):
    user_id = username if username.strip() else "default_user"
    new_sidekick = Sidekick(username=user_id)
    await new_sidekick.setup()
    return "", "", None, new_sidekick

def free_resources(sidekick):
    if sidekick:
        sidekick.cleanup()

with gr.Blocks(theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick AI Assistant (Autonomous Multi-Agent)")
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        username_input = gr.Textbox(label="Username / Session ID", value="user_1", placeholder="Enter your unique ID for persistent memory")
        load_btn = gr.Button("Load Session", variant="secondary")

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick Chat", height=400)
        
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="What can Sidekick do for you today?")
        with gr.Row():
            success_criteria = gr.Textbox(show_label=False, placeholder="Define success criteria for this task...")

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    load_btn.click(setup, [username_input], [sidekick])
    ui.load(setup, [username_input], [sidekick])

    message.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    go_button.click(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    reset_button.click(reset, [username_input], [message, success_criteria, chatbot, sidekick])

ui.launch(inbrowser=True)