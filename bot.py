from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils import executor
import requests
import logging
import asyncio
from bs4 import BeautifulSoup
import re

API_TOKEN = '7511573802:AAFIvNDQqC8JI4cIX63MwAMriJOpceHF9PA'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

user_data = {}

@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.reply("Привет! Введи свой логин:")

@dp.message_handler(lambda msg: 'username' not in user_data.get(msg.from_user.id, {}))
async def receive_login(message: Message):
    user_data[message.from_user.id] = {'username': message.text.strip()}
    await message.reply("Теперь введи пароль:")

@dp.message_handler(lambda msg: 'password' not in user_data.get(msg.from_user.id, {}))
async def receive_password(message: Message):
    user_data[message.from_user.id]['password'] = message.text.strip()
    
    login_url = 'https://mpets.mobi/welcome'
    session = requests.Session()
    response = session.get(login_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    captcha_img = soup.find('img', {'src': re.compile(r'/captcha\?r=\d+')})
    
    if captcha_img:
        captcha_url = 'https://mpets.mobi' + captcha_img['src']
        user_data[message.from_user.id]['captcha_url'] = captcha_url
        user_data[message.from_user.id]['session'] = session
        await message.reply(f"Пожалуйста, решите капчу по следующему URL: {captcha_url} и отправьте ответ в формате 'captcha: решение'.")
    else:
        await message.reply("Не удалось получить URL капчи. Попробуйте снова.")

@dp.message_handler(lambda msg: msg.text.startswith('captcha:'))
async def receive_captcha(message: Message):
    user_id = message.from_user.id
    captcha_solution = message.text.split("captcha:")[1].strip()
    
    if 'session' not in user_data.get(user_id, {}):
        await message.reply("Не удалось найти активную сессию. Попробуйте снова.")
        return
    
    session = user_data[user_id]['session']
    login_url = 'https://mpets.mobi/login'
    data = {
        'name': user_data[user_id]['username'],
        'password': user_data[user_id]['password'],
        'captcha': captcha_solution
    }
    
    response = session.post(login_url, data=data)
    
    if 'welcome' in response.url:
        await message.reply("Авторизация успешна, бот запущен!")
        user_data[user_id]['authorized'] = True
        asyncio.create_task(start_automation(user_id, session))
    else:
        await message.reply("Ошибка авторизации. Проверьте логин, пароль и капчу.")

async def start_automation(user_id, session):
    while True:
        if user_data.get(user_id, {}).get('authorized'):
            # Кормление
            for _ in range(5):
                session.get('https://mpets.mobi/?action=food')
                await asyncio.sleep(60)  # 1 минута ожидания
            
            # Игры
            for _ in range(5):
                session.get('https://mpets.mobi/?action=play')
                await asyncio.sleep(60)  # 1 минута ожидания
            
            # Выставка
            for _ in range(5):
                session.get('https://mpets.mobi/show')
                await asyncio.sleep(60)  # 1 минута ожидания
            
            # Поляна
            for _ in range(5):
                session.get('https://mpets.mobi/glade_dig')
                await asyncio.sleep(60)  # 1 минута ожидания

            # Перерыв
            await asyncio.sleep(2 * 60 * 60)  # 2 часа

            # Прогулка
            session.get('https://mpets.mobi/go_travel?id=4')
            await asyncio.sleep(12 * 60 * 60)  # 12 часов перерыва

        else:
            await asyncio.sleep(60)  # Проверка авторизации каждую минуту

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)