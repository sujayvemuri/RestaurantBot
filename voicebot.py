## Run this command in terminal  before executing this program
## rasa run -m models --endpoints endpoints.yml --port 5002 --credentials credentials.yml
## and also run this in seperate terminal
## rasa run actions

from colorama import Fore, Back, Style, init
import colorama
import speech_recognition as sr
import requests
import win32com.client as winc1

init()
def myCommand():
    "listens for commands"
    r = sr.Recognizer()
    with sr.Microphone() as source:
        #r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        print(Fore.WHITE + '\nSpeak...')
        audio = r.listen(source)
    try:
        command = r.recognize_google(audio).lower()
        print(Fore.BLUE + 'You said: ' + command + '\n')
    #loop back to continue to listen for commands if unrecognizable speech is received
    except sr.UnknownValueError:
        #print('....')
        command = myCommand();
    return command

#print("Talk")

bot_message = ""
while bot_message != "Goodbye :(":
	message = myCommand()
	
	#print("Sending message now...")
	
	r = requests.post('http://localhost:5002/webhooks/rest/webhook', json={"message": message})
	
	print(Fore.YELLOW + "Cube says: ", end=' ')
	#print(r.json())
	for i in r.json():
		bot_message = i['text']
		#if 'buttons' in i:
		#	print(i['buttons'])
		print(Fore.YELLOW + f"{bot_message}")
		
		options=[]
		if 'buttons' in i:
			for j in i['buttons']:
				options.append(j['title'])
				print(Fore.YELLOW + "-"+f"{j['title']}")
		
		
	speak = winc1.Dispatch("SAPI.SpVoice")
	speak.Speak(bot_message)
	for k in options:
		speak.Speak(k)