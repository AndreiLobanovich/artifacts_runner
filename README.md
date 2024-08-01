# Artifacts MMO player agent

## Описание

Этот проект представляет собой клиент для взаимодействия с API игры Artifacts MMO. Клиент написан на Python и использует библиотеку `requests` для выполнения HTTP-запросов к API.

## Установка

1. Клонируйте репозиторий:
    ```sh
    git clone <URL репозитория>
    cd <название директории>
    ```

2. Создайте виртуальное окружение и активируйте его:
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # для Windows используйте .venv\Scripts\activate
    ```

3. Установите зависимости:
    ```sh
    pip install -r requirements.txt
    ```

4. Создайте файл `.env` в корне проекта и добавьте в него ваш API токен:
    ```dotenv
    API_TOKEN=<ваш API токен>
    ```

## Использование

### Основные классы и функции

- `ArtifactsAPI`: Основной класс для взаимодействия с API.
  - `move(x, y, name)`: Перемещение персонажа.
  - `fight(name)`: Атака.
  - `gather_resource(name)`: Сбор ресурсов.
  - `craft(name, qtt, code)`: Крафт предметов.
  - `get_new_task(name)`: Получение нового задания.
  - `unequip(name, slot)`: Снятие экипировки.
  - `get_char_inventory(name)`: Получение инвентаря персонажа.
  - `get_item(item_code)`: Получение информации о предмете.

### Пример использования

```python
import asyncio
from api.ArtifactsAPI import ArtifactsAPI

async def main():
    api = ArtifactsAPI()

    # Перемещение персонажа
    await api.move(1, 2, "character_name")

    # Атака
    await api.fight("character_name")

    # Сбор ресурсов
    await api.gather_resource("character_name")

    # Крафт предмета
    await api.craft("character_name", qtt=2, code="iron_sword")

    # Получение нового задания
    await api.get_new_task("character_name")

    # Снятие экипировки
    await api.unequip("character_name")

    # Получение инвентаря персонажа
    inventory = await api.get_char_inventory("character_name")
    print(inventory)

    # Получение информации о предмете
    item_info = await api.get_item("item_code")
    print(item_info)

asyncio.run(main())