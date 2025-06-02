# Restaurante
Aplicación web para gestionar el menú, pedidos y órdenes de un restaurante.

## Proyecto del Grupo 1
Integrantes:
- Alejo Arce
- Ignacio González
- Daniel Sardinas
- Eliezer Sardinas

## Clonar repositorio en un directorio
git clone https://github.com/igna-gnzlz/Restaurante-TPI-LabPyL.git

## Aplicar entorno virtual en el repo clonado
cd Restaurante-TPI-LabPyL  
python -m venv env

## Activar entorno virtual
- Linux/Mac: source env/bin/activate
- Windows: source env/Scripts/activate
- Windows (alternativa): ./env/Scripts.activate

## Actualizar pip
python.exe -m pip install --upgrade pip

## Instalar dependencias
pip install -r requirements.txt

## Instalar navegadores para correr tests E2E
playwright install

## Hacer migraciones (si hay modelos nuevos o modificados)
python manage.py makemigrations

## Ejecutar migraciones
python manage.py migrate

## Llenar base de datos con fixture
python manage.py loaddata products.json

## Correr app
python manage.py runserver
