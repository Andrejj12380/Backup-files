# coding=utf-8
import requests
from progress.bar import FillingSquaresBar
import json


class VKUser:
    VK_HOST = 'https://api.vk.com/method/'
    TOKEN = input('Введите токен VK: ')
    VERSION = '5.131'
    user_id = input('Введите id пользователя: ')
    album_id = input('Из какого альбома загрузить фото?\nПрофиль, Стена или Сохраненные: ')
    ya_token = input('Введите токен Яндекс.Диска: ')
    YA_HOST = 'https://cloud-api.yandex.net:443'
    photos_dict = {}
    folder_name = ''
    json_struct = []

    def __init__(self):
        self.params = {
            'access_token': self.TOKEN,
            'v': self.VERSION
        }

    def _get_album_id(self):
        answer = {'profile': ['профиль', 'проф', 'профиля', 'пр'],
                  'wall': ['стена', 'стен', 'стены', 'ст'],
                  'saved': ['сохраненное', 'сохраненные', 'сохран', 'сох']}
        for eng, rus in answer.items():
            for word in rus:
                if self.album_id.lower() == word.lower():
                    return eng
        else:
            return print('Такого альбома не существует')

    def _get_user_id(self):
        try:
            user_id = self.user_id
            request = self.VK_HOST + 'users.get'
            request_params = {
                'user_ids': user_id,
                'fields': 'id'
            }
            id_response = requests.get(request, params={**self.params, **request_params}).json()
            self.folder_name = f'{id_response["response"][0]["first_name"]} ' \
                               f'{id_response["response"][0]["last_name"]} {self._get_album_id().capitalize()}'
            return int(id_response['response'][0]['id'])
        except Exception:
            print('Пользователь не найден')
            exit()

    def get_photos_dict(self):
        request = self.VK_HOST + 'photos.get'
        request_params = {
            'owner_id': f'{self._get_user_id()}',
            'album_id': f'{self._get_album_id()}',
            'extended': 1,
            'count': 1000
        }
        try:
            response = requests.get(request, params={**self.params, **request_params}).json()
            count_photos = int(input(f'Найдено {response["response"]["count"]} фото.\n'
                                     f'Введите количество фотографий для загрузки: '))
            request_params['count'] = count_photos
            response_by_count = requests.get(request, params={**self.params, **request_params}).json()
            for photo in response_by_count['response']['items']:
                self.photos_dict[f'{photo["id"]}'] = {f'{photo["sizes"][-1]["url"]}': f'{photo["likes"]["count"]}'}
                self.json_struct.append({'file_name': f'{photo["likes"]["count"]}.jpg',
                                         f'size': f'{photo["sizes"][-1]["type"]}'})
            with open('result.json', 'w', encoding='utf-8') as file:
                json.dump(self.json_struct, file, ensure_ascii=False, indent=2)
            return self.photos_dict
        except Exception:
            print('Доступ к альбому запрещён.')
            exit()

    def get_headers(self):
        headers = {'Content-Type': 'application/json',
                   'Authorization': f'OAuth {self.ya_token}'}
        if len(self.ya_token) < 10:
            print('Недопустимый токен')
            exit()
        else:
            return headers

    def create_folder(self):
        url = f'{self.YA_HOST}/v1/disk/resources/'
        headers = self.get_headers()
        params = {'path': self.folder_name}
        requests.put(url=url, headers=headers, params=params)

    def upload(self):
        self.get_photos_dict()
        self.create_folder()
        bar = FillingSquaresBar('Progress', max=len(self.photos_dict), width=50)
        count = 0
        status_code = 0
        for ids, info in self.photos_dict.items():
            for link, likes in info.items():
                path = f'/{self.folder_name}/{str(likes)}.jpg'
                url = f'{self.YA_HOST}/v1/disk/resources/upload/'
                headers = self.get_headers()
                params = {'path': path, 'url': f'{link}'}
                response = requests.post(url=url, headers=headers, params=params)
                status_code = response.status_code
            if status_code == 202:
                count += 1
                bar.message = f'{count} фото из {len(self.photos_dict)}'
                bar.next()
            else:
                bar.finish()
                print('Загрузка прервана')
                exit()
        bar.finish()
        print('Загрузка завершена!')


user = VKUser()
user.upload()
