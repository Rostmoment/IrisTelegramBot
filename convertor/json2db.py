import json
import os
import sqlite3
json_folder = 'chats'
db_connection = sqlite3.connect('data.db')
db_cursor = db_connection.cursor()
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        rank INTEGER,
        nick TEXT,
        messageCount INTEGER,
        warn INTEGER,
        firstDate TEXT,
        id INTEGER,
        customNick INTEGER,
        username TEXT
    )
''')
field_mapping = {
    'rank': 'rank',
    'nick': 'nick',
    'message': 'messageCount',
    'varn': 'warn',
    'registration': 'firstDate',
    'Id': 'id',
    'CustomNick': 'customNick',
    'Username': 'username'
}
for filename in os.listdir(json_folder):
    if filename.endswith('.json'):
        print(filename)
        with open(os.path.join(json_folder, filename), 'r') as json_file:
            data = json.load(json_file)
            user_data = {
                db_field: data[json_field]
                for json_field, db_field in field_mapping.items()
            }
            db_cursor.execute('''
                INSERT INTO users (rank, nick, messageCount, warn, firstDate, id, customNick, username)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_data['rank'], user_data['nick'], user_data['messageCount'], user_data['warn'], user_data['firstDate'], user_data['id'], user_data['customNick'], user_data['username']))
db_connection.commit()
db_connection.close()
