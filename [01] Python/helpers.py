import tiktoken
import openai

def count_tokens(text, selected_model):
    encoding = tiktoken.encoding_for_model(selected_model)
    num_tokens = encoding.encode(text)
    return len(num_tokens)


def estimate_input_cost(model_name, token_count):
    if model_name == "gpt-3.5-turbo-0613":
        cost_per_1000_tokens = 0.0015
    if model_name == "gpt-3.5-turbo-16k-0613":
        cost_per_1000_tokens = 0.003
    if model_name == "gpt-4-0613":
        cost_per_1000_tokens = 0.03
    if model_name == "gpt-4-32k-0613":
        cost_per_1000_tokens = 0.06
    estimated_cost = (token_count / 1000) * cost_per_1000_tokens
    return estimated_cost