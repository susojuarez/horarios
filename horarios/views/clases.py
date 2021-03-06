from horarios.models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from custom_decorators import *
from collections import namedtuple
import json
import pytz
from django.conf import settings
import datetime


def _json_object_hook(d): return namedtuple('object', d.keys())(*d.values())

def json2obj(data): return json.loads(data, object_hook=_json_object_hook)

@json_response 
def get_clases_json(request):
    try:
        fecha = datetime.datetime.strptime(request.POST['fecha'], "%d/%m/%y").date()
        clases = Clase.objects.filter(fecha=fecha, estatus='activa')
    except:
        return { 'error': 'no fue posible obtener las clases del dia %s' % fecha }

    lista_clases = []
    
    for clase in clases:
        lista_clases.append({
                'clase_id': str(clase.id),         
                'hora': str(clase.hora.hora),
                'salon': str(clase.salon.nombre),
                'grupo': str(clase.grupo.nombre),
                'cantidad_alumnos': str(clase.alumnos.all().count())
            });
        
    return lista_clases
@json_response 
def guardar_alumno(request, alumno_id, clase_id):
    try:
        clase = Clase.objects.get(pk=clase_id)
        alumno = Alumno.objects.get(pk=alumno_id)
    except:
        return { 'error': 'no fue posible obtener las clases del dia' }
    try:
        alumno_clase = AlumnosClase.objects.create(clase = clase, alumno = alumno)
        return {'clase_id':str(clase.id) }
    except:
        return {'error':'error ya existe alumno'}
@json_response 
def borrar_alumno(request, alumno_id):
    try:
        clase_alumno = AlumnosClase.objects.get(pk=alumno_id)
    except:
        return { 'error': 'no fue posible obtener las clases del dia' }
    alumno = clase_alumno.id
    clase_alumno.delete()
    return {'alumno':str(clase_alumno.clase.id)}
    
@json_response 
def update_clase_json(request):
    response = {}
    salones = json2obj(request.POST['clases'])
    try:
        fecha = datetime.datetime.strptime(request.POST['fecha'], "%d/%m/%y").date()
        hora = Horario.objects.get(hora=request.POST['hora'])
        grupo = Grupo.objects.get(nombre=request.POST['grupo'])
    except:
        return {'error':'error en los datos enviados'}
    
    clases_actuales = Clase.objects.filter(fecha=fecha,hora=hora,grupo=grupo)
    for clase in clases_actuales:
            if clase.alumnos.count() > 0:
                clase.estatus = 'cancelada'
                clase.save()
                response[clase]='cancelada'
            else:
                response[clase]='borrada'
                clase.delete()
            
            
    for salon in salones:
        try:
            salon = Salon.objects.get(nombre=salon)
        except:
            response['error-salon']='El salon %s no existe' % salon
        try:
            clase = Clase.objects.get_or_create(fecha=fecha,salon=salon,grupo=grupo,hora=hora)[0]
            clase.estatus = 'activa'
            clase.save()
            response[clase]='activada'
        except:
            response['error al crear clase']='%s' % clase
    
    return response


def alumnos_clase(request, clase_id):
    try:
        clase = Clase.objects.get(pk=clase_id)
    except:
        return { 'error': 'error al acceder a la clase' }
    alumnos_globales = Alumno.objects.all().exclude(clases__clase=clase)
    return render(request, 'alumnos.html', {'alumnos': clase.alumnos.all(), 'alumnos_globales':alumnos_globales, 'clase':clase })

@json_response 
def tabla_alumnos(request, clase_id):
    try:
        clase = Clase.objects.get(pk=clase_id)
    except:
        return { 'error': 'no fue posible obtener las clases del dia %s' }
    tabla_alumnos = ""
    
    alumnos = clase.alumnos.all()
    for count, alumno in enumerate(alumnos):
        tabla_alumnos = tabla_alumnos + """
                <tr>
                  <td>%s</td>  
                  <td>%s</td>
                  <td style="text-align:left;">%s</td>
                  <td style="text-align:left;"> 
                  <span id="%s" style="color:#ff262d; cursor:pointer;" class="alumnos-remove alumnos-save glyphicon glyphicon-remove-circle"></span>
                  </td>
                </tr>
        """ % (count+1,alumno.alumno.matricula,alumno.alumno.nombre,alumno.id)
    return {'tabla_alumnos':tabla_alumnos, 'total':str(alumnos.count())}


@json_response 
def guardar_alumno_clase(request, clase_id):
    try:
        clase = Clase.objects.get(pk=clase_id)
        alumno = Alumno.objects.get_or_create(nombre=(request.POST['nombre']).upper(), matricula=request.POST['matricula'])[0]
        clasealumno = AlumnosClase.objects.get_or_create(clase=clase, alumno=alumno)
    except:
        return { 'error': 'no fue posible obtener las clases del dia' }
   
    return {'exito':'se guardo el alumno con exito'}   



 