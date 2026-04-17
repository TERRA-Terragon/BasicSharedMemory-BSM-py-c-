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
std::string cup_size(char * a){
    int size = 0;
    std::string res = std::string(a);
    int multy_size = res.size();
    multy_size= res.size();
    for (char var : res) {
        if (var == '#')
            size++;
    }
    if (size >= 2)
        return srez(res,5);
    else
        return srez(res, 2);
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
//template<typename T>
//bool is_vector(const T&) {
//    return false;
//}
//
//template<typename T>
//bool is_vector<std::vector<T>>() {
//    return true;
//}



bool state = true;
void add_in_memory(char* pData, std::string a) {
    const char* message = a.data();
    strcpy_s(pData, 256, message);
    std::cout << " Данные записаны. Adress:" << (void*)pData << " Data:" << pData << std::endl;
    std::cout << "Запустите Python скрипт..." << std::endl;
}
void read_memory(int a, const wchar_t* nameproce) {
    // Открываем существующее отображение файла
    HANDLE hMemory = OpenFileMapping(
        FILE_MAP_READ,  // Запрос только на чтение
        FALSE,          // Наследование handle
        nameproce  // Имя общей памяти
    );

    if (!hMemory) {
        std::cout << "Ошибка открытия памяти! Код: " << GetLastError() << std::endl;
        return;
    }

    // Получаем указатель на данные
    char* pData = (char*)MapViewOfFile(hMemory, FILE_MAP_READ, 0, 0, 256);

    if (!pData) {
        std::cout << "Ошибка отображения памяти! Код: " << GetLastError() << std::endl;
        CloseHandle(hMemory);
        return;
    }

    // Читаем и выводим данные
    std::cout << "\nДанные прочитаны. Adress:" << (void*)pData << " Data:" << cup_size(pData) << std::endl;
    for (int i = 0; i < strlen(pData);i++) {
        if (pData[i] == '|') {
            std::cout << "Завершение считывания общей памяти" << std::endl;
            state = false;
            return;
        }
    }
    // Если нужна дополнительная обработка данных
    if (a > 0) {
        std::cout << "Дополнительная обработка: Длина данных = " << strlen(pData) << std::endl;
    }

    // Освобождаем ресурсы
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

    // Явно очищаем память
    ZeroMemory(pData, 256);

    // Записываем простой ASCII текст для теста
 //   const char* message = "Hello from C++ Process!";
 //   strcpy_s(pData, 256, message);
 //   std::cout << "Данные записаны. Adress:" << (void*)pData << " Data:" << pData << std::endl;
//    std::cout << "Запустите Python скрипт..." << std::endl;
    std::string data = "123EX0";
    while (state) {
        data += '=';
        if (strlen(pData) == 10)
            data += '|';
        add_in_memory(pData, FinalPull(data));
        read_memory(1, L"Game1");
        
        //UnmapViewOfFile(pData);
        //CloseHandle(hMemory);
        Sleep(2000);
    }
    //std::cout<< FinalPull(std::vector<int> {12,3,4});
}