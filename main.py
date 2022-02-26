import requests
import os
from datetime import datetime
from tqdm import tqdm
import json

photos_info = {} # словарь, выгруженный из VK {количество лайков: {размер, ссылка}}
count_dict = {} # количество фотографий в профиле: количество запрашиваемых

class VkPhotos:

    def __init__(self, id_:str):
        self.id_ = id_ #Инициализация id профиля в ВК

    def search_photos(self):
        params = {
            'owner_id': self.id_,
            'access_token': '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008',
            'v': '5.131',
            'count': '10',
            'album_id': 'profile',
            'extended': '1',
            'photo_sizes': '0'}
        response = requests.get('https://api.vk.com/method/photos.get', params=params)
        data = response.json()
        try:
            for key, value in data.items():
                count_dict.setdefault(value['count'], params['count']) # Добавление значений в словарь с данными о количестве фото в профиле и количестве запрашиваемых пользователем
                for intelligence in value['items']:
                    if str(intelligence['likes']['count']) in photos_info.keys(): # Проверка словаря на наличие ключа с указанным количеством лайков, в случае наличия - добавление даты.
                        photos_info.setdefault(str(intelligence['likes']['count']) + '_' +
                                               str((datetime.utcfromtimestamp(intelligence['date']).strftime('%Y-%m-%d'))),
                                               {'size': str(intelligence['sizes'][-1]['type']), "link": str(intelligence['sizes'][-1]['url'])})
                    else:
                        photos_info.setdefault(str(intelligence['likes']['count']), {'size': str(intelligence['sizes'][-1]['type']),
                                                                                   "link": str(intelligence['sizes'][-1]['url'])})
        except:
            error_code = data['error']['error_code'] # Обработка ошибок, полученных от ВК
            if data['error']:
                print(f'Ошибка {error_code}, список кодов ошибок по ссылке: https://dev.vk.com/reference/errors')

class YaUploader:
    def __init__(self, token: str):
        self.token = token # Инициализация токена
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                   'Authorization': f'OAuth {self.token}'} # Инициализация headers
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources' #Инициализация url

    def create_folder(self, path):
        """Создание папки. path: Путь к создаваемой папке."""
        requests.put(f'{self.url}?path={path}', headers=self.headers)

    def upload(self, loadfile, savefile, replace=False):
        """Загрузка файла на Яндекс диск."""
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        result = requests.get(f'{upload_url}/upload?path={savefile}&overwrite={replace}', headers=headers).json()
        with open(loadfile, 'rb') as f:
            try:
                requests.put(result['href'], files={'file':f})
                #print(f'Файл {savefile} успешно сохранен')
            except KeyError:
                print(result) # обработка возможных ошибок, возвращение значения ошибки

def download_upload():
    photos_list = []  # список, формируемый для выходного json файла
    person_search = VkPhotos(id_) # Указание id профиля ВК для поиска данных
    person_search.search_photos() # Запуск метода для получения необходимых данных с конкретным id
    for k, v in tqdm(photos_info.items(), desc='Загрузка файлов', leave=True, unit=' Photos'):
        uploader = YaUploader(token) # запуск метода загрузки в классе Яндекса
        uploader.create_folder(id_) # запуск метода создания папки на Яндекс-диске с именем id профиля Вк
        img_data = requests.get(v['link']).content # загрузка фотографии по ссылке, полученной от ВК
        with open(k, 'wb') as handler: # открытие фотографии по ссылке, полученной от ВК на запись
            handler.write(img_data) # запись фотографии по ссылке, полученной от ВК, в память ПК
        uploader = YaUploader(token) # запуск класса яндекса
        uploader.upload(k, f'/{id_}/{str(k)}.jpg') # создание папки и указание пути для загрузки на Яндекс диске
        photos_list.append({'name': str(k) + '.jpg', 'size': str(v['size'])}) # добавление значений в словарь для выходного json
        os.remove(k) #удаление временного файла из памяти ПК
    with open('upload.json', 'w') as file: # открытие json файла на запись
        json.dump(photos_list, file, indent=2, ensure_ascii=False) #  запись json файла
        print('Создан файл "upload.json"')


if __name__ == '__main__':
    id_ = '' # ввести id пользователя Вк
    token = '' # ввести токен Яндекс-диска
    download_upload()