# Микросервис модификации изображений
Этот сервис предоставляет возможность удалить фон, удалить дубликаты по приближенным хэшам и реализует вклейку изображения в фон через пирамиду изображений
# Использование
1. Перейдите на страницу http://0.0.0.0:8002/docs
2. Выберите вид модификации изображения
3. rem_bg тело запроса не требует.
4. rem_dup тело запроса не требует.
5. Вклейка изображений в фон, укажите 2 id изображений из таблицы `selected_images`

   Например:
    ```
    {
      "first_image_id": 0,
      "second_image_id": 0
    }
    ```
    Результат вклейки можно наблюдать в таблице `pyramid_images`