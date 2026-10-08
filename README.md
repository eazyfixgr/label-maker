# Label Maker (Δημιουργία Ταμπέλας)

A simple desktop app to create labels and signs (ταμπέλες) with custom text, font, colour and templates.

> **Download:** grab the latest `LabelMaker.exe` from the [Releases](https://github.com/eazyfixgr/label-maker/releases) page. No installation required.

## Features

- Create labels/signs from text
- Choose font, size and colour
- Save and reuse templates (`config.json`)
- Export to image
- Simple tkinter interface (Python + Pillow)

## Run from source

```bash
python -m pip install pillow
python app.py
```

## Build a standalone EXE

```bash
python -m pip install pyinstaller pillow
python -m PyInstaller --onefile --windowed --name LabelMaker app.py
```

The executable is created in `dist/LabelMaker.exe`.

## License

Released under the [MIT License](LICENSE).

---

# Δημιουργία Ταμπέλας (Ελληνικά)

Εφαρμογή για τη δημιουργία ταμπελών/πινακίδων με κείμενο, γραμματοσειρά, χρώμα και πρότυπα.

> **Λήψη:** κατεβάστε το `LabelMaker.exe` από τη σελίδα [Releases](https://github.com/eazyfixgr/label-maker/releases). Δεν απαιτείται εγκατάσταση.
