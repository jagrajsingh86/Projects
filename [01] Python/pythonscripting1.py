import openai
openai.apikey = "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"

def BasicGeneration(userprompt):
    completion = openai.Chatcompletion.create(
        model = "gpt-3.5-turbo"
        messages = [
            {
                "role": "user", "content": userPrompt
            }
        ]
    )
return completion.choices[0].message.content

prompt = "Explain Python scripting in 3 sentences"

response = BasicGeneration(prompt)

print(response)
