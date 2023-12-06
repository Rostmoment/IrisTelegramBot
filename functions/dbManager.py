from .functions import *
func = Functions()
class Database:
    def __init__(self, tables):
        self.tables = tables
    def username2id(self, data: str):
        TableData = self.tables.cursor()
        data = data.replace(" ", "")
        if not func.startInList("123456789", data):
            TableData.execute(f"SELECT id FROM users WHERE username = '{data}'")
        else:
           TableData.execute(f"SELECT username FROM users WHERE id = {data}")
        userData = TableData.fetchall()
        if len(userData) == 1:
            return userData[0][0]
        elif len(userData) == 0:
            return "0"

    def setValue(self, tableName: str, valueName: str, value: str or int, conditions = None):
        TableData = self.tables.cursor()
        if conditions is None:
            if type(value) == type(1):
                TableData.execute(f"UPDATE {tableName} SET {valueName} = {value}")
            else:
                TableData.execute(f"UPDATE {tableName} SET {valueName} = '{value}'")
        else:
            if type(value) == type(1):
                TableData.execute(f"UPDATE {tableName} SET {valueName} = {value} {conditions}")
            else:
                TableData.execute(f"UPDATE {tableName} SET {valueName} = '{value}' {conditions}")
        self.tables.commit()
    def getValue(self, tableName: str, valuName: str, conditions = None):
        TableData = self.tables.cursor()
        if conditions is None:
            TableData.execute(f"SELECT {valuName} FROM {tableName}")
        else:
            TableData.execute(f"SELECT {valuName} FROM {tableName} {conditions}")
        return TableData.fetchall()
    def addMsgToCount(self, msg):
        TableData = self.tables.cursor()
        TableData.execute(f"SELECT messageCount FROM users WHERE id = {msg.from_user.id}")
        res = TableData.fetchall()[0][0]
        res += 1
        TableData.execute(f"UPDATE users SET messageCount = {res} WHERE id = {msg.from_user.id}")
        self.tables.commit()
    def CreateDB(self):
        TableData = self.tables.cursor()
        TableData.execute("""
        CREATE TABLE IF NOT EXISTS users (
        firstDate TEXT,
        nick TEXT,
        username TEXT,
        id INTEGER,
        rank INTEGER DEFAULT 0,
        customNick INTEGER DEFAULT 0,
        messageCount INTEGER DEFAULT 0,
        warn INTEGER DEFAULT 0,
        nextFarm TEXT DEFAULT 0,
        rostCoins INTEGER DEFAULT 0
        )""")
        return self.tables
    def addUser(self, user):
        TableData = self.tables.cursor()
        if user.last_name is None:
            TableData.execute(f"""INSERT INTO users (firstDate, nick, username, id, rank, customNick, messageCount, warn) 
            VALUES('{datetime.datetime.now()}', '{user.first_name}', '{user.username}', {user.id}, 0, 0, 0, 0)""")
        else:
            TableData.execute(f"""INSERT INTO users (firstDate, nick, username, id, rank, customNick, messageCount, warn) 
            VALUES('{datetime.datetime.now()}', '{user.first_name} {user.last_name}', '{user.username}', {user.id}, 0, 0, 0, 0)""")
        self.tables.commit()
    def updateUsers(self, msg):
       TableData = self.tables.cursor()
       TableData.execute(f"SELECT id FROM users WHERE id = {msg.from_user.id}")
       userData = TableData.fetchall()
       if len(userData) == 0:
           TableData.execute(f"""INSERT INTO users (firstDate, nick, username, id, rank, customNick, messageCount, warn) 
           VALUES('{datetime.datetime.now()}', '{msg.from_user.full_name}', '{msg.from_user.username}', {msg.from_user.id}, 0, 0, 0, 0)""")
       if msg.reply_to_message:
           TableData.execute(f"SELECT id FROM users WHERE id = {msg.reply_to_message.from_user.id}")
           userData = TableData.fetchall()
           if len(userData) == 0:
               TableData.execute(f"""INSERT INTO users (firstDate, nick, username, id, rank, customNick, messageCount, warn) 
               VALUES('{datetime.datetime.now()}', '{msg.reply_to_message.from_user.full_name}', '{msg.reply_to_message.from_user.username}', {msg.reply_to_message.from_user.id}, 0, 0, 0, 0)""")
           TableData.execute(f"SELECT nick, customNick FROM users WHERE id = {msg.reply_to_message.from_user.id}")
           res = TableData.fetchall()[0]
           if not res[1] and res[0] != msg.from_user.full_name:
               TableData.execute(f"UPDATE users SET nick = '{msg.reply_to_message.from_user.full_name}' WHERE id = {msg.reply_to_message.from_user.id}")
           TableData.execute(f"SELECT username FROM users WHERE id = {msg.reply_to_message.from_user.id}")
           res = TableData.fetchall()[0][0]
           if res != msg.from_user.username:
               TableData.execute(f"UPDATE users SET username = '{msg.reply_to_message.from_user.username}' WHERE id = {msg.reply_to_message.from_user.id}")
       TableData.execute(f"SELECT nick, customNick FROM users WHERE id = {msg.from_user.id}")
       res = TableData.fetchall()[0]
       if not res[1] and res[0] != msg.from_user.full_name:
           TableData.execute(f"UPDATE users SET nick = '{msg.from_user.full_name}' WHERE id = {msg.from_user.id}")
       TableData.execute(f"SELECT username FROM users WHERE id = {msg.from_user.id}")
       res = TableData.fetchall()[0][0]
       if res != msg.from_user.username:
           TableData.execute(f"UPDATE users SET username = '{msg.from_user.username}' WHERE id = {msg.from_user.id}")
       self.tables.commit()
