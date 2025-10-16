from bs4 import BeautifulSoup
import requests

url = "https://www.python.org/jobs/"
response = requests.get(url)

soup = BeautifulSoup(response.content, "html.parser")

job_posts = soup.find_all('h2', class_={'listing-company'})

for job_post in job_posts:
    title = job_post.a.text
    print(title)

    

