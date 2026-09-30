from user_input import get_user_input
from groq_clients import ask_groq

def main():
    user_query = get_user_input()

    messages = [
        {"role": "system", "content": "You are June, a coding agent."},
        {"role": "user", "content": user_query}
    ]

    response = ask_groq(messages)

    print("\nJune:", response)


if __name__ == "__main__":
    main()