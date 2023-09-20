from django.shortcuts import render

# Create your views here.

# analyzer/views.py

from django.http import HttpResponse
from syslog_analyzer_project.globals import registros
import os
import datetime
import sqlite3
import re
import openai
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadFileForm, ShowAnswerForm
from .models import UploadedFile, FoundError
import json
from django.http import JsonResponse

current_time = datetime.datetime.now()

openai.api_key = "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"  # Reemplaza con tu API key

def seleccionar_registro(request):
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        if registro_id:
            try:
                # Obtén el registro directamente del diccionario global 'registros'
                registro = registros.get(int(registro_id))
                if registro:
                    message = registro['registro']

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user",
                                   "content": "I have the following problem in Linux: " + message + " My question is: How to fix the problem?"}]
                    )
                    answer = response.choices[0].message.content

                    return render(request, 'analyzer/chat_consulta.html', {'message': message, 'message2': answer})

                    # Si no necesitas guardar el registro en un archivo de texto, puedes eliminar estas líneas
                    # with open('registro_seleccionado.txt', 'w') as file:
                    #     file.write(message)

                    # Puedes agregar un mensaje de éxito si lo deseas
                    messages.success(request,
                                     "Registro seleccionado y guardado en el archivo 'registro_seleccionado.txt'.")

                else:
                    messages.error(request, "El registro seleccionado no existe.")

            except Exception as e:
                # Puedes agregar un mensaje de error si ocurre una excepción
                messages.error(request, f"Error al seleccionar el registro: {str(e)}")

        else:
            # Puedes agregar un mensaje de error si no se ha seleccionado ningún registro
            messages.error(request, "Por favor, seleccione un registro antes de continuar.")

    return redirect('consulta_registros')  # Redirigir a la página de consulta de registros

def agrupar_registros(registro):
    try:

        # Clasificar el registro y retornar la clasificación
        palabras_clave = ['networkmanager', 'kernel', 'pycharm']

        # Check if registro is of type bytes
        if isinstance(registro, bytes):
            valor = registro.decode('utf-8').lower()
        else:
            valor = registro.lower()

        for keyword in palabras_clave:
            if keyword in valor:
                return keyword.capitalize()  # Devolver la palabra clave con la primera letra en mayúscula

        return "Linux"  # Si no se encuentra ninguna palabra clave, se clasifica como "General"
    except Exception as e:
        # Capturar cualquier excepción que pueda ocurrir durante la lectura
        error_message = f"Error al Clasificar Registros: {str(e)}"
        print("Funcion Clasificar Registros.- Error:  ", error_message)
        print("Presiona Enter para continuar...")
        input()  # El prog

def clasificar_registro(registro):
    try:

        # Clasificar el registro y retornar la clasificación
        palabras_clave = ['err', 'fail', 'error', 'warning', 'info', 'could']

        # Check if registro is of type bytes
        if isinstance(registro, bytes):
            valor = registro.decode('utf-8').lower()
        else:
            valor = registro.lower()

        for keyword in palabras_clave:
            if keyword in valor:
                return keyword.capitalize()  # Devolver la palabra clave con la primera letra en mayúscula

        return "General"  # Si no se encuentra ninguna palabra clave, se clasifica como "General"
    except Exception as e:
        # Capturar cualquier excepción que pueda ocurrir durante la lectura
        error_message = f"Error al Clasificar Registros: {str(e)}"
        print("Funcion Clasificar Registros.- Error:  ", error_message)
        print("Presiona Enter para continuar...")
        input()  # El prog



def mostrar_registro(registro):
    try:
        # Convert registro to a string if it is a list
        if isinstance(registro, list):
            registro = " ".join(registro)

        # Agregar una columna con la clasificación al registro completo
        clasificacion = clasificar_registro(registro)
        registro_con_clasificacion = [clasificacion] + registro.split()
        agrupacion = agrupar_registros(registro)


        # Supongamos que el registro tiene el formato 'YYYY-MM-DD HH:MM:SS'
        # Si es así, puedes dividir el registro en fecha y hora de la siguiente manera:

        # Supongamos que el registro tiene el formato 'YYYY-MM-DD HH:MM:SS'
        # Si es así, puedes dividir el registro en fecha y hora de la siguiente manera:

        # Dividir el registro en fecha y hora
        componentes = registro.split()  # Esto dividirá el registro en una lista de palabras

        if len(componentes) >= 2:  # Asegurémonos de que haya al menos fecha y hora en el registro
            fecha = componentes[0] + "/" + componentes[1]
            hora = componentes[2]  # El segundo elemento es la hora
        else:
            fecha = "No disponible"  # Define un valor predeterminado si no hay suficientes componentes
            hora = "No disponible"



        # Insertar datos en la base de datos
        group = agrupacion
        tipo = clasificacion
        message = " ".join(registro)

        # Crear un nuevo identificador único (por ejemplo, utilizando un contador)
        nuevo_id = len(registros) + 1

        # Crear un diccionario para el registro actual
        registro_actual = {
            "agrupacion": group,
            "clasificacion": tipo,
            "fecha": fecha,
            "hora": hora,
            "registro": message
        }

        # Agregar el registro al diccionario utilizando el nuevo_id como clave
        registros[nuevo_id] = registro_actual

    except Exception as e:
        # Capturar cualquier excepción que pueda ocurrir durante la lectura
        error_message = f"Error al Mostrar o Insertar Registros: {str(e)}"
        print("Funcion Mostrar Registros.- Error:  ", error_message)

def upload_action(request):
    form = UploadFileForm()

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            try:
                # Leer el archivo línea por línea y procesar cada línea
                for line in uploaded_file:
                    # Procesar la línea aquí
                    # Hacemos el split de la línea
                    datos_registro = [elemento.decode('utf-8') for elemento in line.split()]
                    # Mostramos el registro
                    mostrar_registro(datos_registro)
                    pass

                # Si llegamos hasta aquí, el análisis del archivo fue exitoso

                return render(request, 'analyzer/consulta.html', {'registros': registros})
            except Exception as e:
                # Capturar cualquier excepción que pueda ocurrir durante la lectura
                error_message = f"Error al analizar el archivo: {str(e)}"
                return render(request, 'analyzer/upload.html', {'form': form, 'error_message': error_message})
    else:
        form = UploadFileForm()
    return render(request, 'analyzer/upload.html', {'form': form})

def consulta_registros(request):
    if request.method == 'POST':
        return render(request, 'analyzer/consulta.html', {'registros': registros})
    else:
        return render(request, 'analyzer/consulta.html')


