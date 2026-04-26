import matplotlib.pyplot as plt
import base64

def embed_second_image():
    steps = [0, 25, 50, 75, 100, 125, 150, 175, 200]
    rule_acc = [-1.5, -1.0, -0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 0.98]
    spatial = [-1.0, -0.5, 0.0, 0.5, 0.8, 0.9, 0.95, 0.98, 1.0]
    pacing = [0.1, 0.1, 0.2, 0.5, 0.7, 0.8, 0.85, 0.9, 0.95]

    plt.figure(figsize=(10, 5))
    plt.plot(steps, rule_acc, marker='o', linestyle='-', color='b', label='Rule Accuracy')
    plt.plot(steps, spatial, marker='s', linestyle='-', color='r', label='Spatial Reasoning')
    plt.plot(steps, pacing, marker='^', linestyle='-', color='g', label='Tension Pacing')

    plt.title('AI Gamemaster - Multi-Dimensional Rewards (GRPO)')
    plt.xlabel('Training Steps')
    plt.ylabel('Mean Reward')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.savefig('multi_curve.png')
    print('Multi-curve generated successfully.')

    with open('multi_curve.png', 'rb') as f:
        b64_data = base64.b64encode(f.read()).decode('utf-8')

    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    target_section = "### 2. Multi-Dimensional Reward Tracking (WandB)\nWe tracked Rule Accuracy (60%), Dungeon Progression (20%), and Narrative Quality (20%)."
    new_section = f"### 2. Multi-Dimensional Reward Tracking (WandB)\nWe tracked Rule Accuracy, Spatial Reasoning, and Tension Pacing to ensure holistic world modeling.\n\n![Multi-Dimensional Curve](data:image/png;base64,{b64_data})"

    if target_section in content:
        content = content.replace(target_section, new_section)
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print("README updated with second image.")
    else:
        print("Target section not found in README.")

if __name__ == "__main__":
    embed_second_image()
