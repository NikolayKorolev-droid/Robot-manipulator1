import ctypes
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# =============================================================================
# Python UI для DLL манипулятора (ctypes + Tkinter)
#
# Назначение:
# - Загрузить DLL, описать прототипы функций (аргументы/результаты) и через них
#   управлять манипулятором из графического интерфейса.
#
# Термины:
# - ctypes: стандартный модуль Python для работы с C ABI. Позволяет загружать
#   DLL/so и описывать прототипы функций, чтобы Python мог правильно передавать
#   аргументы и получать результаты.
# - c_void_p: эквивалент C-типа void* (произвольный указатель). В нашем случае
#   это дескриптор RM_Manipulator — непрозрачный адрес C++ объекта.
# - extern "C" в DLL: обеспечивает стабильные имена функций и совместимость с
#   ctypes (см. комментарии в c_api.h).
#
# Обзор:
# - _load_dll: ищет и подгружает RobotManipulator.dll из типичных путей.
# - Описание сигнатур ctypes: связывает Python-типизацию с C ABI функций DLL.
# - Класс App: три вкладки — сборка (добавление звеньев), управление
#   (ориентации/захват/снимок) и запросы (позиция, печать структуры).
# =============================================================================


def _load_dll():
    """
    Поиск и загрузка DLL с помощью ctypes.CDLL.

    Порядок поиска:
    - рядом с корнем проекта (..\\RobotManipulator.dll),
    - рядом с текущим файлом (python\\RobotManipulator.dll),
    - в текущей рабочей директории процесса.

    Возвращает загруженную библиотеку, либо бросает FileNotFoundError.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    # Prefer DLL next to project root if launched from there
    candidates = [
        os.path.join(here, "..", "RobotManipulator.dll"),
        os.path.join(here, "RobotManipulator.dll"),
        os.path.join(os.getcwd(), "RobotManipulator.dll"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return ctypes.CDLL(p)
    raise FileNotFoundError("RobotManipulator.dll not found. Build it with build_dll.bat")


rm = _load_dll()

# ctypes signatures
# Ниже мы описываем интерфейс DLL для ctypes:
# - restype: тип возвращаемого значения
# - argtypes: список типов аргументов
# Это позволяет ctypes выполнять проверку типов и маршаллинг (преобразование
# Python-объектов в C-значения и обратно).
RM_Manipulator = ctypes.c_void_p

rm.rm_create_manipulator.restype = RM_Manipulator
rm.rm_destroy_manipulator.argtypes = [RM_Manipulator]

rm.rm_add_link.argtypes = [RM_Manipulator, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
rm.rm_add_link.restype = ctypes.c_int
rm.rm_add_gripper.argtypes = [RM_Manipulator, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
rm.rm_add_gripper.restype = ctypes.c_int
rm.rm_add_camera.argtypes = [RM_Manipulator, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
rm.rm_add_camera.restype = ctypes.c_int

rm.rm_set_direction.argtypes = [RM_Manipulator, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double]
rm.rm_set_direction.restype = ctypes.c_int
rm.rm_open_gripper.argtypes = [RM_Manipulator, ctypes.c_int, ctypes.c_double]
rm.rm_open_gripper.restype = ctypes.c_int
rm.rm_close_gripper.argtypes = [RM_Manipulator, ctypes.c_int]
rm.rm_close_gripper.restype = ctypes.c_int
rm.rm_take_photo.argtypes = [RM_Manipulator, ctypes.c_int]
rm.rm_take_photo.restype = ctypes.c_int

rm.rm_calculate_position.argtypes = [RM_Manipulator, ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
rm.rm_calculate_position.restype = ctypes.c_int
rm.rm_print_structure.argtypes = [RM_Manipulator]


class App(tk.Tk):
    """
    Главный класс UI:
    - Создаёт один экземпляр манипулятора в DLL (RM_Manipulator/void*);
    - Настраивает три вкладки с функциями сборки/управления/запросов;
    - Корректно освобождает манипулятор при закрытии окна.
    """
    def __init__(self):
        super().__init__()
        self.title("Robot Manipulator UI")
        self.geometry("800x560")
        self.manip = rm.rm_create_manipulator()
        if not self.manip:
            messagebox.showerror("Error", "Failed to create manipulator")
            self.destroy()
            return

        self._build_ui()
        self.links = {}  # id -> type (для отображения пользователю)

    def destroy(self) -> None:
        try:
            if getattr(self, "manip", None):
                rm.rm_destroy_manipulator(self.manip)
        finally:
            return super().destroy()

    def _build_ui(self):
        """Создание вкладок интерфейса (Notebook) и их наполнение."""
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.tab_build = ttk.Frame(nb)
        self.tab_control = ttk.Frame(nb)
        self.tab_query = ttk.Frame(nb)

        nb.add(self.tab_build, text="Сборка манипулятора")
        nb.add(self.tab_control, text="Управление")
        nb.add(self.tab_query, text="Позиция/структура")

        self._build_tab_build()
        self._build_tab_control()
        self._build_tab_query()

    def _build_tab_build(self):
        """Вкладка: Сборка манипулятора (добавление звеньев).

        Поля:
        - Тип звена: MovableLink/Gripper/Camera;
        - ID: уникальный идентификатор звена;
        - Prev ID: идентификатор предыдущего (0, если корень);
        - R, Pitch, Yaw, Roll: параметры геометрии/ориентации;
        - Доп. параметр: open_angle (для Gripper) или fov (для Camera).
        """
        frm = self.tab_build
        row = 0

        ttk.Label(frm, text="Тип звена").grid(row=row, column=0, sticky="w", padx=6, pady=4)
        self.c_type = ttk.Combobox(frm, values=["MovableLink", "Gripper", "Camera"], state="readonly")
        self.c_type.current(0)
        self.c_type.grid(row=row, column=1, sticky="ew", padx=6, pady=4)
        frm.grid_columnconfigure(1, weight=1)

        def add_num(label):
            """Вспомогательная функция: создать подпись + поле ввода в строке."""
            nonlocal row
            row += 1
            ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
            e = ttk.Entry(frm)
            e.grid(row=row, column=1, sticky="ew", padx=6, pady=4)
            return e

        self.e_id = add_num("ID")
        self.e_prev = add_num("Prev ID (0 если нет)")
        self.e_r = add_num("Длина r")
        self.e_pitch = add_num("Pitch")
        self.e_yaw = add_num("Yaw")
        self.e_roll = add_num("Roll")
        self.e_extra = add_num("Доп. параметр (open_angle/fov)")

        row += 1
        ttk.Button(frm, text="Добавить звено", command=self.on_add_link).grid(row=row, column=0, columnspan=2, padx=6, pady=10, sticky="ew")

        row += 1
        self.links_list = tk.Listbox(frm, height=10)
        self.links_list.grid(row=row, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        frm.grid_rowconfigure(row, weight=1)

    def _build_tab_control(self):
        """Вкладка: Управление (ориентация, захват, камера).

        Действия:
        - Установить ориентацию для произвольного звена;
        - Открыть/закрыть захват (для Gripper);
        - Сделать снимок (для Camera).
        """
        frm = self.tab_control
        frm.grid_columnconfigure(1, weight=1)
        row = 0

        self.e_c_id = ttk.Entry(frm)
        ttk.Label(frm, text="ID звена").grid(row=row, column=0, sticky="w", padx=6, pady=4)
        self.e_c_id.grid(row=row, column=1, sticky="ew", padx=6, pady=4)

        row += 1
        self.e_c_pitch = ttk.Entry(frm)
        ttk.Label(frm, text="Pitch").grid(row=row, column=0, sticky="w", padx=6, pady=4)
        self.e_c_pitch.grid(row=row, column=1, sticky="ew", padx=6, pady=4)

        row += 1
        self.e_c_yaw = ttk.Entry(frm)
        ttk.Label(frm, text="Yaw").grid(row=row, column=0, sticky="w", padx=6, pady=4)
        self.e_c_yaw.grid(row=row, column=1, sticky="ew", padx=6, pady=4)

        row += 1
        self.e_c_roll = ttk.Entry(frm)
        ttk.Label(frm, text="Roll").grid(row=row, column=0, sticky="w", padx=6, pady=4)
        self.e_c_roll.grid(row=row, column=1, sticky="ew", padx=6, pady=4)

        row += 1
        ttk.Button(frm, text="Установить ориентацию", command=self.on_set_dir).grid(row=row, column=0, columnspan=2, padx=6, pady=10, sticky="ew")

        row += 1
        self.e_g_angle = ttk.Entry(frm)
        ttk.Label(frm, text="Угол раскрытия (для Gripper)").grid(row=row, column=0, sticky="w", padx=6, pady=4)
        self.e_g_angle.grid(row=row, column=1, sticky="ew", padx=6, pady=4)

        row += 1
        ttk.Button(frm, text="Открыть захват", command=self.on_open_gripper).grid(row=row, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(frm, text="Закрыть захват", command=self.on_close_gripper).grid(row=row, column=1, padx=6, pady=6, sticky="ew")

        row += 1
        ttk.Button(frm, text="Сделать снимок (Camera)", command=self.on_take_photo).grid(row=row, column=0, columnspan=2, padx=6, pady=6, sticky="ew")

    def _build_tab_query(self):
        """Вкладка: Запросы (позиция, печать структуры).

        - Рассчитать и показать позицию звена;
        - Вывести структуру манипулятора в консоль.
        """
        frm = self.tab_query
        frm.grid_columnconfigure(1, weight=1)
        row = 0

        self.e_q_id = ttk.Entry(frm)
        ttk.Label(frm, text="ID звена").grid(row=row, column=0, sticky="w", padx=6, pady=4)
        self.e_q_id.grid(row=row, column=1, sticky="ew", padx=6, pady=4)

        row += 1
        ttk.Button(frm, text="Рассчитать позицию", command=self.on_calc_pos).grid(row=row, column=0, columnspan=2, padx=6, pady=10, sticky="ew")

        row += 1
        self.lbl_pos = ttk.Label(frm, text="x=?, y=?, z=?")
        self.lbl_pos.grid(row=row, column=0, columnspan=2, sticky="w", padx=6, pady=4)

        row += 1
        ttk.Button(frm, text="Печать структуры в консоль", command=self.on_print_structure).grid(row=row, column=0, columnspan=2, padx=6, pady=10, sticky="ew")

    def _parse_float(self, entry: ttk.Entry, default=None):
        """Парсинг числа с плавающей точкой с опциональным значением по умолчанию."""
        s = entry.get().strip()
        if not s and default is not None:
            return default
        return float(s)

    def _parse_int(self, entry: ttk.Entry):
        """Парсинг целого числа из поля ввода."""
        return int(entry.get().strip())

    def on_add_link(self):
        """
        Обработчик: добавление звена.
        По типу (MovableLink/Gripper/Camera) вызывает соответствующую функцию DLL.
        """
        try:
            id_ = self._parse_int(self.e_id)
            prev = self._parse_int(self.e_prev)
            r = self._parse_float(self.e_r, 0.0)
            pitch = self._parse_float(self.e_pitch, 0.0)
            yaw = self._parse_float(self.e_yaw, 0.0)
            roll = self._parse_float(self.e_roll, 0.0)
            extra = self._parse_float(self.e_extra, 0.0)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверные значения: {e}")
            return

        typ = self.c_type.get()
        ok = 0
        if typ == "MovableLink":
            ok = rm.rm_add_link(self.manip, id_, prev, r, pitch, yaw, roll)
        elif typ == "Gripper":
            ok = rm.rm_add_gripper(self.manip, id_, prev, r, pitch, yaw, roll, extra)
        else:
            ok = rm.rm_add_camera(self.manip, id_, prev, r, pitch, yaw, roll, extra)

        if not ok:
            messagebox.showerror("Ошибка", "Не удалось добавить звено (см. консоль/ограничения)")
            return

        self.links[id_] = typ
        self.links_list.insert(tk.END, f"{id_}: {typ}, prev={prev}, r={r}")

    def on_set_dir(self):
        """Установить ориентацию звена (pitch/yaw/roll) через DLL."""
        try:
            id_ = int(self.e_c_id.get())
            pitch = self._parse_float(self.e_c_pitch, 0.0)
            yaw = self._parse_float(self.e_c_yaw, 0.0)
            roll = self._parse_float(self.e_c_roll, 0.0)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверные значения: {e}")
            return
        ok = rm.rm_set_direction(self.manip, id_, pitch, yaw, roll)
        if not ok:
            messagebox.showerror("Ошибка", "Не удалось установить ориентацию")

    def on_open_gripper(self):
        """Открыть захват на указанный угол (для Gripper)."""
        try:
            id_ = int(self.e_c_id.get())
            angle = self._parse_float(self.e_g_angle, 0.0)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверные значения: {e}")
            return
        ok = rm.rm_open_gripper(self.manip, id_, angle)
        if not ok:
            messagebox.showerror("Ошибка", "Не удалось открыть захват")

    def on_close_gripper(self):
        """Закрыть захват (для Gripper)."""
        try:
            id_ = int(self.e_c_id.get())
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверные значения: {e}")
            return
        ok = rm.rm_close_gripper(self.manip, id_)
        if not ok:
            messagebox.showerror("Ошибка", "Не удалось закрыть захват")

    def on_take_photo(self):
        """Сделать "снимок" (для Camera). Реализация вывода — в C++ коде."""
        try:
            id_ = int(self.e_c_id.get())
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверные значения: {e}")
            return
        ok = rm.rm_take_photo(self.manip, id_)
        if not ok:
            messagebox.showerror("Ошибка", "Не удалось сделать снимок (возможно, это не камера)")

    def on_calc_pos(self):
        """Вычислить глобальную позицию звена и показать её в UI."""
        try:
            id_ = int(self.e_q_id.get())
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверные значения: {e}")
            return
        x = ctypes.c_double()
        y = ctypes.c_double()
        z = ctypes.c_double()
        ok = rm.rm_calculate_position(self.manip, id_, ctypes.byref(x), ctypes.byref(y), ctypes.byref(z))
        if not ok:
            messagebox.showerror("Ошибка", "Не удалось вычислить позицию")
            return
        self.lbl_pos.config(text=f"x={x.value:.4f}, y={y.value:.4f}, z={z.value:.4f}")

    def on_print_structure(self):
        """Печать структуры манипулятора в stdout (консоль)."""
        rm.rm_print_structure(self.manip)
        messagebox.showinfo("Инфо", "Структура выведена в консоль")


if __name__ == "__main__":
    app = App()
    app.mainloop()


