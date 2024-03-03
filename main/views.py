from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage
from .forms import registroUsuariosForm, inicioSesionForm
from .models import Usuarios, Producto

import re

# Variables
NOMBRELENGTHMIN = 2
APELLIDOSLENGTHMIN = 3
DOCLENGTHMIN = 6 #Minimo de carácteres para el documento
PASSLENGTHMIN = 8 #Minimo de carácteres para la contraseña

EMAILREGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
NUMBERWITHPOINTSREGEX = r'\B(?=(\d{3})+(?!\d))'
#Arrays - listas
adminIds = [0, 1]

#HTTDOCS
HTMLEDITARCUENTA = "editar_cuenta.html"
HTMLHOME = "home.html"
HTMLREGISTRO = "registro.html"
HTMLCATALOGO = "catalogo.html"
HTMLCARRITO = "cart.html"

#Notificaciones
EXITO_1 = "El usuario ha sido creado correctamente."
EXITO_2 = "Sus datos fueron actualizados correctamente"
EXITO_3 = "Contraseña actualizada correctamente"
ERROR_1 = "El documento que intentó ingresar, ya existe."
ERROR_2 = "Formulario inválido."
ERROR_3 = "Error desconocido."
ERROR_4 = "Usuario o contraseña incorrecta."
ERROR_5 = "Este usuario no pudo ser redireccionado. Comunique este error."
ERROR_6 = "Usuario o documento demasiado corto(s)."
ERROR_7 = "Algun campo quedó vacío."
ERROR_8 = "La contraseña anterior no es la correcta."
ERROR_9 = "Alguna(s) de las contraseñas no cumplen con la longitud minima."
ERROR_10 = "Las contraseñas nuevas no coinciden"
ERROR_11 = "Nombre o apellidos no cumplen con la longitud minima."
ERROR_12 = "Formato de email no válido"

#-----------Functions----------#
#Quita espacio al principio y al final de los campos de un formulario
def stripForm(form):
    for campo in form.fields:
        if isinstance(form.cleaned_data[campo], str):
            form.cleaned_data[campo] = form.cleaned_data[campo].strip()
    return form 

#Verifica que una lista de strings no esté vacía
def isEmpty(elements):
    return any(len(element.strip()) == 0 for element in elements)

#Verifica la validez de un email
def isValidEmail(email):
    if re.match(EMAILREGEX, email):
        return True
    return False

#Agregar punto decimal a los números
def numberWithPoints(numero):
    return re.sub(NUMBERWITHPOINTSREGEX, '.', str(numero))

