from avalon.libs import AvalonMapViewer, check_tesseract

def main():
    check_tesseract()
    app = AvalonMapViewer()
    app.mainloop()

if __name__ == "__main__":
    main()