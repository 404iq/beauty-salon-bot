import os
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards import services_kb, masters_kb, dates_kb, times_kb, confirm_kb
from bot.database import add_booking

router = Router()


# --- FSM: описываем шаги процесса записи ---
# Каждый State — это «экран», на котором сейчас находится пользователь.
class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_master  = State()
    choosing_date    = State()
    choosing_time    = State()
    confirming       = State()


# ── Шаг 1: пользователь нажал кнопку «Записаться» ──────────────────────────

@router.message(F.text == "📅 Записаться")
async def step_services(message: Message, state: FSMContext):
    await state.set_state(BookingStates.choosing_service)
    await message.answer("Выберите <b>услугу</b>:", reply_markup=services_kb())


# ── Шаг 2: пользователь выбрал услугу → показать мастеров ──────────────────

@router.callback_query(BookingStates.choosing_service, lambda c: c.data.startswith("service:"))
async def step_masters(callback: CallbackQuery, state: FSMContext):
    service = callback.data.split(":", 1)[1]
    await state.update_data(service=service)
    await state.set_state(BookingStates.choosing_master)
    await callback.message.edit_text(
        f"Услуга: <b>{service}</b>\n\nВыберите <b>мастера</b>:",
        reply_markup=masters_kb(service),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_services")
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(BookingStates.choosing_service)
    await callback.message.edit_text(
        "Выберите <b>услугу</b>:",
        reply_markup=services_kb(),
    )
    await callback.answer()


# ── Шаг 3: пользователь выбрал мастера → показать даты ─────────────────────

@router.callback_query(BookingStates.choosing_master, lambda c: c.data.startswith("master:"))
async def step_dates(callback: CallbackQuery, state: FSMContext):
    master = callback.data.split(":", 1)[1]
    await state.update_data(master=master)
    data = await state.get_data()
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        f"Услуга: <b>{data['service']}</b>\n"
        f"Мастер: <b>{master}</b>\n\n"
        "Выберите <b>дату</b>:",
        reply_markup=dates_kb(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_masters")
async def back_to_masters(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    service = data.get("service", "")
    await state.set_state(BookingStates.choosing_master)
    await callback.message.edit_text(
        f"Услуга: <b>{service}</b>\n\nВыберите <b>мастера</b>:",
        reply_markup=masters_kb(service),
    )
    await callback.answer()


# ── Шаг 4: пользователь выбрал дату → показать время ───────────────────────

@router.callback_query(BookingStates.choosing_date, lambda c: c.data.startswith("date:"))
async def step_times(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":", 1)[1]
    await state.update_data(date=date_str)
    data = await state.get_data()
    await state.set_state(BookingStates.choosing_time)
    await callback.message.edit_text(
        f"Услуга: <b>{data['service']}</b>\n"
        f"Мастер: <b>{data['master']}</b>\n"
        f"Дата: <b>{date_str}</b>\n\n"
        "Выберите <b>время</b>:",
        reply_markup=times_kb(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_dates")
async def back_to_dates(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        f"Услуга: <b>{data['service']}</b>\n"
        f"Мастер: <b>{data['master']}</b>\n\n"
        "Выберите <b>дату</b>:",
        reply_markup=dates_kb(),
    )
    await callback.answer()


# ── Шаг 5: пользователь выбрал время → показать подтверждение ──────────────

@router.callback_query(BookingStates.choosing_time, lambda c: c.data.startswith("time:"))
async def step_confirm(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.split(":", 1)[1]
    await state.update_data(time=time_str)
    data = await state.get_data()
    await state.set_state(BookingStates.confirming)
    summary = (
        "📋 <b>Подтверждение записи</b>\n\n"
        f"Услуга:  <b>{data['service']}</b>\n"
        f"Мастер:  <b>{data['master']}</b>\n"
        f"Дата:    <b>{data['date']}</b>\n"
        f"Время:   <b>{time_str}</b>\n\n"
        "Всё верно?"
    )
    await callback.message.edit_text(summary, reply_markup=confirm_kb())
    await callback.answer()


# ── Шаг 6a: подтверждение → сохранить в БД, уведомить владельца ────────────

@router.callback_query(BookingStates.confirming, lambda c: c.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = callback.from_user

    booking_id = await add_booking(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        service=data["service"],
        master=data["master"],
        date=data["date"],
        time=data["time"],
    )

    # Уведомляем владельца салона
    owner_chat_id = os.getenv("OWNER_CHAT_ID")
    if owner_chat_id:
        owner_text = (
            "🔔 <b>Новая запись!</b>\n\n"
            f"Клиент: {user.full_name}"
            + (f" (@{user.username})" if user.username else "") + "\n"
            f"Услуга: {data['service']}\n"
            f"Мастер: {data['master']}\n"
            f"Дата:   {data['date']}\n"
            f"Время:  {data['time']}\n"
            f"ID записи: #{booking_id}"
        )
        try:
            await bot.send_message(int(owner_chat_id), owner_text)
        except Exception:
            pass

    await state.clear()
    await callback.message.edit_text(
        "✅ <b>Запись подтверждена!</b>\n\n"
        f"Ждём вас {data['date']} в {data['time']}.\n"
        "До встречи! 💅"
    )
    await callback.answer()


# ── Шаг 6b: пользователь нажал «Отменить» на экране подтверждения ──────────

@router.callback_query(BookingStates.confirming, lambda c: c.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Запись отменена. Выберите действие в меню ниже.")
    await callback.answer()
