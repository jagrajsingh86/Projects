from openai import OpenAI

client = OpenAI(api_key="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")


selected_model = "gpt-3.5-turbo"
# Initialize the list of messages
messages = [{"role": "system", "content": "You are a helpful assistant."}]


# Start a chat
def continue_chat(user_message):
    # Add the user's message to the list
    messages.append({"role": "user", "content": user_message})

    # Get the chat response
    response = client.chat.completions.create(model="gpt-3.5-turbo",  # or gpt-4 if available
    messages=messages)
    # Add the AI's response to the list
    messages.append(
        {"role": "assistant", "content": response.choices[0].message.content}
    )

    return response.choices[0].message.content


# Chat with the bot
while True:
    user_message = input("You: ")
    if user_message.lower() == "quit":
        break

    ai_response = continue_chat(user_message)
    print("AI: ", ai_response)
