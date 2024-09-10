import os
import shutil
import threading
from PyQt5.QtWidgets import QFileDialog, QApplication
from pathlib import Path
from data_processor import convert_tx0_to_txt, filter_temperature_data_by_date, calibrate_resistivity
import tempfile
import subprocess
import platform

# Global variables to store file paths
global_tx0_input_folder = None  # Global variable to store the path of the tx0 folder
global_selected_temperature_file = None  # Global variable to store the selected temperature file path


def setup_ui_logic(ui, MainWindow):
    """
    Bind UI events and logic.

    Parameters:
        ui: Instance of Ui_MainWindow.
        MainWindow: Instance of QMainWindow.
    """
    # Set up the "Browser" button click event for Tx0 files
    ui.pushButtonBrowserFiles.clicked.connect(lambda: open_file_browser(ui.textEditProcessedTxtPreview, tx0=True))

    # Set up the "Browser" button click event for Temperature files
    ui.pushButtonBrowserTempFiles.clicked.connect(lambda: open_file_browser(ui.textEditProcessedTempPreview, tx0=False))

    # Set up the "Start" button click event (for data processing)
    ui.pushButtonStartDataProcessing.clicked.connect(lambda: start_data_processing_thread(ui))

    # Set up the "Exit" menu exit event
    ui.actionExit.triggered.connect(lambda: exit_application(MainWindow))

    # Set up "OpenTx0Dir" button click event
    ui.pushButtonOpenTx0Dir.clicked.connect(lambda: open_directory(global_tx0_input_folder))

    # Set up "OpenTempDir" button click event
    ui.pushButtonTempDir.clicked.connect(lambda: open_directory(global_selected_temperature_file))


def open_file_browser(text_edit, tx0=True):
    """
    Open a file selection dialog and copy selected files to the specified directory.

    Parameters:
        text_edit: QTextEdit component to display selected file paths.
        tx0: Boolean to determine if selecting tx0 files or temperature file.
    """
    global global_tx0_input_folder, global_selected_temperature_file

    options = QFileDialog.Options()

    if tx0:
        files, _ = QFileDialog.getOpenFileNames(None, "Select Tx0 Files", "", "Tx0 Files (*.tx0);;All Files (*)",
                                                options=options)
        if files:
            global_tx0_input_folder = tempfile.mkdtemp()  # Temporary directory to store Tx0 files
            for file_path in files:
                if os.path.isfile(file_path) and file_path.endswith('.tx0'):
                    shutil.copy(file_path, global_tx0_input_folder)

            # Display Tx0 file paths in the text edit
            text_edit.clear()
            for file in files:
                text_edit.append(file)
    else:
        file, _ = QFileDialog.getOpenFileName(None, "Select Temperature File", "", "Text Files (*.txt);;All Files (*)",
                                              options=options)
        if file:
            global_selected_temperature_file = file

            # Display temperature file path in the text edit
            text_edit.clear()
            text_edit.append(file)


def start_data_processing_thread(ui):
    """
    Start a thread for data processing.

    Parameters:
        ui: Instance of Ui_MainWindow.
    """
    processing_thread = threading.Thread(target=start_data_processing, args=(ui,))
    processing_thread.start()


def start_data_processing(ui):
    """
    Logic to execute when the "Start" button is clicked.

    Parameters:
        ui: Instance of Ui_MainWindow.
    """
    global global_tx0_input_folder
    global global_selected_temperature_file

    # Get the converter option
    converter_choice = "1" if ui.XZcheckBox.isChecked() else "2"

    # If the tx0 folder is not set, prompt the user to select it
    if not global_tx0_input_folder:
        print("Please use the 'Browser' button to select tx0 files first.")
        return

    # If the temperature file is not set, prompt the user to select it
    if not global_selected_temperature_file:
        print("Please use the 'Browser' button to select the temperature file first.")
        return

    # Set output directories
    txt_output_folder = Path(tempfile.mkdtemp())
    filtered_temp_output = Path(tempfile.mkdtemp(), 'Newtem.txt')
    corrected_output_folder_detailed = Path(os.getcwd(),
                                            'outputs/corrected_resistivity_detailed')  # Save in project folder
    corrected_output_folder_simplified = Path(os.getcwd(),
                                              'outputs/corrected_resistivity_simplified')  # Save in project folder

    # Step 1: Convert tx0 to txt
    convert_tx0_to_txt(global_tx0_input_folder, txt_output_folder, converter_choice)
    print("Conversion from tx0 to txt completed.")

    # Step 2: Filter temperature data by date
    filter_temperature_data_by_date(txt_output_folder, global_selected_temperature_file, filtered_temp_output)
    print("Temperature data filtering completed.")

    # Step 3: Calibrate resistivity
    calibrate_resistivity(txt_output_folder, corrected_output_folder_detailed, corrected_output_folder_simplified,
                          filtered_temp_output)
    print("Resistivity calibration completed.")

    print("Data processing completed.")




def exit_application(MainWindow):
    """
    Exit the application.

    Parameters:
        MainWindow: Instance of QMainWindow.
    """
    QApplication.quit()




def open_directory(directory):
    """
    Open the specified directory in the system's file explorer.

    Parameters:
        directory: Path to the directory to open.
    """
    if directory:
        if platform.system() == "Windows":
            os.startfile(directory)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", directory])
        else:
            subprocess.Popen(["xdg-open", directory])
    else:
        print("Directory path is empty. Please select a valid directory.")