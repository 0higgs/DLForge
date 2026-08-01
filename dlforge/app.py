from __future__ import annotations

import io
import os
import queue
import sys
import threading
import tkinter as tk
import urllib.request
from pathlib import Path
from tkinter import filedialog
from urllib.parse import urlparse

import customtkinter as ctk
from PIL import Image, ImageOps

from .engine import DownloadEngine, DownloadOptions


BG = "#080C17"
SURFACE = "#101726"
SURFACE_2 = "#151E30"
SURFACE_3 = "#1B263B"
BORDER = "#25324A"
TEXT = "#F7F9FC"
MUTED = "#8E9BB3"
ACCENT = "#7C5CFC"
ACCENT_HOVER = "#9278FF"
SUCCESS = "#35D49A"
WARNING = "#FFB454"
DANGER = "#FF647C"


class DLForgeApp(ctk.CTk):
    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("DLForge")
        icon_path = Path(__file__).resolve().parents[1] / "assets" / "dlforge.ico"
        if getattr(sys, "frozen", False):
            icon_path = Path(getattr(sys, "_MEIPASS")) / "assets" / "dlforge.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))
        self.geometry("1180x800")
        self.minsize(920, 700)
        self.configure(fg_color=BG)

        self.events: queue.Queue[dict] = queue.Queue()
        self.engine = DownloadEngine(self.events.put)
        self.last_file: Path | None = None
        self.selected_vars: dict[int, tk.BooleanVar] = {}
        self._thumbnail_image: ctk.CTkImage | None = None
        self._toast_widget: ctk.CTkFrame | None = None
        self._parsing = False
        self._parse_frame = 0
        self._running = False
        self._pulse_on = False
        self._target_progress = 0.0
        self._display_progress = 0.0
        self._progress_job: str | None = None
        self._log_lines: list[str] = []
        self._log_window: ctk.CTkToplevel | None = None
        self._log_view: ctk.CTkTextbox | None = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(80, self._drain_events)
        self.after(650, self._pulse_status)

    def _build_ui(self) -> None:
        self._build_header()
        self._build_task_card()
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=SURFACE_3,
            scrollbar_button_hover_color=ACCENT,
        )
        self.content.pack(fill="both", expand=True, padx=(28, 18), pady=(0, 12))
        self._build_link_card()
        self.workspace = ctk.CTkFrame(self.content, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True)
        self.workspace.grid_columnconfigure(0, weight=7)
        self.workspace.grid_columnconfigure(1, weight=4)
        self.left_column = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.right_column = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.right_column.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self._build_metadata_card(self.left_column)
        self._build_playlist_card(self.left_column)
        self._build_settings_card(self.right_column)
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent", height=66)
        header.pack(fill="x", padx=32, pady=(12, 10))
        header.pack_propagate(False)
        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left", fill="y")
        ctk.CTkLabel(
            brand, text="D", width=42, height=42, corner_radius=13, fg_color=ACCENT,
            text_color="white", font=("Segoe UI", 22, "bold"),
        ).pack(side="left", pady=3)
        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", padx=(13, 0), pady=3)
        ctk.CTkLabel(brand_text, text="DLForge", text_color=TEXT, font=("Segoe UI", 23, "bold")).pack(anchor="w")
        ctk.CTkLabel(
            brand_text, text="Media downloader  ·  powered by yt-dlp",
            text_color=MUTED, font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(1, 0))
        self.header_status = ctk.CTkLabel(
            header, text="  ●  READY  ", height=34, corner_radius=17,
            fg_color=SURFACE_2, text_color=SUCCESS, font=("Segoe UI", 10, "bold"),
        )
        self.header_status.pack(side="right", pady=12)

    def _card(self, parent: ctk.CTkBaseClass, **kwargs) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            parent, fg_color=SURFACE, corner_radius=18,
            border_width=1, border_color=BORDER, **kwargs,
        )

    def _build_link_card(self) -> None:
        card = self._card(self.content)
        card.pack(fill="x", pady=(0, 14))
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=20)
        heading = ctk.CTkFrame(body, fg_color="transparent")
        heading.pack(fill="x", pady=(0, 11))
        ctk.CTkLabel(heading, text="添加视频链接", text_color=TEXT, font=("Microsoft YaHei UI", 15, "bold")).pack(side="left")
        ctk.CTkLabel(heading, text="支持单视频、合集与播放列表", text_color=MUTED, font=("Microsoft YaHei UI", 10)).pack(side="right")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(
            row, textvariable=self.url_var, height=48, corner_radius=12,
            fg_color=SURFACE_2, border_color=BORDER, border_width=1,
            text_color=TEXT, placeholder_text="粘贴 YouTube、Bilibili 或其他 yt-dlp 支持的链接…",
            placeholder_text_color="#68758D", font=("Segoe UI", 12),
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _event: self._inspect_url())
        ctk.CTkButton(
            row, text="粘贴", width=76, height=48, corner_radius=12,
            fg_color=SURFACE_3, hover_color="#24314B", text_color=TEXT,
            command=self._paste_url,
        ).pack(side="left", padx=(10, 0))
        self.inspect_button = ctk.CTkButton(
            row, text="解析链接  →", width=126, height=48, corner_radius=12,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white",
            font=("Microsoft YaHei UI", 11, "bold"), command=self._inspect_url,
        )
        self.inspect_button.pack(side="left", padx=(10, 0))

    def _build_metadata_card(self, parent: ctk.CTkBaseClass) -> None:
        self.meta_card = self._card(parent)
        self.meta_card.pack(fill="x", pady=(0, 14))
        body = ctk.CTkFrame(self.meta_card, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=18)
        self.thumbnail_label = ctk.CTkLabel(
            body, text="▶", width=220, height=124, corner_radius=14,
            fg_color="#0A0F1C", text_color="#53617A", font=("Segoe UI Symbol", 34),
        )
        self.thumbnail_label.pack(side="left")
        info = ctk.CTkFrame(body, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(20, 8), pady=5)
        self.meta_badge = ctk.CTkLabel(
            info, text="  等待解析  ", height=25, corner_radius=8,
            fg_color=SURFACE_3, text_color=MUTED, font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.meta_badge.pack(anchor="w")
        self.meta_title = tk.StringVar(value="粘贴链接，开始锻造你的媒体文件")
        self.meta_detail = tk.StringVar(value="解析后将在这里显示标题、作者、时长和分集信息")
        ctk.CTkLabel(
            info, textvariable=self.meta_title, text_color=TEXT,
            font=("Microsoft YaHei UI", 17, "bold"), anchor="w",
            justify="left", wraplength=430,
        ).pack(fill="x", anchor="w", pady=(11, 5))
        ctk.CTkLabel(
            info, textvariable=self.meta_detail, text_color=MUTED,
            font=("Microsoft YaHei UI", 10), anchor="w",
        ).pack(fill="x", anchor="w")

    def _build_playlist_card(self, parent: ctk.CTkBaseClass) -> None:
        self.playlist_card = self._card(parent)
        header = ctk.CTkFrame(self.playlist_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(17, 10))
        ctk.CTkLabel(header, text="视频 / 分集", text_color=TEXT, font=("Microsoft YaHei UI", 14, "bold")).pack(side="left")
        self.selection_label = ctk.CTkLabel(header, text="0 项", text_color=MUTED, font=("Microsoft YaHei UI", 10))
        self.selection_label.pack(side="left", padx=(10, 0))
        ctk.CTkButton(
            header, text="清除", width=58, height=28, corner_radius=9,
            fg_color="transparent", hover_color=SURFACE_3, border_width=1,
            border_color=BORDER, command=lambda: self._set_all_entries(False),
        ).pack(side="right")
        ctk.CTkButton(
            header, text="全选", width=58, height=28, corner_radius=9,
            fg_color=SURFACE_3, hover_color="#24314B",
            command=lambda: self._set_all_entries(True),
        ).pack(side="right", padx=(0, 8))
        self.playlist_scroll = ctk.CTkScrollableFrame(
            self.playlist_card, height=235, fg_color="#0B111E", corner_radius=12,
            scrollbar_button_color=SURFACE_3, scrollbar_button_hover_color=ACCENT,
        )
        self.playlist_scroll.pack(fill="x", padx=16, pady=(0, 16))
        self.playlist_card.pack_forget()

    def _build_settings_card(self, parent: ctk.CTkBaseClass) -> None:
        self.settings_card = self._card(parent)
        self.settings_card.pack(fill="x", pady=(0, 14))
        body = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=18)
        ctk.CTkLabel(body, text="下载设置", text_color=TEXT, font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", pady=(0, 16))
        quality = ctk.CTkFrame(body, fg_color="transparent")
        quality.pack(fill="x")
        ctk.CTkLabel(quality, text="输出质量", text_color=TEXT, font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        self.preset_var = tk.StringVar(value="最佳 MP4")
        self.preset = ctk.CTkSegmentedButton(
            quality, values=["最佳 MP4", "1080p", "720p", "MP3"],
            variable=self.preset_var, height=38, corner_radius=10,
            fg_color=SURFACE_2, selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER, unselected_color=SURFACE_2,
            unselected_hover_color=SURFACE_3, font=("Segoe UI", 10, "bold"),
        )
        self.preset.pack(fill="x")

        scope = ctk.CTkFrame(body, fg_color="transparent")
        scope.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(scope, text="下载范围", text_color=TEXT, font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        ctk.CTkLabel(
            scope,
            text="当前：只下载链接对应视频；已选：下载勾选分集；全部：下载完整列表",
            text_color=MUTED,
            font=("Microsoft YaHei UI", 9),
            justify="left",
            wraplength=340,
        ).pack(anchor="w", pady=(4, 8))
        self.scope_var = tk.StringVar(value="仅当前")
        self.scope_control = ctk.CTkSegmentedButton(
            scope,
            values=["仅当前", "已选分集", "全部列表"],
            variable=self.scope_var,
            command=self._scope_changed,
            height=38,
            corner_radius=10,
            fg_color=SURFACE_2,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=SURFACE_2,
            unselected_hover_color=SURFACE_3,
            font=("Microsoft YaHei UI", 9, "bold"),
            state="disabled",
        )
        self.scope_control.pack(fill="x")

        destination = ctk.CTkFrame(body, fg_color="transparent")
        destination.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(destination, text="保存位置", text_color=TEXT, font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        destination_row = ctk.CTkFrame(destination, fg_color="transparent")
        destination_row.pack(fill="x")
        self.output_var = tk.StringVar(value=str(Path.home() / "Downloads" / "DLForge"))
        ctk.CTkEntry(
            destination_row, textvariable=self.output_var, height=38, corner_radius=10,
            fg_color=SURFACE_2, border_color=BORDER, text_color=TEXT,
        ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            destination_row, text="浏览…", width=74, height=38, corner_radius=10,
            fg_color=SURFACE_3, hover_color="#24314B", command=self._choose_output,
        ).pack(side="left", padx=(8, 0))
        options = ctk.CTkFrame(body, fg_color="transparent")
        options.pack(fill="x", pady=(18, 0))
        self.subtitles_var = tk.BooleanVar()
        ctk.CTkSwitch(
            options, text="下载中英文字幕", variable=self.subtitles_var,
            progress_color=ACCENT, button_hover_color=ACCENT_HOVER,
            text_color=MUTED, font=("Microsoft YaHei UI", 10),
        ).pack(side="left")

    def _build_task_card(self) -> None:
        self.task_card = self._card(self)
        self.task_card.pack(side="bottom", fill="x", padx=28, pady=(0, 18))
        body = ctk.CTkFrame(self.task_card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=14)
        self.progress = ctk.CTkProgressBar(
            body, height=7, corner_radius=4, fg_color=SURFACE_3, progress_color=ACCENT,
        )
        self.progress.set(0)
        self.progress.pack(fill="x", pady=(0, 12))
        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.pack(fill="x")
        status_group = ctk.CTkFrame(actions, fg_color="transparent")
        status_group.pack(side="left", fill="x", expand=True)
        self.status_dot = ctk.CTkLabel(status_group, text="●", width=16, text_color="#53617A", font=("Segoe UI", 12))
        self.status_dot.pack(side="left")
        self.status_var = tk.StringVar(value="准备就绪")
        ctk.CTkLabel(status_group, textvariable=self.status_var, text_color=TEXT, font=("Microsoft YaHei UI", 11, "bold")).pack(side="left", padx=(4, 0))
        self.percent_label = ctk.CTkLabel(status_group, text="0%", text_color=ACCENT_HOVER, font=("Segoe UI", 14, "bold"))
        self.percent_label.pack(side="left", padx=(14, 0))
        self.download_button = ctk.CTkButton(
            actions, text="开始下载  ↓", width=158, height=44, corner_radius=12,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            font=("Microsoft YaHei UI", 11, "bold"), command=self._start_download,
        )
        self.download_button.pack(side="right")
        self.cancel_button = ctk.CTkButton(
            actions, text="取消任务", width=100, height=44, corner_radius=12,
            fg_color="transparent", hover_color="#3A2130", border_width=1,
            border_color="#563044", text_color=DANGER, state="disabled",
            command=self._cancel_download,
        )
        self.cancel_button.pack(side="right", padx=(8, 10))
        ctk.CTkButton(
            actions, text="打开文件夹", width=110, height=44, corner_radius=12,
            fg_color=SURFACE_3, hover_color="#24314B", command=self._open_output,
        ).pack(side="right", padx=(0, 8))
        self.log_toggle = ctk.CTkButton(
            actions, text="任务日志", width=92, height=44, corner_radius=12,
            fg_color="transparent", hover_color=SURFACE_3, text_color=MUTED,
            command=self._toggle_log,
        )
        self.log_toggle.pack(side="right", padx=(0, 8))

    def _paste_url(self) -> None:
        try:
            value = self.clipboard_get().strip()
        except tk.TclError:
            self._show_toast("剪贴板里没有可用文本", "warning")
            return
        self.url_var.set(value)
        self.url_entry.focus_set()
        if self._valid_url():
            self.after(120, self._inspect_url)

    def _valid_url(self) -> str | None:
        value = self.url_var.get().strip()
        parsed = urlparse(value)
        return value if parsed.scheme in {"http", "https"} and parsed.netloc else None

    def _inspect_url(self) -> None:
        url = self._valid_url()
        if not url:
            self._show_toast("请输入以 http:// 或 https:// 开头的有效链接", "error")
            self._shake(self.url_entry)
            return
        self.inspect_button.configure(state="disabled")
        self.engine.inspect(url)

    def _choose_output(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.output_var.get())
        if chosen:
            self.output_var.set(chosen)

    def _start_download(self) -> None:
        url = self._valid_url()
        if not url:
            self._show_toast("请先输入并解析有效链接", "error")
            self._shake(self.url_entry)
            return
        selected_items = tuple(sorted(index for index, var in self.selected_vars.items() if var.get()))
        scope = self.scope_var.get()
        if scope == "已选分集" and not selected_items:
            self._show_toast("请先在左侧勾选要下载的分集", "warning")
            return
        playlist_mode = scope in {"已选分集", "全部列表"}
        requested_items = selected_items if scope == "已选分集" else ()
        preset_map = {"最佳 MP4": "best", "1080p": "1080", "720p": "720", "MP3": "audio"}
        options = DownloadOptions(
            url=url, output_dir=Path(self.output_var.get()).expanduser(),
            preset=preset_map[self.preset_var.get()], playlist=playlist_mode,
            subtitles=self.subtitles_var.get(), playlist_items=requested_items,
        )
        self._target_progress = 0
        self._display_progress = 0
        self.progress.set(0)
        self.percent_label.configure(text="0%")
        self._set_running(True)
        self.engine.download(options)

    def _cancel_download(self) -> None:
        self.status_var.set("正在停止下载与媒体处理…")
        self.cancel_button.configure(state="disabled", text="停止中…")
        self.engine.cancel()

    def _set_running(self, running: bool) -> None:
        self._running = running
        self.download_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled", text="取消任务")
        self.header_status.configure(
            text="  ●  WORKING  " if running else "  ●  READY  ",
            text_color=ACCENT_HOVER if running else SUCCESS,
        )

    def _drain_events(self) -> None:
        try:
            while True:
                self._handle_event(self.events.get_nowait())
        except queue.Empty:
            pass
        self.after(80, self._drain_events)

    def _handle_event(self, event: dict) -> None:
        kind = event["type"]
        if kind == "inspect_started":
            self._parsing = True
            self._parse_frame = 0
            self.meta_badge.configure(text="  正在解析  ", text_color=ACCENT_HOVER)
            self.meta_title.set("正在读取视频信息")
            self.meta_detail.set("正在识别视频、作者、时长与列表结构…")
            self._animate_parsing()
        elif kind == "metadata":
            self._parsing = False
            self.inspect_button.configure(state="normal", text="重新解析  ↻")
            entries = event.get("entries") or []
            self.meta_badge.configure(
                text=f"  {len(entries)} 个项目  " if entries else "  单个视频  ",
                text_color=SUCCESS,
            )
            self.meta_title.set(event["title"])
            count_text = f"  ·  {len(entries)} 个项目" if entries else ""
            self.meta_detail.set(f'{event["uploader"]}  ·  {self._format_duration(event.get("duration"))}{count_text}')
            self._show_entries(entries)
            if event.get("thumbnail"):
                self._load_thumbnail_async(event["thumbnail"])
            self._show_toast("视频信息解析完成", "success")
        elif kind == "thumbnail_bytes":
            self._apply_thumbnail(event["data"])
        elif kind == "started":
            self.status_var.set("正在连接媒体源…")
            self._append_log("任务已开始")
        elif kind == "progress":
            self._set_progress_target(event["percent"])
            speed = event["speed"] or "--"
            eta = event["eta"] or "--"
            self.status_var.set(f"正在下载  ·  {speed}  ·  剩余 {eta}")
        elif kind == "file":
            self.last_file = Path(event["path"])
            self._append_log(f'已保存：{event["path"]}')
        elif kind == "log":
            self._append_log(event["message"])
        elif kind == "finished":
            self._set_progress_target(100)
            self.status_var.set("下载完成，文件已经锻造完毕")
            self._set_running(False)
            self.status_dot.configure(text_color=SUCCESS)
            self._show_toast("下载完成", "success")
        elif kind == "cancelling":
            self.status_var.set("正在停止下载与媒体处理…")
            self.cancel_button.configure(state="disabled", text="停止中…")
        elif kind == "cancelled":
            self.status_var.set("任务已取消，后台进程均已停止")
            self._append_log("任务已由用户取消")
            self._set_running(False)
            self.status_dot.configure(text_color=WARNING)
            self._show_toast("下载任务已取消", "warning")
        elif kind == "inspect_error":
            self._parsing = False
            self.inspect_button.configure(state="normal", text="重试解析  ↻")
            self.meta_badge.configure(text="  解析失败  ", text_color=DANGER)
            self.meta_title.set("未能解析这个链接")
            self.meta_detail.set(event["message"])
            self._show_entries([])
            self._show_toast(event["message"], "error")
        elif kind == "error":
            self.status_var.set("任务失败，请展开日志查看详情")
            self._append_log(event["message"])
            self._set_running(False)
            self.status_dot.configure(text_color=DANGER)
            self._show_toast(event["message"], "error")

    def _show_entries(self, entries: list[dict]) -> None:
        for child in self.playlist_scroll.winfo_children():
            child.destroy()
        self.selected_vars.clear()
        if not entries:
            self.playlist_card.pack_forget()
            self.scope_var.set("仅当前")
            self.scope_control.configure(state="disabled")
            return
        self.playlist_card.pack(fill="x", pady=(0, 14))
        self.scope_control.configure(state="normal")
        self.scope_var.set("仅当前")
        self.selection_label.configure(text=f"{len(entries)} 项 · 尚未选择")
        for position, entry in enumerate(entries):
            index = int(entry.get("index") or position + 1)
            variable = tk.BooleanVar(value=False)
            self.selected_vars[index] = variable
            row = ctk.CTkFrame(self.playlist_scroll, fg_color="transparent", corner_radius=10, height=42)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            ctk.CTkCheckBox(
                row, text="", width=24, variable=variable, fg_color=ACCENT,
                hover_color=ACCENT_HOVER, border_color="#52617A",
                command=self._selection_changed,
            ).pack(side="left", padx=(10, 4))
            ctk.CTkLabel(
                row, text=f"{index:02d}", width=38, height=25, corner_radius=8,
                fg_color=SURFACE_3, text_color=ACCENT_HOVER,
                font=("Cascadia Mono", 9, "bold"),
            ).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(
                row, text=entry.get("title") or f"第 {index} 项",
                text_color=TEXT, font=("Microsoft YaHei UI", 10), anchor="w",
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                row, text=self._format_duration(entry.get("duration")),
                text_color=MUTED, font=("Cascadia Mono", 9),
            ).pack(side="right", padx=12)
            self.after(position * 12, lambda widget=row: widget.configure(fg_color=SURFACE_2))

    def _selection_changed(self) -> None:
        selected = sum(1 for var in self.selected_vars.values() if var.get())
        total = len(self.selected_vars)
        self.selection_label.configure(text=f"{total} 项 · 已选择 {selected}")
        if selected:
            self.scope_var.set("已选分集")
        elif self.scope_var.get() == "已选分集":
            self.scope_var.set("仅当前")

    def _set_all_entries(self, selected: bool) -> None:
        for variable in self.selected_vars.values():
            variable.set(selected)
        self._selection_changed()
        self.scope_var.set("全部列表" if selected else "仅当前")
        if selected:
            self.selection_label.configure(text=f"{len(self.selected_vars)} 项 · 将下载全部")

    def _scope_changed(self, choice: str) -> None:
        if choice == "已选分集" and not any(var.get() for var in self.selected_vars.values()):
            self._show_toast("先在左侧列表勾选一个或多个分集", "warning")
            self.scope_var.set("仅当前")
        elif choice == "全部列表":
            self.selection_label.configure(text=f"{len(self.selected_vars)} 项 · 将下载全部")

    def _load_thumbnail_async(self, url: str) -> None:
        def worker() -> None:
            try:
                request = urllib.request.Request(
                    url.replace("http://", "https://", 1),
                    headers={"User-Agent": "Mozilla/5.0 DLForge/0.3"},
                )
                with urllib.request.urlopen(request, timeout=12) as response:
                    self.events.put({"type": "thumbnail_bytes", "data": response.read(8 * 1024 * 1024)})
            except OSError:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _apply_thumbnail(self, data: bytes) -> None:
        try:
            image = Image.open(io.BytesIO(data)).convert("RGB")
            image = ImageOps.fit(image, (440, 248), method=Image.Resampling.LANCZOS)
            self._thumbnail_image = ctk.CTkImage(light_image=image, dark_image=image, size=(220, 124))
            self.thumbnail_label.configure(image=self._thumbnail_image, text="")
        except (OSError, ValueError):
            pass

    def _animate_parsing(self) -> None:
        if not self._parsing:
            return
        dots = ("·", "··", "···")
        self.inspect_button.configure(text=f"解析中 {dots[self._parse_frame % 3]}")
        self.meta_badge.configure(fg_color="#211D3B" if self._parse_frame % 2 else SURFACE_3)
        self._parse_frame += 1
        self.after(320, self._animate_parsing)

    def _set_progress_target(self, percent: float) -> None:
        self._target_progress = max(0.0, min(100.0, percent))
        if self._progress_job is None:
            self._animate_progress()

    def _animate_progress(self) -> None:
        delta = self._target_progress - self._display_progress
        if abs(delta) < 0.08:
            self._display_progress = self._target_progress
            self._progress_job = None
        else:
            self._display_progress += delta * 0.16
            self._progress_job = self.after(16, self._animate_progress)
        self.progress.set(self._display_progress / 100)
        self.percent_label.configure(text=f"{self._display_progress:.0f}%")

    def _pulse_status(self) -> None:
        self._pulse_on = not self._pulse_on
        if self._running:
            self.status_dot.configure(text_color=ACCENT_HOVER if self._pulse_on else "#51419D")
        elif self.status_var.get() == "准备就绪":
            self.status_dot.configure(text_color="#53617A")
        self.after(650, self._pulse_status)

    def _toggle_log(self) -> None:
        if self._log_window is not None and self._log_window.winfo_exists():
            self._log_window.focus_force()
            return
        window = ctk.CTkToplevel(self)
        window.title("DLForge · 任务日志")
        window.geometry("780x430")
        window.minsize(600, 320)
        window.configure(fg_color=BG)
        window.transient(self)
        ctk.CTkLabel(
            window,
            text="任务日志",
            text_color=TEXT,
            font=("Microsoft YaHei UI", 18, "bold"),
        ).pack(anchor="w", padx=22, pady=(20, 10))
        view = ctk.CTkTextbox(
            window,
            corner_radius=12,
            fg_color="#090E19",
            border_width=1,
            border_color=BORDER,
            text_color="#9CACCA",
            font=("Cascadia Mono", 10),
        )
        view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        if self._log_lines:
            view.insert("end", "\n".join(self._log_lines) + "\n")
            view.see("end")
        view.configure(state="disabled")
        self._log_window = window
        self._log_view = view
        window.protocol("WM_DELETE_WINDOW", self._close_log)

    def _close_log(self) -> None:
        if self._log_window is not None and self._log_window.winfo_exists():
            self._log_window.destroy()
        self._log_window = None
        self._log_view = None

    def _append_log(self, message: str) -> None:
        self._log_lines.append(message)
        if len(self._log_lines) > 500:
            self._log_lines = self._log_lines[-500:]
        if self._log_view is not None and self._log_view.winfo_exists():
            self._log_view.configure(state="normal")
            self._log_view.insert("end", message + "\n")
            self._log_view.see("end")
            self._log_view.configure(state="disabled")

    def _on_mousewheel(self, event: tk.Event) -> str:
        delta = int(getattr(event, "delta", 0))
        if delta == 0:
            return "break"
        direction = -1 if delta > 0 else 1
        steps = max(1, min(6, round(abs(delta) / 120)))
        widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        playlist_canvas = self.playlist_scroll._parent_canvas
        if widget is not None and self._is_descendant(widget, self.playlist_scroll):
            top, bottom = playlist_canvas.yview()
            at_boundary = (direction < 0 and top <= 0.001) or (direction > 0 and bottom >= 0.999)
            if not at_boundary:
                playlist_canvas.yview_scroll(direction * steps * 6, "units")
                return "break"
        self.content._parent_canvas.yview_scroll(direction * steps * 7, "units")
        return "break"

    @staticmethod
    def _is_descendant(widget: tk.Misc, parent: tk.Misc) -> bool:
        current: tk.Misc | None = widget
        while current is not None:
            if current == parent:
                return True
            current = getattr(current, "master", None)
        return False

    def _show_toast(self, message: str, kind: str = "success") -> None:
        if self._toast_widget is not None and self._toast_widget.winfo_exists():
            self._toast_widget.destroy()
        colors = {"success": SUCCESS, "warning": WARNING, "error": DANGER}
        icons = {"success": "✓", "warning": "!", "error": "×"}
        color = colors.get(kind, ACCENT)
        toast = ctk.CTkFrame(
            self, width=360, height=58, corner_radius=14,
            fg_color=SURFACE_2, border_width=1, border_color=color,
        )
        toast.place(relx=1, x=-28, y=12, anchor="ne")
        toast.pack_propagate(False)
        ctk.CTkLabel(
            toast, text=icons.get(kind, "i"), width=30,
            text_color=color, font=("Segoe UI", 18, "bold"),
        ).pack(side="left", padx=(12, 2))
        ctk.CTkLabel(
            toast, text=message, text_color=TEXT, font=("Microsoft YaHei UI", 10),
            wraplength=285, justify="left",
        ).pack(side="left", fill="both", expand=True, padx=(4, 14))
        self._toast_widget = toast

        def slide_in(y: int = 12) -> None:
            if not toast.winfo_exists():
                return
            target = 84
            next_y = min(target, y + max(5, (target - y) // 3))
            toast.place_configure(y=next_y)
            if next_y < target:
                self.after(16, lambda: slide_in(next_y))
            else:
                self.after(3400, slide_out)

        def slide_out(x: int = -28) -> None:
            if not toast.winfo_exists():
                return
            next_x = x + 28
            toast.place_configure(x=next_x)
            if next_x < 390:
                self.after(16, lambda: slide_out(next_x))
            else:
                toast.destroy()
        slide_in()

    def _shake(self, widget: ctk.CTkBaseClass) -> None:
        original = widget.cget("border_color")
        sequence = (DANGER, BORDER, DANGER, BORDER)
        for index, color in enumerate(sequence):
            self.after(index * 90, lambda value=color: widget.configure(border_color=value))
        self.after(len(sequence) * 90, lambda: widget.configure(border_color=original))

    def _open_output(self) -> None:
        destination = Path(self.output_var.get()).expanduser()
        destination.mkdir(parents=True, exist_ok=True)
        os.startfile(destination)

    def _on_close(self) -> None:
        self.engine.cancel()
        self.destroy()

    @staticmethod
    def _format_duration(seconds: int | float | None) -> str:
        if not seconds:
            return "--:--"
        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def main() -> None:
    DLForgeApp().mainloop()
