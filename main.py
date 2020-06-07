from enum import Enum
from numpy.core import unicode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager
import argparse
import chromedriver_binary
import json
import os
import re
import requests
import urllib.request
import sys

indent = 2
client_id = ''
oauth = ''
slugs = []
titles = []

def verify(name):
    response = requests.get('https://id.twitch.tv/oauth2/validate',
                            headers={'Authorization': 'OAuth ' + oauth})
    if response.status_code != 200:
        print('Status {0}: error'.format(response.status_code))
    else:
        print('Status {0}: verified client as {1}'.format(response.status_code, response.json()['login']))
    # print(json.dumps(response.json(), indent=indent))

    response = requests.get('https://api.twitch.tv/helix/users',
                            headers={'Authorization': 'Bearer ' + oauth, 'Client-ID': client_id},
                            params={'login': name})
    data = response.json()['data'][0]
    print('Querying clips from {0} (id: {1})'.format(data['display_name'], data['id']))
    # print(json.dumps(response.json(), indent=indent))

def collect(name):
    cout = 0
    response = requests.get('https://api.twitch.tv/kraken/clips/top',
                            headers={'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': client_id},
                            params={'channel': name, 'period': 'all', 'trending': 'false', 'limit': '1'})
    # print(json.dumps(response.json(), indent=indent))
    while response.json()['_cursor']:
        clips = response.json()['clips']
        cout += len(clips)
        for clip in clips:
            slugs.append(clip['embed_url'])
            titles.append(clip['title'])

        response = requests.get('https://api.twitch.tv/kraken/clips/top',
                                headers={'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': client_id},
                                params={'channel': name, 'period': 'all', 'trending': 'false', 'limit': '100', 'cursor': response.json()['_cursor']})
    clips = response.json()['clips']
    cout += len(clips)
    for clip in clips:
        slugs.append(clip['embed_url'])
        titles.append(clip['title'])

        # print(json.dumps(response.json(), indent=indent))
    print('{0} clips found. '.format(cout))

def download(name):
    # print(slugs)
    os.makedirs('{0}-clips'.format(name), exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--mute-audio")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    for i in tqdm(range(len(slugs))):
        driver.get(slugs[i])
        try:
            WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div[1]/div/div/div/div[5]/div/div[1]/div/div[1]/p')))
            src = driver.find_element_by_xpath('//*[@id="root"]/div/div[1]/div/video').get_attribute('src')
            filename = re.sub('[^A-Za-z0-9\\s]+', '', titles[i])
            filename_ext = filename + '.mp4'
            i = 1
            if os.path.exists(filename_ext):
                filename_ext = filename + ' ({0})'.format(i) + '.mp4'
                while os.path.exists(filename_ext):
                    i = i + 1
                    filename_ext = filename + ' ({0})'.format(i) + '.mp4'
            urllib.request.urlretrieve(src, '{0}-clips/'.format(name) + filename_ext)

        except:
            # print('Failed to download clip. ')
            continue

    driver.quit()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-c', '--client', required=True,
                    help="client id associated with your Twitch account")
    ap.add_argument('-o', '--oauth', required=True,
                    help="oauth code associated with your Twitch account")
    ap.add_argument('-u', '--user', required=True,
                    help="name of the Twitch channel to download from")
    args = vars(ap.parse_args())
    global client_id
    global oauth
    client_id = args['client']
    oauth = args['oauth']
    verify(args['user'])
    collect(args['user'])
    download(args['user'])

if __name__ == '__main__':
    main()