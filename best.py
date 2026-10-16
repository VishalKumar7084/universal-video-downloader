import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import yt_dlp
import threading
import shutil
import os
import re

class DownloadTask:
    def __init__(self, parent, url):
        self.url = url
        self.is_cancelled = False
        self.title_updated = False
        
        # TASK FRAME (White background)
        self.frame = tk.Frame(parent, bg="#ffffff", highlightbackground="#bdc3c7", highlightthickness=1)
        self.frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Task Title
        self.title_lbl = tk.Label(self.frame, text=url, font=("Arial", 9, "bold"), anchor="w", bg="#ffffff", fg="#2c3e50")
        self.title_lbl.pack(fill=tk.X, padx=10, pady=(10,5))
        
        # Progress Bar
        self.progress = ttk.Progressbar(self.frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # Bottom Area
        self.bottom_frame = tk.Frame(self.frame, bg="#ffffff")
        self.bottom_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        
        # Status Label
        self.status_lbl = tk.Label(self.bottom_frame, text="Preparing download...", font=("Arial", 8, "bold"), bg="#ffffff", fg="#d35400")
        self.status_lbl.pack(side=tk.LEFT)
        
        # Action Button (Cancel/Clear)
        self.action_btn = tk.Button(self.bottom_frame, text="Cancel", command=self.cancel, 
                                    bg="#e74c3c", fg="white", activebackground="#c0392b", activeforeground="white",
                                    font=("Arial", 8, "bold"), width=10, relief="flat", cursor="hand2")
        self.action_btn.pack(side=tk.RIGHT)
        
    def cancel(self):
        if self.action_btn['text'] == "Cancel":
            self.is_cancelled = True
            self.action_btn.config(state="disabled", text="Stopping...", bg="#95a5a6")
        elif self.action_btn['text'] == "Clear":
            self.frame.destroy()


class YoutubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Video Downloader - Vishal bharti")
        self.root.geometry("650x620") 
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f3f4")

        self.download_path = tk.StringVar()
        self.quality_var = tk.StringVar(value="Best Available")
        self.active_downloads = 0
        self.lock = threading.Lock()

        # HEADER AREA
        header_frame = tk.Frame(root, bg="#2c3e50")
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="Universal Video Downloader", font=("Arial", 16, "bold"), bg="#2c3e50", fg="#ffffff", pady=15).pack()
        
        # INPUT AREA
        tk.Label(root, text="Paste Video URL (YouTube / m3u8 / Public Telegram):", bg="#f0f3f4", fg="#2c3e50", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        self.url_entry = tk.Entry(root, width=65, font=("Arial", 10), relief="solid", bd=1)
        self.url_entry.pack(pady=5, ipady=3)

        tk.Label(root, text="Select Quality (If Available):", bg="#f0f3f4", fg="#2c3e50", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.quality_combo = ttk.Combobox(root, textvariable=self.quality_var, state="readonly", width=30)
        self.quality_combo['values'] = ('Best Available', '1080p', '720p', '480p', '360p', 'Audio Only (MP3)')
        self.quality_combo.current(0)
        self.quality_combo.pack(pady=5)

        # DIRECTORY SELECTION
        dir_frame = tk.Frame(root, bg="#f0f3f4")
        dir_frame.pack(pady=10)
        self.path_entry = tk.Entry(dir_frame, textvariable=self.download_path, width=45, state='readonly', font=("Arial", 10), relief="solid", bd=1)
        self.path_entry.pack(side=tk.LEFT, padx=5, ipady=4)
        
        tk.Button(dir_frame, text="Select Folder", command=self.browse_folder, 
                  bg="#2980b9", fg="white", activebackground="#1f618d", activeforeground="white",
                  font=("Arial", 9, "bold"), relief="flat", padx=10, pady=2, cursor="hand2").pack(side=tk.LEFT)

        # START DOWNLOAD BUTTON
        self.download_btn = tk.Button(root, text="Start Download", command=self.add_to_queue, 
                                      bg="#27ae60", fg="white", activebackground="#1e8449", activeforeground="white",
                                      font=("Arial", 12, "bold"), relief="flat", padx=20, pady=5, cursor="hand2")
        self.download_btn.pack(pady=10)

        self.active_label = tk.Label(root, text="Active Downloads: 0", bg="#f0f3f4", fg="#c0392b", font=("Arial", 10, "bold"))
        self.active_label.pack(pady=2)

        # SCROLLABLE DASHBOARD AREA
        self.canvas_frame = tk.Frame(root, bg="#bdc3c7", bd=1, relief="solid")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        self.canvas = tk.Canvas(self.canvas_frame, bg="#ecf0f1", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_container = tk.Frame(self.canvas, bg="#ecf0f1")
        self.scrollable_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.download_path.set(folder_selected)

    def update_active_count(self, change):
        with self.lock:
            self.active_downloads += change
        self.root.after(0, lambda: self.active_label.config(text=f"Active Downloads: {self.active_downloads}"))

    def add_to_queue(self):
        url = self.url_entry.get().strip()
        path = self.download_path.get()
        quality_choice = self.quality_var.get()

        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        if not path:
            messagebox.showerror("Error", "Please select a download folder")
            return

        if shutil.which("ffmpeg") is None:
            messagebox.showwarning("FFmpeg Missing", "System me FFmpeg install nahi hai!\nHD Quality videos blur aa sakte hain ya bina audio ke save ho sakte hain.")

        self.url_entry.delete(0, tk.END)
        task = DownloadTask(self.scrollable_container, url)

        thread = threading.Thread(target=self.download_worker, args=(url, path, quality_choice, task), daemon=True)
        thread.start()

    def download_worker(self, url, path, quality_choice, task):
        self.update_active_count(1)

        if "t.me/c/" in url:
            self.root.after(0, lambda: task.status_lbl.config(text="Error: Private Telegram link not supported.", fg="#e74c3c"))
            self.root.after(0, lambda: task.action_btn.config(text="Clear", bg="#7f8c8d", state="normal"))
            self.update_active_count(-1)
            return
            
        if "t.me/" in url or "telegram.me/" in url:
            url = url.split('?')[0]

        # --- IMPORTANT YT-DLP OPTIONS FIXES ---
        ydl_opts = {
            'paths': {'home': path},  # Safe way to handle output paths
            'outtmpl': {'default': '%(title).80s [%(id)s].%(ext)s'}, # Limits title length, prevents overwriting
            'windowsfilenames': True, # Fixes OS renaming/illegal char errors
            'noplaylist': True,       # Fixes 2 videos merging (Playlist block)
            'nocolor': True,
            'retries': 15,            # Fixes incomplete large downloads
            'fragment_retries': 15,
            'skip_unavailable_fragments': True,
            'concurrent_fragment_downloads': 5, # Speeds up M3U8 downloads
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        }

        # Handle Quality Selections
        if quality_choice == "Audio Only (MP3)":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        else:
            res_map = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}
            if quality_choice in res_map:
                res = res_map[quality_choice]
                ydl_opts['format'] = f'bestvideo[height<={res}]+bestaudio/best'
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            
            # Ensures proper merging of video+audio files and m3u8 fragments
            ydl_opts['merge_output_format'] = 'mp4'

        def progress_hook(d):
            if task.is_cancelled:
                raise ValueError("CANCELLED_BY_USER")

            if d['status'] == 'downloading':
                if not task.title_updated:
                    info = d.get('info_dict', {})
                    title = info.get('title')
                    if not title:
                        filename = d.get('filename', '')
                        title = os.path.basename(filename)
                    
                    if title:
                        self.root.after(0, lambda: task.title_lbl.config(text=title[:60] + "..."))
                        task.title_updated = True

                # Clean ANSI escape sequences safely using regex
                pct_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0.0%')).strip()
                speed_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_speed_str', 'N/A')).strip()
                eta_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_eta_str', 'N/A')).strip()

                try:
                    pct_val = float(pct_str.replace('%', '').strip())
                except:
                    pct_val = 0.0

                status_text = f"{pct_str} | Speed: {speed_str} | Time Left: {eta_str}"
                
                self.root.after(0, lambda: task.progress.config(value=pct_val))
                self.root.after(0, lambda: task.status_lbl.config(text=status_text, fg="#2980b9"))

            elif d['status'] == 'finished':
                self.root.after(0, lambda: task.status_lbl.config(text="100% | Finalizing & Merging HD Video...", fg="#8e44ad"))
                self.root.after(0, lambda: task.progress.config(value=100))

        ydl_opts['progress_hooks'] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            self.root.after(0, lambda: task.status_lbl.config(text="Download Complete!", fg="#27ae60", font=("Arial", 8, "bold")))
            self.root.after(0, lambda: task.action_btn.config(text="Clear", bg="#58487E", activebackground="#34495e", state="normal"))

        except Exception as e:
            error_msg = str(e)
            if "CANCELLED_BY_USER" in error_msg:
                self.root.after(0, lambda: task.status_lbl.config(text="Download Cancelled.", fg="#e74c3c"))
                self.root.after(0, lambda: task.progress.config(value=0))
            else:
                if "Unsupported URL" in error_msg and "t.me" in url:
                    error_msg = "Invalid/Private Telegram Link"
                self.root.after(0, lambda: task.status_lbl.config(text=f"Failed: {error_msg[:45]}", fg="#c0392b"))
            
            self.root.after(0, lambda: task.action_btn.config(text="Clear", bg="#0AB5C1", activebackground="#34495e", state="normal"))

        finally:
            self.update_active_count(-1)


if __name__ == "__main__":
    root = tk.Tk()
    app = YoutubeDownloaderApp(root)
    root.mainloop()