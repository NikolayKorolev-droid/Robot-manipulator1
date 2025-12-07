@echo off
setlocal EnableExtensions

:: ============================================================================
:: Сборка DLL RobotManipulator (MSVC cl/link)
::
:: Почему так:
:: - Простая последовательность команд без условных блоков "if (not) ...",
::   чтобы избежать ошибок парсинга cmd.
:: - Для каждого исходника явно указываем выходной .obj, чтобы не было
::   неоднозначных путей (особенно при необычных символах в путях).
:: - На линковке перечисляем .obj по именам, так надёжнее, чем шаблоны.
::
:: Переменные:
:: - OUT: имя итоговой DLL
:: - OBJDIR: каталог для промежуточных объектных файлов (.obj)
::
:: Требования окружения:
:: - Запускать из "x64 Native Tools Command Prompt for VS" (или аналогичного),
::   чтобы cl/link были в PATH и переменные окружения настроены vcvarsall.bat.
:: ============================================================================

set OUT=RobotManipulator.dll
set OBJDIR=build_objs

:: Создаём каталог для объектных файлов (ошибку игнорируем, если уже есть)
:: Создаём каталог для объектных файлов; если уже существует, ошибка скрывается.
mkdir "%OBJDIR%" 2>nul

echo Compiling sources...
:: Ключи компилятора (cl):
::  /O2    - оптимизация для скорости
::  /EHsc  - корректная модель исключений C++
::  /MD    - динамическая CRT (подходит для DLL)
::  /c     - только компиляция (без линковки)
::  /Fo    - явное имя выходного .obj
cl /nologo /O2 /EHsc /MD /c MovableLink.cpp /Fo"%OBJDIR%\MovableLink.obj" || goto :err
cl /nologo /O2 /EHsc /MD /c Gripper.cpp /Fo"%OBJDIR%\Gripper.obj" || goto :err
cl /nologo /O2 /EHsc /MD /c Camera.cpp /Fo"%OBJDIR%\Camera.obj" || goto :err
cl /nologo /O2 /EHsc /MD /c Manipulator.cpp /Fo"%OBJDIR%\Manipulator.obj" || goto :err
cl /nologo /O2 /EHsc /MD /c ElementaryMove.cpp /Fo"%OBJDIR%\ElementaryMove.obj" || goto :err
cl /nologo /O2 /EHsc /MD /c Movement.cpp /Fo"%OBJDIR%\Movement.obj" || goto :err
cl /nologo /O2 /EHsc /MD /c c_api.cpp /Fo"%OBJDIR%\c_api.obj" || goto :err

echo Linking DLL...
:: Ключи линкера (link):
::  /DLL  - собрать динамическую библиотеку
::  /OUT  - имя итогового файла
:: Затем перечисление всех объектных файлов
link /nologo /DLL /OUT:%OUT% ^
  "%OBJDIR%\MovableLink.obj" ^
  "%OBJDIR%\Gripper.obj" ^
  "%OBJDIR%\Camera.obj" ^
  "%OBJDIR%\Manipulator.obj" ^
  "%OBJDIR%\ElementaryMove.obj" ^
  "%OBJDIR%\Movement.obj" ^
  "%OBJDIR%\c_api.obj" || goto :err

echo Done. Output: %OUT%
exit /b 0

:err
echo Build failed.
exit /b 1

