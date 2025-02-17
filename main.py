import base64
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QTableWidgetItem, QHeaderView
from PyQt5 import uic, QtWidgets, QtGui
import secrets
import string
import os.path
import hashlib
from PyQt5.QtCore import pyqtSignal
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import ast

masterPassword = ''
masterPasswordHashHex = ''
LOGGED_IN = False
fernetKey = Fernet(Fernet.generate_key())
storedData = list()
encryptedData = fernetKey.encrypt('start'.encode('utf-8'))


def length_isvalid(length):
    if length.isnumeric():
        if int(length) > 0:
            return True
    return False


def checkbox_isvalid(letters, digits, special_characters):
    if not letters:
        if not digits:
            if not special_characters:
                return False
    return True


def password_generator(length, letters, digits, special_characters):
    characters = ''
    if letters:
        characters += string.ascii_letters
    if digits:
        characters += string.digits
    if special_characters:
        characters += string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def master_exists():
    if os.path.exists("MasterPassword.txt"):
        return True  # -> login screen
    else:
        return False  # -> registration screen


def save_master_to_file():
    global masterPassword
    global masterPasswordHashHex
    master_password_hash = hashlib.sha512(masterPassword.encode('utf-8'))
    masterPasswordHashHex = master_password_hash.hexdigest()
    with open("MasterPassword.txt", 'w') as masterFile:
        masterFile.write(masterPasswordHashHex)
    masterFile.close()


def compare_master():
    global masterPassword
    global masterPasswordHashHex
    master_password_hash = hashlib.sha512(masterPassword.encode('utf-8'))
    masterPasswordHashHex = master_password_hash.hexdigest()
    with open("MasterPassword.txt", 'r') as masterFile:
        stored_master_password_hash_hex = masterFile.read()
    masterFile.close()
    if masterPasswordHashHex == stored_master_password_hash_hex:
        return True
    else:
        return False


def display_error(parent, message):
    QMessageBox.about(parent, "Błąd", message)


def data_exists():
    if os.path.exists("data.txt"):
        return True
    else:
        return False


def data_isvalid(self, site, login, password):
    if not len(site) > 0:
        display_error(self, "Strona nie może być pusta")
        return False
    if not len(login) > 0:
        display_error(self, "Login nie może być pusty")
        return False
    if not len(password) > 0:
        display_error(self, "Hasło nie może być puste")
        return False
    return True


def load_data():
    global storedData
    global encryptedData
    with open('data.txt', 'r') as dataFile:
        encryptedData = dataFile.read()[2:-1:1].encode('utf-8')
    decrypt_data()


def save_data():
    global encryptedData
    global storedData
    encrypt_data()
    with open('data.txt', 'w') as dataFile:
        dataFile.write(str(encryptedData))


def generate_fernet_key():
    global masterPassword
    global fernetKey
    password = masterPassword.encode('utf-8')
    salt = masterPassword.encode('utf-8')

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    fernetKey = Fernet(key)


def encrypt_data():
    global storedData
    global encryptedData
    global fernetKey
    encryptedData = fernetKey.encrypt(str(storedData).encode('utf-8'))


def decrypt_data():
    global storedData
    global encryptedData
    global fernetKey
    decrypted_data = fernetKey.decrypt(encryptedData)
    decrypted_data = decrypted_data.decode('utf-8')
    storedData = ast.literal_eval(decrypted_data)


def erase_data():
    if master_exists():
        os.remove("MasterPassword.txt")
    if data_exists():
        os.remove("data.txt")


class MasterPasswordWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('master_password_widget.ui', self)
        self.lineEdit_GP.setReadOnly(True)
        self.pushButton_GP.clicked.connect(self.generate_password)
        self.pushButton_save_master.clicked.connect(self.save_master_password)

    def save_master_password(self):
        global masterPassword
        if self.radioButton_automatic.isChecked():
            masterPassword = self.lineEdit_GP.text()
            save_master_to_file()

        elif self.radioButton_manual.isChecked():
            password1 = self.lineEdit_manual1.text()
            password2 = self.lineEdit_manual2.text()

            # check if passwords are the same
            if not password1 == password2:
                display_error(self, "Hasła nie są identyczne")
                return

            # check if passwords are valid
            if not (len(password1) > 0 and len(password2) > 0):
                display_error(self, "Hasło nie może mieć zerowej długości")
                return

            masterPassword = self.lineEdit_manual1.text()
            save_master_to_file()

        else:
            display_error(self, "Zaznacz, którą metodą chcesz wygenerować hasło")
            return
        self.close()

    def generate_password(self):
        if not self.radioButton_automatic.isChecked():
            return
        length = self.lineEdit_GP_length.text()

        # check if password length is valid
        if not length_isvalid(length):
            display_error(self, "Nieprawidłowa długość hasła")
            return

        length = int(length)
        letters = self.checkBox_letters.isChecked()
        digits = self.checkBox_digits.isChecked()
        special_characters = self.checkBox_special_characters.isChecked()

        # check if there is at least one checkbox selected
        if not checkbox_isvalid(letters, digits, special_characters):
            display_error(self, "Zaznacz przynajmniej jeden typ znaków do wygenerowania hasła")
            return

        password = password_generator(length, letters, digits, special_characters)
        self.lineEdit_GP.setText(password)


class AddPasswordWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('add_password.ui', self)
        self.pushButton_add.clicked.connect(self.add_data)
        self.pushButton_GP.clicked.connect(self.generate_password)
        self.textEdit_GP.setReadOnly(True)

    def add_data(self):
        if self.radioButton_automatic.isChecked():
            site = self.textEdit_site.toPlainText()
            login = self.textEdit_login.toPlainText()
            password = self.textEdit_GP.toPlainText()
        elif self.radioButton_manual.isChecked():
            site = self.textEdit_site.toPlainText()
            login = self.textEdit_login.toPlainText()
            password = self.textEdit_manual.toPlainText()
            # check if password isnt empty
            if not len(password) > 0:
                display_error(self, "Hasło nie może być puste")

            password = self.textEdit_manual.toPlainText()

        else:
            display_error(self, "Zaznacz, którą metodą chcesz wygenerować hasło")
            return
        global storedData
        if not data_isvalid(self, site, login, password):
            return
        data = [site, login, password]
        storedData.append(data)
        save_data()
        self.close()

    def generate_password(self):
        if not self.radioButton_automatic.isChecked():
            return
        length = self.textEdit_GP_length.toPlainText()

        # check if password length is valid
        if not length_isvalid(length):
            QMessageBox.about(self, "Błąd", "Nieprawidłowa długość hasła")
            return

        length = int(length)
        letters = self.checkBox_letters.isChecked()
        digits = self.checkBox_digits.isChecked()
        special_characters = self.checkBox_special_characters.isChecked()

        # check if there is at least one checkbox selected
        if not checkbox_isvalid(letters, digits, special_characters):
            QMessageBox.about(self, "Błąd", "Zaznacz przynajmniej jeden typ znaków do wygenerowania hasła")
            return

        password = password_generator(length, letters, digits, special_characters)
        self.textEdit_GP.setText(password)


class RemovePasswordWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('remove_password.ui', self)
        self.pushButton_delete.clicked.connect(self.delete_password)
        self.lineEdit_site.returnPressed.connect(self.delete_password)
        self.lineEdit_site.setFocus()

    def delete_password(self):
        global storedData
        site_to_delete = self.lineEdit_site.text()
        if not len(site_to_delete) > 0:
            display_error(self, "Pole nie może być puste.")
            return
        site_found = False
        for siteData in storedData:
            if site_to_delete in siteData[0]:
                site_found = True
                storedData.remove(siteData)
        if not site_found:
            display_error(self, "Nie znaleziono danych dla podanej strony.")
            return
        save_data()
        self.close()


