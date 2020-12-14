# Ezequiel the Ghost - музыкальный (и не только) Discord бот 

Данный бот сочетает в себе функционал музыкального плеера, экономическую систему для участников, релизованную с использованием MongoDB, а так же набор команд для администраторов сервера. 

## Полный список команд
![Команды](https://sun9-31.userapi.com/impf/Nf5QdmdXCSwi5uaZs9w4UI7wi5KRn6mzBjWClw/GXt6h1I0bVM.jpg?size=754x541&quality=96&proxy=1&sign=1a4237a6d68d3af53a8bb9d639d8eb75&type=album)

## MongoDB
Для работы с этой базой данных требуется подключить pymongo. При помощи MongoClient создается подключение к кластеру, в котором находится нужная коллекция с документами. 

![Подключение БД](https://sun9-12.userapi.com/impf/MWepaRHenbWrcB70sP1AR2E_hqKA6kSH5OPh3g/RN_QaC4lNF0.jpg?size=455x50&quality=96&proxy=1&sign=28e0f794167b93989c6588a94a0441c5&type=album)

При первом подключении участника к серверу, в коллекции создается документ, с ID, равным ID участника на сервере. Документ содержит так же информацию о балансе, очках опыта и уровне участника.

![Запись в БД](https://sun9-53.userapi.com/impf/RrPDnK4-BZdtFsWwHe63-NltkwiXbriJj9k9Tg/evyhVDEEkKc.jpg?size=745x268&quality=96&proxy=1&sign=cf941c4036e4829594627e06e662e121&type=album)

За каждое отправленное сообщение участники получают 50 очков опыта, которые при достижении определенного числа (считается по формуле 500 + 100 * текущий уровень) обнуляются, а уровень - повышается на 1.
При вызове команды !топ можно увидеть ТОП-10 участников сервера, которые имеют наивысший уровень (реализованно функцией leaders). 

Функция повышения уровня:

![Level up](https://sun9-12.userapi.com/impf/rKxbe0jeT6a08ZlG6QttKrgSMjuUc8CbwkehJA/zZY5iuFXd_I.jpg?size=825x359&quality=96&proxy=1&sign=e38f8da46d75808d13240b21c61f9ddd&type=album)

Функция user_balance вызывается при использовании команды !баланс. Данная функция находит ID пользователя в базе данных и выводит значение соответствующего ключа balance. 
Функция pay_money отнимает указанное пользователем число э-коинов от его собственного баланса, и добавляет это число балансу указанного участника сервера.

## Музыкальный плеер
Данный бот умеет получать музыку с сервиса Youtube и транслировать ее в голосовой канал, благодаря Discord API и модулю youtube-dl. Вся работа описана в классах YTDLSource, Song, SongQueue, VoiceState, Music. 
YTDLSource позволяет получить данные: с помощью youtube_dl.YoutubeDL загружается видео-файл, далее в функции create_source данные из видео-файла обрабатываются, передаются в discord.FFmpegPCMAudio,
где они конвертируются в аудио-формат (PCM AudioSource). 

Использование функции create_sourse командой !play

![Проиграть музыку](https://sun9-35.userapi.com/impf/HsuEf2Lmx64EIv3tTC_-SAJ1s-OMRPR_8-MV4Q/AGtBjPrYcNI.jpg?size=761x322&quality=96&proxy=1&sign=5670f84fc3ecb34ac8add1391564704e&type=album)

Класс Song содержит функцию кастомного вывода информации, SongQueue - функцию очистки очереди и функцию удаления элемента из очереди.

В класее VoiceState содержится функция audio_player_task, позволяющая переключаться на следующий трек, после окончания текущего. 

![Ожидание задачи](https://sun9-12.userapi.com/impf/unAkd2PKdJkYOA6kqrhSN3WajmSh5r19M2ktgA/5HphxZNrMyo.jpg?size=711x594&quality=96&proxy=1&sign=8b1fc57fc5c50bf3aafd1de54f141abc&type=album)

Music содержит описание команд бота. 
 - присоединиться: определяется голосовой канал с пользователем, бот присоединяется к нему;
 - выйти: воспроизведение музыки останавливается, очередь сбрасывается;
 - играет: показывает текущий трек;
 
![Текущий трек](https://sun9-50.userapi.com/impf/TmlJUuBVnVcVbqoD1EyYyHSCrReFwjqrLp5bSA/U7lkp_WmzeQ.jpg?size=606x280&quality=96&proxy=1&sign=9fe7d9032531ac3162940ce9da6ef817&type=album)
 
 - пауза: воспроизведение приостанавливается;
 - продолжить: воспроизведение возобновляется;
 - пропустить: воспроизведение трека останавливается, переход к следующему треку в очереди;
 - очередь: если очередь не пуста, показывает кастомное окно очереди, представленное в виде страниц, по 10 треков каждая;
 
 ![Очередь](https://sun9-67.userapi.com/impf/lm61-nZCCJ5NU95tUoUUNq5dvwKoUnKEGYJ7rg/6r2PQhC5xbg.jpg?size=556x192&quality=96&proxy=1&sign=8129fc0624b8066dd3eb4fee0ffe236e&type=album)
 
 - убрать: если в списке очереди есть треки, удалить соответствующий переданному значению от пользователя (минус 1);
 - проиграть: код команды был приведен выше.
 
 ## Прочие функции + deployment
 
 Помимо вышеперечисленного, у бота есть небольшой пулл функций модерирования, таких как !очистить (позволяет удалить необходимое число сообщений одной командой) и !бан (исключить пользователя из канала и добавить его в бан-лист)
 Бот так же отправляет приветствие при заходе нового участника на сервер. Команды !load !unload !reload использовались во время разработки для экономии времени, в данный момент в них нет необходимости, так как бот был поставлен на хост Heroku. 
 
 ![Heroku](https://sun9-71.userapi.com/impf/5fiDA5mHObexvYvJCRSGk2jtRRvewo0FdamDMA/LetXrpy4fP4.jpg?size=651x80&quality=96&proxy=1&sign=ff80cf0a1ef9a6a351701aec5301748a&type=album)
 
 Со следующими билдпаками
 
 ![Билдпаки](https://sun9-28.userapi.com/impf/p8c4HZqm5QHszAGUSR-XjxKDeGiZ7o5sG25-5A/O1k3myVYyNM.jpg?size=795x254&quality=96&proxy=1&sign=a2a70982ec3f0414c98cd94f01ee5afa&type=album)
 
 ## Все, что использовалось в работе
 
 - Discord API
 - youtube-dl
 - Ffmpeg
 - MongoDB
 - Heroku
 
 Файл requirements.txt содержит список пакетов, необходимых в работе. Версия Python 3.7.9. 
 
 
