// Arduino: LED verde en pin 8, LED rojo en pin 9.
// Recibe por Serial:
//   'G' -> rostro reconocido / acceso permitido (verde)
//   'R' -> rostro NO reconocido / acceso denegado (rojo)

const int LED_VERDE = 8;
const int LED_ROJO  = 9;

void setup() {
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_ROJO, OUTPUT);

  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_ROJO, LOW);

  // Debe coincidir con el baudrate usado en Python
  Serial.begin(115200);
}

void loop() {
  if (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == 'G') {          // Rostro reconocido / acceso OK
      digitalWrite(LED_VERDE, HIGH);
      digitalWrite(LED_ROJO, LOW);
    } else if (c == 'R') {   // Desconocido / acceso NO permitido
      digitalWrite(LED_VERDE, LOW);
      digitalWrite(LED_ROJO, HIGH);
    }
  }
}
