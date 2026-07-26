from aiogram.fsm.state import State, StatesGroup

class BroadcastState(StatesGroup):
    waiting_for_message = State()

class ChannelState(StatesGroup):
    waiting_for_channel_input = State()

class AdminState(StatesGroup):
    waiting_for_admin_id_add = State()

class AdminReplyState(StatesGroup):
    waiting_for_reply = State()

class CaptionEditState(StatesGroup):
    waiting_for_video_caption = State()
    waiting_for_audio_caption = State()
