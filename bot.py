from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType
import asyncio
import json
from binanceparser import *

with open('config.json', 'r') as configfile:
    config = json.load(configfile)
    BOT_TOKEN = config['bot_token']
    global fiat
    fiat = config['fiat']


async def showMerchants(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'ch_tobuy':
        await state.update_data(tradeType='buy')
    elif callback_query.data == 'ch_tosell':
        await state.update_data(tradeType='sell')
    else:
        await state.update_data(asset=callback_query.data)
    savedChoices = await state.get_data()
    topMerchants = await getTopMerchants(savedChoices['tradeType'], savedChoices['asset'], fiat, 5, 'Tinkoff')
    spread = await getTickerSpread(savedChoices['asset'], fiat, 'Tinkoff')
    actualTickerPrice = await getTickerPrice(savedChoices['asset'], fiat)
    if savedChoices['tradeType'] == 'buy':
        editedtext = '*🟢 '+savedChoices['asset'] + '* покупка\n' + 'Цена на бирже: *'+str(actualTickerPrice)+f' {fiat}*\n' + f'Спред: *{spread}*\n\n'
    else:
        editedtext = '*🔴 '+savedChoices['asset'] + '* продажа\n' + 'Цена на бирже: *'+str(actualTickerPrice)+f' {fiat}*\n' + f'Спред: *{spread}*\n\n'
    for merchant in enumerate(topMerchants):
        percentdiff = ((merchant[1] / actualTickerPrice)-1)*100
        if percentdiff > 0:
            editedtext += str(merchant[0]+1) + ') '+str(merchant[1])+f' {fiat} (+'+str(round(percentdiff, 1))+'%)\n\n'
        else:
            editedtext += str(merchant[0]+1) + ') '+str(merchant[1])+f' {fiat} ('+str(round(percentdiff, 1))+'%)\n\n'
    kb = InlineKeyboardMarkup()
    buttonRenew = InlineKeyboardButton(text="Обновить",  callback_data=savedChoices['asset'])
    if savedChoices['tradeType'] == 'buy':
        buttonChangeTrade = InlineKeyboardButton(text="Продажа",  callback_data='ch_tosell')
    else:
        buttonChangeTrade = InlineKeyboardButton(text="Покупка",  callback_data='ch_tobuy')
    buttonBack = InlineKeyboardButton(text="❮ Назад",  callback_data=savedChoices['tradeType'])
    kb.add(buttonRenew).add(buttonChangeTrade).add(buttonBack)
    try:
        await callback_query.message.edit_text(editedtext, parse_mode=types.ParseMode.MARKDOWN)
    except:
        print("Nothing changed in data")
    await callback_query.message.edit_reply_markup(kb)


async def chooseAsset(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.update_data(tradeType=callback_query.data)
    spreads = await getTickersSpreads(["USDT", "BTC", "BUSD", "BNB", "ETH", "SHIB"], fiat, 'Tinkoff')
    editedtext = "*Выберите монету:*"
    kb = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="USDT "+spreads["USDT"],  callback_data="USDT")
    button2 = InlineKeyboardButton(text="BTC "+spreads["BTC"],  callback_data="BTC")
    button3 = InlineKeyboardButton(text="BUSD "+spreads["BUSD"],  callback_data="BUSD")
    button4 = InlineKeyboardButton(text="BNB "+spreads["BNB"],  callback_data="BNB")
    button5 = InlineKeyboardButton(text="ETH "+spreads["ETH"],  callback_data="ETH")
    button6 = InlineKeyboardButton(text="SHIB "+spreads["SHIB"],  callback_data="SHIB")
    buttonRenew = InlineKeyboardButton(text="Обновить", callback_data=callback_query.data)
    buttonback = InlineKeyboardButton(text="❮ Назад", callback_data="mainmenu")
    kb.row(button1, button2, button3)
    kb.row(button4, button5, button6)
    kb.row(buttonRenew)
    kb.row(buttonback)
    try:
        await callback_query.message.edit_text(editedtext, parse_mode=types.ParseMode.MARKDOWN)
    except:
        print("Nothing changed in data")
    try:
        await callback_query.message.edit_reply_markup(kb)
    except:
        print("Nothing changed in data")


async def mainmenu(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    editedtext = "*Выберите тип сделки:*"
    kb = InlineKeyboardMarkup()
    buyButton = InlineKeyboardButton(text="🟢 Покупка",  callback_data="buy")
    sellButton = InlineKeyboardButton(text="🔴 Продажа",  callback_data="sell")
    kb.row(buyButton, sellButton)
    await callback_query.message.edit_text(editedtext, parse_mode=types.ParseMode.MARKDOWN)
    await callback_query.message.edit_reply_markup(kb)


async def start_handle(message: types.Message):
    formedmessage = "*Выберите тип сделки:*"
    kb = InlineKeyboardMarkup()
    buyButton = InlineKeyboardButton(text="🟢 Покупка",  callback_data="buy")
    sellButton = InlineKeyboardButton(text="🔴 Продажа",  callback_data="sell")
    kb.row(buyButton, sellButton)
    await message.answer(formedmessage, parse_mode=types.ParseMode.MARKDOWN, reply_markup=kb)


async def main():
    global bot
    bot = Bot(token=BOT_TOKEN)
    try:
        disp = Dispatcher(bot=bot, storage=MemoryStorage())
        disp.register_message_handler(start_handle, commands={"start", "restart"})
        disp.register_callback_query_handler(mainmenu, lambda c: c.data == 'mainmenu')
        disp.register_callback_query_handler(chooseAsset, lambda c: c.data == 'buy' or c.data == 'sell')
        disp.register_callback_query_handler(showMerchants, lambda c: c.data == 'USDT' or c.data == 'BTC' or c.data == 'BUSD' or c.data ==
                                             'ETH' or c.data == 'BNB' or c.data == 'SHIB' or c.data == 'ch_tobuy' or c.data == 'ch_tosell')
        await disp.start_polling()
    finally:
        await bot.close()


asyncio.run(main())
