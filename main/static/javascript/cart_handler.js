const regexNumeros = input => {
    return /^[0-9]+$/.test(input);
}

$(document).ready(()=> {
    $('.cart-handler').on('click', function(e) {
        e.preventDefault();
        let producto_id = $(this).data('producto-id');
        let url = $(this).data('carthandler-url');
        let action = $(this).data('action');
        let csfrtoken = $('input[name="csrfmiddlewaretoken"]').val();
        $.ajax({
            type: 'POST',
            url: url,
            data: {
                'action': action,
                'producto_id': producto_id,
                'csrfmiddlewaretoken': csfrtoken
            },
            dataType: 'json',
            success: data => {
                if (data.success) {
                    if (action == "2"){
                        if (data.carrito_vacio) {
                            window.location.href = '/cart/';
                        } else {
                            const productoElement = $('#p-' + producto_id);
                            if (productoElement.length) {
                                productoElement.remove();
                            }
                            $('#total_productos').text(`$${data.total_productos}`);
                            $('#iva').text(`$${data.iva}`);
                            $('#total_venta').text(`$${data.total_actualizado}`);
                            $('#productos_cantidad').text(`Carro - ${data.productos_cantidad} item(s)`);
                            createToastNotify(1, "Producto removido", "Producto removido del carrito correctamente.");
                        }
                    }
                    else if (action == "3"){
                        window.location.href = '/cart/';
                    } else{
                        createToastNotify(1, "Error", "Opción no válida.");
                    }
                } else {
                    createToastNotify(1, "Error", "Hubo un error en la petición.");
                }
            },
            error: () => {
                createToastNotify(1, "Error al procesar la solicitud.", "En el proceso de verificación de datos, algo salió mal.");
            }
        });
        
    });
});