# QUICK DEPLOY (run-and-forget)

## Вариант A (рекомендуется): systemd, автозапуск и авто-рестарт

На Linux-сервере в папке проекта выполните:

```bash
cd /path/to/test_bot
chmod +x deploy/install_service.sh deploy/healthcheck.sh
./deploy/install_service.sh
```

Что делает скрипт:
- создает/обновляет `.venv`
- ставит зависимости из `requirements.txt`
- проверяет синтаксис `bot.py`
- устанавливает systemd-сервис `aipidginbot`
- включает автозапуск после reboot и авто-рестарт при падениях

Проверка состояния:

```bash
./deploy/healthcheck.sh
```

Полезные команды:

```bash
sudo systemctl restart aipidginbot
sudo systemctl status aipidginbot
tail -f bot.log
```

---

## Вариант B (если у хостинга нет systemd)

1. Нажмите **Update from GitHub** в панели хостинга.
2. Убедитесь, что в ENV задан `BOT_TOKEN`.
3. Команда запуска:

```bash
python bot.py
```

4. Проверьте в Telegram командой `/version`, что отвечает новая версия.

---

## Если бот отвечает старым текстом
- остановите все дублирующие процессы с тем же токеном
- оставьте только один инстанс
- перезапустите сервис и проверьте `/version`
