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
from typing import Union
import ast
import json

import psutil
import os
import json

TempR={bool:"#b",int:"#i",str:"#s",float:"#f",list:"#ar",dict:"#d",tuple:"#t"}
debug_mode = False
memory = []
copy_vars =[]
descriptors=[]
MAPVIEW = None # видимость дискрипторов

FILE_MAP_READ = 0x0004
FILE_MAP_WRITE = 0x0002
FILE_MAP_ALL_ACCESS = 0x000F
PAGE_READWRITE = 0x04
INVALID_HANDLE_VALUE = -1




class tp(): #TYPE VAR
    def __init__(self,_type,_data,_str_type):
        """For quick information retrieval and type conversion"""
        self._data_ = _data
        self._type_ = _type
        self._str_type_= _str_type
    def get_info(self):
        return list(self._type_,self._data_,self._str_type_)
def typ(f:str) -> Union[str, int, float, bool, list, dict]:
    if "#b" in f:
        return bool()
    elif "#i" in f:
        return int()
    elif "#s" in f:
        return str()
    elif "#f" in f:
        return float()
    elif "#ar" in f and "[" in f and "]" in f:
        return list()
    elif "#d" in f:
        return dict()
    else:
        print(f"Unknown data type")
        return None
def cut_size(a:str)->int:
    if not a or a[0] != '#':
        return 0

    # Спецификаторы: #b, #i, #s, #f, #ar
    if a.startswith('#ar'):
        return 3  # '#ar' - 3 символа
    elif len(a) >= 2 and a[1] in ['b', 'i', 's', 'f']:
        return 2  # '#b', '#i', '#s', '#f' - 2 символа

def intedificator(T) -> str:
    index =""
    try:
        for i in TempR:
            index = TempR[type(T)]
        return index
    except:
        return "None"
def convetrer_type(data):
    index = intedificator(data)
    return f"{index} {data}"


def give_type(T:str):
    return TempR.get(T,None)

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
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
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
            print(f"Данные:{name_process} {hex(pData)} {data_str[cut_size(data_str)::]}")
    elif(data_str!=None):
        return data_str
    last_data = data_str
    # last_data = data_str[cut_size(data_str)::] #если нужно получить без спецификатора
    # Очистка и полное закрытие
    # kernel32.UnmapViewOfFile(pData)
    # kernel32.CloseHandle(hMemory)
    return last_data
    #Для закрытее общей памяти
#
# def close_mem(name:str):
#     kernel32.UnmapViewOfFile(pData)
#     kernel32.CloseHandle(hMemory)
def write_shared_memory_fixed(name_process: str, data):
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
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
    else:
        descriptors.append(hMemory)

    try:
        #вызов MapViewOfFile
        pData = kernel32.MapViewOfFile(hMemory, FILE_MAP_ALL_ACCESS, 0, 0, 256)
        MAPVIEW = pData
        if not pData:
            error_code = ctypes.get_last_error()
            print(f"Ошибка отображения памяти: код {error_code}")
            return False
        if not isinstance(data, str):
            data = str(data)

        #Создаем буфер и записываем
        buffer = ctypes.create_string_buffer(data.encode('utf-8'), 256)
        ctypes.memmove(pData, buffer, 256)
        if (debug_mode == True):
            print(f"Данные:({data})->'{name_process}'")
        return True

    except Exception as e:
        print(f"Ошибка при записи: {e}")
        return False


def clear_memory(name_process: str) -> bool:
    kernel32 = ctypes.WinDLL('kernel32')
    hMemory = kernel32.OpenFileMappingW(FILE_MAP_WRITE, False, name_process)
    if not hMemory:
        return False

    pData = kernel32.MapViewOfFile(hMemory, FILE_MAP_WRITE, 0, 0, 256)
    if pData:
        ctypes.memset(pData, 0, 256)
        kernel32.UnmapViewOfFile(pData)
        kernel32.CloseHandle(hMemory)
        return True
    kernel32.CloseHandle(hMemory)
    return False

