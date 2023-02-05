from pony.orm import *


db = Database()


class Person(db.Entity):
    """
    Контекст пользователя для сохранения шага и сценария, очищается при завершении сценария
    """
    user_id = Required(int, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Registration(db.Entity):
    """
    Запись зарегистрированных пользователей в бд
    """
    user_id = Required(int, unique=True)
    name = Required(str)
    email = Required(str)



db.bind(provider='sqlite', filename='../vk_bot.db', create_db=True)
db.generate_mapping(create_tables=True)
