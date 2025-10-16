from bs4 import BeautifulSoup
import requests
url = "https://www.cognition-labs.com/introducing-devin"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

title = soup.title

meta_tag = soup.find('meta', attrs={'name': 'description'})
# Check if meta_tag is not None before getting its content
if meta_tag:
    meta_description = meta_tag.get('content')
else:
    # If meta_tag is None, set a default value or handle the absence as needed
    meta_description = "No description available."

print(title)
print(meta_description)
