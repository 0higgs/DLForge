import subprocess
import sys


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from dlforge.engine import tool_path

        components = (("yt-dlp", "--version"), ("ffmpeg", "-version"), ("ffprobe", "-version"))
        for component, version_arg in components:
            result = subprocess.run(
                [tool_path(component), version_arg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            if result.returncode != 0:
                raise SystemExit(result.returncode or 1)
        raise SystemExit(0)
    if "--ui-self-test" in sys.argv:
        import traceback
        from pathlib import Path

        from dlforge.app import DLForgeApp

        test_app = DLForgeApp()
        test_result = [0]

        def exercise_ui() -> None:
            try:
                test_app._handle_event(
                    {
                        "type": "metadata",
                        "title": "DLForge 界面交互测试",
                        "uploader": "Self Test",
                        "duration": 3661,
                        "entries": [
                            {"index": 1, "title": "第一段视频", "duration": 61},
                            {"index": 2, "title": "第二段视频", "duration": 125},
                            {"index": 3, "title": "第三段视频", "duration": 180},
                        ],
                    }
                )
                test_app._set_all_entries(True)
                assert test_app.scope_var.get() == "全部列表"
                test_app._set_all_entries(False)
                test_app.selected_vars[2].set(True)
                test_app._selection_changed()
                assert test_app.scope_var.get() == "已选分集"
                assert test_app.task_card.master == test_app
                assert test_app.task_card.pack_info().get("side") == "bottom"
                test_app._on_mousewheel(type("WheelEvent", (), {"delta": -120})())
                test_app._set_running(True)
                test_app._handle_event({"type": "progress", "percent": 67, "speed": "8.2MiB/s", "eta": "00:12"})
                test_app._toggle_log()
                test_app._append_log("UI self-test")
                test_app.after(900, lambda: test_app._handle_event({"type": "cancelled"}))
                test_app.after(1700, test_app.destroy)
            except Exception:
                test_result[0] = 1
                Path("ui-self-test-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
                test_app.destroy()

        test_app.after(150, exercise_ui)
        test_app.after(5000, test_app.destroy)
        test_app.mainloop()
        raise SystemExit(test_result[0])
    from dlforge.app import main

    main()
