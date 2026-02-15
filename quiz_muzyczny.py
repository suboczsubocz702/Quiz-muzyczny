import os
import random
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog
from mutagen import File as MutagenFile


ROUNDS = 10
FRAGMENT_SECONDS = 10

current_player = None

class Track:
    def __init__(self, title, artist, path, duration):
        self.title = title
        self.artist = artist
        self.path = path
        self.duration = duration

def load_library(root):
    tracks = []

    for base, _, files in os.walk(root):
        for name in files:
            if not name.lower().endswith((".mp3", ".wav", ".ogg", ".flac")):
                continue

            path = os.path.join(base, name)

            title = None
            artist = None
            duration = None

            try:
                audio = MutagenFile(path, easy=True)
                if audio:
                    title = (audio.get("title") or [None])[0]
                    artist = (audio.get("artist") or [None])[0]

                audio_full = MutagenFile(path)
                if audio_full and audio_full.info:
                    duration = int(audio_full.info.length)

            except Exception:
                pass

            if not title:
                title = os.path.splitext(name)[0]
            if not artist:
                artist = "Unknown"
            if not duration:
                duration = FRAGMENT_SECONDS + 1

            tracks.append(Track(title, artist, path, duration))

    return tracks

def play_random_fragment(track):
    global current_player

    stop_audio()

    if track.duration <= FRAGMENT_SECONDS:
        start = 0
    else:
        start = random.randint(0, track.duration - FRAGMENT_SECONDS)

    current_player = subprocess.Popen(
        [
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel", "quiet",
            "-ss", str(start),
            "-t", str(FRAGMENT_SECONDS),
            track.path,
        ]
    )


def stop_audio():
    global current_player
    if current_player and current_player.poll() is None:
        current_player.terminate()
    current_player = None

class QuizApp:
    def __init__(self, root, library):
        self.root = root
        self.library = library

        root.title("Music Quiz")
        root.geometry("600x520")

        self.info = tk.Label(root, text="", font=("Arial", 14))
        self.info.pack(pady=10)

        self.play_button = tk.Button(
            root,
            text="▶ Odtwórz fragment",
            command=self.play_clip,
            font=("Arial", 14, "bold"),
            height=2,
        )
        self.play_button.pack(pady=10)

        self.buttons = []
        for _ in range(4):
            b = tk.Button(
                root,
                text="",
                height=3,
                font=("Arial", 14, "bold"),
                wraplength=500,
            )
            b.pack(fill="x", padx=20, pady=5)
            self.buttons.append(b)

        self.next_button = tk.Button(
            root,
            text="Następny utwór",
            font=("Arial", 14, "bold"),
            height=2,
            command=self.next_round,
            state="disabled",
        )
        self.next_button.pack(pady=10)

        self.score = 0
        self.round = 0
        self.correct = None
        self.options = []

        self.next_round()

    def reset_game(self):
        self.score = 0
        self.round = 0
        self.play_button.config(state="normal")
        self.next_button.config(text="Następny utwór", command=self.next_round)
        self.next_round()

    def next_round(self):
        stop_audio()

        if self.round >= ROUNDS:
            self.info.config(text=f"Koniec gry. Wynik: {self.score}/{ROUNDS}")
            for b in self.buttons:
                b.config(state="disabled")

            self.play_button.config(state="disabled")

            self.next_button.config(
                text="Zagraj ponownie",
                state="normal",
                command=self.reset_game,
            )
            return

        self.round += 1
        self.info.config(text=f"Runda {self.round}/{ROUNDS} | Punkty: {self.score}")

        self.correct = random.choice(self.library)
        wrong = random.sample([t for t in self.library if t != self.correct], 3)
        self.options = wrong + [self.correct]
        random.shuffle(self.options)

        for i, t in enumerate(self.options):
            self.buttons[i].config(
                text=f"{t.artist} – {t.title}",
                state="normal",
                command=lambda x=i: self.answer(x),
            )

        self.next_button.config(state="disabled")

    def play_clip(self):
        threading.Thread(
            target=play_random_fragment, args=(self.correct,), daemon=True
        ).start()

    def answer(self, index):
        stop_audio()

        for b in self.buttons:
            b.config(state="disabled")

        if self.options[index] == self.correct:
            self.score += 1
            self.info.config(
                text=f"Poprawnie! {self.correct.artist} – {self.correct.title}"
            )
        else:
            self.info.config(
                text=f"Błąd. {self.correct.artist} – {self.correct.title}"
            )

        self.next_button.config(state="normal")

def main():
    root = tk.Tk()
    root.withdraw()

    folder = filedialog.askdirectory(title="Wybierz folder z muzyką")
    if not folder:
        return

    print("Wczytywanie biblioteki...")
    library = load_library(folder)

    if len(library) < 4:
        print("Potrzebne min. 4 utwory.")
        return

    root.deiconify()
    app = QuizApp(root, library)
    root.mainloop()


if __name__ == "__main__":
    main()

