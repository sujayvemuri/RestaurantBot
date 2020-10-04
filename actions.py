# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/core/actions/#custom-actions/


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from rasa_sdk import Action
from rasa_sdk.events import SlotSet, AllSlotsReset, Restarted
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
import zomatopy
import json
import smtplib
import os
import re
import warnings
warnings.filterwarnings("ignore")
#warnings.filterwarnings("ignore", category=DeprecationWarning)

from email.message import EmailMessage
#from soundex import get_soundex

def get_soundex(name):
	"""Get the soundex code for the string"""
	name = name.upper()

	soundex = ""
	soundex += name[0]

	dictionary = {"BFPV": "1", "CGJKQSXZ":"2", "DT":"3", "L":"4", "MN":"5", "R":"6", "AEIOUHWY":"."}

	for char in name[1:]:
		for key in dictionary.keys():
			if char in key:
				code = dictionary[key]
				if code != soundex[-1]:
					soundex += code

	soundex = soundex.replace(".", "")
	soundex = soundex[:4].ljust(4, "0")

	return soundex

class ActionSearchRestaurants(Action):
	def name(self):
		return 'action_restaurant'
		
	def run(self, dispatcher, tracker, domain):
		config={ "user_key":"2f6fd90e303dfefa2caa9dc48ad2d73e"}
		zomato = zomatopy.initialize_app(config)
		loc = tracker.get_slot('location')
		
		cuisines=['chinese','mexican','italian','american','south indian','north indian']
		cuisine = tracker.get_slot('cuisine')
		soundex_dct={get_soundex(value):value for value in cuisines}
		
		if get_soundex(cuisine) in soundex_dct.keys():
			cuisine=soundex_dct[get_soundex(cuisine)]
		

		price=tracker.get_slot('price')
		temp_dict={'1':[0,300],'2':[300,700],'3':[700]}
		
		
		location_detail=zomato.get_location(loc, 1)
		d1 = json.loads(location_detail)
		
		lat=d1["location_suggestions"][0]["latitude"]
		lon=d1["location_suggestions"][0]["longitude"]
		cuisines_dict={'american':1,'chinese':25,'mexican':73,'italian':55,'north indian':50,'south indian':85}
		
		lst=[]

		#for val in range(0,100,20):
		#	results=zomato.restaurant_search("", lat, lon, str(cuisines_dict.get(cuisine)),start=val)
		#	d = json.loads(results)
		#	for restaurant in d['restaurants']:
		#		lst.append((restaurant['restaurant']['name'],restaurant['restaurant']['location']['address'],float(restaurant['restaurant']['average_cost_for_two']),float(restaurant['restaurant']['user_rating']['aggregate_rating'])))

		results=zomato.restaurant_search("", lat, lon, str(cuisines_dict.get(cuisine)),1000)
		
		d = json.loads(results)
		for restaurant in d['restaurants']:
			lst.append((restaurant['restaurant']['name'],restaurant['restaurant']['location']['address'],float(restaurant['restaurant']['average_cost_for_two']),float(restaurant['restaurant']['user_rating']['aggregate_rating'])))

		temp=['max','maximum','less','lesser','not more']
	
		if len(price)==1:
			price.append(0)
	
		for idx in range(len(price)):
			if isinstance(price[idx],str):
				if price[idx].lower() in temp:
					price[idx]=0
				
		temp=['min','minimum','more','higher','greater']
	
		for value in price:
			if isinstance(value,str):
				if value.lower() in temp:
					price.remove(value)
			
		price=list(map(float,price))
		price=sorted(price)
	
		#lst=[]
		#for restaurant in d['restaurants']:
		#	lst.append((restaurant['restaurant']['name'],restaurant['restaurant']['location']['address'],float(restaurant['restaurant']['average_cost_for_two']),float(restaurant['restaurant']['user_rating']['aggregate_rating'])))
	
		lst1=sorted(lst,key=lambda x:x[3],reverse=True)
		
		if len(price)==1:
			final_lst=list(filter(lambda x:x[2]>=price[0],lst1))[:10]
		else:
			final_lst=list(filter(lambda x:x[2]>=price[0] and x[2]<=price[1],lst1))[:10]
	
		response=""
		if len(final_lst) == 0:
			response= "no results"
		else:
			for restaurant in final_lst[:5]:
				response=response+ restaurant[0]+ " in "+ restaurant[1]+" has been rated "+str(restaurant[3])+"\n"
			restaurant_final_list=final_lst[:10]
	
			file=open("body.txt","w")
			counter=1
			for restaurant in restaurant_final_list:
				file.write("{}. Restaurant Name: {}\n Restaurant locality address: {}\n Average budget for two people: {}\n Zomato user rating: {}\n\n".format(counter,restaurant[0],restaurant[1],restaurant[2],restaurant[3]))
				counter+=1		
			file.close()
		
		dispatcher.utter_message(response)
		
		#restaurant_final_list=final_lst[:10]
		
		#file=open("body.txt","w")
		#counter=1
		#for restaurant in restaurant_final_list:
		#	file.write("{}. Restaurant Name: {}\n Restaurant locality address: {}\n Average budget for two people: {}\n Zomato user rating: {}\n\n".format(counter,restaurant[0],restaurant[1],restaurant[2],restaurant[3]))
		#	counter+=1		
		#file.close()
		return [SlotSet('cuisine',cuisine),SlotSet('noresults',response=="no results")]

