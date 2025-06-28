import requests

url = 'https://caselaw.findlaw.com/'
response = requests.get(url)

with open('findlaw_form.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print('Downloaded findlaw_form.html') 