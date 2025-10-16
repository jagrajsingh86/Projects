import openai

openai.api_key = "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"

def generate_text_with_openai(user_prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-4",  # you can replace this with your preferred model
        messages=[{"role": "user", "content": user_prompt}],
    )
    return completion.choices[0].message.content

prompt = '''As a creative YouTube title generator, craft a unique and captivating title for a video about [video topic]. The title should be concise, encourage clicks, and may incorporate wordplay or humor. Ensure that it avoids overused phrases and generic titles. 

After creating the title, please discuss how your chosen title effectively conveys the main focus of the video and appeals to potential viewers. Analyze the aspects of the title that make it distinctive and successful in capturing attention among competing content.'''

response = generate_text_with_openai(prompt)

print(response)