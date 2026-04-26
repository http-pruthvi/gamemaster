import base64

def embed_loss_curve():
    with open('loss_curve.png', 'rb') as f:
        b64_data = base64.b64encode(f.read()).decode('utf-8')

    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    target_section = "We tracked Rule Accuracy, Spatial Reasoning, and Tension Pacing to ensure holistic world modeling."
    new_section = f"We tracked Rule Accuracy, Spatial Reasoning, and Tension Pacing to ensure holistic world modeling.\n\n### 3. Training Loss Convergence\nAs the agent self-improves, its internal 'loss' (error rate) converges toward zero, indicating mastery of the JSON schema and game rules.\n\n![Loss Curve](data:image/png;base64,{b64_data})"

    if target_section in content:
        content = content.replace(target_section, new_section)
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print("README updated with loss curve.")
    else:
        print("Target section not found.")

if __name__ == "__main__":
    embed_loss_curve()
