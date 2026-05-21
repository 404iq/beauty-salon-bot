from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from bot.keyboards import main_menu_kb

router = Router()

WELCOME_TEXT = (
    "💅 <b>Добро пожаловать в салон красоты «Грация»!</b>\n\n"
    "Здесь вы можете:\n"
    "• записаться к мастеру\n"
    "• посмотреть и отменить свои записи\n\n"
    "Выберите действие в меню ниже 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())
