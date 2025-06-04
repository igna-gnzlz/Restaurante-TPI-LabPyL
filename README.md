# Restaurante
Aplicación web para gestionar el menú, pedidos y órdenes de un restaurante.

## Proyecto del Grupo 1
Integrantes:
- Alejo Arce
- Ignacio González
- Daniel Sardinas
- Eliezer Sardinas

## Clonar repositorio en un directorio
```bash
git clone https://github.com/igna-gnzlz/Restaurante-TPI-LabPyL.git
```
## Aplicar entorno virtual
```bash
python -m venv venv
```
## Activar entorno virtual
- Linux/Mac: `source venv/bin/activate`
- Windows: `source venv/Scripts/activate`
- Windows (alternativa): `./venv/Scripts.activate`

## Actualizar pip
```bash
python.exe -m pip install --upgrade pip
```
## Instalar dependencias
```bash
pip install -r requirements.txt
```
## Instalar navegadores para correr tests E2E
```bash
playwright install
```
## Hacer migraciones (si hay modelos nuevos o modificados)
```bash
python manage.py makemigrations
```
## Ejecutar migraciones
```bash
python manage.py migrate
```
## Llenar base de datos con fixture
```bash
python manage.py loaddata products.json
```
## Correr app
```bash
python manage.py runserver
```
