from aiogram.fsm.state import State, StatesGroup


class AssignmentState(StatesGroup):
    Text = State()
    Document = State()
    Video = State()
