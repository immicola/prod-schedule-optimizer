import math
import collections
import datetime
import os
import redis  # <<< НОВОЕ: Импортируем библиотеку для Redis
import json   # <<< НОВОЕ: Импортируем JSON для сериализации данных

from flask import Flask, request, jsonify
from ortools.sat.python import cp_model

# --- Инициализация веб-сервера Flask ---
app = Flask(__name__)

# --- НОВОЕ: Инициализация подключения к Redis ---
# Используем переменные окружения для гибкости, со значениями по умолчанию
# для локального запуска.
try:
    redis_client = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=int(os.environ.get('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True  # Автоматически декодирует ответы из байтов в строки UTF-8
    )
    # Проверяем соединение при старте
    redis_client.ping()
    print("✅ Успешное подключение к Redis.")
except redis.exceptions.ConnectionError as e:
    redis_client = None
    print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Не удалось подключиться к Redis. Сервер будет работать без кэширования. Ошибка: {e}")
# ------------------------------------------------

# ==============================================================================
#  НАЧАЛО КОДА ИЗ ВАШЕГО СКРИПТА (адаптировано в виде функции)
# ==============================================================================

# ... (весь ваш код с tech_map_data, machines_available, и т.д. остается без изменений) ...
# ... я его скрыл для краткости, но он должен быть здесь ...
tech_map_data = {
    # Данные обновлены согласно списку от 20.05.2024
    # Для новых продуктов добавлены типовые значения времени

    # --- Типовые значения для новых продуктов (можно использовать как шаблон) ---
    # "Название": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},

    "Хлеб «Формовой»":             {"Комбинирование": "0:21:00", "Смешивание": "0:12:00", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:45:00", "Остывание": "1:30:00"},
    "Хлеб «Семейный»":             {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Тостовый хлеб нарезанный":    {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "1:00:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Сэндвич Панини / Сэндвич Панини с кунжутом": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "0:45:00"}, # Взяты данные от "Сэндвич"
    "Багет «Новый»":               {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:25:00", "Остывание": "1:15:00"},
    "Булочка для гамбургера большая / с кунжутом": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "0:45:00"},
    "Сэндвич солодовый с семечками (первый вариант)": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "0:45:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Булочка для хот-дога/гамбургера": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "0:45:00"},
    "Хот-дог/Гамбургер солодовый с семечками": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "0:45:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Сэндвич солодовый с семечками (второй вариант)": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "0:45:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Чиабатта":                    {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:25:00", "Остывание": "1:15:00"},
    "Хлеб «Партия бездрожжевой»":  {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:20:00", "Выпекание": "0:16:30", "Остывание": "1:00:00"}, # Аналог "Тартин бездрожжевой"
    "Сэндвич Зерновой":            {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "0:45:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Немецкий хлеб":               {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Панировочные сухари":         {"Комбинирование": "0:15:00", "Смешивание": "0:10:30", "Формовка": "0:00:00", "Расстойка": "0:00:00", "Выпекание": "0:40:00", "Остывание": "1:20:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Хлеб «Зерновой»":             {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:25:00", "Остывание": "1:15:00"},
    "Бриошь":                      {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:30:00", "Выпекание": "0:20:00", "Остывание": "0:45:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Лепешка с сыром и луком":     {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:20:00", "Выпекание": "0:15:00", "Остывание": "0:30:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Лепешка с кунжутом":          {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:20:00", "Выпекание": "0:15:00", "Остывание": "0:30:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Хлеб «Солодовый с семечками»": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:18:00", "Остывание": "1:00:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Хлеб солодовый с семечками нарезанный": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:18:00", "Остывание": "1:00:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Хлеб «Спорт Актив»":          {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:18:00", "Остывание": "1:00:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Зерновой солодовый хлеб нарезанный": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:25:00", "Остывание": "1:15:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Хлеб «Зерновой солодовый»":   {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:25:00", "Остывание": "1:15:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Гречишный хлеб нарезанный":   {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Кукурузный хлеб":             {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Булочка для хот-дог/гамбургера (World class)": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:22:00", "Остывание": "0:45:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Хлеб «Гречишный»":            {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Хлеб «Столичный»":            {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Хлеб «Здоровье»":             {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:18:00", "Остывание": "1:00:00"},
    "Тостовый хлеб отрубной нарезанный": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Хлеб «Славянский»":           {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Багет \"Премиум\"":             {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:25:00", "Остывание": "1:15:00"},
    "Багет с луком":               {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:20:00", "Выпекание": "0:18:00", "Остывание": "0:45:00"},
    "Хлеб «Деревенский»":          {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:30:00", "Выпекание": "0:18:30", "Остывание": "1:30:00"},
    "Хлеб «Багет отрубной»":       {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:18:00", "Остывание": "0:45:00"},
    "Хлеб «Домашний»":             {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Хлеб «Баварский»":            {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:30:00", "Выпекание": "0:18:30", "Остывание": "1:30:00"},
    "Хлеб «Отрубной»":             {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Хлеб «Диетический»":          {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:37:30", "Выпекание": "0:35:00", "Остывание": "1:30:00"},
    "Хлеб Ржаной":                 {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:30:00", "Выпекание": "0:18:30", "Остывание": "1:30:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Плетенка с посыпкой (мак/кунжут)": {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Батон «Верный»":              {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Хлеб «Жайлы»":                {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Булочки":                     {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:15:00", "Остывание": "0:30:00"}, # <<< НОВЫЙ ПРОДУКТ, добавлены типовые значения
    "Батон «Нарезной»":            {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Хлеб «Мини Формовой»":         {"Комбинирование": "0:21:00", "Смешивание": "0:12:00", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:45:00", "Остывание": "1:30:00"},
    "Хлеб «Борике»":               {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:20:00", "Выпекание": "0:16:30", "Остывание": "1:00:00"}, # Аналог "Береке"
    "Хлеб «Любимый», «Детский»":   {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:25:00", "Выпекание": "0:17:00", "Остывание": "1:00:00"},
    "Хлеб «Бородинский»":          {"Комбинирование": "0:21:00", "Смешивание": "0:10:30", "Формовка": "0:11:00", "Расстойка": "0:20:00", "Выпекание": "0:55:00", "Остывание": "2:00:00"},
} # И так далее, весь ваш большой словарь tech_map_data
machines_available = { "Комбинирование": 2, "Смешивание": 3, "Формовка": 2, "Расстойка": 8, "Выпекание": 6, "Остывание": 25 }
BATCH_SIZE = 100
STAGES = ["Комбинирование", "Смешивание", "Формовка", "Расстойка", "Выпекание", "Остывание"]
MAX_WAIT_COMBINING_MIXING_MIN = 1
MAX_WAIT_MIXING_FORMING_MIN = 1
MAX_WAIT_FORMING_PROOFING_MIN = 5
MAX_WAIT_PROOFING_BAKING_MIN = 5
CRITICAL_STAGE_BEFORE_0 = "Комбинирование"
CRITICAL_STAGE_AFTER_0 = "Смешивание"
CRITICAL_STAGE_BEFORE_1 = "Смешивание"
CRITICAL_STAGE_AFTER_1 = "Формовка"
CRITICAL_STAGE_BEFORE_2 = "Формовка"
CRITICAL_STAGE_AFTER_2 = "Расстойка"
CRITICAL_STAGE_BEFORE_3 = "Расстойка"
CRITICAL_STAGE_AFTER_3 = "Выпекание"
def time_str_to_minutes_int(time_str):
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3: h, m, s = parts; return round(h * 60 + m + s / 60.0)
        elif len(parts) == 2: m, s = parts; return round(m + s / 60.0)
        else: return 0
    except: return 0

def calculate_production_schedule(orders):
    # ... (весь код вашей функции calculate_production_schedule остается без изменений) ...
    # ... я его скрыл для краткости, но он должен быть здесь ...
    tech_map_minutes_int = {}
    for product, stages_data in tech_map_data.items():
        if product not in orders or orders[product] <= 0:
            continue
        tech_map_minutes_int[product] = {}
        for stage_name in STAGES:
            time_str = stages_data.get(stage_name, "0:00:00")
            duration = time_str_to_minutes_int(time_str)
            tech_map_minutes_int[product][stage_name] = duration
    all_batches = []
    proportional_time_stages = ["Комбинирование", "Формовка"]
    for product, quantity_ordered in orders.items():
        if quantity_ordered <= 0: continue
        if product not in tech_map_data:
            print(f"Предупреждение: Продукт '{product}' из заказа отсутствует в технологической карте. Пропускается.")
            continue
        num_full_batches = quantity_ordered // BATCH_SIZE
        remaining_quantity = quantity_ordered % BATCH_SIZE
        total_batches_for_product = num_full_batches
        if remaining_quantity > 0: total_batches_for_product += 1
        for i in range(total_batches_for_product):
            batch_id = f"{product}_batch_{i+1}"
            is_last_partial_batch = (i == total_batches_for_product - 1) and (remaining_quantity > 0)
            current_batch_actual_size = BATCH_SIZE if not is_last_partial_batch else remaining_quantity
            batch_tasks = []
            for stage_index, stage_name in enumerate(STAGES):
                base_duration_for_100 = tech_map_minutes_int.get(product, {}).get(stage_name, 0)
                current_task_duration = base_duration_for_100
                if base_duration_for_100 > 0:
                    if is_last_partial_batch:
                        if stage_name in proportional_time_stages: current_task_duration = math.ceil(base_duration_for_100 * (current_batch_actual_size / BATCH_SIZE))
                    if current_task_duration <= 0 and base_duration_for_100 > 0: current_task_duration = 1
                    if current_task_duration > 0:
                        batch_tasks.append({ "batch_id": batch_id, "stage_index": stage_index, "stage_name": stage_name, "duration": current_task_duration, "product": product, })
            if batch_tasks: all_batches.append({"id": batch_id, "product": product, "tasks": batch_tasks})
    if not all_batches: return []
    horizon = sum(task['duration'] for batch in all_batches for task in batch['tasks'])
    min_machines = min(m_count for m_count in machines_available.values() if m_count > 0)
    if min_machines > 0: horizon = math.ceil(horizon / min_machines) * 2
    else: horizon = horizon * 2 
    horizon += 1000
    model = cp_model.CpModel()
    task_vars = collections.defaultdict(dict)
    task_lookup = {}
    for i, batch in enumerate(all_batches):
        for task in batch['tasks']:
            suffix = f'_{task["batch_id"]}_{task["stage_name"]}'
            start_var = model.NewIntVar(0, horizon, 'start' + suffix)
            end_var = model.NewIntVar(0, horizon, 'end' + suffix)
            interval_var = model.NewIntervalVar(start_var, task['duration'], end_var, 'interval' + suffix)
            task_vars[i][task['stage_index']] = (start_var, end_var, interval_var)
            task_lookup[(task['batch_id'], task['stage_name'])] = (start_var, end_var, interval_var)
    for i, batch in enumerate(all_batches):
        sorted_tasks_for_batch = sorted(batch['tasks'], key=lambda t: t['stage_index'])
        for k in range(len(sorted_tasks_for_batch) - 1):
            curr_idx = sorted_tasks_for_batch[k]['stage_index']
            next_idx = sorted_tasks_for_batch[k+1]['stage_index']
            if curr_idx in task_vars[i] and next_idx in task_vars[i]: model.Add(task_vars[i][next_idx][0] >= task_vars[i][curr_idx][1])
    for stage_index, stage_name in enumerate(STAGES):
        machine_count = machines_available.get(stage_name)
        if not machine_count or machine_count <= 0: continue
        intervals_for_stage = [task_vars[i][stage_index][2] for i, batch in enumerate(all_batches) if stage_index in task_vars[i]]
        if intervals_for_stage: model.AddCumulative(intervals_for_stage, [1] * len(intervals_for_stage), machine_count)
    critical_constraints_defined = [(CRITICAL_STAGE_BEFORE_0, CRITICAL_STAGE_AFTER_0, MAX_WAIT_COMBINING_MIXING_MIN), (CRITICAL_STAGE_BEFORE_1, CRITICAL_STAGE_AFTER_1, MAX_WAIT_MIXING_FORMING_MIN), (CRITICAL_STAGE_BEFORE_2, CRITICAL_STAGE_AFTER_2, MAX_WAIT_FORMING_PROOFING_MIN), (CRITICAL_STAGE_BEFORE_3, CRITICAL_STAGE_AFTER_3, MAX_WAIT_PROOFING_BAKING_MIN)]
    for i, batch in enumerate(all_batches):
        batch_id = batch['id']
        for stage_before, stage_after, max_wait in critical_constraints_defined:
            if stage_before in STAGES and stage_after in STAGES:
                task_before_key = (batch_id, stage_before)
                task_after_key = (batch_id, stage_after)
                if task_before_key in task_lookup and task_after_key in task_lookup: model.Add(task_lookup[task_after_key][0] - task_lookup[task_before_key][1] <= max_wait)
    makespan = model.NewIntVar(0, horizon, 'makespan')
    last_stage_tasks_ends = []
    for i, batch in enumerate(all_batches):
         if batch['tasks']:
            actual_last_stage_idx = batch['tasks'][-1]['stage_index']
            if actual_last_stage_idx in task_vars[i]: last_stage_tasks_ends.append(task_vars[i][actual_last_stage_idx][1])
    if last_stage_tasks_ends: model.AddMaxEquality(makespan, last_stage_tasks_ends)
    else: model.Add(makespan == 0)
    model.Minimize(makespan)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        schedule_data_for_output = []
        for i, batch in enumerate(all_batches):
            for task_info in batch['tasks']:
                stage_idx = task_info['stage_index']
                if stage_idx in task_vars[i]:
                    start_val = solver.Value(task_vars[i][stage_idx][0])
                    schedule_data_for_output.append({ "Product": task_info["product"], "Start_Time_Min": start_val })
        schedule_data_for_output.sort(key=lambda x: x['Start_Time_Min'])
        sorted_products = []
        seen_products = set()
        for task in schedule_data_for_output:
            product_name = task["Product"]
            if product_name not in seen_products:
                seen_products.add(product_name)
                sorted_products.append(product_name)
        return sorted_products
    else:
        return None

# ==============================================================================
#  КОНЕЦ КОДА ИЗ ВАШЕГО СКРИПТА
# ==============================================================================


# --- Определение эндпоинта API ---
@app.route('/api/orders/sort', methods=['POST'])
def sort_orders_endpoint():
    """
    Эндпоинт для приема заказов и возврата отсортированного списка.
    <<< ИЗМЕНЕНО: Добавлена логика кэширования >>>
    """
    
    global redis_client  
    
    # 1. Получаем JSON из тела запроса
    try:
        input_data = request.get_json()
        if not input_data:
            return jsonify({"error": "Тело запроса пустое или содержит невалидный JSON"}), 400
        if not isinstance(input_data, list):
            return jsonify({"error": "Входные данные должны быть массивом (list) JSON объектов"}), 400
    except Exception as e:
        return jsonify({"error": "Неверный формат JSON", "details": str(e)}), 400

    # 2. Преобразуем входной массив в словарь, который понимает наша функция
    orders_dict = {}
    for item in input_data:
        if 'name' not in item or 'amount' not in item:
            return jsonify({"error": "Каждый объект в массиве должен содержать ключи 'name' и 'amount'"}), 400
        if item.get('amount') and int(item['amount']) > 0:
            product_name = item['name'].strip()
            orders_dict[product_name] = int(item['amount'])

    if not orders_dict:
        return jsonify({"message": "Не найдено заказов для планирования (количество > 0).", "data": []}), 200

    # 3. <<< НОВОЕ: Логика кэширования >>>
    sorted_product_list = None
    cache_key = None

    if redis_client:
        try:
            # Создаем стабильный ключ для кеширования.
            # json.dumps с sort_keys=True гарантирует, что один и тот же набор данных
            # всегда будет давать одну и ту же строку, независимо от порядка ключей.
            cache_key = "sort_order:" + json.dumps(orders_dict, sort_keys=True)
            
            # Пытаемся получить результат из кеша
            cached_result = redis_client.get(cache_key)

            if cached_result:
                # Кэш-ХИТ: Результат найден в Redis
                print(f"✅ Кэш-ХИТ для ключа: {cache_key[:100]}...") # Логируем для отладки
                sorted_product_list = json.loads(cached_result) # Десериализуем из JSON
            else:
                # Кэш-ПРОМАХ: В Redis ничего нет
                print(f"🟡 Кэш-ПРОМАХ для ключа: {cache_key[:100]}...")
        
        except redis.exceptions.RedisError as e:
            # Если Redis упал в процессе, работаем без кеша
            print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Ошибка при работе с Redis. Работаем без кеша. Ошибка: {e}")
            redis_client = None # Временно отключаем Redis до следующего запроса

    # 4. <<< ИЗМЕНЕНО: Вызываем основную логику расчета, только если нет результата из кеша >>>
    if sorted_product_list is None:
        print(f"🚀 Запускаем полный расчет для: {orders_dict}")
        sorted_product_list = calculate_production_schedule(orders_dict)

        # <<< НОВОЕ: Сохраняем результат в кеш, если он успешный >>>
        if sorted_product_list is not None and redis_client and cache_key:
            try:
                # Сохраняем результат в Redis на 1 час (3600 секунд)
                redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps(sorted_product_list) # Сериализуем в JSON-строку
                )
                print(f"💾 Результат для ключа {cache_key[:100]}... сохранен в кеш.")
            except redis.exceptions.RedisError as e:
                print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Не удалось сохранить результат в кеш Redis. Ошибка: {e}")


    if sorted_product_list is None:
        return jsonify({"error": "Не удалось найти выполнимое расписание. Проверьте параметры или доступность оборудования."}), 500

    # 5. Формируем ответ (эта часть остается прежней)
    sort_order_map = {name: i + 1 for i, name in enumerate(sorted_product_list)}
    
    output_data = []
    for item in input_data:
        sort_order = sort_order_map.get(item['name'].strip())
        output_data.append({
            "sort_order": sort_order,
            "name": item['name'],
            "amount": item['amount']
        })
        
    output_data.sort(key=lambda item: (item['sort_order'] is None, item['sort_order']))
    
    print(f"Отправка отсортированного ответа. Порядок: {sorted_product_list}")
    return jsonify(output_data)

# --- Запуск сервера ---
if __name__ == '__main__':
    print("Сервер запущен на http://0.0.0.0:8080")
    print("Для остановки сервера нажмите CTRL+C")
    app.run(host='0.0.0.0', port=8080, debug=True)