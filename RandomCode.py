import json
import os.path
from random import randint
import sys
import configparser
import time
from os import path, write
import PySimpleGUI as sg
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

CONFIG = 'config.ini'

class RandomNHCodeGen():
    def __init__(self):
        self.parodies = read_from_file("parodies.json")
        self.characters = read_from_file("characters.json")
        self.tags = read_from_file("tags.json")
        self.artists = read_from_file("artists.json")
        self.groups = read_from_file("groups.json")
        self.languages = read_from_file("languages.json")
        self.categories = read_from_file("categories.json")
        self.not_exist = read_from_file("404Galleries.json")
        self.completed_gallery = int(read_from_file("lastCompleted.txt"))
        try:
            self.blacklist = read_from_file("blacklist.json")
        except FileNotFoundError:
            self.blacklist = []
        self.GENERAL_URL = "https://nhentai.net/g/" 

    def does_exist(self, num, driver):
        """Check if the gallery exists"""
        driver.get("".join([self.GENERAL_URL, str(num), "/"]))
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        error = soup.find("div", class_="container error") #Checks for the error container
        if error is not None: #Error contianer only appear for error pages (eg. 404)
            self.not_exist.append(num) #Some galleries do not exist
            return False
        else:
            return True

    def contains_tag(self, num, tag):
        """Checks if gallery contains tag"""
        if tag in self.tags.keys():
            return num in self.tags[tag]
        if tag in self.artists.keys():
            return num in self.artists[tag]
        if tag in self.categories.keys():
            return num in self.categories[tag]
        if tag in self.characters.keys():
            return num in self.characters[tag]
        if tag in self.groups.keys():
            return num in self.groups[tag]
        if tag in self.languages.keys():
            return num in self.languages[tag]
        if tag in self.parodies.keys():
            return num in self.parodies[tag]

    def find_tag_dict(self, tag):
        """Find the dictionary that contains the tag"""
        if tag in self.tags.keys():
            return self.tags
        if tag in self.artists.keys():
            return self.artists
        if tag in self.groups.keys():
            return self.groups
        if tag in self.parodies.keys():
            return self.parodies
        if tag in self.characters.keys():
            return self.characters
        if tag in self.categories.keys():
            return self.categories

    def generate(self, tag='', lang='all'):
        """Generate random gallery number"""
        valid_gallery = False
        fail = False
        while not valid_gallery: #Will loop until a gallery that meets requirements is produced
            fail = False
            if tag and self.is_valid(tag): #If user entered a tag
                dct = self.find_tag_dict(tag)
                index = randint(0, len(dct[tag]) - 1)
                gallery_num = dct[tag][index]
                if lang != 'all': #If user also specified language
                    if gallery_num not in self.languages[lang]:
                        index = randint(0, len(dct[tag]) - 1)
                        gallery_num = dct[tag][index]
                        fail = True
                if self.blacklist: #Check blacklist
                    for t in self.blacklist:
                        if self.contains_tag(gallery_num, t):
                            index = randint(0, len(dct[tag]) - 1)
                            gallery_num = dct[tag][index]
                            fail = True
            elif lang != 'all': #If user specified a language
                index = randint(0, len(self.languages[lang]) - 1)
                gallery_num = self.languages[lang][index]
                if self.blacklist: #Check blacklist
                    for t in self.blacklist:
                        if self.contains_tag(gallery_num, t):
                            index = randint(0, len(self.languages[lang]) - 1)
                            gallery_num = self.languages[lang][index]
                            fail = True
            else: #User wants complete random (-blacklisted tags)
                gallery_num = randint(1, self.completed_gallery)
                while gallery_num in self.not_exist:
                    gallery_num = randint(1, self.completed_gallery)
                if self.blacklist:
                    for t in self.blacklist:
                        if self.contains_tag(gallery_num, t):
                            gallery_num = randint(1, self.completed_gallery)
                            fail = True
            if not fail:
                valid_gallery = True
        return gallery_num

    def index_galleries(self, restart=False):
        """Order galleries bases on tags"""
        if restart:
            self.parodies = {}
            self.characters = {}
            self.tags = {}
            self.artists = {}
            self.groups = {}
            self.languages = {}
            self.categories = {}
            self.not_exist = []
            self.completed_gallery = 0
        options = Options()
        options.headless = True
        options.add_argument = ("user-agent=Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z‡ Safari/537.36")
        driver = webdriver.Firefox(options=options)
        try:
            driver.get("https://nhentai.net/")
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            max_gallery = soup.find("div", class_="container index-container").find("div", class_="gallery").find("a").get("href").split('/')[2]
            max_gallery = int(max_gallery)
            if self.completed_gallery != max_gallery: #Only run if there are new galleries to index
                for i in range(self.completed_gallery, max_gallery):
                    i += 1 #Starting gallery is already indexed
                    if(self.does_exist(i, driver)):
                        driver.get("".join([self.GENERAL_URL, str(i)])) #Loads the gallery
                        html = driver.page_source
                        soup = BeautifulSoup(html, "html.parser")
                        tag_containers = soup.find_all("div", class_="tag-container field-name") #Finds the divs that contain each tag section
                        for tag in tag_containers: #For each tag section
                            tag_names = tag.find_all("a") #Find all the tags in each section
                            for t in tag_names: #For a tag in the tag grouped from a section
                                t = t.get("href").split('/') #Split the link to read the tag (/'type'/'tag-name'/)
                                if t[1] == "parody": #Chooses the gallery according to what type tags it has
                                    if t[2] in self.parodies: #If the tag is already in the dictionary
                                        self.parodies[t[2]].append(i) #Append the gallery to the tag's list
                                    else: #Else create a new key for the tag
                                        self.parodies[t[2]] = [i]
                                elif t[1] == "character":
                                    if t[2] in self.characters:
                                        self.characters[t[2]].append(i)
                                    else:
                                        self.characters[t[2]] = [i]
                                elif t[1] == "tag":
                                    if t[2] in self.tags:
                                        self.tags[t[2]].append(i)
                                    else:
                                        self.tags[t[2]] = [i]
                                elif t[1] == "artist":
                                    if t[2] in self.artists:
                                        self.artists[t[2]].append(i)
                                    else:
                                        self.artists[t[2]] = [i]
                                elif t[1] == "group":
                                    if t[2] in self.groups:
                                        self.groups[t[2]].append(i)
                                    else:
                                        self.groups[t[2]] = [i]
                                elif t[1] == "language":
                                    if t[2] in self.languages:
                                        self.languages[t[2]].append(i)
                                    else:
                                        self.languages[t[2]] = [i]
                                elif t[1] == "category":
                                    if t[2] in self.categories:
                                        self.categories[t[2]].append(i)
                                    else:
                                        self.categories[t[2]] = [i]
                        self.completed_gallery = i
                        if i % 10 == 0: #Every 10 galleries, print gallery number
                            print(i)
                        elif i == max_gallery: #When the loop reaches the end
                            print("Completed")
                        time.sleep(0.05) #Prevent spamming the server a bit
            else:
                print("Completed")
        finally:
            driver.quit()
            save_to_file("parodies.json", self.parodies) #Save the dictionaries to files
            save_to_file("characters.json", self.characters)
            save_to_file("tags.json", self.tags)
            save_to_file("artists.json", self.artists)
            save_to_file("groups.json", self.groups)
            save_to_file("languages.json", self.languages)
            save_to_file("categories.json", self.categories)
            save_to_file("lastCompleted.txt", self.completed_gallery)
            save_to_file("404Galleries.json", self.not_exist)
    
    def index_gallery(self, num):
        """Index specified gallery"""
        num = int(num)
        options = Options()
        options.headless = True
        options.add_argument = ("user-agent=Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z‡ Safari/537.36")
        driver = webdriver.Firefox(options=options)
        try:
            driver.get("https://nhentai.net/")
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            max_gallery = soup.find("div", class_="container index-container").find("div", class_="gallery").find("a").get("href").split('/')[2]
            max_gallery = int(max_gallery)
            if num <= max_gallery: #Only run if specified gallery is less than total number of galleries
                driver.get("".join([self.GENERAL_URL, str(num)])) #Loads the gallery
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                tag_containers = soup.find_all("div", class_="tag-container field-name") #Finds the divs that contain each tag section
                for tag in tag_containers: #For each tag section
                    tag_names = tag.find_all("a") #Find all the tags in each section
                    for t in tag_names: #For a tag in the tag grouped from a section
                        t = t.get("href").split('/') #Split the link to read the tag (/'type'/'tag-name'/)
                        if t[1] == "parody": #Chooses the gallery according to what type tags it has
                            if t[2] in self.parodies: #If the tag is already in the dictionary
                                self.parodies[t[2]].append(num) #Append the gallery to the tag's list
                            else: #Else create a new key for the tag
                                self.parodies[t[2]] = [num]
                        elif t[1] == "character":
                            if t[2] in self.characters:
                                self.characters[t[2]].append(num)
                            else:
                                self.characters[t[2]] = [num]
                        elif t[1] == "tag":
                            if t[2] in self.tags:
                                self.tags[t[2]].append(num)
                            else:
                                self.tags[t[2]] = [num]
                        elif t[1] == "artist":
                            if t[2] in self.artists:
                                self.artists[t[2]].append(num)
                            else:
                                self.artists[t[2]] = [num]
                        elif t[1] == "group":
                            if t[2] in self.groups:
                                self.groups[t[2]].append(num)
                            else:
                                self.groups[t[2]] = [num]
                        elif t[1] == "language":
                            if t[2] in self.languages:
                                self.languages[t[2]].append(num)
                            else:
                                self.languages[t[2]] = [num]
                        elif t[1] == "category":
                            if t[2] in self.categories:
                                self.categories[t[2]].append(num)
                            else:
                                self.categories[t[2]] = [num]
                print("Completed")
            else:
                print("Completed")
        finally:
            driver.quit()
            save_to_file("parodies.json", self.parodies) #Save the dictionaries to files
            save_to_file("characters.json", self.characters)
            save_to_file("tags.json", self.tags)
            save_to_file("artists.json", self.artists)
            save_to_file("groups.json", self.groups)
            save_to_file("languages.json", self.languages)
            save_to_file("categories.json", self.categories)

    def shallow_check(self, num=1):
        """Quickly check if all galleries have been indexed"""
        options = Options()
        options.headless = True
        options.add_argument = ("user-agent=Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z‡ Safari/537.36")
        driver = webdriver.Firefox(options=options)
        try:
            for i in range(int(num), int(read_from_file("lastCompleted.txt"))): #From 1 (or specified) to last index gallery
                if i % 10 == 0:
                    print(i)
                if not i in self.not_exist and not any(i in val for val in self.parodies.values()): #Checks if gallery exists and is in any of the dictionaries
                    if not any(i in val for val in self.characters.values()):
                        if not any(i in val for val in self.tags.values()):
                            if not any(i in val for val in self.artists.values()):
                                if not any(i in val for val in self.groups.values()):
                                    if not any(i in val for val in self.languages.values()):
                                        if not any(i in val for val in self.categories.values()):
                                            if(self.does_exist(i, driver)): #If gallery exists and was not properly index
                                                print("".join(["Gallery ", str(i), " was not properly indexed"]))
                                                self.index_gallery(i) #Index missing gallery
            print("All galleries indexed")
        finally:
            driver.quit()
            save_to_file("404Galleries.json", self.not_exist)

    def sort_dict(self):
        """Sort the lists in each dictionary"""
        tag_dicts = (self.artists, self.categories, self.characters, self.groups, self.languages, self.parodies, self.tags)
        try:
            for d in tag_dicts:
                for k in d.keys():
                    d[k] = sorted(d.get(k))
            print("Sorted")
        finally:
            save_to_file("parodies.json", self.parodies) #Save the dictionaries to files
            save_to_file("characters.json", self.characters)
            save_to_file("tags.json", self.tags)
            save_to_file("artists.json", self.artists)
            save_to_file("groups.json", self.groups)
            save_to_file("languages.json", self.languages)
            save_to_file("categories.json", self.categories)

    def gui(self):
        """Run the GUI of the program"""
        
        #Loaded from config.ini
        selected_lang = read_config('DEFAULT', 'Language')
        selected_theme = read_config('DEFAULT', 'Theme')
        lang = ["all"]
        lang.extend(sorted(self.languages.keys()))
        sg.theme(selected_theme)
        #Layout of GUI
        generator_layout = [[sg.Text('Enter Tag: '), sg.InputText(key='-TAG-'), sg.Button('Generate')],
                            [sg.Text('Language: '), sg.Drop(lang, default_value=selected_lang, key='-LANGUAGE-', enable_events=True)],
                            [sg.Multiline(size=(63,5), disabled=True, autoscroll=False, key='-OUT-', write_only=True)]]
        settings_layout = [[sg.Text('Change Theme:'), sg.Drop(sg.theme_list(), default_value=selected_theme, key='-THEME-', enable_events=True)],
                            [sg.Text('Blacklist Settings:'), sg.Button('Configure'), sg.Button('Display'), sg.Button('Clear')]]
        layout = [[sg.TabGroup([[sg.Tab('Generator', generator_layout), sg.Tab('Settings', settings_layout)]])]]

        # Create the Window
        window = sg.Window("RandomHNumberGenerator v1.0.0", layout)

        #helper_thread = threading.Thread(target=self.generate, args=(), daemon=True)
        # Event Loop to process "events" and get the "values" of the inputs
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, 'Cancel'): #Save files when gui is closed
                save_to_file("blacklist.json", self.blacklist)
                write_config('DEFAULT', 'Theme', selected_theme)
                write_config('DEFAULT', 'Language', selected_lang)
                break
            if event == 'Generate':
                input_tag = values['-TAG-'].strip().replace(' ', '-')
                selected_lang = values['-LANGUAGE-']
                if self.is_valid(input_tag):
                    if input_tag in self.blacklist or selected_lang in self.blacklist:
                        sg.popup_ok('Tag or language is in blacklist')
                    else:
                        gen_num = self.generate(input_tag, selected_lang)
                        window.find_element('-OUT-').print(gen_num)
                        print(gen_num)
                elif ',' in input_tag:
                    sg.popup_ok('Only enter 1 tag')
                else:
                    sg.popup_ok('Tag does not exist or may be misspelled')
            if event == 'Configure':
                tags = sg.popup_get_text("Enter tags to be blacklisted. Seperate tags with a comma. Prefix tags with '-' to remove.")
                self.blacklist_tags(tags)
                print(self.blacklist)
            if event == 'Display':
                sg.popup_ok(''.join(['Blacklist: \n', str(self.blacklist)]))
            if event == 'Clear':
                self.blacklist = []
            selected_lang = values['-LANGUAGE-']
            selected_theme = values['-THEME-']
        window.close()
    
    def blacklist_tags(self, tags):
        """Blacklists given tags"""
        if tags:
            tags = tags.split(',')
            tags = [tag.strip() for tag in tags]
            for tag in tags:
                tag = tag.replace(' ', '-')
                if tag and self.is_valid(tag):
                    if tag[0] == '-' and tag[1::] in self.blacklist:
                        self.blacklist.remove(tag[1::])
                    elif tag[0] != '-' and tag not in self.blacklist:
                        self.blacklist.append(tag)

    def is_valid(self, tag):
        """Check if tag exists"""
        return (any(tag in val for val in self.tags.keys()) or any(tag in val for val in self.artists.keys())
            or any(tag in val for val in self.categories.keys()) or any(tag in val for val in self.characters.keys())
            or any(tag in val for val in self.groups.keys()) or any(tag in val for val in self.languages.keys())
            or any(tag in val for val in self.parodies.keys()))

def save_to_file(file_name, data):
    """Save data to file"""
    with open(file_name, 'w+') as save_file:
        json.dump(data, save_file)

def read_from_file(file_name):
    """Read data from file"""
    with open(file_name, 'r') as load_file:
        data = json.load(load_file)
        return data

def read_config(header, child):
    """Read from config.ini"""
    config = configparser.ConfigParser()
    config.read(CONFIG)
    if not path.isfile(CONFIG):
        config['DEFAULT'] = {}
        config['DEFAULT']['Theme'] = 'Dark'
        config['DEFAULT']['Language'] = 'all'
        with open(CONFIG, 'w') as configfile:    # save
            config.write(configfile)
    return config.get(header, child)

def write_config(header, child, change):
    """Write to config.ini"""
    config = configparser.ConfigParser()
    config.read(CONFIG)
    config[header][child] = change
    with open(CONFIG, 'w') as configfile:    # save
        config.write(configfile)

if __name__ == "__main__":
    gen = RandomNHCodeGen()
    #gen.index_galleries()
    #gen.shallow_check(sys.argv[1])
    #gen.index_gallery(sys.argv[1])
    gen.gui()