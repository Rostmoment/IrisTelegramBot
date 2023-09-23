import datetime
import requests
import base64
import json
from convertor.entities import *
time_units = {
	"минута": 60,
	"минут": 60,
	"минуты": 60,
	"мн": 60,
	"час": 3600,
	"ч": 3600,
	"часов": 3600,
	"часа": 3600,
	"день": 86400,
	"дней": 86400,
	"дн": 86400,
	"дня": 86400,
	"неделя": 604800,
	"недели": 604800,
	"недель": 604800,
	"нд": 604800,
	"месяц": 2629800,
	"месяцев": 2629800,
	"месяца": 2629800,
	"мс": 2629800
}
class Functions:
	def __init__(self, text = None):
		if text is None:
			self.text = "Hello World!"
			return
		self.text = text
	def startInList(self, getList: list or str, text=None):
		if type(getList) == str:
			getList = list(getList)
		if text is None:
			text = self.text.upper()
		for item in getList:
			if text.startswith(item):
				return len(item)
		return 0
	def toSymbol(self, text: str, symbol: str):
		newText = ""
		for item in text:
			if item == symbol:
				break
			else:
				newText+=item
		return newText
	def createSticker(self, msg):
		entities = []
		if msg.entities:
			entities = convertEntities(msg.entities)
		json = {
			"type": "quote",
			"format": "webp",
			"backgroundColor": "#1b1429",
			"width": 512,
			"height": 768,
			"scale": 2,
			"messages": [
				{
					"entities": entities,
					"chatId": 66478514,
					"avatar": True,
					"from": {
						"id": msg.from_user.id,
						"first_name": msg.from_user.full_name,
						"last_name": "",
						"username": msg.from_user.username,
						"language_code": msg.from_user.language_code,
						"title": msg.from_user.full_name,
						"photo": {
							"small_file_id": "AQADAgADCKoxG7Jh9gMACBbSEZguAAMCAAOyYfYDAATieVimvJOu7M43BQABHgQ",
							"small_file_unique_id": "AQADFtIRmC4AA843BQAB",
							"big_file_id": "AQADAgADCKoxG7Jh9gMACBbSEZguAAMDAAOyYfYDAATieVimvJOu7NA3BQABHgQ",
							"big_file_unique_id": "AQADFtIRmC4AA9A3BQAB"
						},
						"type": "private",
						"name": msg.from_user.full_name
					},
					"text": msg.text,
					"replyMessage": msg.reply_to_message
				}
			]
		}
		try:
			response = requests.post("https://bot.lyo.su/quote/generate", json=json).json()
			buffer = base64.b64decode(response["result"]["image"].encode("utf-8"))
			open("sticker.webp", "wb").write(buffer)
			return True
		except Exception as e:
			print(e)
			return False
	def loadJson(self, dir: str):
		with open(dir) as fh:
			data = json.load(fh)
		return data
	def toDate(self, time: str):
		time_str = ""
		for x in time:
			if x in list("1234567890"):
				time_str += x
			else:
				break
		time_str += " "
		time_str += time[len(time_str)-1:]
		time_str = time_str.lower().strip()
		try:
			value, unit = time_str.split()
			value = float(value)
			if unit not in time_units:
				raise ValueError
			return datetime.datetime.now() + datetime.timedelta(seconds=value * time_units[unit])
		except (ValueError, KeyError):
			return ValueError
	def top(self, N: int, userList: list):
		res = sorted(userList, key = lambda x: x[1], reverse = True)[:N]
		return res
