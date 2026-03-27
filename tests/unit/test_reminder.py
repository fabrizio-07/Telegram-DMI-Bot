# -*- coding: utf-8 -*-
"""Test suite for the /reminder command."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from telegram import InlineKeyboardButton

from module.commands.reminder import (
    reminder,
    reminder_annullato_handler,
    reminder_appello_handler,
    reminder_button_appello,
    reminder_button_sessione,
    reminder_confermato_handler,
    reminder_del_button,
    reminder_del_handler,
    reminder_input_insegnamento,
    reminder_new_handler,
    reminder_prof_handler,
    reminder_sessione_handler,
)


def test_reminder_success_private_chat():
    """Test reminder() function in a private chat."""
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = 12345
    mock_update.message.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {}

    with patch("module.commands.reminder.check_log"), patch(
        "module.commands.reminder.get_locale", return_value="test"
    ):
        reminder(mock_update, mock_context)

        assert "reminder" in mock_context.user_data
        assert mock_context.bot.send_message.call_count == 1
        mock_context.bot.send_message.assert_called_with(
            chat_id=12345,
            text="test",
            reply_markup=mock_context.bot.send_message.call_args[1]["reply_markup"],
        )


def test_reminder_warning_in_group():
    """Test reminder() function warns when used in a group chat."""
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = -987654
    mock_update.message.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {}

    with patch("module.commands.reminder.check_log"), patch(
        "module.commands.reminder.get_locale", return_value="Warning"
    ):
        reminder(mock_update, mock_context)

        assert mock_context.bot.sendMessage.call_count == 2
        assert mock_context.bot.send_message.call_count == 1


def test_reminder_new_handler():
    """Test reminder_new_handler() sets the correct command state."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {}}

    with patch("module.commands.reminder.get_locale", return_value="Inserisci esame"):
        reminder_new_handler(mock_update, mock_context)

        mock_query.answer.assert_called_once()
        assert mock_context.user_data["reminder"]["cmd"] == "input_insegnamento"
        mock_context.bot.send_message.assert_called_once_with(
            chat_id=mock_query.message.chat_id, text="Inserisci esame"
        )


@patch("module.commands.reminder.ExamRegistration.find_by_student")
def test_reminder_del_button(mock_find_by_student):
    """Test reminder_del_button() generates keyboard with existing reminders."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {}}

    mock_exam_1 = MagicMock(insegnamento="Analisi", data="2026-06-15")
    mock_find_by_student.return_value = [mock_exam_1]

    with patch(
        "module.commands.reminder.get_locale", return_value="Seleziona da eliminare"
    ):
        reminder_del_button(mock_update, mock_context)

        assert len(mock_context.user_data["reminder"]["reminder_list"]) == 1
        mock_context.bot.send_message.assert_called_once()
        kwargs = mock_context.bot.send_message.call_args.kwargs
        assert "reply_markup" in kwargs


@patch("module.commands.reminder.DbManager.delete_from")
def test_reminder_del_handler_single(mock_delete_from):
    """Test reminder_del_handler() deleting a specific reminder."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.data = "rem_delete_0"
    mock_query.from_user.language_code = "it"

    mock_exam = MagicMock(
        studenti="123", insegnamento="Analisi", docenti="Rossi", data="2026-06-15"
    )
    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {"reminder_list": [mock_exam]}}

    with patch("module.commands.reminder.get_locale", return_value="Eliminato"):
        reminder_del_handler(mock_update, mock_context)

        mock_delete_from.assert_called_once_with(
            table_name="exams_reg",
            where="studenti = ? AND insegnamento = ? AND docenti = ?",
            where_args=("123", "Analisi", "Rossi"),
        )
        mock_context.bot.send_message.assert_called_once()


