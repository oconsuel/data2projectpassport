def assemble_poster_params(user_answers, project):
    params = {}
    if project:
        params["Название проекта"] = project.get("name")
        params["Краткое описание"] = project.get("summary_short")
        if project.get("tags"):
            params["Ключевые слова"] = ", ".join(project.get("tags"))
    if user_answers.get("style", {}).get("selected"):
        params["Стиль"] = ", ".join(user_answers["style"]["selected"])
    if user_answers.get("composition", {}).get("selected"):
        params["Состав"] = ", ".join(user_answers["composition"]["selected"])
    if user_answers.get("content", {}).get("selected"):
        params["Содержание"] = ", ".join(user_answers["content"]["selected"])
        if "remove_text" in user_answers["content"]["selected"]:
            params["Без текста"] = "да"
    if user_answers.get("colors", {}).get("selected"):
        params["Цвета"] = ", ".join(user_answers["colors"]["selected"])
    if user_answers.get("other", {}).get("text"):
        params["Дополнительно"] = user_answers["other"]["text"]
    if user_answers.get("final", {}).get("text"):
        params["Комментарий"] = user_answers["final"]["text"]
    params["Требования к структуре"] = (
        "infographic layout, divided into several card-style blocks or sections, each block with an icon representing a different aspect of the project, clear areas for each concept, structured like a project summary, no text, no letters, no words, no typography, modern web design, clean lines, vibrant colors"
    )
    params["Требования к оформлению"] = (
        "Если в параметрах есть Название проекта, Краткое описание или Ключевые слова, визуализируй их. Не добавляй текст, но подчеркни основные темы проекта визуально."
    )
    return params
