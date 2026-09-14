# Actividad 4: Sistema de Control de Iluminación por Gestos de la Mano (ESP32 + MediaPipe)

**Estudiante:** Johan Andrés Canchala Arenas  
**Asignatura:** Microcontroladores / Sistemas Embebidos  
**Universidad Militar Nueva Granada**  

---

## 1. Descripción General del Proyecto
Este proyecto implementa un sistema interactivo de visión artificial y control embebido capaz de reconocer gestos de la mano en tiempo real mediante una webcam utilizando **MediaPipe Hand Landmarker** y **OpenCV**. Los gestos reconocidos se traducen en comandos seriales enviados a un microcontrolador **ESP32**, el cual modula la intensidad de un conjunto de LEDs mediante modulación por ancho de pulsos (**PWM**) o activa secuencias automáticas no bloqueantes administradas por una máquina de estados con `millis()`.

---

## 2. Diagrama de Bloques y Arquitectura del Sistema

```mermaid
graph LR
    A[Webcam PC] -->|Frames de Video| B(MediaPipe / OpenCV)
    B -->|Clasificación de Gestos| C(Controlador Serial Python)
    C -->|Byte ASCII 9600 Baud| D[UART / Puerto Serial USB]
    D -->|Lectura no bloqueante| E[ESP32 Firmware]
    E -->|Salida PWM 30%| F[LED Amarillo GPIO 25]
    E -->|Salida PWM 70%| G[LED Azul GPIO 26]
    E -->|Salida PWM 100%| H[LED Rojo GPIO 27]
    E -->|Máquina de Estados millis| I[Secuencias 1 y 2]
