from user_input import get_user_input
from core.agent import run_agent
from models.prompts import AGENT_PROMPT
from models.key_manager import NoKeysConfigured, AllKeysUnavailable


def main():
    messages = [{"role": "system", "content": AGENT_PROMPT}]
    print("June is ready. Type 'exit' to quit.\n")

    while True:
        try:
            query = get_user_input().strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            break

        checkpoint = len(messages)
        messages.append({"role": "user", "content": query})
        try:
            answer = run_agent(messages)
            print("\nJune:", answer, "\n")
        except NoKeysConfigured as e:
            print(f"\n[setup] {e}\n")
            break
        except AllKeysUnavailable as e:
            del messages[checkpoint:]
            print(f"\n[limit] {e}\n")
        except KeyboardInterrupt:
            del messages[checkpoint:]
            print("\n[interrupted]\n")
        except Exception as e:
            del messages[checkpoint:]
            print(f"\n[error] {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    main()
  