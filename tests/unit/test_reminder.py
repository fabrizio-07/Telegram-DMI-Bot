# -*- coding: utf-8 -*-
"""/reminder testing"""

from unittest.mock import MagicMock, patch

from module.commands.reminder import reminder, reminder_input_insegnamento


def test_reminder_success_private_chat():
    """Test reminder() function, chat privata"""
    # --- ARRANGE ---
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = 12345
    mock_update.message.from_user.language_code = 'it'

    mock_context = MagicMock()
    mock_context.user_data = {}

    with patch('module.commands.reminder.check_log'), patch(
        'module.commands.reminder.get_locale', return_value="test"
    ):

        # --- ACT ---
        reminder(mock_update, mock_context)

        # --- ASSERT ---
        assert 'reminder' in mock_context.user_data
        assert mock_context.user_data['reminder']['cmd'] == "input_insegnamento"

        assert mock_context.bot.send_message.call_count == 1
        mock_context.bot.send_message.assert_called_with(chat_id=12345, text="test")


def test_reminder_warning_in_group():
    """Test reminder() function, chat di gruppo"""

    # --- ARRANGE ---
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = -987654
    mock_update.message.from_user.language_code = 'it'

    mock_context = MagicMock()
    mock_context.user_data = {}

    with patch('module.commands.reminder.check_log'), patch(
        'module.commands.reminder.get_locale', return_value="Warning %placeholder%"
    ):

        # --- ACT ---
        reminder(mock_update, mock_context)

        # --- ASSERT ---
        assert mock_context.bot.sendMessage.call_count == 2
        assert mock_context.bot.send_message.call_count == 1


def test_reminder_clear_context():
    """Test clear di context.user_data['reminder']"""
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = 12345
    mock_update.message.from_user.language_code = 'it'

    mock_context = MagicMock()
    mock_context.user_data = {
        'reminder': {
            'insegnamento': 'Analisi',
            'professore': 'Mario Rossi',
            'cmd': 'vecchio_stato',
        }
    }

    with patch('module.commands.reminder.check_log'), patch(
        'module.commands.reminder.get_locale', return_value="test"
    ):
        reminder(mock_update, mock_context)

        assert 'reminder' in mock_context.user_data
        assert 'insegnamento' not in mock_context.user_data['reminder']
        assert 'professore' not in mock_context.user_data['reminder']

        assert mock_context.user_data['reminder']['cmd'] == 'input_insegnamento'


@patch('module.commands.reminder.Exam.find')
@patch('module.commands.reminder.get_locale')
def test_reminder_input_insegnamento(mock_get_locale, mock_exam_find):
    """Test reminder_input_insegnamento() function"""

    # --- ARRANGE ---
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = 12345
    mock_update.message.from_user.language_code = 'it'
    mock_update.message.text = "ins: Analisi"

    mock_context = MagicMock()
    mock_context.user_data = {'reminder': {'cmd': 'input_insegnamento'}}

    exam1 = MagicMock(docenti="Prof. Rossi")
    exam2 = MagicMock(docenti="Prof. Rossi")
    mock_exam_find.return_value = [exam1, exam2]
    mock_get_locale.return_value = "Hai scelto %placeholder%"

    # --- ACT ---
    reminder_input_insegnamento(mock_update, mock_context)

    # --- ASSERT ---
    assert 'cmd' not in mock_context.user_data['reminder']

    assert len(mock_context.user_data['reminder']['prof_list']) == 1
    assert mock_context.user_data['reminder']['prof_list'][0] == "Prof. Rossi"

    assert mock_context.bot.send_message.call_count == 1


def test_reminder_input_insegnamento_empty_context():
    """Test reminder_input_insegnamento() function with empty context.user_data"""

    # --- ARRANGE ---
    mock_update = MagicMock()

    mock_context = MagicMock()
    mock_context.user_data = {}

    # --- ACT ---
    reminder_input_insegnamento(mock_update, mock_context)

    # --- ASSERT ---
    assert not mock_context.user_data
    assert 'reminder' not in mock_context.user_data


@patch('module.commands.reminder.Exam.find')
@patch('module.commands.reminder.get_locale')
def test_reminder_input_insegnamento_empty_db_query(mock_get_locale, mock_exam_find):
    """Test reminder_input_insegnamento() function with empty Exam query"""

    # --- ARRANGE ---
    mock_update = MagicMock()
    mock_update.message.from_user.language_code = 'it'
    mock_update.message.text = "ins: MateriaInesistente"

    mock_context = MagicMock()
    mock_context.user_data = {'reminder': {'cmd': 'input_insegnamento'}}

    # Prepariamo i return dei mock
    mock_exam_find.return_value = []
    mock_get_locale.return_value = "Non ho trovato nulla per %placeholder%"

    # --- ACT ---
    reminder_input_insegnamento(mock_update, mock_context)

    # --- ASSERT ---
    mock_exam_find.assert_called_once()

    assert mock_context.bot.send_message.call_count == 1

    kwargs = mock_context.bot.send_message.call_args
    assert 'reply_markup' not in kwargs

    assert 'cmd' not in mock_context.user_data['reminder']


@patch('module.commands.reminder.Exam.find')
@patch('module.commands.reminder.get_locale')
def test_reminder_input_insegnamento_subject_not_found(mock_get_locale, mock_exam_find):
    """Test reminder_input_insegnamento() function with empty update.message.text"""

    # --- ARRANGE ---
    mock_update = MagicMock()
    mock_update.message.from_user.language_code = 'it'
    mock_update.message.text = "MateriaInesistente"

    mock_context = MagicMock()
    mock_context.user_data = {'reminder': {'cmd': 'input_insegnamento'}}

    # Prepariamo i return dei mock
    mock_exam_find.return_value = []
    mock_get_locale.return_value = "Non ho trovato nulla per %placeholder%"

    # --- ACT ---
    reminder_input_insegnamento(mock_update, mock_context)

    # --- ASSERT ---
    mock_exam_find.assert_called_once()

    assert mock_context.bot.send_message.call_count == 1

    kwargs = mock_context.bot.send_message.call_args
    assert 'reply_markup' not in kwargs

    assert 'cmd' not in mock_context.user_data['reminder']
