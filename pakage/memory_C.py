import ctypes
import datetime
import time
import datetime
import asyncio
from ctypes import *
from ctypes import wintypes
from ctypes import c_char_p, c_char
import os
import sys

import psutil
import os
import json

TempR={bool:"#b",int:"#i",str:"#s",float:"#f",list:"#ar",dict:"#d"}
debug_mode = False
memory = []

FILE_MAP_READ = 0x0004
FILE_MAP_WRITE = 0x0002
FILE_MAP_ALL_ACCESS = 0x000F
PAGE_READWRITE = 0x04
INVALID_HANDLE_VALUE = -1

def cut_size(a:str)->int:
    if not a or a[0] != '#':
        return 0

    # Спецификаторы: #b, #i, #s, #f, #ar
    if a.startswith('#ar'):
        return 3  # '#ar' - 3 символа
    elif len(a) >= 2 and a[1] in ['b', 'i', 's', 'f']:
        return 2  # '#b', '#i', '#s', '#f' - 2 символа

def intedificator(T:str) -> str:
    index =""
    for i in TempR:
        index = TempR[type(T)]
    return index
def convetrer_type(data):
    if not("#"in data):
        return f"{intedificator(data)} {data}"
    return data
def StateChek(a:str)-> bool:
    if(debug_mode==True):
        print(f"Значение чтения:{a}")
    if a is None:
        return True
    elif("|" in a):
        return False
    else:
        return True

def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True

    print("Требуются права администратора...")
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    return False
def read_shared_memory_fixed(name_process : str,Mreturn:bool):
    kernel32 = ctypes.WinDLL('kernel32')
    # Настройка функций
    kernel32.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.OpenFileMappingW.restype = wintypes.HANDLE
    kernel32.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
    kernel32.MapViewOfFile.restype = wintypes.LPVOID
    # Открываем память
    hMemory = kernel32.OpenFileMappingW(FILE_MAP_READ, False, name_process)
    if not hMemory:
        print(f'{datetime.datetime.now().strftime("[%H:%M:%S] ")}Память пуста!')
        return
    # Подключаем память Это и есть адрес(является указателем)
    pData = kernel32.MapViewOfFile(hMemory, FILE_MAP_READ, 0, 0, 256)
    # Создаем буфер и копируем данные
    buffer = ctypes.create_string_buffer(256)
    ctypes.memmove(buffer, pData, 256)

    # Ищем нуль-терминатор
    data_bytes = buffer.value.split(b'\x00')[0]
    data_str = data_bytes.decode('utf-8', errors='ignore')
    if(Mreturn!=True and data_str!=None):
        if (debug_mode == True):
            print(f"Данные из памяти: {name_process} {hex(pData)} {data_str[cut_size(data_str)::]}")
    elif(data_str!=None):
        return data_str

    # Очистка
    # kernel32.UnmapViewOfFile(pData)
    # kernel32.CloseHandle(hMemory)
    #Для закрытее общей памяти
#
# def close_mem():
#     kernel32.UnmapViewOfFile(pData)
#     kernel32.CloseHandle(hMemory)
def write_shared_memory_fixed(name_process: str, data):
    kernel32 = ctypes.WinDLL('kernel32')

    # Настройка функций CreateFileMapping - УПРОЩЕННАЯ ВЕРСИЯ
    kernel32.CreateFileMappingW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                            wintypes.DWORD, wintypes.DWORD, wintypes.LPCWSTR]
    kernel32.CreateFileMappingW.restype = wintypes.HANDLE

    kernel32.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                       wintypes.DWORD, ctypes.c_size_t]
    kernel32.MapViewOfFile.restype = wintypes.LPVOID

    # Создаем разделяемую память
    hMemory = kernel32.CreateFileMappingW(
        INVALID_HANDLE_VALUE,  # Используем файл подкачки
        None,  # Атрибуты безопасности по умолчанию (None вместо SECURITY_ATTRIBUTES)
        PAGE_READWRITE,  # Права на чтение/запись
        0,  # Размер старшего двойного слова
        256,  # Размер младшего двойного слова
        name_process  # Имя памяти
    )

    if not hMemory:
        error_code = ctypes.get_last_error()
        print(f"Ошибка создания памяти '{name_process}': код {error_code}")
        return False

    try:
        # ПРАВИЛЬНЫЙ вызов MapViewOfFile
        pData = kernel32.MapViewOfFile(hMemory, FILE_MAP_ALL_ACCESS, 0, 0, 256)
        if not pData:
            error_code = ctypes.get_last_error()
            print(f"Ошибка отображения памяти: код {error_code}")
            return False

        # Подготавливаем данные
        if not isinstance(data, str):
            data = str(data)


        # Создаем буфер и записываем
        buffer = ctypes.create_string_buffer(data.encode('utf-8'), 256)
        ctypes.memmove(pData, buffer, 256)
        if (debug_mode == True):
            print(f"Данные ({data}) успешно записаны в '{name_process}'")
        return True

    except Exception as e:
        print(f"Ошибка при записи: {e}")
        return False


# read_shared_memory_fixed("Game")
# if not run_as_admin():
#     print("Перезапустите скрипт с правами администратора!")
#     sys.exit(1)
class mem():
    def __init__(self,DM:bool,PROCESS_NAME:str,DAT:str):
        self.STATE= True
        if PROCESS_NAME==None and DAT==None:
            self.PROCESS_NAME = "Game1"
            self.DAT = "Hello from Python Process"
        else:
            self.PROCESS_NAME = PROCESS_NAME
            self.DAT = DAT
        self.PROCESS = None
        self.MEM_INFO = None
        self.debug_mode= DM
        global debug_mode
        debug_mode = self.debug_mode

    def start(self):
        """The method creates a process
And displays how much memory is used"""
        if(debug_mode==True):
            print("Режим отладки")
        self.DAT = convetrer_type(self.DAT)
        self.PROCESS = psutil.Process(os.getpid())
        self.MEM_INFO = self.PROCESS.memory_info()
        memory.append(psutil.Process(os.getpid()))

    def rewrite(self ,data:str , process_name:str):
        """The method allows you to overwrite the values of a variable passed to shared memory.
state allows you to stop transmitting data/changing it
need parameter for changing, if True, then the value changes
data is the value of the variable"""
        self.DAT = convetrer_type(data)
        self.STATE = StateChek(read_shared_memory_fixed(self.PROCESS_NAME[:-1],True))
    def work(self):
        """The main work cycle"""
        try:
            while self.STATE:
                if (debug_mode == True):
                    print(f"Используется памяти: {self.MEM_INFO.rss / 1024 / 1024:.2f} MB")
                self.rewrite(f"{self.DAT}"+"2",
                             self.PROCESS_NAME)
                write_shared_memory_fixed(self.PROCESS_NAME,self.DAT)
                read_shared_memory_fixed(f"{self.PROCESS_NAME}"[:-1],False)
                time.sleep(2)
        except Exception as e:
            print(e)
        write_shared_memory_fixed(self.PROCESS_NAME, "|")
        time.sleep(2)
        print("Прекращение работы")