class mem():
    def __init__(self,DM:bool,PROCESS_NAME:str,DAT: Union[str, int, float, bool, list, dict]):
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
        self.READ_DATA =None
        self.split_list_mode=False
        global debug_mode
        debug_mode = self.debug_mode
    def give_var(self,data:str):
        temp = data
        if(temp.startswith("#s")):
            temp=temp[2:]
            return str(temp)
        if(temp.startswith("#ar")):
            temp=temp[3:]
            if(temp.startswith("[") and temp.endwith("]")):
                temp = f"{temp[1::-1].strip()}"
                temp = temp.map(int).split(",")
                return temp

    def give_all_shared_memory(self,t:bool)-> list:
        return descriptors
    def stop(self):
        try:
            return False
        except Exception() as e:
            print(e)
    def start(self):
        try:
            property = open("porperty.txt","r+")
            if(property.read()!=None):
                Exception
            else:
                global debug_mode
                debug_mode = bool(property.read())
        except Exception as e:
            print(f"Error:{e}")
            property = open("porperty.txt", "w+")
            property.write(True)
            property.close()
        else:
            debug_mode == property.read()
        if(debug_mode==True):
            print("Режим отладки")
        self.DAT = convetrer_type(self.DAT)
        self.PROCESS = psutil.Process(os.getpid())
        self.MEM_INFO = self.PROCESS.memory_info()
        memory.append(psutil.Process(os.getpid()))

    def rewrite(self ,data:str , process_name:str):
        self.DAT = convetrer_type(data)
        self.STATE = StateChek(read_shared_memory_fixed(self.PROCESS_NAME[:-1],True))
        self.stop()
    # def write(self,name:str,data):
    #     write_shared_memory_fixed(name, data)
    # def write(self,data):
    #     write_shared_memory_fixed(self.PROCESS_NAME, convetrer_type(data))
    def write(self, data,name=None):
        if(name==None):
            name =self.PROCESS_NAME
        write_shared_memory_fixed(self.PROCESS_NAME, convetrer_type(data))

    def write_list(self, data):
        if self.split_list_mode:
            for item in data:
                formatted = convetrer_type(item)
                write_shared_memory_fixed(self.PROCESS_NAME, formatted)
        else:
            formatted = convetrer_type(data)
            write_shared_memory_fixed(self.PROCESS_NAME, formatted)

        # for i in array:
        #     write_shared_memory_fixed(self.PROCESS_NAME, convetrer_type(i))
    def work(self):
        """The main work cycle"""
        try:
            while self.STATE:
                if (debug_mode == True):
                    print(f"Используется памяти: {self.MEM_INFO.rss / 1024 / 1024:.2f} MB")
                self.rewrite(f"{self.DAT}"+"2",self.PROCESS_NAME)
                write_shared_memory_fixed(self.PROCESS_NAME,self.DAT)
                temp = read_shared_memory_fixed(f"{self.PROCESS_NAME}"[:-1],False)
                if temp !=None:
                    print(type(self.give_var(temp)))
                time.sleep(2)
                if self.stop():
                    break
        except Exception as e:
            print(e)
    def claer(self):
        print(f"Все дискрипторы:{descriptors}")
        for i in descriptors:
            ctypes.WinDLL('kernel32').CloseHandle(i)
            print(f"{i} память была очищена")
        ctypes.WinDLL('kernel32').UnmapViewOfFile(MAPVIEW)
    async def read(self,name=None):
        if(name==None):
            name=self.PROCESS_NAME
        try:
            if (debug_mode == True):
                print(f"Используется памяти: {self.MEM_INFO.rss / 1024 / 1024:.2f} MB")
            print(read_shared_memory_fixed(f"{name}"[:-1], False))
            time.sleep(2)
        except Exception as e:
            print(e)

        # write_shared_memory_fixed(self.PROCESS_NAME, "|")
    def stop(self):
        copy_vars.clear()
        memory.clear()
    async def test(self):
        print("Starts test:")
        self.write(True)
        self.write(1)
        self.write(-10000000)
        self.write(4.55555)
        self.write({1: 2, 2: 3})
        self.write("")
        self.write(1, [1, 2, 3, 4, 5, 7])
        self.write((1, 3, 4, 5, 6, 0, "1"))
        self.write(["1", 4, 1.234, True])
        await asyncio.sleep(0.1)
        self.split_list_mode = False
        self.write_list([1, 2, 3, 4, 5])
        self.write_list([10, 20, 30])
        self.write_list(["a", "b", "c"])
        self.write_list([1.1, 2.2, 3.3])
        self.write_list([True, False, True])
        self.write_list([1, "two", 3.0, True])
        self.write_list([])
        await asyncio.sleep(0.1)
        self.split_list_mode = True
        self.write_list([100, 200, 300])
        self.write_list(["x", "y", "z"])
        self.write_list([1.5, 2.5, 3.5])
        await asyncio.sleep(0.1)
        self.split_list_mode = False
        self.write({"name": "John", "age": 30})
        self.write({"city": "Moscow", "year": 2024})
        self.write({1: "one", 2: "two", 3: "three"})
        self.write({"mixed": 42, "float": 3.14, "bool": True})
        self.write({})
        await asyncio.sleep(0.1)
        self.write((1, 2, 3))
        self.write(("a", "b", "c"))
        self.write((1.1, 2.2, 3.3))
        self.write((True, False, True))
        self.write((1, "two", 3.0, False))
        self.write(())
        await asyncio.sleep(0.1)
        self.write([1, [2, 3], 4])
        self.write({"key": [1, 2, 3]})
        self.write([{"a": 1}, {"b": 2}])
        self.write({"list": [1, 2], "dict": {"x": 1}})
        await asyncio.sleep(0.1)
        self.write(0)
        self.write(-0)
        self.write(2 ** 31 - 1)
        self.write(-2 ** 31)
        self.write(1e-10)
        self.write(1e10)
        self.write(float('inf'))
        self.write(float('-inf'))
        self.write(float('nan'))
    def start_test(self):
        a =asyncio.create_task(self.test())
a =mem(True,None,None)
a.start()
# print(a.start.__doc__)
# a.work()
a.start_test()


while (True):
    b= int(input("Введите 0 чтобы выйти :"))
    if(b==0):
        break
a.claer()
