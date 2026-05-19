#include <windows.h>
#include <iostream>
#include <cstring>
#include <string>
#include <typeindex>
#include <map>
#include <vector>

std::map<std::type_index, std::string> Types = {
    {typeid(bool), "#b"},
    {typeid(int), "#i"},
    {typeid(double), "#d"},
    {typeid(std::string), "#s"},
    {typeid(std::vector<int>), "#ar#i"},
    {typeid(std::vector<double>), "#ar#d"},
    {typeid(std::vector<std::string>), "#ar#s"}
};
std::string srez(std::string c,int a) {
    std::string R;
    for (int i = 0; i< c.length();i++)
        if (i >= a)
            R += c[i];
    return R;
}
std::string cup_size(char* a) {
    std::string res = std::string(a);

    //ищем первый пробел или конец после спецификатора
    int start_pos = 0;
    if (res[0] == '#') {
        if (res[1] == 'a' && res[2] == 'r') {
            start_pos = 3;  //пропускаем "#ar"
        }
        else if (res[1] == 'b' || res[1] == 'i' || res[1] == 's' || res[1] == 'f') {
            start_pos = 2;  //пропускаем "#b", "#i", "#s", "#f"
            //пропускаем пробел если есть
            if (res[start_pos] == ' ') start_pos++;
        }
    }

    //возвращаем строку без спецификатора типа
    return res.substr(start_pos);
}
template<typename T>
std::string mas(T a) {
    std::string local = "[";
    for (int i = 0;i < a.size();i++) {
        local += std::to_string(a[i]);
        if (a.size() - 1 != i)
            local+= ",";
    }
    local += "]";
    return local;
}
const wchar_t* name_in_memory = L"Game";
//TempR={int:"#i",str:"#s",float:"#f",list:"#ar",dict:"#d"}
template<typename T>
T pull = T{};
template<typename T>
std::string FinalPull(T a) {

    return Types[typeid(a)] + " " + (mas(a));
}



bool state = true;
void add_in_memory(char* pData, std::string a) {
    const char* message = a.data();
    strcpy_s(pData, 256, message);
    std::cout << " Данные записаны. Adress:" << (void*)pData << " Data:" << pData << std::endl;
    std::cout << "Запустите Python скрипт..." << std::endl;
}
void read_memory(int a, const wchar_t* nameproce) {
    //открываем существующее отображение файла
    HANDLE hMemory = OpenFileMapping(
        FILE_MAP_READ,  //запрос только на чтение
        FALSE,          //наследование handle
        nameproce  //имя общей памяти
    );

    if (!hMemory) {
        std::cout << "Ошибка открытия памяти! Код: " << GetLastError() << std::endl;
        return;
    }

    char* pData = (char*)MapViewOfFile(hMemory, FILE_MAP_READ, 0, 0, 256);

    if (!pData) {
        std::cout << "Ошибка отображения памяти! Код: " << GetLastError() << std::endl;
        CloseHandle(hMemory);
        return;
    }

    std::cout << "\nДанные прочитаны. Adress:" << (void*)pData << " Data:" << cup_size(pData) << std::endl;
    for (int i = 0; i < strlen(pData);i++) {
        if (pData[i] == '|') {
            std::cout << "Завершение считывания общей памяти" << std::endl;
            state = false;
            return;
        }
    }
    //если нужна дополнительная обработка данных
    if (a > 0) {
        std::cout << "Дополнительная обработка: Длина данных = " << strlen(pData) << std::endl;
    }

    //очистка
    UnmapViewOfFile(pData);
    CloseHandle(hMemory);
}
int main() {
    setlocale(LC_ALL, "");


    HANDLE hMemory = CreateFileMapping(
        INVALID_HANDLE_VALUE,
        NULL,
        PAGE_READWRITE,
        0,
        256,
        name_in_memory
    );

    if (!hMemory) {
        std::cout << "Ошибка создания памяти! Код: " << GetLastError() << std::endl;
        system("pause");
        return 1;
    }

    char* pData = (char*)MapViewOfFile(hMemory, FILE_MAP_ALL_ACCESS, 0, 0, 256);

    //явно очищаем память
    ZeroMemory(pData, 256);

    std::string data = "123EX0";
    while (state) {
        data += '=';
        if (strlen(pData) == 20)
            data += '|';
        add_in_memory(pData, FinalPull(data));
        read_memory(1, L"Game1");
        Sleep(2000);
    }
}
