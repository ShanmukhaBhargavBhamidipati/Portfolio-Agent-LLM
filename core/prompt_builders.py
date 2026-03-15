def build_inspiration_summary_block(summaries):
    if not summaries:
        return "No inspiration URLs were analyzed."

    blocks = []
    
    for i, summary in enumerate(summaries, start=1):
        blocks.append(f"Inspiration Website {i}\n{summary.to_prompt_block()}")

    return "\n\n" + ("\n\n" + ("-" * 60) + "\n\n").join(blocks)