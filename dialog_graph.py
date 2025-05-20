DIALOG_GRAPH = {
    "start": {
        "question": "Что не устраивает в постере? (Можно выбрать несколько вариантов)",
        "options": {
            "style": "Стиль изображения",
            "composition": "Композиция / расположение элементов",
            "content": "Содержание / смысл",
            "colors": "Цвета и палитра",
            "other": "Другое (указать в комментарии)"
        },
        "multi": True,
        "next": "details"
    },
    "details": {
        "branches": ["style", "composition", "content", "colors", "other"],
        "back": "start"
    },
    "style": {
        "question": "Какой стиль вам хотелось бы видеть? (Можно выбрать несколько вариантов)",
        "options": {
            "modern": "Современный",
            "classic": "Классический",
            "minimalism": "Минимализм",
            "more_detail": "Больше деталей",
            "less_detail": "Меньше деталей"
        },
        "multi": True,
        "comment": True,
        "back": "start"
    },
    "composition": {
        "question": "Что не так с композицией? (Можно выбрать несколько вариантов)",
        "options": {
            "too_busy": "Слишком много элементов",
            "too_empty": "Слишком мало элементов",
            "arrangement": "Неудачное расположение"
        },
        "multi": True,
        "comment": True,
        "back": "style"
    },
    "content": {
        "question": "Что хотелось бы изменить в содержании? (Можно выбрать несколько вариантов)",
        "options": {
            "add_text": "Добавить текст",
            "remove_text": "Убрать текст",
            "change_theme": "Изменить тему"
        },
        "multi": True,
        "comment": True,
        "back": "composition"
    },
    "colors": {
        "question": "Что изменить в цветах? (Можно выбрать несколько вариантов)",
        "options": {
            "make_brighter": "Сделать ярче",
            "make_softer": "Сделать мягче",
            "change_palette": "Поменять палитру"
        },
        "multi": True,
        "comment": True,
        "back": "content"
    },
    "other": {
        "question": "Опишите, что бы вы хотели изменить:",
        "input": "text",
        "back": "colors"
    },
    "final": {
        "question": "Добавьте дополнительный комментарий (необязательно):",
        "input": "text",
        "back": "other"
    }
}