class ShowPasswordsWidget(QWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi('show_passwords.ui', self)
        self.show_passwords(storedData)
        self.pushButton.clicked.connect(self.search)

    def show_passwords(self, data):
        global storedData
        self.tableWidget.clear()
        self.tableWidget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers) # Make table read-only
        self.tableWidget.setRowCount(len(data) + 1)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setItem(0, 0, QTableWidgetItem("Strona"))
        self.tableWidget.setItem(0, 1, QTableWidgetItem("Login"))
        self.tableWidget.setItem(0, 2, QTableWidgetItem("Hasło"))
        self.tableWidget.item(0, 0).setBackground(QtGui.QColor(150, 150, 150))
        self.tableWidget.item(0, 1).setBackground(QtGui.QColor(150, 150, 150))
        self.tableWidget.item(0, 2).setBackground(QtGui.QColor(150, 150, 150))
        counter = 1
        for site_data in data:
            for i in range(3):
                self.tableWidget.setItem(counter, i, QTableWidgetItem(str(site_data[i])))
                if counter % 2 == 0:
                    color = QtGui.QColor(0, 150, 255)
                else:
                    color = QtGui.QColor(0, 255, 150)
                self.tableWidget.item(counter, i).setBackground(color)
            counter += 1
        # Table will fit the screen horizontally
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Remove the horizontal and vertical cell counters
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setVisible(False)
        # self.tableWidget.verticalScrollBar().setVisible(True)
        self.tableWidget.setStyleSheet("QTableWidgetItem {border-color: black; border-style: outset; border-width: 2px}")

    def search(self):
        global storedData
        search_data = list()
        search_string = self.lineEdit.text()
        if len(search_string) == 0:
            self.show_passwords(storedData)
            return
        for site_data in storedData:
            if search_string in site_data[0]:
                search_data.append(site_data)
        self.show_passwords(search_data)


class LoginWidget(QWidget):
    loggedSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi('login.ui', self)
        self.pushButton_login.clicked.connect(self.login)
        self.lineEdit_login.returnPressed.connect(self.login)
        self.lineEdit_login.setFocus()

    def login(self):
        # check if master password is correct
        password = self.lineEdit_login.text()
        if not len(password) > 0:
            display_error(self, "Hasło nie może mieć zerowej długości")
            return
        global masterPassword
        global LOGGED_IN
        masterPassword = password
        if compare_master():
            LOGGED_IN = True
        if LOGGED_IN:
            self.loggedSignal.emit()
            self.close()
        else:
            display_error(self, "Nieprawidłowe hasło")
            return


class RegistrationWidget(QWidget):
    registeredSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi('registration.ui', self)
        self.pushButton_register.clicked.connect(self.register)

    def register(self):
        master1 = self.textEdit_register1.toPlainText()
        master2 = self.textEdit_register2.toPlainText()
        if not master1 == master2:
            display_error(self, "Hasła nie są identyczne")
            return
        if not (len(master1) > 0 and len(master2) > 0):
            display_error(self, "Hasło nie może być puste")
            return
        # update global variable and save master to file
        global masterPassword
        masterPassword = master1
        save_master_to_file()
        # if registration is complete emit a signal and close the window
        self.registeredSignal.emit()
        self.close()


class InformationWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('info.ui', self)
        self.textEdit.setReadOnly(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('app.ui', self)
        self.pushButton_master.clicked.connect(self.create_master_widget)
        self.pushButton_add_password.clicked.connect(self.create_add_password_widget)
        self.pushButton_remove_password.clicked.connect(self.create_remove_password_widget)
        self.pushButton_show.clicked.connect(self.create_show_passwords_widget)
        self.action_info.triggered.connect(self.create_info_widget)
        self.action_exit.triggered.connect(self.close)
        self.action_erase_everything.triggered.connect(self.erase_and_close)  # -> Buggy feature

    def erase_and_close(self):
        erase_data()
        self.close()

    def create_master_widget(self):
        self.master_widget = MasterPasswordWidget()
        self.master_widget.show()

    def create_add_password_widget(self):
        self.add_password_widget = AddPasswordWidget()
        self.add_password_widget.show()

    def create_remove_password_widget(self):
        self.remove_password_widget = RemovePasswordWidget()
        self.remove_password_widget.show()

    def create_show_passwords_widget(self):
        self.show_passwords_widget = ShowPasswordsWidget()
        self.show_passwords_widget.show()

    def create_info_widget(self):
        self.info_widget = InformationWidget()
        self.info_widget.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    mainWindow = MainWindow()

    if master_exists():  # login screen
        loginWidget = LoginWidget()
        loginWidget.show()
        loginWidget.loggedSignal.connect(mainWindow.show)
    else:
        # registration screen
        registrationWidget = RegistrationWidget()
        registrationWidget.show()
        registrationWidget.registeredSignal.connect(mainWindow.show)

    generate_fernet_key()
    if os.path.exists('data.txt'):
        load_data()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print('Closing Window...')
    # DEBUG
