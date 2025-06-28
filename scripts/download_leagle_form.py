import requests

url = 'https://www.leagle.com/leaglesearch'
response = requests.get(url)

with open('leagle_form.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print('Downloaded leagle_form.html') 