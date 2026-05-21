import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

from bot.database import get_user_bookings, get_booking_by_id, delete_booking
from bot.keyboards import my_bookings_kb

router = Router()


@router.message(F.text == "📋 Мои записи")
async def show_bookings(message: Message):
    bookings = await get_user_bookings(message.from_user.id)

    if not bookings:
        await message.answer("У вас пока нет активных записей.\n\nЗапишитесь через кнопку «Записаться»!")
        return

    lines = ["📋 <b>Ваши записи:</b>\n"]
    for b in bookings:
        lines.append(
            f"• <b>{b['date']} {b['time']}</b> — {b['service']} ({b['master']})"
        )
    lines.append("\nНажмите на запись, чтобы отменить её:")

    await message.answer("\n".join(lines), reply_markup=my_bookings_kb(bookings))


@router.callback_query(lambda c: c.data.startswith("cancel:"))
async def cancel_booking(callback: CallbackQuery, bot: Bot):
    booking_id = int(callback.data.split(":", 1)[1])

    # Получаем детали записи ДО удаления — после удаления их уже не достать
    booking = await get_booking_by_id(booking_id)
    deleted = await delete_booking(booking_id, callback.from_user.id)

    if deleted and booking:
        # Уведомляем менеджера об отмене
        owner_chat_id = os.getenv("OWNER_CHAT_ID")
        if owner_chat_id:
            user = callback.from_user
            owner_text = (
                "🔴 <b>Запись отменена клиентом!</b>\n\n"
                f"Клиент: {user.full_name}"
                + (f" (@{user.username})" if user.username else "") + "\n"
                f"Услуга: {booking['service']}\n"
                f"Мастер: {booking['master']}\n"
                f"Дата:   {booking['date']}\n"
                f"Время:  {booking['time']}\n"
                f"ID записи: #{booking_id}"
            )
            try:
                await bot.send_message(int(owner_chat_id), owner_text)
            except Exception:
                pass

    bookings = await get_user_bookings(callback.from_user.id)

    status_line = "✅ <b>Запись отменена.</b>\n\n" if deleted else "⚠️ Запись не найдена или уже была отменена.\n\n"

    if not bookings:
        await callback.message.edit_text(status_line + "Записей больше нет.", reply_markup=None)
    else:
        lines = [status_line + "📋 <b>Ваши записи:</b>\n"]
        for b in bookings:
            lines.append(
                f"• <b>{b['date']} {b['time']}</b> — {b['service']} ({b['master']})"
            )
        lines.append("\nНажмите на запись, чтобы отменить её:")
        await callback.message.edit_text("\n".join(lines), reply_markup=my_bookings_kb(bookings))

    await callback.answer()
