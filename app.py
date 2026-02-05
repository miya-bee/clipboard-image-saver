import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageGrab
import os
import time
import threading
from pathlib import Path

class ClipboardWatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("クリップボード画像保存アプリ")
        self.root.geometry("300x150")
        self.root.resizable(False, False)

        # 状態管理フラグ
        self.is_monitoring = False
        self.last_image_bytes = None # 重複保存防止用

        # 保存先設定 (ユーザーのピクチャフォルダ)
        self.save_dir = Path.home() / "Pictures"
        
        # GUIパーツの配置
        self.status_label = tk.Label(root, text="待機中", font=("Meiryo", 12), fg="gray")
        self.status_label.pack(pady=10)

        self.btn_start = tk.Button(root, text="監視開始", command=self.start_monitoring, width=15, bg="#dddddd")
        self.btn_start.pack(pady=5)

        self.btn_stop = tk.Button(root, text="監視中止", command=self.stop_monitoring, width=15, state=tk.DISABLED)
        self.btn_stop.pack(pady=5)

    def get_next_filename(self):
        """0001から始まる連番ファイル名を生成する"""
        files = list(self.save_dir.glob("*.jpg"))
        max_num = 0
        for f in files:
            try:
                # ファイル名が数字4桁かどうかチェック
                stem = f.stem # 拡張子なしのファイル名
                if stem.isdigit() and len(stem) == 4:
                    num = int(stem)
                    if num > max_num:
                        max_num = num
            except ValueError:
                continue
        
        return self.save_dir / f"{max_num + 1:04d}.jpg"

    def start_monitoring(self):
        self.is_monitoring = True
        self.status_label.config(text="監視中...", fg="green")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        
        # 別スレッドで監視を開始（GUIを固まらせないため）
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()

    def stop_monitoring(self):
        self.is_monitoring = False
        self.status_label.config(text="停止しました", fg="red")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

    def monitor_loop(self):
        while self.is_monitoring:
            try:
                # クリップボードの中身を取得
                im = ImageGrab.grabclipboard()

                if isinstance(im, Image.Image):
                    # 画像データの場合のみ処理 (ファイルコピーなどは除外)
                    current_bytes = im.tobytes()

                    # 直前に保存した画像と違う場合のみ保存 (重複防止)
                    if self.last_image_bytes != current_bytes:
                        save_path = self.get_next_filename()
                        # JPEG形式で保存
                        im.convert("RGB").save(save_path, "JPEG")
                        
                        # 状態更新
                        self.last_image_bytes = current_bytes
                        print(f"Saved: {save_path}") # デバッグ用ログ
                        
                        # GUIのラベル更新（スレッドセーフにするためafter使用）
                        self.root.after(0, lambda p=save_path.name: self.status_label.config(text=f"保存: {p}"))
                
                else:
                    # クリップボードが画像でない、または空の場合
                    # リセットはしない（連続保存を防ぐため、何か別のものがコピーされるまでは保持）
                    pass

            except Exception as e:
                print(f"Error: {e}")

            # 0.5秒待機 (CPU負荷軽減)
            time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClipboardWatcherApp(root)
    root.mainloop()