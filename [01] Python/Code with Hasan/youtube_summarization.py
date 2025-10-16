import helpers
import llm
from prompts import youtube_prompts

selected_model = "gpt-4"

youtube_url = "https://www.youtube.com/watch?v=BXFZDdbo2dY"

video_transcript = helpers.get_video_transcript(youtube_url)

#Split video into chunks if needed

chunks = ( 
            helpers.split_text_into_chunks(video_transcript, helpers.max_tokens_per_chunk)
            if helpers.count_tokens(video_transcript, selected_model)
            > helpers.max_tokens_per_chunk
            else [video_transcript]          
          )

#initialize overall output
overall_output = ""

for chunk in chunks:
    prompt = youtube_prompts.youtube_to_points_summary.format(transcript=chunk)
    chunk_output = llm.llm_generate_text(prompt, "OpenAI", selected_model)
    overall_output += chunk_output

print(overall_output)

#prompt = youtube_prompts.youtube_to_points_summary.format(transcript=video_transcript)

#response = llm.llm_generate_text_with_save(prompt, "OpenAI", selected_model)

#print(response)
