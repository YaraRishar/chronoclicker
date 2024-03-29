# chronoclicker
Chronoclicker - это автокликер для вара, использующий в основном Selenium WebDriver. На данный момент (v1.0) кликер умеет: качать активность, УН, КУ, ПУ, т. е. ходить по локациям по маршруту и выполнять любые действия.
github: https://github.com/YaraRishar/chronoclicker
vk: https://vk.com/chronoclicker
## Описание работы кликера
При запуске кликер открывает вебдрайвер - отдельный браузер (в данном случае Chrome For Testing), в котором открывается только вкладка Игровой. Если вы запустили кликер в первый раз, то спустя 5-30 секунд ожидания вы увидите страницу входа на catwar. **Важно:** данные, которые вы использовали для входа на вар, сохраняются на вашем компьютере. Местонахождение этих данных зависит от операционной системы, на Manjaro Linux (и, скорее всего, на всех Linux) они хранятся в папке selenium, она создаётся при запуске вебдрайвера там же, где лежит main.py. На всякий случай **НЕ ПЕРЕСЫЛАЙТЕ НИКОМУ ПАПКУ SELENIUM!** Если вы хотите поделиться с кем-то кликером, то скиньте им ссылку на гитхаб/паблик вк (см. первый абзац), где лежит версия точно без ваших данных.
Вебдрайвер контролируется командами из приложения main.py.
Вид консоли может отличаться на других операционных системах, но так выглядит кликер после захода с вашими данными. Секция "коты на локации" замазана анонимности ради (игнорируйте сидящих с белой стрелкой, readme пишется во время похорон). Если вы видите надпись "Загружается...", но вебдрайвер не открывается даже спустя несколько минут ожидания, напишите в ЛС паблика.
После символов ">>>" можно ввести команду, которая будет исполняться в вебдрайвере. comm_help выводит просто список доступных команд, гайд ниже содержит их описания и примеры использования.
## Установка
### Вариант А: воспользоваться готовым приложением
Этот вариант предпочтителен только в том случае, если вы *совсем* не хотите устанавливать Python и доверяете рандому из интернета (ака мне). Исходный код всё ещё лежит в архиве с приложением, папка source, так что желательно ознакомиться с тем, что вы запускаете - ко всем функциям есть комментарии.
1. Скачайте архив chronoclicker_v1.0.zip
2. Распакуйте его с помощью 7zip или rar.
3. В распакованном архиве лежит main.exe - это и есть кликер (подробнее о его работе рассказано в предыдущем пункте).
4. Запустите main.exe, при этом должно появиться окно консоли с надписью "Загрузка..." и окно вебдрайвера.
5. После того, как вы ввели свои данные, опять же, не отправляйте папку с кликером никому, так как они могут храниться и в ней.
6. Зайдите в Игровую (в окне вебдрайвера).
7. В окно консоли после символов ">>>" введите любую команду из гайда ниже, например, "do Копать землю" без кавычек. Если ваш персонаж действительно начал копать, то вы успешно установили кликер. Если вебдрайвер крашнулся, то напишите в ЛС паблика со скрином ошибки/крашлогом.
### Вариант Б: скомпилировать код самостоятельно
Чуть более сложный вариант, но в какой-то мере гарантирует, что вы знаете, что делаете.
1. Установите последнюю версию Python с официального сайта (https://www.python.org/) с добавлением python в переменную PATH.
2. Откройте командную строку (win+R, в открывшемся окошке наберите cmd).
3. Кликер использует два пакета: selenium и selenium_stealth, первый обеспечивает работу вебдрайвера, второй прячет кликер от варовского античита. Для их установки в командной строке наберите py -m pip install selenium и py -m pip install selenium_stealth.
4. С гитхаба (https://github.com/YaraRishar/chronoclicker) скачайте исходный код (зелёная кнопка Code, в выпадающем меню Download ZIP).
5. В распакованном архиве лежит main.py, откройте его в Python IDLE (устанавливается вместе с Python) или в PyCharm (если есть).
6. Попробуйте запустить код: F5 или зелёный треугольник в правом верхнем углу. Если вы видите надпись "Загружается...", то вебдрайвер откроется через ~20 секунд при первом запуске. Далее следуйте инструкциям со скриншотами из варианта A.
7. Если же программа крашнулась, то скачайте chromedriver (https://googlechromelabs.github.io/chrome-for-testing/#stable), вероятно, нужная версия указана в таблице как chromedriver - win64.
8. В файле config.json найдите параметр "driver_path": "" и в кавычки вставьте путь к chromedriver.exe.
9. Теперь вебдрайвер должен запуститься. Если, несмотря на правильность пути, программа крашится, то напишите в ЛС паблика со скринами ошибки.
## Гайд по командам
#####  go название_локации1 - название_локации2
Команда перехода, маршрут проходится один раз. Пример:
go Обжитая айн прогалина - Тёплые камни
##### patrol название_локации1 - название_локации2
Команда перехода, маршрут повторяется бесконечно (для маршрута из 3 локаций: 1 - 2 - 3 - 2 - 1 - 2 - 3 и так далее).
##### do действие1 - действие2
Команда для исполнения последовательности действий один раз. Пример:
do Принюхаться - Копать землю - Вылизаться
##### repeat действие1 - действие2
Команда для бесконечного повторения действий. Пример:
repeat Принюхаться - Копать землю
*Заметка:* если действие нюха недоступно на данный момент, то кликер пропустит его и выполнит копание. Но если на следующее повторение цикла нюх доступен, то он будет выполнен. То же самое верно и для переходов.
##### swim локация_для_отсыпа
Команда для плавания с отсыпом на соседней локации. Критическое количество пикселей сна (при котором начнётся отсып) указывается в config. Для справки: 20 пикс. = ~43 минуты сна, 30 пикс. = ~40 минут сна. Считаются "оставшиеся" зелёные пиксели.
ВНИМАНИЕ: перед использованием этой команды проверьте на безопасной ПУ локации, работает ли она на вашем устройстве. Если команда не работает (а она, вероятно, не работает), то на безопасной локации вы можете просто запустить repeat Поплавать.
##### alias name comm
Команда для создания сокращений для часто используемых команд.
Пример:  
alias кач_актив patrol Морозная поляна - Поляна для отдыха  
В дальнейшем команда patrol Морозная поляна - Поляна для отдыха будет исполняться при вводе кач_актив. Все названия сокращений должны быть без пробелов. Сокращения сохраняются в файле config.json, их можно редактировать и напрямую в обычном блокноте, но придерживайтесь формата! Бэкап конфига хранится в папке internal.
##### say сообщение
Написать сообщение в чат Игровой.
##### info
вывести информацию об окружающей среде (список котов на локации и доступных переходов убран из 1.0 из-за нестабильности)
##### char
вывести информацию о персонаже (т. е. имя, луны, должность, навыки). Из навыков показывает только УН, КУ, ПУ, БУ.
##### hist
Вывести историю действий.
##### clear_hist
Очистить историю.
##### comm_help
Вывести список доступных команд.
##### refresh
Перезагрузить страницу.
##### cancel
Отменить действие.
##### settings key - value
Команда для изменения настроек. Пример:
settings is_headless - True
## Что делают настройки в config.json
##### long_break_chance
После каждого "круга" действий/каждого перехода есть шанс, что кликер прекратит работу на некоторое количество секунд, имитируя AFK. По умолчанию этот шанс равен 0.05, что соответствует 5%. Тогда 10% == 0.1, 95% == 0.95 и так далее. Если вы оставляете кликер на ночь, лучше не понижайте этот шанс до 0 или 0.01.
##### long_break_duration
Это и есть "некоторое количество секунд", указанное в предыдущем пункте. По умолчанию AFK-перерыв длится от 10 до 500 секунд, значение выбирается рандомно в этих границах.
##### short_break_duration
Этот параметр отвечает за перерыв после каждого действия, по умолчанию от 1 до 15 секунд. Теоретически его можно понизить, например, до 0-1, но во избежание бана лучше так не делать.
##### critical_sleep_pixels
Используется только для команды swim, которая скорее всего не работает в v0.1. Обозначает количество оставшихся зелёных пикселей в параметре сна, при котором персонаж прекращает плавать и идёт отсыпаться. 
##### is_headless
Запуск вебдрайвера без интерфейса. Если вы не хотите, чтобы окно браузера забирало память/мешало вам/етс, то вы можете изменить это значение на True и играть в вар с консоли.
##### driver_path
Путь к вашему chromedriver, если вам понадобилось его скачивать при установке. По умолчанию равен "".
##### max_waiting_time
Сколько вебдрайвер может ожидать загрузки страницы. Если у вас плохой интернет и загрузка занимает больше 3 секунд, измените это значение на 10 или 15.
##### monitor_chat_while_waiting
Если значение стоит на True, то во время действий/переходов в консоль будут выводиться сообщения из чата Игровой. Полезно, если вы запускаете кликер в headless-режиме. По умолчанию False.
