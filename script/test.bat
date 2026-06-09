@echo off
REM Test the Reel Script Generator with sample input

echo Testing Reel Script Generator...
echo.
echo Setting up test input...

REM Create a test input file
(
echo what is a diode
echo 1
echo 10
echo 2
) > test_input.txt

REM Run the generator with test input
python main.py < test_input.txt

REM Clean up
del test_input.txt

pause
