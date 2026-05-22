@echo off
chcp 65001 >nul
echo ========================================
echo   安装Python依赖库
echo ========================================
echo.
echo 正在安装 pandas, openpyxl, xlrd...
echo.

pip install pandas openpyxl xlrd

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 现在可以运行: python clean_comprehensive_scores.py
echo.
pause
