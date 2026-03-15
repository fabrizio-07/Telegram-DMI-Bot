# -*- coding: utf-8 -*-
"""/esami command"""

import re
from typing import List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from module.data import Exam
from module.data.vars import PLACE_HOLDER, TEXT_IDS
from module.shared import check_log
from module.utils.multi_lang_utils import get_locale


def reminder(update: Update, context: CallbackContext) -> None:
    """Called by the /reminder command.
    Sets a reimnder to sign up for a certain exam date.

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "reminder")

    if (
        'reminder' in context.user_data
    ):  # ripulisce il dict dell'user relativo a /reminder da eventuali dati presenti
        context.user_data['reminder'].clear()
    else:  # crea il dict che conterrà i dati del comando /reminder all'interno della key ['reminder'] di user data
        context.user_data['reminder'] = {}

    user_id: int = update.message.from_user.id
    chat_id: int = update.message.chat_id
    locale: str = update.message.from_user.language_code
    if chat_id != user_id:  # forza ad eseguire il comando in una chat privata
        context.bot.sendMessage(
            chat_id=chat_id,
            text=get_locale(locale, TEXT_IDS.USE_WARNING_TEXT_ID).replace(
                PLACE_HOLDER, "/reminder"
            ),
        )
        context.bot.sendMessage(
            chat_id=user_id,
            text=get_locale(locale, TEXT_IDS.GROUP_WARNING_TEXT_ID).replace(
                PLACE_HOLDER, "/reminder"
            ),
        )

    message_text = get_locale(locale, TEXT_IDS.EXAMS_USAGE_TEXT_ID)

    context.bot.send_message(chat_id=update.message.chat_id, text=message_text)

    context.user_data['reminder']['cmd'] = "input_insegnamento"


def reminder_input_insegnamento(update: Update, context: CallbackContext) -> None:
    """Catches the 'ins: <subject>', queries the DB, and asks for the professor."""
    if not context.user_data or 'reminder' not in context.user_data:
        return

    locale = update.message.from_user.language_code

    if context.user_data['reminder'].get('cmd', None) == "input_insegnamento":
        raw_subject = re.sub(r"^(?!=<[/])[Ii]ns:\s+", "", update.message.text)
        exams = Exam.find("", "", "", raw_subject)

        del context.user_data['reminder']['cmd']

        if len(exams) > 0:
            professors = list(
                {getattr(exam, 'docenti', 'Sconosciuto') for exam in exams}
            )

            context.user_data['reminder']['insegnamento'] = raw_subject
            context.user_data['reminder']['prof_list'] = professors

            keyboard = []
            for idx, prof in enumerate(professors):
                keyboard.append(
                    [InlineKeyboardButton(prof, callback_data=f"rem_prof_{idx}")]
                )

            context.bot.send_message(
                chat_id=update.message.chat_id,
                # gestire la scritta usando locale sia per inglese che per italiano
                text=get_locale(
                    locale, TEXT_IDS.REMINDER_FOUND_SUBJECT_TEXT_ID
                ).replace(PLACE_HOLDER, raw_subject),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                # gestire la scritta usando locale sia per inglese che per italiano
                text=get_locale(
                    locale, TEXT_IDS.REMINDER_NOT_FOUND_SUBJECT_TEXT_ID
                ).replace(PLACE_HOLDER, raw_subject),
            )


def reminder_prof_handler(update: Update, context: CallbackContext) -> None:
    """Handles the inline button click for the professor selection."""
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    if not context.user_data or 'reminder' not in context.user_data:
        return

    prof_idx = int(query.data.replace("rem_prof_", ""))

    prof_name = context.user_data['reminder']['prof_list'][prof_idx]
    # subject = context.user_data['reminder']['insegnamento']

    context.user_data['reminder']['professore'] = prof_name

    reminder_button_sessione(
        update=update, context=context, chat_id=chat_id, message_id=message_id
    )


def reminder_sessione_handler(update: Update, context: CallbackContext) -> None:
    """Handles the inline button click for the session selection."""
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    if not context.user_data or 'reminder' not in context.user_data:
        return

    sessione_id = query.data.replace("rem_sess_", "")
    context.user_data['reminder']['sessione'] = sessione_id

    # reminder_appello_button...

    # suppongo si debba chidere la sessione e poi proporre le date di appello (tutti e due sempre con bottoni) dopo di che
    # salvare nella tabella reminder chat_id dello studente, data, materia e professore e data del reminder.
    # data remindere = data appello - 15 gg


def reminder_button_sessione(
    update: Update, context: CallbackContext, chat_id: int, message_id: int
) -> None:
    """Called by one of the buttons of the /reminder command.
    Allows the user to choose a session among the ones proposed

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    locale = update.callback_query.from_user.language_code
    message_text: str = get_locale(locale, TEXT_IDS.EXAMS_SELECT_SESSION_TEXT_ID)

    keyboard: List[List[InlineKeyboardButton]] = [[]]
    keyboard = [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.EXAMS_SESSION_1_TEXT_ID),
                callback_data="rem_sess_prima",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.EXAMS_SESSION_2_TEXT_ID),
                callback_data="rem_sess_seconda",
            ),
        ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.EXAMS_SESSION_3_TEXT_ID),
                callback_data="rem_sess_terza",
            ),
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.EXAMS_SESSION_4_TEXT_ID),
                callback_data="rem_sess_straordinaria",
            ),
        ],
    ]

    context.bot.editMessageText(
        text=message_text,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
