from binance import Client
import numpy as np

api_key = "SRtOfJ4ov6VdeYvcuUNqtmlbaU35mDiUVRpKZz9GYmik1YpiH9RY2xeiYtcTmL0s"
Secret_key = "QZJzCvnQCDZy3RCBoliGCWhcv3gifs5uQ7yXhtma7l2Of8sNYzphnQqrtcad8bt6"

client = Client(api_key, Secret_key)
# Пара для анализа
symbol = "BETABUSD"
# За какое время берем данные (ДНИ)
data = "1 day ago UTC"
# интервал с котором получаем информацию (МИНУТЫ)
interval = "1m"
# За какое время (дни) я буду раcсчитывать показатели для дальнейшей проверки
estimated_time = 2
# Поправка для получения хороших чисел EMA (180 свеч) (8 дней)
correction_time = 8


# Находим среднее положительное значение осциллятора индикатора MACD
def get_avg_macd_oscillator(macd_indiactor):
    sum_value = 0
    count_positive = 0
    for indicator in macd_indiactor:
        if indicator[1] > 0:
            sum_value += indicator[1]
            count_positive += 1
    return sum_value / count_positive


# Получаем данные по символу c определенным интервалом за нужное количество дней
# возвращаем список данных
def get_list_data(_symbol, _interval, _data, _correction_time):
    # в заввисимости от типа записи даты прибавим поправку на время для более точного расчета показателей индекса
    splited_data = _data.split(' ')
    if len(splited_data) == 4:
        splited_data[0] = str(int(splited_data[0]) + correction_time)
    result_data = ' '.join(splited_data)
    candles = client.get_historical_klines(_symbol, _interval, result_data)
    return candles


# Получаем МА значения кривой
def get_ma_data(candles_list, ma_value):  # считает MA, ma_value

    ma_list = (
        []
    )  # список (дата, значение МА, стоимость на закрытие свечи) с посчитанными значениями MA

    # начинаем расчет MA и записываем значение в массив
    i = 0
    i_time = 0
    close_value = 0
    while i != len(candles_list) - ma_value + 1:
        sum_value = 0.0
        for j in range(i, i + ma_value):
            sum_value += float(candles_list[j][4])
            i_time = candles_list[j][0]
            close_value = candles_list[j][4]
        ma_list.append([i_time, sum_value / ma_value, close_value, ma_value])
        i += 1
    return ma_list


# Получаем значения ЕМА для свечей
def get_ema_data(candles_list, ma_value):  # считает EMA (экспоненциальную), ma_value
    ma_list = (
        []
    )  # список (дата, значение EМА, стоимость на закрытие свечи) с посчитанными значениями MA

    # начинаем расчет EMA и записываем значение в массив
    i = 0
    weight_koeff = 2 / (ma_value + 1)
    result_value = 0.0
    sum_value = 0.0
    while i != len(candles_list) - ma_value + 1:
        if i == 0:
            for j in range(i, i + ma_value):
                # Считаем на первой итерации EMA
                sum_value += float(candles_list[j][4])
                result_value = sum_value / ma_value
        else:
            result_value = (
                float(candles_list[i + ma_value - 1][4]) - ma_list[-1][1]
            ) * weight_koeff + result_value

        ma_list.append(
            [
                candles_list[i + ma_value - 1][0],  # Время
                result_value,                       # Значение ЕМА
                candles_list[i + ma_value - 1][4],  # Цена закрытия свечи
                candles_list[i + ma_value - 1][1],  # Цена открытия свечи
                ma_value,                           # Значение МА
            ]
        )
        i += 1
    return ma_list


