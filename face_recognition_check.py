import face_recognition

def load_face_encoding(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if len(encodings) == 0:
        print(f"No face found in {image_path}")
        return None
    return encodings[0]

def compare_faces(face1, face2):
    return face_recognition.face_distance([face1], face2)[0]

def main():
    face1 = load_face_encoding("image1.png")
    face2 = load_face_encoding("image2.png")
    face3 = load_face_encoding("image3.png")

    if face1 is None or face2 is None or face3 is None:
        print("Face loading failed. Please check the images.")
        return

    similarity_1_2 = compare_faces(face1, face2)
    similarity_1_3 = compare_faces(face1, face3)

    print(f"Similarity (Image1 ↔ Image2): {similarity_1_2:.4f}")
    print(f"Similarity (Image1 ↔ Image3): {similarity_1_3:.4f}")

    if similarity_1_2 < similarity_1_3:
        print("Image1 is more similar to Image2.")
    else:
        print("Image1 is more similar to Image3.")

if __name__ == "__main__":
    main()
