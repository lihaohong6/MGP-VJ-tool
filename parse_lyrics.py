from main import create_lyrics
from models.song import get_manual_lyrics


def main():
    lyrics = get_manual_lyrics()
    print(create_lyrics(lyrics))


if __name__ == "__main__":
    main()
