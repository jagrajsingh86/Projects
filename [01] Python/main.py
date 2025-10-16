import helpers
import openai
import llm
from PromptTemplates import textanalysis, ideas

selected_model = "gpt-3.5-turbo"
input_text = """Maternity products"""

prompt = ideas.domain_brand_names.format(sentence = input_text)

# #Calculate Prompt Cost
# token_count = helpers.count_tokens(prompt, selected_model)
# estimated_cost = helpers.estimate_input_cost(selected_model, token_count)
# print(f"Cost: {estimated_cost}")


#Get Response from LLM
response = llm.llm_generate_text(prompt, "OpenAI", selected_model)
print("Result:")
print(response)