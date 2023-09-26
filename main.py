# импортируем модули
import logging
import os
import random
import datetime
import asyncio
import sqlite3 as sq
from aiogram import Bot, Dispatcher, types
from aiogram.utils import markdown
# Импортируем остальные модули
from system.command import *
# Кастом модуль, посмотрите dbManager.py в папке functions, чтобы увидеть как он работает
from functions.dbManager import Database, Functions
# Инициализация логирования
logging.basicConfig(level=logging.INFO)
# Инициализация бота и диспетчера
from system.bot import *
bot = Bot(token=token, parse_mode="HTML")
dp = Dispatcher()
permissions = {
    "can_send_messages": False,
    "can_send_other_messages": False
}
# Определение обработчика сообщений
@dp.message()
async def getMessageText(msg: types.Message):
    # Просто чтобы было удобнее
    text = msg.text
    send = msg.answer
    # Подключаем класс функций
    functions = Functions(text)
    botData = functions.loadJson("settings/settings.json")
    commandSettings = functions.loadJson("settings/commandSettings.json")
    # Создаем/загружаем файл с данными
    db = Database(sq.connect("data.db"))
    tables = db.CreateDB()
    Database(tables).CreateDB()
    # Используем try, чтобы обработать возможные ошибки и вызвать finally
    try:
        # Создаем новую переменную для редактировния таблицы
        tablesData = tables.cursor()
        # Если нету записи об пользователе то создаем, а если есть то обновляем данные которые не актуальные
        db.updateUsers(msg)
        if msg.chat.type != "private":
            db.addMsgToCount(msg)
        # Сохраняем ранг пользователя в переменную rank чтобы потом проверять какой ранг админа у него
        tablesData.execute(f"SELECT rank FROM users WHERE id = {msg.from_user.id}")
        rank = tablesData.fetchall()[0][0]
        # Если сообщения без текста то не проверяем его
        if not msg.text:
            return
        # Снимает всех с админа
        if text.upper() in ["/СНЯТЬ ВСЕХ", "!СНЯТЬ ВСЕХ", ".СНЯТЬ ВСЕХ"]:
            if rank < commandSettings["adminEditor"]:
                rank = botData[f'rank{commandSettings["adminEditor"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['adminEditor']})")
                return
            tablesData.execute("UPDATE users SET rank = 0")
            await send("❎ Все модераторы разжалованы\n\n💬 Создатель чата может ввести команду\n\"<code>восстановить создателя\"</code>")
            return
        # Проверяем есть ли у команд префикс, если да то удаляем, все команды которые выше этой строки работают только с префиксом
        if text[0] in ["!", ".", "/"]:
            text = text[1:]
        # Удаление ника
        if text.upper() == "-НИК":
            tablesData.execute(f"UPDATE users SET customNick = 0 WHERE id = {msg.from_user.id}")
            await send("❎ Ник пользователя удалён")
            db.updateUsers(msg)
        # Смена ника
        if text.upper().startswith("+НИК"):
            nick = text[5:]
            if len(nick) > botData["symbolLimit"]:
                await send(f"✏️ Максимальная длина ника {botData['symbolLimit']} символов")
                return
            tablesData.execute(f"SELECT nick, id FROM users WHERE nick = '{nick}'")
            res = tablesData.fetchall()
            if len(res) != 0:
                hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={tablesData.fetchall()[0][1]}")
                await send(f"❌ Такой ник уже занят пользователем {hyperlink}!")
                return
            tablesData.execute(f"UPDATE users SET customNick = 1 WHERE id = {msg.from_user.id}")
            tablesData.execute(f"UPDATE users SET nick = '{nick}' WHERE id = {msg.from_user.id}")
            await send(f"✅ Ник пользователя изменен на «{nick}»")
        # Список админов
        if functions.startInList(whoAdmin):
            totalAdmins = 0
            for x in range(1, 6):
                tablesData.execute(f"SELECT nick, id FROM users WHERE rank = {x}")
                res = tablesData.fetchall()
                totalAdmins += len(res)
            if totalAdmins == 0:
                await send("🗓 В этом чате царит анархия...")
                return
            text = ""
            for x in range(-5, 0):
                x = -x
                rank = botData[f"rank{x}"]
                tablesData.execute(f"SELECT nick, id, username FROM users WHERE rank = {x}")
                res = tablesData.fetchall()
                if len(res) == 1:
                    status = await userBot.get_users(res[0][2])
                    status = status.status
                    if status == enums.UserStatus.ONLINE:
                        status = "🎾"
                    else:
                        status = "🏐"
                    hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={res[0][1]}")
                    text += f"{'⭐'*x} {rank[0]}\n{status} {hyperlink}\n\n"
                elif len(res) > 1:
                    text += f"{'⭐' * x} {rank[4]}\n"
                    for y in range(len(res)):
                        status = await userBot.get_users(res[y][2])
                        status = status.status
                        if status == enums.UserStatus.ONLINE:
                            status = "🎾"
                        else:
                            status = "🏐"
                        hyperlink = markdown.hlink(res[y][0], f"tg://openmessage?user_id={res[y][1]}")
                        text += f"{status} {hyperlink}\n"
                    text += "\n"
            await send(text)
        # Востановить создателя
        if functions.startInList(returnOwner):
            owner = await bot.get_chat_member(msg.chat.id, msg.from_user.id)
            owner = owner.status
            if str(owner) == "ChatMemberStatus.CREATOR":
                tablesData.execute(f"UPDATE users SET rank = 5 WHERE id = {msg.from_user.id}")
                await send("✅ Создатель беседы восстановлен в правах")
        # Смена ранга человека
        if text.upper().startswith("НАЗНАЧИТЬ"):
            parameters = text.split(" ")
            if rank < commandSettings["adminEditor"]:
                rank = botData[f'rank{commandSettings["adminEditor"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['adminEditor']})")
                return
            if not parameters[1].isdigit():
                await send("❌ ранг должен был целым числом от 0 до 5")
                return
            if 0 > int(parameters[1]) > 5:
                await send("❌ ранг должен был целым числом от 0 до 5")
                return
            rank = int(parameters[1])
            if msg.reply_to_message:
                tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.reply_to_message.from_user.id}")
                hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.reply_to_message.from_user.id}")
                tablesData.execute(f"UPDATE users SET rank = {rank} WHERE id = {msg.reply_to_message.from_user.id}")
            else:
                user = parameters[2][1:]
                print(user)
                if user.isdigit():
                    tablesData.execute(f"SELECT nick, id FROM users WHERE id = {int(user)}")
                    res = tablesData.fetchall()
                    if len(res) == 0:
                        user = await userBot.get_users(int(user))
                        if not user.is_contact:
                            db.addUser(user)
                        else:
                            return
                        tablesData.execute(f"SELECT nick, id FROM users WHERE id = {user.id}")
                        res = tablesData.fetchall()
                else:
                    user = await userBot.get_users(user)
                    tablesData.execute(f"SELECT nick, id FROM users WHERE id = {user.id}")
                    res = tablesData.fetchall()
                    if len(res) == 0:
                        if not user.is_contact:
                            db.addUser(user)
                        else:
                            return
                    tablesData.execute(f"SELECT nick, id FROM users WHERE id = {user.id}")
                    res = tablesData.fetchall()
                    tablesData.execute(f"UPDATE users SET rank = {rank} WHERE id = {user.id}")
                hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={res[0][1]}")
            rank = botData[f'rank{rank}'][3]
            await send(f"{hyperlink} назначен {rank}")
        # Команда, которая показывает айди пользователя
        if functions.startInList(getId):
            if rank < commandSettings["getId"]:
                rank = botData[f'rank{commandSettings["getId"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['getId']})")
                return
            # Если сообщение отправлено в ответ на другое сообщения, то выводим айди пользователя, которому ответили на сообщения
            if msg.reply_to_message:
                tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.reply_to_message.from_user.id}")
                hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.reply_to_message.from_user.id}")
                await send(f"🆔 пользователя {hyperlink} равен\n<code>@{msg.reply_to_message.from_user.id}</code>\n🆔 сообщения равен <code>@{msg.message_id}</code>")
            # Если сообщения не в ответ и длина сообщения равно длине команды (то-есть никто не указан в сообщении) выводим айди пользователя, который написал команду
            elif not msg.reply_to_message and len(text) == functions.startInList(getId):
                tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.from_user.id}")
                hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.from_user.id}")
                await send(f"🆔 пользователя {hyperlink} равен\n<code>@{msg.from_user.id}</code>\n🆔 чата равен <code>@{msg.chat.id}</code>")
            # Если сообщения не подходит ни под одно из условий выше, то выполняем 3 вариант
            else:
                user = text[functions.startInList(getId) + 2:]
                if functions.startInList("123456789", user):
                    user = await userBot.get_users(int(user))
                else:
                    user = await userBot.get_users(user)
                tablesData.execute(f"SELECT nick FROM users WHERE id = {user.id}")
                res = tablesData.fetchall()
                if len(res) == 0:
                    if not user.is_contact:
                        db.addUser(user)
                        tablesData.execute(f"SELECT nick FROM users WHERE id = {user.id}")
                        res = tablesData.fetchall()
                        hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={user.id}")
                    else:
                        hyperlink = markdown.hlink("???", f"tg://openmessage?user_id={user.id}")
                else:
                    hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={user.id}")
                await send(f"🆔 пользователя {hyperlink} равен\n<code>@{user.id}</code>")
        # Создание стикеров с сообщения
        if functions.startInList(sticker):
            text = text[len(functions.toSymbol(text, " ")):]
            textForSticker = text[len(functions.toSymbol(text, " ")):]
            textForSticker = textForSticker.strip()
            if msg.reply_to_message:
                functions.createSticker(msg.reply_to_message)
                stickerToSend = types.FSInputFile("sticker.webp")
                await msg.answer_sticker(sticker=stickerToSend)
                os.remove("sticker.webp")
        # Отметить всех
        if functions.startInList(tagAll):
            if rank < commandSettings["tagAll"]:
                rank = botData[f'rank{commandSettings["tagAll"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['tagAll']})")
                return
            text = text[functions.startInList(tagAll)+1:]
            tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.from_user.id}")
            hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.from_user.id}")
            textToSend = f"📢 Модератор {hyperlink} объявил общий сбор! (тут короче количесвто)\n"
            async for member in userBot.get_chat_members(msg.chat.id):
                if not member.user.username is None:
                    textToSend += f"@{member.user.username} "
            textToSend = textToSend.replace("тут короче количесвто", str(textToSend.count("@")))
            if text:
                textToSend += f"\n\n💬 ТЕКСТ ОБЪЯВЛЕНИЯ: \n{text}"
            await send(textToSend)
        # Бан
        if functions.startInList(ban):
            prichina, period = "", ""
            if rank < commandSettings["ban"]:
                rank = botData[f'rank{commandSettings["mute"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['ban']})")
                return
            text = text[functions.startInList(ban)+1:]
            text = text.strip()
            parameters = text.split("\n")
            tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.from_user.id}")
            moderlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.from_user.id}")
            if msg.reply_to_message:
                tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.reply_to_message.from_user.id}")
                hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.reply_to_message.from_user.id}")
                if len(text) == 0:
                    await bot.ban_chat_member(chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id, until_date=datetime.datetime.now()+datetime.timedelta(days=1))
                    await send(f"🔴 {hyperlink} забанен на 1 день\n👤 Модератор: {moderlink}")
                    return
                if len(parameters) > 1:
                    for x in range(1, len(parameters)):
                        prichina += f"{parameters[x]}\n"
                    await send(f"🔴 {hyperlink} забанен на {parameters[0]}\n👤 Модератор: {moderlink}\n💬 Причина: {prichina}")
                    await bot.ban_chat_member(chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id, until_date=functions.toDate(parameters[0]))
                else:
                    if functions.toDate(parameters[0]) is ValueError:
                        for x in parameters:
                            prichina += x
                        await bot.ban_chat_member(chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id, until_date=datetime.datetime.now() + datetime.timedelta(days=1))
                        await send(f"🔴 {hyperlink} забанен на 1 день\n👤 Модератор: {moderlink}\n💬 Причина: {prichina}")
                        return
                    await bot.ban_chat_member(chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id, until_date=functions.toDate(parameters[0]))
                    await send(f"🔴 {hyperlink} забанен на {parameters[0]}\n👤 Модератор: {moderlink}")
                return
            if len(parameters) > 1:
                for x in range(1, len(parameters)):
                    prichina += f"{parameters[x]}\n"
            parameters = parameters[0]
            parameters.strip()
            if parameters.count("@") > 0:
                period = functions.toSymbol(parameters, "@")
                user = parameters[len(functions.toSymbol(parameters, "@"))+1:]
                user = user.strip()
            else:
                user = parameters[1:]
            if not functions.startInList("123456789", user):
                user = await userBot.get_users(user)
            else:
                user = await userBot.get_users(int(user))
            tablesData.execute(f"SELECT nick FROM users WHERE id = {user.id}")
            res = tablesData.fetchall()
            if len(res) == 0:
                if not user.is_contact:
                    db.addUser(user)
                    tablesData.execute(f"SELECT nick FROM users WHERE id = {user.id}")
                    res = tablesData.fetchall()
                    hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={user.id}")
                else:
                    hyperlink = markdown.hlink("???", f"tg://openmessage?user_id={user.id}")
            else:
                hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={user.id}")
            if period:
                await bot.ban_chat_member(chat_id=msg.chat.id, user_id=user.id, until_date=functions.toDate(period))
                if prichina:
                    await send(f"🔴 {hyperlink} забанен на {period}\n👤 Модератор: {moderlink}\n💬 Причина: {prichina}")
                else:
                    await send(f"🔴 {hyperlink} забанен на {period}\n👤 Модератор: {moderlink}")
                return
            await bot.ban_chat_member(chat_id=msg.chat.id, user_id=user.id, until_date=datetime.datetime.now() + datetime.timedelta(days=1))
            if prichina:
                await send(f"🔴 {hyperlink} забанен на 1 день\n👤 Модератор: {moderlink}\n💬 Причина: {prichina}")
            else:
                await send(f"🔴 {hyperlink} забанен на 1 день\n👤 Модератор: {moderlink}")
        # Мут
        if functions.startInList(mute):
            prichina, period = "", ""
            if rank < commandSettings["mute"]:
                rank = botData[f'rank{commandSettings["mute"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['mute']})")
                return
            text = text[functions.startInList(mute)+1:]
            text = text.strip()
            parameters = text.split("\n")
            tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.from_user.id}")
            moderlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.from_user.id}")
            if msg.reply_to_message:
                tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.reply_to_message.from_user.id}")
                hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.reply_to_message.from_user.id}")
                if len(text) == 0:
                    await bot.restrict_chat_member(permissions=permissions, chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id, until_date=datetime.datetime.now()+datetime.timedelta(days=1))
                    await send(f"🔇 {hyperlink} лишается права слова на 1 день\n👤 Модератор: {moderlink}")
                    return
                if len(parameters) > 1:
                    for x in range(1, len(parameters)):
                        prichina += f"{parameters[x]}\n"
                    await send(f"🔇 {hyperlink} лишается права слова на {parameters[0]}\n👤 Модератор: {moderlink}\n💬 Причина: {prichina}")
                    await bot.restrict_chat_member(permissions=permissions, chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id, until_date=functions.toDate(parameters[0]))
                else:
                    if functions.toDate(parameters[0]) is ValueError:
                        for x in parameters:
                            prichina += x
                        await bot.restrict_chat_member(permissions=permissions, chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id, until_date=datetime.datetime.now() + datetime.timedelta(days=1))
                        await send(f"🔇 {hyperlink} лишается права слова на 1 день\n👤 Модератор: {moderlink}\n💬 Причина: {prichina}")
                        return
                    await bot.restrict_chat_member(permissions=permissions, chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id, until_date=functions.toDate(parameters[0]))
                    await send(f"🔇 {hyperlink} лишается права слова на {parameters[0]}\n👤 Модератор: {moderlink}")
                return
            if len(parameters) > 1:
                for x in range(1, len(parameters)):
                    prichina += f"{parameters[x]}\n"
            parameters = parameters[0]
            parameters.strip()
            if parameters.count("@") > 0:
                period = functions.toSymbol(parameters, "@")
                user = parameters[len(functions.toSymbol(parameters, "@"))+1:]
                user = user.strip()
            else:
                user = parameters[1:]
            if not functions.startInList("123456789", user):
                user = await userBot.get_users(user)
            else:
                user = await userBot.get_users(int(user))
            tablesData.execute(f"SELECT nick FROM users WHERE id = {user.id}")
            res = tablesData.fetchall()
            if len(res) == 0:
                if not user.is_contact:
                    db.addUser(user)
                    tablesData.execute(f"SELECT nick FROM users WHERE id = {user.id}")
                    res = tablesData.fetchall()
                    hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={user.id}")
                else:
                    hyperlink = markdown.hlink("???", f"tg://openmessage?user_id={user.id}")
            else:
                hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={user.id}")
            if period:
                await bot.restrict_chat_member(permissions=permissions, chat_id=msg.chat.id, user_id=user.id, until_date=functions.toDate(period))
                if prichina:
                    await send(f"🔇 {hyperlink} лишается права слова на {period}\n👤 Модератор: {moderlink}\n💬 Причина: {prichina}")
                else:
                    await send(f"🔇 {hyperlink} лишается права слова на {period}\n👤 Модератор: {moderlink}")
                return
            await bot.restrict_chat_member(permissions=permissions, chat_id=msg.chat.id, user_id=user.id, until_date=datetime.datetime.now() + datetime.timedelta(days=1))
            if prichina:
                await send(f"🔇 {hyperlink} лишается права слова на 1 день\n👤 Модератор: {moderlink}\n💬 Причина: {prichina}")
            else:
                await send(f"🔇 {hyperlink} лишается права слова на 1 день\n👤 Модератор: {moderlink}")

        # Кик
        if functions.startInList(kick):
            if rank < commandSettings["kick"]:
                rank = botData[f'rank{commandSettings["kick"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['kick']})")
                return
            parameters = text.split()
            if msg.reply_to_message:
                tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.reply_to_message.from_user.id}")
                hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={msg.reply_to_message.from_user.id}")
                tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.from_user.id}")
                await bot.ban_chat_member(chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id)
                await bot.unban_chat_member(chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id)
                if len(parameters) == 1:
                    await send(f"🔴 {hyperlink} был исключен с чата\n👤Модератор: {markdown.hlink(tablesData.fetchall()[0][0], f'tg://openmessage?user_id={msg.from_user.id}')}")
                    return
                else:
                    await send(f"🔴 {hyperlink} был исключен с чата\n👤Модератор: {markdown.hlink(tablesData.fetchall()[0][0], f'tg://openmessage?user_id={msg.from_user.id}')}\n💬Причина: {parameters[1]}")
                return
            if not functions.startInList("123456789", parameters[1][1]):
                user = await userBot.get_users(parameters[1][1:])
                user = user.id
            else:
                user = int(parameters[1][1:])
            tablesData.execute(f"SELECT nick FROM users WHERE id = {user}")
            hyperlink = markdown.hlink(tablesData.fetchall()[0][0], f"tg://openmessage?user_id={user}")
            await bot.ban_chat_member(chat_id=msg.chat.id, user_id=user)
            await bot.unban_chat_member(chat_id=msg.chat.id, user_id=user)
            tablesData.execute(f"SELECT nick FROM users WHERE id = {msg.from_user.id}")
            if len(parameters) == 2:
                await send(f"🔴 {hyperlink} был исключен с чата\n👤Модератор: {markdown.hlink(tablesData.fetchall()[0][0], f'tg://openmessage?user_id={msg.from_user.id}')}")
            else:
                await send(f"🔴 {hyperlink} был исключен с чата\n👤Модератор: {markdown.hlink(tablesData.fetchall()[0][0], f'tg://openmessage?user_id={msg.from_user.id}')}\n💬Причина: {parameters[2]}")
        # Проверка работает ли бот
        if text.upper() == "ПИНГ":
            await send("ПОНГ")
        if text.upper() == "ПИУ":
            await send("ПАУ")
        if text.upper() == "КИНГ":
            await send("КОНГ")
        if text.upper() == "БОТ":
            await send("✅ На месте")
        if text.upper() == "ТИК":
            await send("ТОК")
        # Топ по сообщениям
        if functions.startInList(topCommand):
            if rank < commandSettings["topCommand"]:
                rank = botData[f'rank{commandSettings["topCommand"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['topCommand']})")
                return
            tablesData.execute(f"SELECT id, messageCount FROM users WHERE messageCount>0")
            res = tablesData.fetchall()
            totalMessage = 0
            N = text[functions.startInList(topCommand)+1:]
            for x in range(len((res))):
                totalMessage += res[x][1]
            if N.isdigit() or N.isnumeric():
                N = int(N)
            else:
                N = 10
            if N > len(res):
                N = len(res)
            if N == 0 or N < 0:
                await send("📊 Количество мест должно быть больше чем 0")
                return
            text = ""
            text += f"📊 Топ {N} самых активных участников чатa\n\n"
            top = functions.top(N, res)
            for i in range(1, N + 1):
                tablesData.execute(f"SELECT nick FROM users WHERE id = {top[i - 1][0]}")
                res = tablesData.fetchall()
                hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={top[i - 1][0]}")
                text += f"{i}. {hyperlink} — {top[i - 1][1]}\n"
            text += f"\nВсего сообщений от пользователей было насчитано: {totalMessage}"
            await send(text)
        # Рандом
        if functions.startInList(rng):
            if rank < commandSettings["rng"]:
                rank = botData[f'rank{commandSettings["rng"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['rng']})")
                return
            commandTemp = text.split()
            parameters = []
            commandTemp.pop(0)
            for x in commandTemp:
                parameters.append(float(x))
            if len(parameters) == 0:
                await send(f"🎲 Случайное число из диапазона [0 --- 10] с округлением до 2 символа выпало на {round(random.uniform(0, 10), 2)}")
            elif len(parameters) == 1:
                if parameters[0] == 0:
                    await send(f"🎲 Результат оказался совершенно непредсказуемый, ни за что не поверите, но случайное число из диапазона [0 --- 0] с округлением до 2 символа выпало на 0.0\nДа, все в шоке и нет слов")
                    return
                if parameters[0] < 0:
                    await send("📝 Первое число диапазона должно быть меньше второго")
                    return
                await send(f"🎲 Случайное число из диапазона [0 --- {parameters[0]}] с округлением до 2 символа выпало на {round(random.uniform(0, parameters[0]), 2)}")
            elif len(parameters) == 2:
                if parameters[0] == parameters[1]:
                    await send(f"🎲 Результат оказался совершенно непредсказуемый, ни за что не поверите, но случайное число из диапазона [{parameters[0]} --- {parameters[0]}] с округлением до 2 символа выпало на {parameters[0]}\nДа, все в шоке и нет слов")
                    return
                if parameters[0] > parameters[1]:
                    await send("📝 Первое число диапазона должно быть меньше второго")
                    return
                await send(f"🎲 Случайное число из диапазона [{parameters[0]} --- {parameters[1]}] с округлением до 2 символа выпало на {round(random.uniform(parameters[0], parameters[1]), 2)}")
            else:
                if parameters[0] == parameters[1]:
                    await send(f"🎲 Результат оказался совершенно непредсказуемый, ни за что не поверите, но случайное число из диапазона [{parameters[0]} --- {parameters[0]}] с округлением до {int(parameters[2])} символа выпало на {parameters[0]}\nДа, все в шоке и нет слов")
                    return
                if parameters[0] > parameters[1]:
                    await send("📝 Первое число диапазона должно быть меньше второго")
                    return
                await send(f"🎲 Случайное число из диапазона [{parameters[0]} --- {parameters[1]}] с округлением до {int(parameters[2])} символа выпало на {round(random.uniform(parameters[0], parameters[1]), int(parameters[2]))}")
    # Если случилась ошибка отправляем сообщения об ошибке
    except Exception as e:
        await send(f"⚠ Ошибка в {e.__traceback__.tb_lineno} строке!\n\n<code>{e}</code>")
    # Используем finally чтобы после обработки команды либо ошибки чтобы применить изменения и закрыть бд
    finally:
        tables.commit()
        tables.close()
# Запускаем бота
async def start():
    await userBot.start()
    await dp.start_polling(bot)
    await asyncio.Future()
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
