import datetime
import requests
import base64
import json
import importlib.util
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

	def getAllCommands(self):
		spec = importlib.util.spec_from_file_location("command", "system/command.py")
		commandModule = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(commandModule)
		combinedCommands = []
		for attributeName in dir(commandModule):
			attribute = getattr(commandModule, attributeName)
			if isinstance(attribute, list):
				combinedCommands.extend(attribute)
		combinedCommands = list(set(combinedCommands))
		combinedCommands.sort()
		return combinedCommands
	def startInList(self, getList: list or str, text=None, returnText = False):
		if type(getList) == str:
			getList = list(getList)
		if text is None:
			text = self.text.upper()
		for item in getList:
			if text.startswith(item):
				if returnText:
					return len(item), item
				else:
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
	def unpackList(self, getList: list, upperAll=False):
		if not upperAll:
			getList = [item for sublist in getList for item in sublist]
		else:
			getList = [item.upper() for sublist in getList for item in sublist]
		return getList
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
