from aiogram.types import (
    InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date, timedelta

from bot.data import SERVICES, TIME_SLOTS, get_masters_for_service


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Прикреплённая клавиатура снизу — всегда видна, не уплывает вверх."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться")],
            [KeyboardButton(text="📋 Мои записи")],
        ],
        resize_keyboard=True,
    )


def services_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in SERVICES:
        builder.button(text=service, callback_data=f"service:{service}")
    builder.adjust(1)
    return builder.as_markup()


def masters_kb(service: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for master in get_masters_for_service(service):
        builder.button(text=f"👩 {master}", callback_data=f"master:{master}")
    builder.button(text="◀️ Назад", callback_data="back_to_services")
    builder.adjust(1)
    return builder.as_markup()


def dates_kb() -> InlineKeyboardMarkup:
    """Генерирует кнопки на ближайшие 7 дней (кроме воскресенья — выходной)."""
    builder = InlineKeyboardBuilder()
    today = date.today()
    added = 0
    delta = 1
    while added < 7:
        day = today + timedelta(days=delta)
        if day.weekday() != 6:  # 6 = воскресенье
            label = day.strftime("%d.%m (%a)").replace(
                "Mon", "Пн").replace("Tue", "Вт").replace("Wed", "Ср"
            ).replace("Thu", "Чт").replace("Fri", "Пт").replace("Sat", "Сб")
            builder.button(text=label, callback_data=f"date:{day.isoformat()}")
            added += 1
        delta += 1
    builder.button(text="◀️ Назад", callback_data="back_to_masters")
    builder.adjust(2)
    return builder.as_markup()


def times_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in TIME_SLOTS:
        builder.button(text=slot, callback_data=f"time:{slot}")
    builder.button(text="◀️ Назад", callback_data="back_to_dates")
    builder.adjust(3)
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_booking")
    builder.button(text="❌ Отменить", callback_data="cancel_booking")
    builder.adjust(2)
    return builder.as_markup()


def my_bookings_kb(bookings: list[dict]) -> InlineKeyboardMarkup:
    """Для каждой записи — кнопка отмены с id записи в callback_data."""
    builder = InlineKeyboardBuilder()
    for b in bookings:
        label = f"❌ {b['date']} {b['time']} — {b['service']}"
        builder.button(text=label, callback_data=f"cancel:{b['id']}")
    builder.adjust(1)
    return builder.as_markup()
