from ctypes import POINTER, Structure, byref, create_unicode_buffer, windll
from ctypes import wintypes as win
from pathlib import Path


class OpenFileName(Structure):
    _fields_ = [
        ("size", win.DWORD),
        ("owner", win.HWND),
        ("instance", win.HINSTANCE),
        ("filters", win.LPCWSTR),
        ("custom_filter", win.LPWSTR),
        ("max_custom_filter", win.DWORD),
        ("filter_index", win.DWORD),
        ("filename", win.LPWSTR),
        ("max_filename", win.DWORD),
        ("file_title", win.LPWSTR),
        ("max_file_title", win.DWORD),
        ("initial_dir", win.LPCWSTR),
        ("title", win.LPCWSTR),
        ("flags", win.DWORD),
        ("file_offset", win.WORD),
        ("extension_offset", win.WORD),
        ("default_extension", win.LPCWSTR),
        ("custom_data", win.LPARAM),
        ("hook", win.LPVOID),
        ("template_name", win.LPCWSTR),
        ("reserved", win.LPVOID),
        ("reserved_flags", win.DWORD),
        ("extended_flags", win.DWORD),
    ]


def choose_audio_file(owner: int, extensions: str) -> Path | None:
    from ctypes import cast, sizeof

    filename = create_unicode_buffer(32_768)
    filters = f"Pliki audio\0{extensions}\0Wszystkie pliki\0*.*\0\0"
    dialog = OpenFileName()
    dialog.size = sizeof(dialog)
    dialog.owner = owner
    dialog.filters = filters
    dialog.filter_index = 1
    dialog.filename = cast(filename, win.LPWSTR)
    dialog.max_filename = len(filename)
    dialog.title = "Wybierz plik audio"
    explorer, file_must_exist, no_change_dir = 0x80000, 0x1000, 0x8
    dialog.flags = explorer | file_must_exist | no_change_dir

    open_file = windll.comdlg32.GetOpenFileNameW
    open_file.argtypes = [POINTER(OpenFileName)]
    open_file.restype = win.BOOL
    if open_file(byref(dialog)):
        return Path(filename.value)
    error = windll.comdlg32.CommDlgExtendedError()
    if error:
        raise OSError(f"Błąd okna wyboru pliku ({error}).")
    return None
