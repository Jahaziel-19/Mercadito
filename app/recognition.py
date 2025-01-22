import app.recognition as recognition
from models import db, Docente, Admin
import cv2
import os

def registrar_docente(docente):
    # Captura de imagen desde la cámara
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    
    if ret:
        # Guardar la imagen capturada
        image_path = f'static/fotos_docentes/{docente.id}.jpg'
        cv2.imwrite(image_path, frame)

        # Procesar la imagen para obtener el encoding
        image = recognition.load_image_file(image_path)
        encoding = recognition.face_encodings(image)[0]

        # Guardar el encoding en la base de datos (puedes crear un nuevo campo en el modelo Docente)
        docente.encoding = encoding.tobytes()  # Convierte a bytes para almacenar en la base de datos

        db.session.commit()

    video_capture.release()

def reconocer_usuario():
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()

    if ret:
        # Procesar la imagen capturada
        rgb_frame = frame[:, :, ::-1]  # Convertir BGR a RGB

        # Encontrar todas las caras en la imagen actual y obtener sus encodings
        face_locations = recognition.face_locations(rgb_frame)
        face_encodings = recognition.face_encodings(rgb_frame, face_locations)

        usuarios_reconocidos = []

        for face_encoding in face_encodings:
            # Comparar con los encodings almacenados en la base de datos
            for docente in Docente.query.all():
                stored_encoding = np.frombuffer(docente.encoding)  # Convierte de bytes a numpy array
                matches = recognition.compare_faces([stored_encoding], face_encoding)

                if matches[0]:
                    usuarios_reconocidos.append(docente)

            for admin in Admin.query.all():
                stored_encoding = np.frombuffer(admin.encoding)  # Convierte de bytes a numpy array
                matches = recognition.compare_faces([stored_encoding], face_encoding)

                if matches[0]:
                    usuarios_reconocidos.append(admin)

        return usuarios_reconocidos

    video_capture.release()