# Import necessary libraries
import streamlit as st
import helpers  # Assuming this contains helper functions like get_video_transcript and split_text_into_chunks
import llm  # Assuming this contains a function llm_generate_text for generating text using a language model
from prompts import youtube_prompts  # Importing predefined YouTube prompts

# Set up your Streamlit app
def main():
    # Title of the app
    st.title("YouTube Video Summary Generator")

    # Text input for YouTube URL
    youtube_url = st.text_input("Enter YouTube Video URL:", "https://www.youtube.com/watch?v=u0o3IlsEQbI")

    # Selection box for choosing the model
    selected_model = st.selectbox("Choose the model to use:", ["gpt-3.5-turbo", "gpt-4"])

    # Button to fetch and process the video transcript
    if st.button("Generate Summary"):
        # Display a message while the video transcript is being fetched and processed
        with st.spinner("Fetching video transcript..."):
            video_transcript = helpers.get_video_transcript(youtube_url)

        # Conditionally split the transcript into chunks if it's too long for the model
        chunks = (
            helpers.split_text_into_chunks(video_transcript, helpers.max_tokens_per_chunk)
            if helpers.count_tokens(video_transcript, selected_model) > helpers.max_tokens_per_chunk
            else [video_transcript]
        )

        # Initialize overall output
        overall_output = ""

        # Process each chunk and generate summary
        for chunk in chunks:
            prompt = youtube_prompts.youtube_to_points_summary.format(transcript=chunk)
            chunk_output = llm.llm_generate_text(prompt, "OpenAI", selected_model)
            overall_output += chunk_output

        # Display the generated summary in the app
        st.subheader("Generated Summary:")
        st.write(overall_output)

# Check if the script is run as the main program and call the main function
if __name__ == "__main__":
    main()
