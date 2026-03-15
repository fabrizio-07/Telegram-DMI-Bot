import pytest
from unittest.mock import MagicMock, patch
from module.commands.reminder import reminder


# Successo in Chat Privata
def test_reminder_success_private_chat():
    # --- ARRANGE ---
    # Simuliamo un update che arriva da una chat privata (user_id == chat_id)
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = 12345
    mock_update.message.from_user.language_code = 'it'

    mock_context = MagicMock()
    mock_context.user_data = {}  # Partiamo da un contesto vuoto

    # Mockiamo le funzioni esterne per non farle eseguire davvero
    with patch('module.commands.reminder.check_log'), patch(
        'module.commands.reminder.get_locale', return_value="test"
    ):

        # --- ACT ---
        reminder(mock_update, mock_context)

        # --- ASSERT ---
        # 1. Verifica che il dizionario sia stato inizializzato correttamente
        assert 'reminder' in mock_context.user_data
        assert mock_context.user_data['reminder']['cmd'] == "input_insegnamento"

        # 2. Verifica che il bot abbia inviato ESATTAMENTE un messaggio (quello di usage)
        # In chat privata non deve inviare i warning per i gruppi
        assert mock_context.bot.send_message.call_count == 1
        mock_context.bot.send_message.assert_called_with(chat_id=12345, text="test")


# Warning in Chat di Gruppo
def test_reminder_warning_in_group():
    # --- ARRANGE ---
    # Simuliamo un gruppo: l'ID della chat è diverso dall'ID dell'utente
    mock_update = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.chat_id = -987654  # ID tipico di un gruppo
    mock_update.message.from_user.language_code = 'it'

    mock_context = MagicMock()
    mock_context.user_data = {}

    with patch('module.commands.reminder.check_log'), patch(
        'module.commands.reminder.get_locale', return_value="Warning %placeholder%"
    ):

        # --- ACT ---
        reminder(mock_update, mock_context)

        # --- ASSERT ---
        # 1. Verifica che siano stati inviati i messaggi di warning (sendMessage)
        # più il messaggio di usage finale (send_message)
        # Nota: nel tuo codice usi sia sendMessage che send_message
        assert mock_context.bot.sendMessage.call_count == 2
        assert mock_context.bot.send_message.call_count == 1


# Clear di context.user_data['reminder']
def test_reminder_clear_context():

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
