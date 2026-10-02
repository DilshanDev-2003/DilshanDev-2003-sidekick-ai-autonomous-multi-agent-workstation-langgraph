import gradio as gr
from sidekick import Sidekick

async def setup(username):
    user_id = username if username.strip() else "default_user"
    sidekick = Sidekick(username=user_id)
    await sidekick.setup()
    return sidekick

async def process_message(sidekick, message, success_criteria, history):
    if not sidekick:
        return history, sidekick
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick

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