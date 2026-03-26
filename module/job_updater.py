"""Job updater"""

from datetime import datetime, timedelta
import logging

from telegram.ext import CallbackContext

from module.data import Exam, Lesson, Professor, TimetableSlot
from module.shared import check_print_old_exams, get_year_code

from module.data.db_manager import DbManager

from module.data.vars import PLACE_HOLDER, TEXT_IDS
from module.utils.multi_lang_utils import get_locale

logger = logging.getLogger(__name__)


def check_exam_reminders(context: CallbackContext) -> None:
    """Job function to check for exams 15 days from now and send reminder."""

    target_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')

    try:
        reminders = DbManager.select_from(
            table_name="exams_reg",
            where="data = ?",
            where_args=(target_date,),
        )

        for rem in reminders:
            student_id = rem.get('studenti')
            subject = rem.get('insegnamento', 'N/D')
            prof = rem.get('docenti', 'N/D')
            exam_date = rem.get('data', target_date)

            message_text = (
                f"Reminder Esame\n"
                f"La prenotazione per l'esame di {subject} con il prof. {prof} "
                f"previsto per il *{exam_date}* é aperta.\n"
            )

            try:
                context.bot.send_message(
                    chat_id=student_id, text=message_text, parse_mode='Markdown'
                )
            except Exception as msg_err:
                logger.error(
                    f"Errore nell'invio del messaggio a {student_id}: {msg_err}"
                )

    except Exception as db_err:
        logger.error(
            f"Database error nel controllo all'interno della funzione check_exam_reminders: {db_err}"
        )


def updater_lep(_: CallbackContext):
    """Called with a set frequence.
    Updates all the scrapables

    Args:
        context: context passed by the handler
    """
    year_exam = get_year_code(
        11, 30
    )  # aaaa/12/01 (cambio nuovo anno esami) data dal quale esami del vecchio a nuovo anno coesistono

    Exam.scrape(
        f"1{year_exam}", delete=True
    )  # flag che permette di eliminare tutti gli esami presenti in tabella exams
    if check_print_old_exams(year_exam):
        Exam.scrape(f"1{int(year_exam) - 1}")

    Professor.scrape(delete=True)
    TimetableSlot.scrape(delete=True)
    Lesson.scrape(
        f"1{get_year_code(9, 20)}", delete=True
    )  # aaaa/09/21 (cambio nuovo anno lezioni) data dal quale vengono prelevate le lezioni del nuovo anno
