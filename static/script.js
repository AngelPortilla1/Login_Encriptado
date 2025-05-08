$(document).ready(function () {
    let modoRegistro = false;
    
    function toggleModoRegistro() {
        modoRegistro = !modoRegistro;
        if (modoRegistro) {
            $("#correo_group").show();
            $("#do_login").val("REGISTRAR");
            $(".box-login-title h2").text("REGISTRO");
        } else {
            $("#correo_group").hide();
            $("#do_login").val("INGRESAR");
            $(".box-login-title h2").text("LOGIN");
        }
    }
    
    // Función para verificar si el usuario está autenticado
    function verificarAutenticacion() {
        const token = localStorage.getItem("jwt_token");
        if (!token) {
            return false;
        }
        return true;
    }

    // Función para manejar la expiración del token
    function manejarErrorToken() {
        localStorage.removeItem("jwt_token");
        alert("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.");
        // Aquí podrías redirigir al login si es necesario
    }

    // Función para obtener el perfil del usuario
    function obtenerPerfil() {
        if (!verificarAutenticacion()) {
            console.log("No hay token disponible");
            return;
        }

        const token = localStorage.getItem("jwt_token");
        fetch("/perfil", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                console.log("Perfil:", data.usuario);
                // Aquí puedes mostrar los datos del perfil en la interfaz
                mostrarDatosPerfil(data.usuario);
            } else {
                console.error("Error al obtener perfil:", data.message);
                if (data.message.includes("token")) {
                    manejarErrorToken();
                }
            }
        })
        .catch(err => {
            console.error("Error al obtener perfil:", err);
            manejarErrorToken();
        });
    }

    // Función para mostrar los datos del perfil
    function mostrarDatosPerfil(usuario) {
        // Aquí puedes implementar la lógica para mostrar los datos del usuario
        // Por ejemplo, actualizar elementos HTML con la información del perfil
        console.log("Mostrando datos del usuario:", usuario);
    }
    
    $("#do_login").click(function (e) {
        e.preventDefault();
        closeLoginInfo();
        $(".fieldset-body span").hide().removeClass("i-save i-warning i-close");
        
        let proceed = true;
        $("#login_form input:visible").each(function () {
            if (!$.trim($(this).val())) {
                $(this).parent().find('span').addClass("i-warning").show();
                proceed = false;
            }
        });
        
        if (!proceed) return;
        
        const nick_name = $("#user").val();
        const contrasena = $("#pass").val();
        const email = $("#correo").val();
        
        const ruta = modoRegistro ? "/register" : "/login";
        
        const payload = modoRegistro
            ? { nick_name: nick_name, contrasena: contrasena, email: email }
            : { nick_name: nick_name, contrasena: contrasena };
        
        fetch(ruta, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                $(".fieldset-body span").addClass("i-save").show();
                alert(`✅ ${data.message}`);
                if (data.token) {
                    console.log("Token recibido:", data.token);
                    localStorage.setItem("jwt_token", data.token);
                    // Redirigir al dashboard después del login exitoso
                    window.location.href = "/dashboard";
                }
                if (modoRegistro) {
                    toggleModoRegistro();
                }
            } else {
                $(".fieldset-body span").addClass("i-close").show();
                alert("❌ " + data.message);
            }
        })
        .catch(err => {
            alert("❌ Error al conectar con el servidor: " + err);
        });
    });
    
    $("#crear_cuenta_btn").click(function () {
        toggleModoRegistro();
    });
    
    $("#login_form input").keyup(function () {
        $(this).parent().find('span').hide();
    });
    
    openLoginInfo();
    setTimeout(closeLoginInfo, 1000);
});

function openLoginInfo() {
    $('.b-form').css("opacity", "0.01");
    $('.box-form').css("left", "-37%");
    $('.box-info').css("right", "-37%");
}

function closeLoginInfo() {
    $('.b-form').css("opacity", "1");
    $('.box-form').css("left", "0px");
    $('.box-info').css("right", "-5px");
}

$(window).on('resize', function () {
    closeLoginInfo();
});