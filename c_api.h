//=============================================================================
// C-compatible API for Robot Manipulator DLL
//
// Назначение:
// - Предоставляет стабильный C ABI поверх C++ классов, чтобы вызывать DLL
//   из Python (ctypes), C и других языков FFI. Используются простые типы и
//   extern "C" для исключения name mangling.
//
// Термины:
// - extern "C": специальная конструкция C++ для экспорта/импорта функций с
//   соглашением вызова и именованием как у языка C (без "name mangling").
//   Это делает имена функций в DLL предсказуемыми и совместимыми с FFI.
// - ABI (Application Binary Interface): двоичный интерфейс на уровне вызовов
//   функций, типов аргументов и соглашений вызова. Стабильный C ABI позволяет
//   другим языкам безопасно вызывать функции DLL.
// - Дескриптор RM_Manipulator (void*): "непрозрачный" указатель, который
//   снаружи трактуется как абстрактный handle. Внутри он указывает на
//   реальный C++ объект класса Manipulator. В Python он отображается как
//   ctypes.c_void_p, то есть просто адрес без знания о структуре.
//
// Идея использования:
// - Создайте манипулятор через rm_create_manipulator();
// - Добавляйте звенья (обычное/захват/камера);
// - Управляйте ориентацией/захватом/камерой;
// - Запрашивайте позицию или печать структуры;
// - Освободите манипулятор через rm_destroy_manipulator().
//=============================================================================
#ifndef C_API_H
#define C_API_H

#ifdef _WIN32
#  define RM_EXPORT __declspec(dllexport)
#else
#  define RM_EXPORT
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Непрозрачный дескриптор C++ объекта Manipulator.
// Извне — это просто адрес (указатель). Внутри DLL мы приводим его обратно
// к типу Manipulator* и работаем с настоящим объектом C++.
typedef void* RM_Manipulator;

//-------------------------------------------------------------------------
// Lifecycle
//-------------------------------------------------------------------------
// Создает новый C++ Manipulator.
// Возврат:
// - Непрозрачный дескриптор RM_Manipulator, либо nullptr при ошибке.
RM_EXPORT RM_Manipulator rm_create_manipulator();
// Уничтожает ранее созданный манипулятор.
// Параметры:
// - manip: дескриптор, полученный из rm_create_manipulator (nullptr допустим).
RM_EXPORT void rm_destroy_manipulator(RM_Manipulator manip);

//-------------------------------------------------------------------------
// Construction (построение)
//-------------------------------------------------------------------------
// Добавляет обычное подвижное звено (MovableLink).
// Параметры:
// - manip: дескриптор манипулятора
// - id: уникальный идентификатор звена
// - prev_id: идентификатор предыдущего звена в цепи (0, если нет)
// - r: длина звена
// - pitch/yaw/roll: ориентация звена относительно предыдущего
// Возврат: 1 — успех, 0 — ошибка/исключение.
RM_EXPORT int rm_add_link(RM_Manipulator manip, int id, int prev_id, double r, double pitch, double yaw, double roll);
// Добавляет захват (Gripper) с параметром open_angle.
// Параметры: как у rm_add_link + open_angle — угол раскрытия захвата.
// Возврат: 1 — успех, 0 — ошибка/исключение.
RM_EXPORT int rm_add_gripper(RM_Manipulator manip, int id, int prev_id, double r, double pitch, double yaw, double roll, double open_angle);
// Добавляет камеру (Camera) с параметром fov.
// fov (field of view): угол обзора камеры.
// Возврат: 1 — успех, 0 — ошибка/исключение.
RM_EXPORT int rm_add_camera(RM_Manipulator manip, int id, int prev_id, double r, double pitch, double yaw, double roll, double fov);

//-------------------------------------------------------------------------
// Control (управление)
//-------------------------------------------------------------------------
// Устанавливает ориентацию звена по id.
// Параметры: id звена и новые углы (pitch/yaw/roll).
// Возврат: 1 — успех, 0 — ошибка/исключение.
RM_EXPORT int rm_set_direction(RM_Manipulator manip, int id, double pitch, double yaw, double roll);
// Открывает захват на заданный угол.
// Параметры: id захвата, угол открытия.
// Возврат: 1 — успех, 0 — ошибка/исключение.
RM_EXPORT int rm_open_gripper(RM_Manipulator manip, int id, double angle);
// Закрывает захват.
// Параметры: id захвата.
// Возврат: 1 — успех, 0 — ошибка/исключение.
RM_EXPORT int rm_close_gripper(RM_Manipulator manip, int id);
// Делает "снимок" камерой по id (логика/вывод определена в реализации C++).
// Возврат: 1 — успех, 0 — ошибка/исключение.
RM_EXPORT int rm_take_photo(RM_Manipulator manip, int id);

//-------------------------------------------------------------------------
// Query (запросы)
//-------------------------------------------------------------------------
// Вычисляет позицию звена (глобальные координаты).
// Параметры:
// - id: идентификатор звена
// - out_x/out_y/out_z: указатели на double, куда будет записана позиция
// Возврат: 1 — успех (значения записаны), 0 — ошибка/исключение.
RM_EXPORT int rm_calculate_position(RM_Manipulator manip, int id, double* out_x, double* out_y, double* out_z);
// Печатает структуру манипулятора в stdout (консоль процесса).
// Параметры: manip — дескриптор манипулятора.
RM_EXPORT void rm_print_structure(RM_Manipulator manip);

#ifdef __cplusplus
}
#endif

#endif // C_API_H


