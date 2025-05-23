from aiogram.fsm.state import State, StatesGroup


class AssignmentState(StatesGroup):
    Text = State()
    Document = State()
    Video = State()
    Documents = State()


class UserDataState(StatesGroup):
    FullName = State()
    PhoneNumber = State()
    Email = State()
