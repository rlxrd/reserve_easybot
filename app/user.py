from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.database.requests import set_user, update_user, set_reserve
import app.keyboards as kb

router = Router()


class Reg(StatesGroup):
    name = State()
    contact = State()


class Reserve(StatesGroup):
    barber = State()
    service = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await set_user(message.from_user.id)
    if user:
        await message.answer(f'Доброго времени суток, {user.name}!', reply_markup=kb.main)
        await state.clear()
    else:
        await message.answer('Добро пожаловать! Пожалуйста пройдите регистрацию.\n\nВведите Ваше имя.')
        await state.set_state(Reg.name)


@router.message(Reg.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Reg.contact)
    await message.answer('Отправьте номер телефона', reply_markup=kb.contact)


@router.message(Reg.contact, F.contact)
async def reg_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    await update_user(message.from_user.id, data['name'], message.contact.phone_number)
    await state.clear()
    await message.answer(f'Выберите услугу ниже.', reply_markup=kb.main)


@router.message(F.text == 'Записаться на услугу')
async def get_service(message: Message, state: FSMContext):
    await state.set_state(Reserve.barber)
    await message.answer('Выберите барбера', reply_markup=await kb.barbers())


@router.callback_query(F.data.startswith('barber_'), Reserve.barber)
async def get_service_2(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Мастер выбран.')
    await state.update_data(barber=callback.data.split('_')[1])
    await state.set_state(Reserve.service)
    await callback.message.answer('Выберите услугу', reply_markup=await kb.services())


@router.callback_query(F.data.startswith('service_'), Reserve.service)
async def get_service_2(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Услуга выбрана.')
    data = await state.get_data()
    await set_reserve(callback.from_user.id, data['barber'], callback.data.split('_')[1])
    await callback.message.answer('Вы успешно записаны. Менеджер перезвонит вам в рабочее время.', reply_markup=kb.main)