# Decorador que valida que el usuario no esté logueado para hacer algo.
def unloginRequired(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('registro')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def Catalogo(request):
    carrito = request.session.get('carrito', {})
    PRODUCTOS_POR_PAGINA = 12
    productos = Producto.objects.order_by('id')
    if request.method == "POST":
        pass
    
    paginator = Paginator(productos, PRODUCTOS_POR_PAGINA)
    productos = paginator.page(request.GET.get('page', 1))
    
    return render(request, HTMLCATALOGO,{
        'productos': productos
    })

@login_required
def CartHandler(request):
    carrito = request.session.get('carrito', {})
    if request.method == "POST":
        event = ""
        action = request.POST.get('action')
        producto_id = request.POST.get('producto_id')
        
        #Añadir
        if action == "1":
            try:
                producto = Producto.objects.get(pk=producto_id)
                cantidad = int(request.POST.get('cantidad', 1)) 
                total_producto = int(cantidad) * int(producto.precio)
                print(total_producto)
                carrito[producto_id] = {
                    'descripcion': producto.descripcion,
                    'precio': producto.precio,
                    'referencia_fabrica': producto.referencia_fabrica,
                    'cantidad': cantidad,
                    'total_producto': total_producto,
                }
                event = "Producto añadido"
                request.session['carrito'] = carrito
                return JsonResponse({'success': True, 'event': event,})
            except Producto.DoesNotExist:
                event = "El producto no existe"
              
        #Borrar  
        elif action == "2":
            if producto_id in carrito:
                del carrito[producto_id]
                event = "Producto borrado"
                carrito_vacio = len(carrito) == 0  
            total_productos_actualizado = sum(int(item['total_producto']) for item in carrito.values())
            iva_actualizado = total_productos_actualizado * 0.19
            total_actualizado = total_productos_actualizado + iva_actualizado
            request.session['carrito'] = carrito
            
            return JsonResponse({'success': True, 'event': event, 'total_productos': total_actualizado,
                                'iva': iva_actualizado, 'total_actualizado': total_actualizado, 'carrito_vacio': carrito_vacio})

    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
            
def getCartPrice(carrito):
    total_productos = 0
    if carrito:
        for key, producto in carrito.items():
            total_productos += int(producto['precio']) * int(producto['cantidad'])
            producto['precio_str'] = numberWithPoints(producto['precio'])
            producto['total_producto_str'] = numberWithPoints(producto['total_producto'])
        return  total_productos
    
@login_required
def Cart(request):
    #Valor total de los productos
    carrito = request.session.get('carrito', {})
    total_productos = 0
    iva = 0
    if carrito:
        total_productos = getCartPrice(carrito)
        iva = round(total_productos * 0.19)
    return render(request, HTMLCARRITO, {'productos':carrito,
                                         'total_productos': numberWithPoints(total_productos),
                                         'iva': numberWithPoints(iva),
                                         'total_venta':numberWithPoints(total_productos+iva)})
    
@login_required
def EditarCuenta(request):
    user = get_object_or_404(Usuarios, pk=str(request.user.id))
    if request.method == "POST":
        print(request.POST)
        print("nombre" in request.POST)
        print("pass_data" in request.POST)
        if "acc_data" in request.POST:
            nombre = request.POST.get("nombre", "").strip()
            apellidos = request.POST.get("apellidos", "").strip()
            email = request.POST.get("email", "").strip()
            print(f"nombre {nombre}")
            if isEmpty([nombre, apellidos, email]):
                return render(request, HTMLEDITARCUENTA,{"account_data_event": ERROR_7})
            
            if len(nombre) < NOMBRELENGTHMIN or len(apellidos) < APELLIDOSLENGTHMIN:
                return render(request, HTMLEDITARCUENTA, {"account_data_event": ERROR_11})
            
            if not isValidEmail(email):
                return render(request, HTMLEDITARCUENTA, {"account_data_event":ERROR_12})
       
            user.first_name = nombre
            user.last_name = apellidos
            user.email = email
            user.save()
            
            return render(request, HTMLEDITARCUENTA, {"account_data_event": EXITO_2})
            
        elif "pass_data" in request.POST:
            
            oldPassword = request.POST.get('oldPassword')
            newPassword = request.POST.get('password')
            newPassword1 = request.POST.get('password1')
            
            if user.check_password(oldPassword):
                if len(newPassword) >= PASSLENGTHMIN or len(newPassword1) >= PASSLENGTHMIN:
                    if newPassword == newPassword1:
                        user.set_password(newPassword)
                        user.save()
                        return redirect(reverse('home'))
                    else:
                        return render(request, HTMLEDITARCUENTA,{ "password_change_event": ERROR_10 })
                else:
                    return render(request, HTMLEDITARCUENTA,{ "password_change_event": ERROR_9 })
            else:
                return render(request, HTMLEDITARCUENTA, { "password_change_event": ERROR_8 })
    
    
    return render(request, HTMLEDITARCUENTA)

@unloginRequired
def Home(request):
    newForm = inicioSesionForm()
    if request.method == 'POST':
        form = inicioSesionForm(request.POST)
        if form.is_valid():
            form = stripForm(form)
            
            documento = form.cleaned_data['documento']
            password = form.cleaned_data['password']
            
            #Verificar el minimo de carácteres para cada campo
            if len(documento) < DOCLENGTHMIN or len(password) < PASSLENGTHMIN:
                recycledForm = inicioSesionForm(initial={'documento': documento})
                return render(request, HTMLHOME, {'form': recycledForm,
                                                     'error': ERROR_6})
            
            logedUser = authenticate(request, username=documento, password=password)
            
            #Verificar que el usuario exista y su contraseña sea correcta
            if logedUser is None:
                recycledForm = inicioSesionForm(initial={'documento': documento})
                return render(request, HTMLHOME, {'form': recycledForm,
                                                    'error':ERROR_4})
            else:
                login(request, logedUser)
                userType = logedUser.tipo_usuario_id
                print(f"-------------->usertype {userType}")
                if userType == 0:
                    return redirect(reverse('registro'))
                elif userType == 1:
                    return redirect(reverse('registro'))
                elif userType == 2:
                    return redirect(reverse('registro'))
                elif userType == 3:
                    return redirect(reverse('registro'))
                elif userType == 4:
                    return redirect(reverse('registro'))
                else:
                    logout(request)
                    return render(request, HTMLHOME, {'form': newForm,
                                                         'error': ERROR_5})
        else:
            return render(request, HTMLHOME,{'form':newForm,
                                                'error': ERROR_2})
    return render(request, HTMLHOME, {'form': newForm})

@login_required
def Registro(request):
    newForm = registroUsuariosForm()
    if request.method == "POST":
        form = registroUsuariosForm(request.POST)
        #Verificar que el documento no se haya registrado antes.
        if form.has_error("username", code="unique"):
            return render(request, HTMLREGISTRO, {
                    "form": form,
                    "evento": ERROR_1,
                    "exito": False,
                })
        
        #Verificar la validez del formulario (campos en blanco, tipos de datos correctos)
        if form.is_valid():
            #Quitar espacios al principio y al final de los campos de texto
            form = stripForm(form)
            #Guardar el usuario nuevo
            try:
                documento = form.cleaned_data['username']
                password = form.cleaned_data['password']
                
                if len(documento) < DOCLENGTHMIN or len(password) < PASSLENGTHMIN:
                    return render(request, HTMLREGISTRO, {
                      "form": form,
                      "evento": ERROR_6,
                      "exito": False  
                    })
                
                user = form.save(commit=False)
                user.username = documento
                user.set_password(password)
                user.email = form.cleaned_data['email']
                user.save()
                
                return render(request, HTMLREGISTRO, {
                    "form": newForm,
                    "evento": EXITO_1,
                    "exito": True,
                    "documento": f"Usuario login: {documento}",
                    "password": f"Contraseña: {form.cleaned_data['password']}"
                })
            except Exception as e:
                return render(request, HTMLREGISTRO, {
                    "form": form,
                    "evento": ERROR_3,
                    "exito": False,
                })
        else:
            return render(request, HTMLREGISTRO, {
                    "form": form,
                    "evento": ERROR_2,
                    "exito": False,
                })
    #GET
    return render(request, HTMLREGISTRO, {'form': newForm })

@login_required
def Logout(request):
    logout(request)
    return redirect(reverse('home'))