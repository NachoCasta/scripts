import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pyYify import yify
from qbittorrent import Client as TorrentClient
from time import sleep
import os
import shutil
import glob

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of the spreadsheet.
SPREADSHEET_ID = '1PRpJEAu-eJjl354fYccp5lyP_m2g3htjMT990EAT7ak'
RANGE_NAME = 'Películas!A2:E'
VALUE_INPUT_OPTION = "USER_ENTERED"

# Where to download the torrents
DOWNLOAD_PATH = "downloads"
DRIVE_PATH = '/Volumes/GoogleDrive/Mi unidad/Entretenimiento/Peliculas'

MAX_CONCURRENT_DOWNLOADS = 5


class Movie:
    def __init__(self, name, year):
        self.name = name
        self.year = int(year)
        self.local_path = self.get_path()

    def __repr__(self):
        return "{} ({})".format(self.name, self.year)

    def get_path(self):
        return os.path.abspath("{}/{}".format(DOWNLOAD_PATH, normalize(str(self))))

    def get_torrent(self):
        # Intenta 5 veces en caso de error
        for i in range(5):
            try:
                results = list(filter(
                    lambda r: r.year == self.year,
                    yify.search_movies(self.name, "All")
                ))
                break
            except Exception:
                continue
        else:
            return None
        if not results:
            self.yts = False
            return None
        self.yts = True
        result = results[0]
        torrents = [
            t for t in result.torrents if t.quality in ["720p", "1080p"]]
        torrents.sort(key=lambda t: parse_size(t.size), reverse=True)
        if not torrents:
            return None
        torrent = torrents[0]
        return torrent

    def clean_folder(self):
        folder = list(os.listdir(self.local_path))[0]
        folder_path = "{}/{}".format(self.local_path, folder)
        if os.path.isdir(folder_path):
            for f in os.listdir(folder_path):
                file_path = "{}/{}".format(folder_path, f)
                shutil.move(file_path, self.local_path)
            os.rmdir(folder_path)
        for f in os.listdir(self.local_path):
            if not '.mp4' in f and not '.avi' in f and not '.mkv' in f:
                try:
                    os.remove('{}/{}'.format(self.local_path, f))
                except PermissionError:
                    shutil.rmtree('{}/{}'.format(self.local_path, f))

    def delete_folder(self):
        try:
            os.rmdir(self.local_path)
        except Exception:
            pass

    def move_to_drive(self):
        drive_folder_path = "{}/{}".format(DRIVE_PATH, self)
        if os.path.isdir(drive_folder_path):
            for f in os.listdir(self.local_path):
                file_path = "{}/{}".format(self.local_path, f)
                if not os.path.isfile("{}/{}".format(drive_folder_path, f)):
                    shutil.move(file_path, drive_folder_path)
            try:
                os.rmdir(self.local_path)
            except Exception:
                pass
        else:
            shutil.move(self.local_path, DRIVE_PATH)


class AutoTorrent:
    def __init__(self):
        self.init_google_sheets()
        self.init_qb()
        self.downloading = {}

    def init_google_sheets(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        self.google_sheets = build('sheets', 'v4', credentials=creds)

    def init_qb(self):
        self.qb = TorrentClient("http://127.0.0.1:8080/")
        self.qb.login("admin", "adminadmin")

    def get_movies(self):
        sheet = self.google_sheets.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        filtered = filter(
            lambda m: m[0] in ["No Descargada", "Auto Descargando"] and (
                len(m) < 5 or m[4] not in ["No", "Pocos Seeds"]),
            values
        )
        movies = map(lambda m: Movie(m[1], m[2]), filtered)
        return movies

    def download_movie(self, movie):
        torrent = movie.get_torrent()
        if not torrent:
            print("    Torrent not found for {}. Skipping".format(movie))
            self.update_movie_yts(movie, "No")
            return
        magnet = torrent.magnet
        path = movie.local_path
        if not os.path.isdir(path):
            os.mkdir(path)
        self.qb.download_from_link(magnet, savepath=path)
        self.update_movie(movie, "Auto Descargando")
        for t in self.qb.torrents():
            if os.path.normpath(t["save_path"]) == os.path.normpath(path):
                torrent_hash = t["hash"]
                break
        self.downloading[torrent_hash] = movie
        print("    Started downloading {}".format(movie))

    def update_movie(self, movie, status):
        sheet = self.google_sheets.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=RANGE_NAME).execute()
        values = list(result.get('values', []))
        for value in values:
            if value[1] == movie.name and int(value[2]) == movie.year:
                value[0] = status
        body = {
            'values': values
        }
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption=VALUE_INPUT_OPTION,
            body=body).execute()

    def update_movie_yts(self, movie, yts):
        sheet = self.google_sheets.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=RANGE_NAME).execute()
        values = list(result.get('values', []))
        for value in values:
            if value[1] == movie.name and int(value[2]) == movie.year:
                if len(value) == 4:
                    value.append(yts)
                else:
                    value[4] = yts
        body = {
            'values': values
        }
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption=VALUE_INPUT_OPTION,
            body=body).execute()

    def should_download(self):
        current_torrents = len(self.qb.torrents(filter="downloading"))
        less_than_max = current_torrents < MAX_CONCURRENT_DOWNLOADS
        just_started = len(self.downloading) < MAX_CONCURRENT_DOWNLOADS
        return less_than_max or just_started

    def start(self):
        movies = self.get_movies()
        while True:
            sleep(1)
            self.clean_torrents()
            if not self.should_download():
                continue
            movie = next(movies)
            print(movie)
            self.download_movie(movie)

    def clean_torrents(self):
        timed_out = []
        done = []
        for torrent in self.qb.torrents():
            if torrent["progress"] == 1:
                done.append(torrent["hash"])
            elif is_timed_out(torrent):
                timed_out.append(torrent["hash"])
        for h in timed_out:
            if h not in self.downloading:
                continue
            movie = self.downloading[h]
            print("{} timed out. Removing".format(movie))
            self.update_movie(movie, "No Descargada")
            self.update_movie_yts(movie, "Pocos Seeds")
            self.qb.delete(h)
            movie.delete_folder()
        for h in done:
            if h not in self.downloading:
                continue
            movie = self.downloading[h]
            self.update_movie(movie, "Descargada")
            self.qb.delete(h)
            movie.clean_folder()
            movie.move_to_drive()
            print("{} finished downloading. Moving to Google Drive".format(movie))


def parse_size(size):
    value, unit = size.split(" ")
    value = float(value)
    if unit == "GB":
        value *= 1000
    return value


def normalize(s):
    remove = ":-`'\";.,/"
    for c in remove:
        s = s.replace(c, "")
    return s.strip()


# Constants for is_timed_out
SLOW_TIMEOUT = 300
SLOW_ETA = 2 * 60 * 60
SLOW_PROGRESS = 0.1
MAX_TIME = 5 * 60 * 60


def is_timed_out(torrent):
    time_active = torrent["time_active"]
    eta = torrent["eta"]
    progress = torrent["progress"]
    too_slow = time_active >= SLOW_TIMEOUT and eta >= SLOW_ETA and progress <= SLOW_PROGRESS
    got_stuck = time_active >= MAX_TIME
    return too_slow or got_stuck


def main():
    auto_torrent = AutoTorrent()
    auto_torrent.start()


if __name__ == '__main__':
    main()