@patch("module.commands.reminder.DbManager.delete_from")
def test_reminder_del_handler_all(mock_delete_from):
    """Test reminder_del_handler() deleting all reminders for a user."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.data = "rem_delete_-1"
    mock_query.from_user.language_code = "it"

    mock_context = MagicMock()

    with patch("module.commands.reminder.get_locale", return_value="Tutti eliminati"):
        reminder_del_handler(mock_update, mock_context)

        mock_delete_from.assert_called_once()
        mock_context.bot.send_message.assert_called_once()


@patch("module.commands.reminder.get_locale")
def test_reminder_button_sessione(mock_get_locale):
    """Test reminder_button_sessione() generates the correct session keyboard."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    chat_id = 12345
    message_id = 67890

    # Mocking the localization function to just return a dummy string
    mock_get_locale.return_value = "Mocked string"

    # Call the function
    reminder_button_sessione(
        update=mock_update, context=mock_context, chat_id=chat_id, message_id=message_id
    )

    # Assert editMessageText was called
    mock_context.bot.editMessageText.assert_called_once()

    # Extract the arguments passed to editMessageText
    call_kwargs = mock_context.bot.editMessageText.call_args.kwargs

    assert call_kwargs["chat_id"] == chat_id
    assert call_kwargs["message_id"] == message_id
    assert call_kwargs["text"] == "Mocked string"

    # Verify the inline keyboard structure (2 rows, 2 buttons each)
    reply_markup = call_kwargs["reply_markup"]
    assert reply_markup is not None
    assert len(reply_markup.inline_keyboard) == 2
    assert len(reply_markup.inline_keyboard[0]) == 2
    assert len(reply_markup.inline_keyboard[1]) == 2

    # Verify callback data for the sessions
    assert reply_markup.inline_keyboard[0][0].callback_data == "rem_sess_prima"
    assert reply_markup.inline_keyboard[0][1].callback_data == "rem_sess_seconda"
    assert reply_markup.inline_keyboard[1][0].callback_data == "rem_sess_terza"
    assert reply_markup.inline_keyboard[1][1].callback_data == "rem_sess_straordinaria"


@patch("module.commands.reminder.Exam.find")
def test_reminder_input_insegnamento(mock_exam_find):
    """Test reminder_input_insegnamento() populates temp_exams_list properly."""
    mock_update = MagicMock()
    mock_update.message.from_user.language_code = "it"
    mock_update.message.text = "ins: Analisi"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {"cmd": "input_insegnamento"}}

    exam1 = MagicMock(insegnamento="Analisi 1", docenti="Prof. Rossi")
    mock_exam_find.return_value = [exam1]

    with patch("module.commands.reminder.get_locale", return_value="Seleziona prof"):
        reminder_input_insegnamento(mock_update, mock_context)

        assert "cmd" not in mock_context.user_data["reminder"]
        assert len(mock_context.user_data["reminder"]["temp_exams_list"]) == 1
        assert (
            mock_context.user_data["reminder"]["temp_exams_list"][0]["prof"]
            == "Prof. Rossi"
        )
        mock_context.bot.send_message.assert_called_once()


@patch("module.commands.reminder.reminder_button_sessione")
def test_reminder_prof_handler(mock_but_sess):
    """Test reminder_prof_handler() sets the professor and calls session keyboard."""
    mock_update = MagicMock()
    mock_query = mock_update.callback_query
    mock_query.data = "rem_prof_0"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {"temp_exams_list": [{"subj": "Analisi", "prof": "Prof. Rossi"}]}
    }

    reminder_prof_handler(mock_update, mock_context)

    assert mock_context.user_data["reminder"]["professore"] == "Prof. Rossi"
    assert "temp_exams_list" not in mock_context.user_data["reminder"]
    mock_but_sess.assert_called_once()


@patch("module.commands.reminder.reminder_button_appello")
def test_reminder_sessione_handler(mock_button_appello):
    """Test reminder_sessione_handler() sets session and moves to appello."""
    mock_update = MagicMock()
    mock_update.callback_query.data = "rem_sess_prima"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {}}

    reminder_sessione_handler(mock_update, mock_context)

    assert mock_context.user_data["reminder"]["sessione"] == "prima"
    mock_button_appello.assert_called_once()


def test_reminder_appello_handler():
    """Test reminder_appello_handler() asks for confirmation."""
    mock_update = MagicMock()
    mock_update.callback_query.data = "rem_appello_2026-06-15"
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {"insegnamento": "Analisi", "professore": "Rossi"}
    }

    with patch("module.commands.reminder.get_locale", return_value="Confermi?"):
        reminder_appello_handler(mock_update, mock_context)

        assert mock_context.user_data["reminder"]["appello"] == "2026-06-15"
        mock_context.bot.editMessageText.assert_called_once()


