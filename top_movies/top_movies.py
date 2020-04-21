import os
from difflib import SequenceMatcher
import jellyfish


def normalize(s):
    remove = ":-`'\";.,"
    for c in remove:
        s = s.replace(c, "")
    return s.lower().strip()


def similar(a, b):
    return jellyfish.levenshtein_distance(normalize(a), normalize(b)) <= 3


def get_current_movies():
    def parse_movie(m):
        return {
            "movie_title": m[:m.rindex(" (")],
            "title_year": m[m.rindex("(")+1:-1]
        }

    movies = [parse_movie(m) for m in os.listdir(
        "/Volumes/GoogleDrive/Mi unidad/Entretenimiento/Peliculas") if "(" in m]
    return movies


def get_top_movies():
    with open("movie_metadata.csv", "r") as file:
        headers = file.readline().split(",")
        targets = ["movie_title", "title_year", "imdb_score"]
        indexes = list(map(lambda t: headers.index(t), targets))

        def parse_movie(m):
            return {key: m[index].strip().strip('"')
                    for key, index in zip(targets, indexes)}

        def valid_movie(m):
            try:
                year = int(m["title_year"])
                score = float(m["imdb_score"])
                return year < 3000 and score <= 10
            except Exception:
                return False

        movies = filter(valid_movie, sorted(
            [parse_movie(line.split(",")) for line in file.readlines()],
            key=lambda m: m["imdb_score"],
            reverse=True))
    return list(movies)


def get_missing_movies():
    current = get_current_movies()
    movies = get_top_movies()
    missing = []
    for i, movie in enumerate(movies):
        if i % 50 == 0:
            print(f"{round((i+1) * 100 / len(movies))} %")
        for current_movie in current:
            same_name = similar(
                current_movie["movie_title"], movie["movie_title"])
            same_year = current_movie["title_year"] == movie["title_year"]
            if same_name and same_year:
                break
        else:
            missing.append(movie)
    return missing


if __name__ == "__main__":
    movies = get_missing_movies()
    with open("missing.csv", "w") as file:
        file.write("Película;Año;Imdb Score\n")
        for movie in movies:
            file.write(
                f"{movie['movie_title']};{movie['title_year']};{movie['imdb_score'].replace('.',',')}\n")
