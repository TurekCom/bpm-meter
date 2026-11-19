import logging
from pathlib import Path
import sys
from threading import Thread

import wx

from win_file_dialog import choose_audio_file


class Meter(wx.Frame):
    def __init__(self):
        super().__init__(None, title="BPM Meter")
        self.busy = False
        panel = wx.Panel(self)
        self.open_button = wx.Button(panel, label="&Otwórz plik audio…")
        self.open_button.Bind(wx.EVT_BUTTON, self.open_file)
        self.file_label = wx.StaticText(panel, label="Nie wybrano pliku.", style=wx.ST_ELLIPSIZE_MIDDLE)
        label = wx.StaticText(panel, label="&Wynik pomiaru")
        self.result = wx.TextCtrl(panel, value="Gotowy do pomiaru.", style=wx.TE_READONLY,
                                  name="Wynik pomiaru")
        self.result.SetMinSize(self.FromDIP((420, -1)))

        layout = wx.BoxSizer(wx.VERTICAL)
        margin = self.FromDIP(16)
        for control in (self.open_button, self.file_label, label, self.result):
            layout.Add(control, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, margin)
        layout.AddSpacer(margin)
        panel.SetSizer(layout)
        frame_layout = wx.BoxSizer(wx.VERTICAL)
        frame_layout.Add(panel, 1, wx.EXPAND)
        self.SetSizerAndFit(frame_layout)
        self.SetMinSize(self.GetSize())

        extra_id = wx.ID_HIGHEST + 1
        self.Bind(wx.EVT_MENU, self.open_file, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.show_cadence, id=extra_id)
        self.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord("O"), wx.ID_OPEN),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("B"), extra_id),
        ]))
        self.open_button.SetFocus()

    def open_file(self, _event):
        if self.busy:
            return
        formats = "*.wav;*.mp3;*.flac;*.ogg;*.opus;*.m4a;*.aac;*.aif;*.aiff;*.wma;*.m4b"
        try:
            path = choose_audio_file(self.GetHandle(), formats)
        except OSError as error:
            wx.MessageBox(str(error), "BPM Meter", wx.OK | wx.ICON_ERROR, self)
            return
        if path is not None:
            wx.CallAfter(self.start_analysis, path)

    def start_analysis(self, path):
        self.busy = True
        self.file_label.SetLabelText(path.name)
        self.result.SetValue("Trwa pomiar tempa…")
        self.open_button.SetFocus()
        Thread(target=self.analyze, args=(path,), daemon=True).start()

    def analyze(self, path):
        try:
            from tempo import AudioError, measure_bpm

            try:
                bpm = measure_bpm(path)
                if bpm is None:
                    message = "Nie wykryto wyraźnego, powtarzalnego tempa."
                else:
                    number = f"{bpm:.2f}".replace(".", ",")
                    message = f"Tempo: {number} BPM"
            except AudioError as error:
                message = str(error)
        except Exception:
            logging.exception("Błąd analizy audio")
            message = "Wystąpił błąd podczas pomiaru tempa."
        wx.CallAfter(self.finish_analysis, message)

    def finish_analysis(self, message):
        if self.IsBeingDeleted():
            return
        self.busy = False
        self.result.SetValue(message)
        if self.IsActive():
            self.result.SetFocus()
            self.result.SelectAll()

    def show_cadence(self, _event):
        if not self.busy:
            wx.MessageBox("120 BPM. Pół sekundy między uderzeniami.", "Metronom", wx.OK, self)


if __name__ == "__main__":
    app = wx.App()
    frame = Meter()
    frame.Centre()
    frame.Show()
    if len(sys.argv) > 1:
        wx.CallAfter(frame.start_analysis, Path(sys.argv[1]))
    app.MainLoop()