class ActionSearchCity(Action):
	def name(self):
		return 'action_city'
	
	def run(self, dispatcher, tracker, domain):
		url="https://en.wikipedia.org/wiki/Classification_of_Indian_cities"
		r = requests.get(url,verify=False)
		soup = BeautifulSoup(r.text, "html.parser")
		
		tier_cities=list(map(lambda x:x.text.lower(),soup.find('table',class_='wikitable').find_all('a')))
		
		synonym_names={}
		r=requests.get('https://www.scoopwhoop.com/news/whats-in-a-name/#.45rdcz1m2',verify=False)
		containers=BeautifulSoup(r.text,'html.parser').find('div',class_='article-body').find_all('h2')
		
		for container in containers:
			if re.search(r'^[0-9]{1,2}.+',container.text.strip()):
				synonym_names[container.text.strip().split()[1].lower()]=container.text.strip().split()[-1].lower()
		
		for index,value in enumerate(tier_cities):
			if value in synonym_names.keys():
				tier_cities[index]=synonym_names[value]
		
		soundex_dict_tier={get_soundex(name):name for name in tier_cities}
		soundex_dict_syn={get_soundex(key):value for key,value in synonym_names.items()}
		
		loc=tracker.get_slot('location')
		loc_soundex=get_soundex(loc)
		
		val=False
		if loc_soundex in soundex_dict_tier.keys():
			val=True
			loc=soundex_dict_tier[loc_soundex]
		if loc_soundex in soundex_dict_syn.keys() and not val:
			val=True
			loc=soundex_dict_syn[loc_soundex]
		
		return [SlotSet('location',loc),SlotSet('location_type',val)]

class ActionSendMail(Action):
	def name(self):
		return 'action_send_mail'
	
	def run(self,dispatcher,tracker,domain):

		body=""
		file=open('body.txt','r')
		
		for line in file.readlines():
			body+=line
		file.close()
		
		gmail_user="google@gmail.com"
		gmail_password="password"
		
		msg = EmailMessage()
		msg.set_content(body)

		msg['Subject'] = " Restaurant recommendations in "+tracker.get_slot("location").title()
		msg['From'] = gmail_user
		msg['To'] = tracker.get_slot('email')

		# Send the message via our own SMTP server.
		try:
			server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
			server.login(gmail_user, gmail_password)
			server.send_message(msg)
			server.quit()
			dispatcher.utter_template("utter_email_Sent", tracker)
		
		except:
			dispatcher.utter_template("utter_email_error", tracker)
		
		return [SlotSet('email',msg['To'])]

class ActionGetCuisineSlection(Action):
	def name(self):
		return 'action_get_cuisine'
	
	def run(self,dispatcher,tracker,domain):
		val=tracker.get_slot('num')
		cuisines=['chinese','mexican','italian','american','south indian','north indian']
		
		return [SlotSet('cuisine',cuisines[int(val)-1])]

class ActionGetPriceSelection(Action):
	def name(self):
		return 'action_get_price'
	
	def run(self,dispatcher,tracker,domain):
		val=tracker.get_slot('num')
		temp_dict={'1':[0,300],'2':[300,700],'3':[700]}
		
		return [SlotSet('price',temp_dict[str(val)])]

class ActionResetSlots(Action):
	def name(self):
		return 'action_reset'
		
	def run(self, dispatcher, tracker, domain):
		#AllSlotsReset()
		return [AllSlotsReset()]

class ActionRestarted(Action): 	
    def name(self): 		
        return 'action_restarted' 	
    def run(self, dispatcher, tracker, domain): 
        return[Restarted()] 