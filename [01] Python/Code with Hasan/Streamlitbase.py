import sys
import newspaper as nk
import streamlit as st
import openai
def openAI_generate_text(prompt, model, api_key):
    completion = openai.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content
def get_article_from_url(url):
    try:
        # Scrape the web page for content using newspaper
        article = nk.Article(url)
        # Download the article's content with a timeout of 10 seconds
        article.download()
        # Check if the download was successful before parsing the article
        if article.download_state == 2:
            article.parse()
            # Get the main text content of the article
            article_text = article.text
            return article_text
        else:
            st.write("Error: Unable to download article from URL:", url)
            return None
    except Exception as e:
        st.write("An error occurred while processing the URL:", url)
        st.write(str(e))
        return None
def tool_1_prompt(api_key):
    st.title("Prompt Tester")
    prompt = st.text_area("Enter Prompt:")
    model = st.selectbox("Choose a model", ["gpt-3.5-turbo", "gpt-4", "curie"])
    if st.button("Test"):
        result = openAI_generate_text(prompt, model, api_key)
        st.write(result)
def tool_2_blog_url(api_key):
    st.title("Blog AI Automator")
    blog_url = st.text_input("Enter Blog URL:")
    user_prompt = st.text_area("Enter Prompt:")
    model = st.selectbox("Choose a model", ["gpt-3.5-turbo", "gpt-4", "curie"])
    # https://learnwithhasan.com/chatgpt-earthquake/
    # Generate a bullet point summary for the following blog:
    if st.button("Generate"):
        blog_article = get_article_from_url(blog_url)
        st.write("Article Scraped")
        st.write("Processing...")
        prompt = user_prompt + blog_article
        result = openAI_generate_text(prompt, model, api_key)
        st.markdown("### Result:")
        st.success("Successfully generated result!")
        st.write(result)
def main():
    # Sidebar
    st.sidebar.header("Settings")
    # Input for OpenAI API key in the sidebar
    api_key = st.sidebar.text_input("OpenAI API key (Optional)", type="password")
    # Tool selection as a dropdown in the sidebar
    tool_selection = st.sidebar.selectbox(
        "Choose a tool", ["Prompt Tester", "Blog AI Automator"]
    )
    # Depending on the tool selection, display the UI
    if tool_selection == "Prompt Tester":
        tool_1_prompt(api_key)
    elif tool_selection == "Blog AI Automator":
        tool_2_blog_url(api_key)
if __name__ == "__main__":
    main()