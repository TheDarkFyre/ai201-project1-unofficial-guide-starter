import gradio as gr
from generate import answer as get_answer
from retrieve import retrieve

def handle_query(question):
    chunks = retrieve(question)
    response = get_answer(question)
    sources = "\n".join(
        f"[{i}] Review - {c['metadata'].get('professor_name')} | {c['metadata'].get('course')}"
        for i, c in enumerate(chunks, 1)
    )
    return response, sources

with gr.Blocks() as demo:
    inp = gr.Textbox(label="Your question")
    btn = gr.Button("Ask")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

demo.launch()