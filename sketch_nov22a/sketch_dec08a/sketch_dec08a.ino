#include <Servo.h>

// =======================
// CONFIGURACIÓN DE PINES
// =======================
const int LED_VERDE = 8;
const int LED_ROJO  = 9;
const int SERVO_PIN = 10;

// =======================
// CALIBRACIÓN DEL SERVO (PUERTA)
// =======================
// AUMENTA este valor si el 0 debe ir MÁS a la derecha
// Valores típicos: 10 – 25
const int OFFSET_CERRADO = 0;          // <-- MÁS A LA DERECHA QUE ANTES
const int ANGULO_CERRADO = OFFSET_CERRADO;
const int ANGULO_ABIERTO = OFFSET_CERRADO + 90;

// =======================
// CONFIGURACIÓN TIEMPOS
// =======================
const unsigned long TIEMPO_ABIERTO = 10000; // 10 s sin 'G'

// =======================
// MOVIMIENTO SUAVE DEL SERVO
// =======================
const int PASO_SERVO = 1;                 // grados por paso
const unsigned long INTERVALO_SERVO = 15; // ms entre pasos

// =======================
// VARIABLES DE ESTADO
// =======================
Servo microServo;

bool puertaAbierta = false;
bool moviendo = false;

int anguloActual = ANGULO_CERRADO;
int anguloObjetivo = ANGULO_CERRADO;

unsigned long ultimoReconocidoMs = 0;
unsigned long ultimoPasoServoMs = 0;

void setup() {
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_ROJO,  OUTPUT);

  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_ROJO,  LOW);

  microServo.attach(SERVO_PIN);

  // 🔒 Forzar posición cerrada calibrada al iniciar
  anguloActual = ANGULO_CERRADO;
  anguloObjetivo = ANGULO_CERRADO;
  microServo.write(anguloActual);

  Serial.begin(115200);
}

void loop() {
  // --------------------------------
  // 1) LEER COMANDOS DESDE PYTHON
  // --------------------------------
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    // --------- ROSTRO RECONOCIDO ---------
    if (c == 'G') {
      digitalWrite(LED_VERDE, HIGH);
      digitalWrite(LED_ROJO,  LOW);

      // Abrir suavemente si estaba cerrada
      if (!puertaAbierta) {
        anguloObjetivo = ANGULO_ABIERTO;
        moviendo = true;
        puertaAbierta = true;
      }

      // Reiniciar temporizador
      ultimoReconocidoMs = millis();
    }

    // --------- NO RECONOCIDO ---------
    else if (c == 'R') {
      // Mostrar rojo solo si la puerta está cerrada
      if (!puertaAbierta) {
        digitalWrite(LED_VERDE, LOW);
        digitalWrite(LED_ROJO,  HIGH);
      }
    }

    // --------- SIN ROSTRO ---------
    else if (c == 'N') {
      if (!puertaAbierta) {
        digitalWrite(LED_VERDE, LOW);
        digitalWrite(LED_ROJO,  LOW);
      }
    }
  }

  // --------------------------------
  // 2) CIERRE AUTOMÁTICO POR TIEMPO
  // --------------------------------
  if (puertaAbierta) {
    if (millis() - ultimoReconocidoMs >= TIEMPO_ABIERTO) {
      anguloObjetivo = ANGULO_CERRADO;
      moviendo = true;
      puertaAbierta = false;

      digitalWrite(LED_VERDE, LOW);
      digitalWrite(LED_ROJO,  LOW);
    }
  } else {
    anguloObjetivo = ANGULO_CERRADO;
  }

  // --------------------------------
  // 3) MOVIMIENTO SUAVE DEL SERVO
  // --------------------------------
  if (moviendo) {
    if (millis() - ultimoPasoServoMs >= INTERVALO_SERVO) {
      ultimoPasoServoMs = millis();

      if (anguloActual < anguloObjetivo) {
        anguloActual += PASO_SERVO;
        if (anguloActual > anguloObjetivo) anguloActual = anguloObjetivo;
      } 
      else if (anguloActual > anguloObjetivo) {
        anguloActual -= PASO_SERVO;
        if (anguloActual < anguloObjetivo) anguloActual = anguloObjetivo;
      }

      microServo.write(anguloActual);

      if (anguloActual == anguloObjetivo) {
        moviendo = false;
      }
    }
  }
}
