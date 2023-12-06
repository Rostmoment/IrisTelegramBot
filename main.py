# импортируем модули
import logging
import jsonpickle
import string
import random
import datetime
import asyncio
import sqlite3 as sq
from aiogram import Bot, Dispatcher, types
from aiogram.utils import markdown
# Импортируем остальные модули
from system.bot import *
from system.command import *
# Кастом модуль, посмотрите dbManager.py в папке functions, чтобы увидеть как он работает
from functions.dbManager import Database, Functions
# Инициализация логирования
logging.basicConfig(level=logging.INFO)
# Инициализация бота и диспетчера
bot = Bot(token=token, parse_mode="HTML")
dp = Dispatcher()
permissions = {
    "can_send_messages": False,
    "can_send_other_messages": False
}
allowedLetters = [" ", "І", "Є", "Ї", "А", "Б", "В", "Г", "Д", "Е", "Ё", "Ж", "З", "И", "Й", "К", "Л", "М", "Н", "О", "П", "Р", "С", "Т", "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ъ", "Ы", "Ь", "Э", "Ю", "Я"]
stringDatetimeFormat = "%Y-%m-%d %H:%M:%S.%f"
# Определение обработчика сообщений
@dp.message()
async def getMessageText(msg: types.Message):
    # Просто чтобы было удобнее
    global userRank, message
    text = msg.text
    send = msg.answer
    reply = msg.reply
    db = sq.connect("users.db")
    cursor = db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER,
    premium INTEGER
    )""")
    db.commit()
    cursor.execute(f"SELECT id FROM users WHERE id = {msg.from_user.id}")
    userData = cursor.fetchall()
    # Записываем есть ли у пользователя премиум
    premium = False
    if len(userData) == 0:
        cursor.execute(f"INSERT INTO users (id, premium) VALUES({msg.from_user.id}, 0)")
        db.commit()
    else:
        cursor.execute(f"SELECT premium FROM users WHERE id = {msg.from_user.id}")
        premium = cursor.fetchall()
        premium = premium[0][0]
        premium = bool(premium)
    # Подключаем класс функций
    functions = Functions(text)
    # Получаем настройки из json файлов
    botData = functions.loadJson("settings/settings.json")
    commandSettings = functions.loadJson("settings/commandSettings.json")
    # Создаем/загружаем файл с данными
    db = Database(sq.connect(f"chats/{msg.chat.id}.db"))
    tables = db.CreateDB()
    Database(tables).CreateDB()
    # Используем try, чтобы обработать возможные ошибки и вызвать finally
    try:
        # Создаем новую переменную для редактирования таблиц
        tablesData = tables.cursor()
        # Если нету записи об пользователе то создаем, а если есть то обновляем данные которые не актуальные
        db.updateUsers(msg)
        if msg.chat.type != "private":
            db.addMsgToCount(msg)
        # Сохраняем ранг пользователя в переменную rank чтобы потом проверять какой ранг админа у него
        tablesData.execute(f"SELECT rank FROM users WHERE id = {msg.from_user.id}")
        rank = tablesData.fetchall()[0][0]
        if msg.reply_to_message:
            tablesData.execute(f"SELECT rank FROM users WHERE id = {msg.reply_to_message.from_user.id}")
            userRank = tablesData.fetchall()[0][0]
        # Если сообщения без текста то не проверяем его
        if not msg.text:
            return
        if msg.chat.type == "private":
            await send("Бот работает только в чатах!")
        # JSON сообщения
        if functions.startInList(getJson):
            with open("json.txt", "w") as fh:
                fh.write(str(jsonpickle.encode(msg)))
            fileToSend = types.FSInputFile("json.txt")
            await msg.answer_document(fileToSend)
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
            if not msg.reply_to_message:
                tablesData.execute(f"UPDATE users SET customNick = 0 WHERE id = {msg.from_user.id}")
            elif rank == 5:
                tablesData.execute(f"UPDATE users SET customNick = 0 WHERE id = {msg.reply_to_message.from_user.id}")
            await send("❎ Ник пользователя удалён")
            db.updateUsers(msg)
        # Смена ника
        if text.upper().startswith("+НИК"):
            nick = text[5:]
            if len(nick) > botData["symbolLimit"]:
                await send(f"✏️ Максимальная длина ника {botData['symbolLimit']} символов")
                return
            if len(nick) < 4:
                await send("✏️ В нике должно быть минимум 4 символа")
                return
            if ("ROST" in nick.upper() or "RОST" in nick.upper()) and msg.from_user.id != 1179525928:
                await send("Самый умный тут?")
                return
            for x in nick:
                if not x.upper() in (list(string.ascii_letters) + list(string.digits) + allowedLetters):
                    await send(f"✏️ Нельзя использовать символ «{x}»")
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
        # Магазин префиксов
        if text.upper().startswith("+ПРЕФИКС "):
            rostCoins = db.getValue("users", "rostCoins", f"WHERE id = {msg.from_user.id}")[0][0]
            prefix = text[9:]
            if rostCoins < 500:
                await send(f"❌ Префикс стоит 500 РостКоинов!\n🪙 Вам не хватает {500-rostCoins} РостКоинов")
                return
            status = await bot.get_chat_member(msg.chat.id, msg.from_user.id)
            status = str(status.status)
            if status == "ChatMemberStatus.MEMBER":
                await bot.promote_chat_member(msg.chat.id, msg.from_user.id, is_anonymous=False,  can_manage_chat=False, can_delete_messages=False,
                                              can_manage_video_chats=False, can_restrict_members=False, can_promote_members=False,
                                              can_invite_users=True, can_post_messages=False, can_edit_messages=False, can_pin_messages=False,
                                              can_change_info=False, can_manage_topics=False)
            await bot.set_chat_administrator_custom_title(msg.chat.id, msg.from_user.id, prefix)
            await send(f"✅ Префикс изменен на {prefix}")
            db.setValue("users", "rostCoins", rostCoins - 500, f"WHERE id = {msg.from_user.id}")
        # Передать РостКоины
        if text.upper().startswith("ПЕРЕДАТЬ"):
            text = text[9:]
            text = text.split("@")
            coins = text[0]
            coins = coins.replace(" ", "")
            if coins.isdigit():
                try:
                    coins = int(coins)
                except Exception as e:
                    await send("❌ Неверно ведено значения!")
                    return
            else:
                await send("❌ Неверно ведено значения!")
                return
            rostCoins = db.getValue("users", "rostCoins", f"WHERE id = {msg.from_user.id}")[0][0]
            if msg.reply_to_message:
                userToGetCoins = msg.reply_to_message.from_user.id
            elif len(text) == 1:
                userToGetCoins = msg.from_user.id
            else:
                userToGetCoins = text[1]
                if userToGetCoins.isdigit():
                    userToGetCoins = int(userToGetCoins)
                else:
                    userToGetCoins = await userBot.get_users(userToGetCoins)
                    userToGetCoins = userToGetCoins.id

            if coins > rostCoins:
                await send("❌ Недостаточно РостКоинов на балансе!")
                return
            db.setValue("users", "rostCoins", rostCoins-coins, f"WHERE id = {msg.from_user.id}")
            rostCoins = db.getValue("users", "rostCoins", f"WHERE id = {userToGetCoins}")[0][0]
            db.setValue("users", "rostCoins", rostCoins + coins, f"WHERE id = {userToGetCoins}")
            nick = db.getValue("users", "nick", f"WHERE id = {msg.from_user.id}")[0][0]
            user = markdown.hlink(nick, f"tg://openmessage?user_id={msg.from_user.id}")
            userToGetCoinsNick = db.getValue("users", "nick", f"WHERE id = {userToGetCoins}")[0][0]
            userToGetCoinsNick2 = markdown.hlink(userToGetCoinsNick, f"tg://openmessage?user_id={userToGetCoins}")
            await send(f"✅ {user} успешно передал {coins} РостКоинов к {userToGetCoinsNick2}!")
            return
        # Казино
        if text.upper().startswith("КАЗИНО "):
            rostCoins = db.getValue("users", "rostCoins", f"WHERE id = {msg.from_user.id}")[0][0]
            coins = text[7:]
            multiplier = random.randint(2, 4)
            if coins.isdigit():
                coins = int(coins)
            else:
                await send("❌ Ошибка! Число введено неверно!")
                return
            if coins > rostCoins:
                await send("❌ Недостаточно РостКоинов на балансе!")
                return
            if 20 > coins:
                await send("🪙 Ставка должна быть минимум 20 РостКоинов")
                return
            result = random.randint(0, 99)
            if result < 60:
                multiplier = random.uniform(0.5, 1)
                await reply(f"😞 Вам не повезло...\n🪙 -{round(coins * multiplier)} с баланса")
                db.setValue("users", "rostCoins", rostCoins - round(coins * multiplier),
                            f"WHERE id = {msg.from_user.id}")
            elif result < 90:
                await reply("❓ Не знаю радоваться ли вам или нет, но вы ничего не выиграли и ничего не потеряли")
                return
            else:
                multiplier = random.randint(2, 4)
                await reply(f"🍀 УДАЧА! +{round(coins * multiplier)} к изначальному балансу!")
                db.setValue("users", "rostCoins", rostCoins + (coins * multiplier), f"WHERE id = {msg.from_user.id}")
                return

        # Ферма
        if functions.startInList(farm):
            DK = db.getValue("users", "nextFarm", f"WHERE id = {msg.from_user.id}")[0][0]
            if DK == "0" or DK == "Rostmoment":
                DK = datetime.datetime.now()
            else:
                DK = datetime.datetime.strptime(DK, stringDatetimeFormat)
            rostCoins = db.getValue("users", "rostCoins", f"WHERE id = {msg.from_user.id}")[0][0]
            name = f"message{msg.message_id}"
            if DK > datetime.datetime.now():
                difference = DK - datetime.datetime.now()
                hours = difference.total_seconds() // 3600
                minutes = (difference.total_seconds() % 3600) // 60
                seconds = difference.total_seconds() % 60
                locals()[name] = await reply(f"❌ НЕЗАЧЁТ! Добывать РостКоины можно раз в 2 часа!\n📅 Следущая добыча через {round(hours)}ч. {round(minutes)}м. {round(seconds)}с.")
            elif DK <= datetime.datetime.now():
                coinsToAdd = random.randint(20, 75)
                if random.randint(0, 100) == 1:
                    coinsToAdd = random.randint(100, 500)
                    locals()[name] = await reply(f"🔑 УДАЧА!!! Вам удалось найти потерянный кем-то ключ от хранилища РостКоинов 🪙\n+{coinsToAdd} РостКоинов к балансу!")
                else:
                    locals()[name] = await reply(f"✅ ЗАЧЁТ! +{coinsToAdd} РостКоинов 🪙 к балансу")
                db.setValue("users", "rostCoins", rostCoins + coinsToAdd, f"WHERE id = {msg.from_user.id}")
                db.setValue("users", "nextFarm", str(datetime.datetime.now() + datetime.timedelta(hours=2)), f"WHERE id = {msg.from_user.id}")
            await asyncio.sleep(10)
            await msg.delete()
            await locals()[name].delete()
        # Профиль
        if functions.startInList(profile):
            if msg.reply_to_message:
                userIdToGetProfile = msg.reply_to_message.from_user.id
            elif len(text) == functions.startInList(profile):
                userIdToGetProfile = msg.from_user.id
            else:
                newText = text[text.find("@")+1:]
                newText = newText.strip()
                if newText.isdigit():
                    userIdToGetProfile = int(newText)
                else:
                    userIdToGetProfile = await userBot.get_users(newText)
                    userIdToGetProfile = userIdToGetProfile.id
                user = await userBot.get_users(userIdToGetProfile)
                firstDate = db.getValue("users", "id", f"WHERE id = {userIdToGetProfile}")
                if len(firstDate) == 0:
                    db.addUser(user)
            firstDate = db.getValue("users", "firstDate", f"WHERE id = {userIdToGetProfile}")[0][0]
            nick = db.getValue("users", "nick", f"WHERE id = {userIdToGetProfile}")[0][0]
            messageCount = db.getValue("users", "messageCount", f"WHERE id = {userIdToGetProfile}")[0][0]
            rostCoins = db.getValue("users", "rostCoins", f"WHERE id = {userIdToGetProfile}")[0][0]
            rank = db.getValue("users", "rank ", f"WHERE id = {userIdToGetProfile}")[0][0]
            rank = botData[f'rank{rank}'][3]
            await send(f"👤 Это пользователь {nick}\n🆔 Его уникальное значения айди: {userIdToGetProfile}\n⭐ В этом чате он является {rank}\n📅 Впервые в этом чате появиля в {firstDate}\n💬 Он в этом чате отправил {messageCount} сообщений\n🪙 У него на балансе {rostCoins} РостКоинов")
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
                if rank <= userRank:
                    await send("📝 Ранг модератора недостаточен, чтобы наказывать как-то модератора старшему или равному по рангу")
                    return
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
            tablesData.execute(f"SELECT rank FROM users WHERE id = {user.id}")
            userRank = tablesData.fetchall()[0][0]
            if rank <= userRank:
                await send("📝 Ранг модератора недостаточен, чтобы наказывать как-то модератора старшему или равному по рангу")
                return
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
                if rank <= userRank:
                    await send("📝 Ранг модератора недостаточен, чтобы наказывать как-то модератора старшему или равному по рангу")
                    return
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
            tablesData.execute(f"SELECT rank FROM users WHERE id = {user.id}")
            userRank = tablesData.fetchall()[0][0]
            if rank <= userRank:
                await send("📝 Ранг модератора недостаточен, чтобы наказывать как-то модератора старшему или равному по рангу")
                return
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
                if rank <= userRank:
                    await send("📝 Ранг модератора недостаточен, чтобы наказывать как-то модератора старшему или равному по рангу")
                    return
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
            tablesData.execute(f"SELECT rank FROM users WHERE id = {user}")
            userRank = tablesData.fetchall()[0][0]
            if rank <= userRank:
                await send("📝 Ранг модератора недостаточен, чтобы наказывать как-то модератора старшему или равному по рангу")
                return
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
        # Топ по ростКоинам
        if text.upper().startswith("РТОП"):
            if rank < commandSettings["topCommand"]:
                rank = botData[f'rank{commandSettings["topCommand"]}'][0]
                await send(f"Команда доступна только с ранга «{rank}» ({commandSettings['topCommand']})")
                return
            tablesData.execute(f"SELECT id, rostCoins FROM users WHERE rostCoins>0")
            res = tablesData.fetchall()
            totalCoins = 0
            N = text[5:]
            for x in range(len((res))):
                totalCoins += res[x][1]
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
            text += f"📊 Топ {N} самых богатых участников чатa по РостКоинам 🪙\n\n"
            top = functions.top(N, res)
            for i in range(1, N + 1):
                tablesData.execute(f"SELECT nick FROM users WHERE id = {top[i - 1][0]}")
                res = tablesData.fetchall()
                hyperlink = markdown.hlink(res[0][0], f"tg://openmessage?user_id={top[i - 1][0]}")
                text += f"{i}. {hyperlink} — {top[i - 1][1]}\n"
            text += f"\nОбщее количесвто РостКоинов 🪙 в участников: {totalCoins}"
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
    # Используем finally чтобы после обработки команды либо ошибки применить изменения и закрыть бд
    finally:
        tables.commit()
        tables.close()
# Чтобы бот НЕ читал сообщения кода он выключен, это нужно чтобы он не упал иза обробки слишком большого количества сообщений
async def on_startup(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
# Запускаем бота
async def start():
    dp.startup.register(on_startup)
    await userBot.start()
    await dp.start_polling(bot)
    await asyncio.Future()
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