# Получаем MACD значение кривой
def get_macd_data(candles_list, ma_min_value, ma_max_value):
    macd_list = (
        []
    )  # список (дата, значение МА, стоимость на закрытие свечи) с посчитанными значениями MA

    ema_min_list = get_ema_data(candles_list, ma_min_value)
    ema_max_list = get_ema_data(candles_list, ma_max_value)
    # начинаем расчет MA и записываем значение в массив
    i = 0
    while i != len(ema_max_list):
        result_value = float(ema_min_list[i + len(ema_min_list) - len(ema_max_list)][1]) - float(ema_max_list[i][1])
        macd_list.append(
            [
                ema_max_list[i][0],                                          # Время
                result_value,                                                # Значение сигнала MACD (разница)
                ema_min_list[i + len(ema_min_list) - len(ema_max_list)][1],  # Значение минимального ЕМА
                ema_max_list[i][1],                                          # Значение максимального ЕМА
                ema_max_list[i][2],                                          # Цена закрытия свечи
                ema_max_list[i][3]                                           # Цена открытия свечи
            ]
        )
        i += 1
    return macd_list


# Получаем все значения индикатора MACD
def get_macd_indicator(candles_list, ma_min_value, ma_max_value, signal_value):

    macd_list = get_macd_data(candles_list, ma_min_value, ma_max_value)

    first_signal_value = 0

    i = 0
    while i != signal_value:  # Определим SMA для первого времени для значения Signal
        first_signal_value += float(macd_list[i][1])
        i += 1

    first_signal_value = first_signal_value / signal_value

    macd_signal_list = (
        []
    )

    i = 0
    result_value = 0.0
    while i != len(macd_list) - signal_value + 1:
        if i == 0:
            result_value = first_signal_value
        else:
            result_value = float(macd_list[i + signal_value - 1][1]) * (2 / (signal_value + 1)) + result_value * (1 - (2 / (signal_value + 1)))

        diff = macd_list[i + signal_value - 1][1] - result_value

        macd_signal_list.append(
            [
                macd_list[i + signal_value - 1][0],  # Время
                diff,                                # Разность (осциллятор) индикатора MACD
                macd_list[i + signal_value - 1][1],  # MACD value
                result_value,                        # Signal value
                macd_list[i + signal_value - 1][2],  # Min EMA value
                macd_list[i + signal_value - 1][3],  # MAX EMA value
                ma_min_value,                        # MIN EMA
                ma_max_value,                        # MAX EMA
                signal_value,                        # Signal
                macd_list[i + signal_value - 1][4],  # Цена закрытия свечи
                macd_list[i + signal_value - 1][5]   # Цена открытия свечи
            ]
        )
        i += 1

    return macd_signal_list