@patch("module.commands.reminder.ExamRegistration")
def test_reminder_confermato_handler(mock_exam_reg):
    """Test reminder_confermato_handler() successfully saves to DB."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {
            "appello": "2026-06-15",
            "insegnamento": "Analisi",
            "professore": "Rossi",
        }
    }

    mock_instance = mock_exam_reg.return_value

    with patch("module.commands.reminder.get_locale", return_value="Salvato"):
        reminder_confermato_handler(mock_update, mock_context)

        mock_instance.save.assert_called_once()
        assert not mock_context.user_data["reminder"]  # Should be cleared
        mock_context.bot.editMessageText.assert_called_once()


def test_reminder_annullato_handler():
    """Test reminder_annullato_handler() clears user_data and aborts."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {"reminder": {"appello": "2026-06-15"}}

    with patch("module.commands.reminder.get_locale", return_value="Annullato"):
        reminder_annullato_handler(mock_update, mock_context)

        assert "reminder" not in mock_context.user_data
        mock_context.bot.editMessageText.assert_called_once()


@patch("module.commands.reminder.Exam.find")
def test_reminder_button_appello_parses_dates(mock_exam_find):
    """Test reminder_button_appello() properly extracts ast.literal_eval dates."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"
    mock_chat_id = 123
    mock_message_id = 456

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {
            "insegnamento": "Analisi",
            "professore": "Rossi",
            "sessione": "prima",
        }
    }

    # Simulate database returning a stringified list of dates
    mock_exam = MagicMock(docenti="Rossi", prima="['2026-06-15', '2026-07-01']")
    mock_exam_find.return_value = [mock_exam]

    with patch("module.commands.reminder.get_locale", return_value="Scegli data"):
        reminder_button_appello(
            mock_update, mock_context, mock_chat_id, mock_message_id
        )

        mock_context.bot.editMessageText.assert_called_once()
        kwargs = mock_context.bot.editMessageText.call_args.kwargs
        reply_markup = kwargs["reply_markup"]

        # Verify the inline keyboard created buttons for the parsed dates
        assert reply_markup is not None
        assert (
            reply_markup.inline_keyboard[0][0].callback_data == "rem_appello_2026-06-15"
        )
        assert (
            reply_markup.inline_keyboard[1][0].callback_data == "rem_appello_2026-07-01"
        )


def test_empty_context_early_returns():
    """Test early returns across various handlers when context is missing."""
    mock_update = MagicMock()
    mock_context = MagicMock()
    mock_context.user_data = {}  # Empty user_data

    # These should all return immediately without throwing errors
    reminder_input_insegnamento(mock_update, mock_context)
    reminder_prof_handler(mock_update, mock_context)
    reminder_sessione_handler(mock_update, mock_context)
    reminder_appello_handler(mock_update, mock_context)

    # Assert that no bot messages were sent because it aborted early
    mock_context.bot.send_message.assert_not_called()
    mock_context.bot.editMessageText.assert_not_called()


@patch("module.commands.reminder.ExamRegistration")
def test_reminder_confermato_handler_db_exception(mock_exam_reg):
    """Test reminder_confermato_handler() handles database exceptions gracefully."""
    mock_update = MagicMock()
    mock_update.callback_query.from_user.language_code = "it"

    mock_context = MagicMock()
    mock_context.user_data = {
        "reminder": {
            "appello": "2026-06-15",
            "insegnamento": "Analisi",
            "professore": "Rossi",
        }
    }

    # Force the save() method to throw an Exception
    mock_instance = mock_exam_reg.return_value
    mock_instance.save.side_effect = Exception("Database error")

    with patch("module.commands.reminder.get_locale", return_value="Errore duplicato"):
        reminder_confermato_handler(mock_update, mock_context)

        # Ensure the exception was caught and the error message was sent to the user
        mock_context.bot.editMessageText.assert_called_once()
        assert (
            mock_context.bot.editMessageText.call_args.kwargs["text"]
            == "Errore duplicato"
        )
