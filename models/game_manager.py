import os
import subprocess
import sys

class GameManager:
    def __init__(self):
        self.games_dir = "games"

    def get_game_list(self):
        # Tự động quét file .py trong thư mục games
        games = []
        if os.path.exists(self.games_dir):
            for file in os.listdir(self.games_dir):
                if file.endswith(".py"):
                    games.append(file.replace(".py", ""))
        return games

    def launch_game(self, game_name):
        game_path = os.path.join(self.games_dir, f"{game_name}.py")
        if os.path.exists(game_path):
            # Chạy Pygame như một tiến trình riêng biệt
            subprocess.Popen([sys.executable, game_path])
            return True
        return False