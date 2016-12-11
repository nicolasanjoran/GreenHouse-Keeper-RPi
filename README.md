# GreenHouse-Keeper

## Description

This is a Python tool that can manage a Greenhouse by controlling its temperature based on top of a RPi Zero. This tool is especially designed to open/close the doors in order to cool the temperature down in case of hot weather. 

## Hardware

* Raspberry Pi Zero (5$)
* TC74A I2C Temperature sensor
* Switches

## RPi Pinout

### Temperature sensor
3. (I2C SDA) temperature sensor
5. (I2C SCL) temperature sensor

### Engine Position sensor
27. (GPIO0) Engine 1 position sensor 0
29. (GPIO5) Engine 1 position sensor 1
31. (GPIO6) Engine 1 position sensor 2
33. (GPIO13) Engine 1 position sensor 3
35. (GPIO19) Engine 1 position sensor 4
37. (GPIO26) Engine 2 position sensor 0
40. (GPIO21) Engine 2 position sensor 1
38. (GPI20) Engine 2 position sensor 2
36. (GPI16) Engine 2 position sensor 3
32. (GPIO12) Engine 2 position sensor 4

### Engine open/close commands
28. (GPIO1) Engine 1 open command
26. (GPIO7) Engine 1 close command
24. (GPIO8) Engine 2 open command
22. (GPIO25) Engine 2 close command