def find_revenue_macd(macd_indicator, buy_value, tax_percent=0.1):

    tax_value = tax_percent / 100  # Переводим проценты в десятичное число
    usd_balance = 10000.0  # изменяемый баланс кошелька в долларах
    open_usd_balance = usd_balance  # Сумма кошелька в начале
    crypto_balance = 0  # баланс в крипте

    revenue_fer_deal = 0
    count_plus_deal = 0
    count_minus_deal = 0
    count_operation = 0  # количество операций
    result = []  # Список для вывода результата
    deals = []  # сумма, которую принесла операция
    is_buy_trend = 0  # нужен для того, чтобы после продажи сразу не произошла покупка при положительном MACD
    last_buy_value = 0  # цена прошлой сделки
    max_macd_on_trend = -1  # максимальное значение macd для самой усппешной продажи
    increase_macd_value = 0  # насколько процентов уменьшилось значение индикитора MACD

    for i in range(0, len(macd_indicator), 1):

        if i == 0:  # пропускаем первую итерацию, потому что нельзя сказать, стоит покупать или продавать крипту
            continue

        macd_value = float(macd_indicator[(i - 1)][1])  # Значение осциллятора

        if macd_value < 0 and usd_balance != 0:
            is_buy_trend = 0

        if macd_value >= buy_value and is_buy_trend == 0:  # покупка крипты
            count_crypto = int((1 - tax_value) * usd_balance / float(macd_indicator[i][10]))  # сколько мы можем криптовалют купить
            crypto_balance += count_crypto  # Добавляем крипту в кошелек
            deal_value = (count_crypto * float(macd_indicator[i][10]) * (1 + tax_value))  # сколько отдаем долларов
            revenue_fer_deal = deal_value
            usd_balance = 0  # вычитаем доллары из баланса
            count_operation += 1
            is_buy_trend = 1
            last_buy_value = float(macd_indicator[i][10])
            deals.append([f"покупка {macd_indicator[i][0]} ", deal_value])

        if float(macd_indicator[i][10]) > 1.01 * last_buy_value and crypto_balance != 0:  # продажа крипты
            deal_value = crypto_balance * float(macd_indicator[i][10]) * (1 - tax_value)  # За сколько долларов продали
            usd_balance += deal_value  # Пополняем кошелек долларов
            crypto_balance = 0  # Вычитаем крипту из кошелька
            count_operation += 1
            last_buy_value = 0  # Обнуляем цену покупки
            deals.append([f"продажа {macd_indicator[i][0]} ", deal_value - revenue_fer_deal])
            if deal_value > revenue_fer_deal:
                count_plus_deal += 1
            else:
                count_minus_deal += 1

        if float(macd_indicator[i][10]) < last_buy_value * 0.99 and crypto_balance != 0:  #  стоп лосс
            deal_value = crypto_balance * float(macd_indicator[i][10]) * (1 - tax_value)  # За сколько долларов продали
            usd_balance += deal_value  # Пополняем кошелек долларов
            crypto_balance = 0  # Вычитаем крипту из кошелька
            count_operation += 1
            last_buy_value = 0  # Обнуляем цену покупки
            deals.append([f"Стоп лосс продажа {macd_indicator[i][0]} ", deal_value - revenue_fer_deal])
            if deal_value > revenue_fer_deal:
                count_plus_deal += 1
            else:
                count_minus_deal += 1

        i += 1

    if crypto_balance != 0:
        deal_value = crypto_balance * float(macd_indicator[-1][10])
        usd_balance += deal_value
        if deal_value > revenue_fer_deal:
            count_plus_deal += 1
            count_operation += 1
        else:
            count_minus_deal += 1
            count_operation += 1

    result.append(
        [
            usd_balance / open_usd_balance,
            f"Статистика за {data.split(' ')[0]} дней, интервал {interval}, пара {symbol}\n"
            f"МА меньшая = {macd_indicator[0][6]}, МА большая = {macd_indicator[0][7]}, MA сигнал = {macd_indicator[0][8]}\n"
            f"Остаток средств = {usd_balance}, выручка {usd_balance - open_usd_balance} долларов, увеличили кошелек в {usd_balance/open_usd_balance} раз\n"
            f"Количество операций = {count_operation}\n"
            f"Количество пар сделок в + {count_plus_deal}\n"
            f"Количество пар сделок в - {count_minus_deal}\n",
        ]
    )

    result.append(deals)

    return result


def optimization_macd_rsi(list_data, min_ma_value, max_ma_value, ma_signal):

    result = []  # Список со всеми результатами
    max_value = [[0, "ggg"]]  # лучшее сочетание МА
    for min_ma in range(min_ma_value, max_ma_value, 1):
        for max_ma in range(min_ma + 1, max_ma_value + 1, 1):
            for signal in range(1, ma_signal + 1, 1):
                result.append(
                    find_revenue_macd(get_macd_indicator(list_data, min_ma, max_ma, signal))
                )
        print(min_ma)

    for dat in result:
        if dat[0][0] > max_value[0][0]:
            max_value = dat

    return max_value


def main():
    result = []  # список с результатом вычислений

    list_data = get_list_data(symbol, interval, data, correction_time)  # получаем список выборки с БД
    macd = get_macd_indicator(list_data, 14, 26, 9)
    avg_buy_value = get_avg_macd_oscillator(macd) * 2.8
    # print(f"значение осциллятора{avg_buy_value}")
    # фыв = find_revenue_macd(macd, avg_buy_value)
    # print(фыв)

    print(macd)

    # with open("result-macd_wo_rsi.txt", "w") as file:
    #     result = optimization_macd_rsi(list_data, 1, 50, 50)
    #     file.write(result[0][1])
    #     for deal in result[1]:
    #         file.write(f"\n{deal[0]} : {deal[1]}")


if __name__ == "__main__":
    main()
