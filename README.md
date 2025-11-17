# SHODAN AI Stable CLI

Búsquedas en Shodan mediante lenguaje natural, con capa heurística y soporte opcional para OpenAI.

## Características principales
- Conversión automática de lenguaje natural a queries Shodan
- Integración opcional con IA (OpenAI) o modo heurístico offline
- Guardado seguro de credenciales (`chmod 600`)
- Instalación automática de dependencias faltantes
- Soporte multiplataforma (Linux, macOS, Windows)
- Modo de ayuda `-h` y modo variable `-V` para alias global

## Instalación rápida
```bash
git clone https://github.com/youruser/shodan-ai.git
cd shodan-ai
python3 shodan_ai_stable.py "servidores apache en chile"
```

## Seguridad
El sistema nunca imprime claves, no las envía a terceros y las almacena sólo si el usuario lo autoriza.

## Autor
**@dm20911 (SombreroBlancoCiberseguridad)** 


## Badges

[![Status](https://img.shields.io/badge/status-stable-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-orange.svg)]()
[![Security](https://img.shields.io/badge/security-focused-critical)]()
