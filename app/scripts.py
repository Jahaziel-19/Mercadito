from flask import jsonify, render_template
import random
from models import Admin, Docente, Alumno, Invitado

def random_int(length):
    min_value = 10 ** (length - 1)
    max_value = (10 ** length) - 1
    return random.randint(min_value, max_value)

def verificar_correo_existente(email):
    """
    Verifica si el correo ya está registrado en cualquiera de los modelos de usuario.
    Retorna True si el correo ya existe, de lo contrario retorna False.
    """
    return (
        Admin.query.filter_by(email=email).first() or
        Docente.query.filter_by(email=email).first() or
        Alumno.query.filter_by(email=email).first() or
        Invitado.query.filter_by(email=email).first()
    )

# scripts.py
'''
def escanear_qr():
    qrCode = cv2.QRCodeDetector()
    cap = cv2.VideoCapture(0)  # Abrir la cámara

    if not cap.isOpened():
        print("No se puede abrir la cámara")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se puede recibir el fotograma")
            break

        # Detectar y decodificar el QR
        ret_qr, decoded_info, points, _ = qrCode.detectAndDecodeMulti(frame)
        if ret_qr and decoded_info[0]:  # Verificar si se ha detectado un QR válido
            pedido_id = decoded_info[0]
            # Dibujar un marco alrededor del QR detectado
            for point in points:
                frame = cv2.polylines(frame, [point.astype(int)], True, (0, 255, 0), 8)

            # Enviar una señal al frontend con el ID del pedido detectado
            frame = cv2.putText(frame, f"QR Detectado: {pedido_id}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            yield f"data:{pedido_id}\n\n".encode()

        # Convertir el fotograma a JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()
'''