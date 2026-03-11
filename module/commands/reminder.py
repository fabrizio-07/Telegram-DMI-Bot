# -*- coding: utf-8 -*-
"""/esami command"""

import logging
import re
from typing import List, Optional, Tuple

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from module.data import Exam
from module.data.vars import PLACE_HOLDER, TEXT_IDS
from module.shared import check_log, send_message
from module.utils.multi_lang_utils import get_locale, get_locale_code


def reminder(update: Update, context: CallbackContext) -> None:
    """Called by the /esami command.
    Execute an exam query.

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

    # todo: gestire la scritta usando locale sia per inglese che per italiano
    message_text = "Di quale materia vuoi prenotarti?"

    context.bot.send_message(chat_id=update.message.chat_id, text=message_text)

    context.user_data['reminder']['cmd'] = "input_insegnamento"


def reminder_input_insegnamento(update: Update, context: CallbackContext) -> None:
    """Catches the 'ins: <subject>', queries the DB, and asks for the professor."""
    if not context.user_data or 'reminder' not in context.user_data:
        return

    if context.user_data['reminder'].get('cmd', None) == "input_insegnamento":
        raw_subject = re.sub(r"^(?!=<[/])[Ii]ns:\s+", "", update.message.text)
        exams = Exam.find("", "", "", raw_subject)

        del context.user_data['reminder']['cmd']

        if len(exams) > 0:
            professors = list(
                set([getattr(exam, 'docenti', 'Sconosciuto') for exam in exams])
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
                # todo: gestire la scritta usando locale sia per inglese che per italiano
                text=f"Ho trovato la materia '{raw_subject}'. Seleziona il professore:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                # todo: gestire la scritta usando locale sia per inglese che per italiano
                text=f"Non ho trovato nessuna materia corrispondente a '{raw_subject}' nel database.",
            )


def reminder_prof_handler(update: Update, context: CallbackContext) -> None:
    """Handles the inline button click for the professor selection."""
    query = update.callback_query
    query.answer()

    if not context.user_data or 'reminder' not in context.user_data:
        return

    prof_idx = int(query.data.replace("rem_prof_", ""))

    prof_name = context.user_data['reminder']['prof_list'][prof_idx]
    subject = context.user_data['reminder']['insegnamento']

    context.user_data['reminder']['professore'] = prof_name
