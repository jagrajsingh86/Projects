import openai
# replace with your api key
def generate_text_with_openai(user_prompt):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",  # you can replace this with your preferred model
        messages=[{"role": "user", "content": user_prompt}],
    )
    return completion.choices[0].message.content

prompt = "Generate topics to study for [Corporate Finance]"
response = generate_text_with_openai(prompt)
print(response)