"""
Analyze conversation message distribution.
"""
from pathlib import Path
from src.utils.data_loader import ConversationLoader

def analyze():
    conv_path = Path(__file__).parent.parent.parent.parent / "references" / "conversation_-2--sensetivity_2026-03-12-1103.agi.json"
    loader = ConversationLoader(str(conv_path))
    messages = loader.get_messages()

    print(f"Total messages: {len(messages)}")
    print(f"\nMessage token distribution:")
    print("-" * 60)

    cumulative = 0
    for i, msg in enumerate(messages):
        content = loader._extract_content(msg)
        tokens = loader.count_tokens(content)
        cumulative += tokens

        if i < 10 or i >= len(messages) - 5:
            print(f"Msg {i+1:2d}: {tokens:7d} tokens | Cumulative: {cumulative:7d}")
        elif i == 10:
            print("...")

    print("-" * 60)
    print(f"\nTotal tokens: {cumulative}")

    # Test slice creation
    print("\n\nTesting slice creation with target=50000:")
    target = 50000
    tolerance = 0.1
    lower = target * (1 - tolerance)
    upper = target * (1 + tolerance)
    print(f"Acceptable range: {lower:.0f} - {upper:.0f} tokens")

    result = []
    current_tokens = 0

    for i, msg in enumerate(messages):
        content = loader._extract_content(msg)
        msg_tokens = loader.count_tokens(content)

        print(f"\nMsg {i+1}: {msg_tokens} tokens")
        print(f"  Current: {current_tokens}, Would be: {current_tokens + msg_tokens}")

        if current_tokens + msg_tokens > upper:
            print(f"  -> STOP: Would exceed upper bound ({upper})")
            break

        result.append(content)
        current_tokens += msg_tokens
        print(f"  -> ADDED. New total: {current_tokens}")

        if current_tokens >= lower:
            print(f"  -> STOP: Reached lower bound ({lower})")
            break

    print(f"\nFinal slice: {current_tokens} tokens from {len(result)} messages")

if __name__ == "__main__":
    analyze()
