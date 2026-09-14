#define PIN_LED_AMARILLO  25
#define PIN_LED_AZUL      26
#define PIN_LED_ROJO      27
#define PWM_FREQ       5000   
#define PWM_RESOLUTION    8   
#define DUTY_30   77    
#define DUTY_70  179    
#define DUTY_100 255    

typedef enum {
  MODO_PWM,        
  MODO_SEQ1,       
  MODO_SEQ2       
} SistemaMode;

SistemaMode modoActual = MODO_PWM;

uint8_t  seqPaso      = 0; 
uint32_t seqTimestamp = 0;    

void apagarTodos();
void setPWM(uint8_t dutyA, uint8_t dutyB, uint8_t dutyR);
void procesarComando(char cmd);
void ejecutarSecuencia1();
void ejecutarSecuencia2();

void setup() {
  Serial.begin(9600);
  Serial.println("[ESP32] Sistema iniciado. Esperando comandos...");
  ledcAttach(PIN_LED_AMARILLO, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(PIN_LED_AZUL,     PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(PIN_LED_ROJO,     PWM_FREQ, PWM_RESOLUTION);

  apagarTodos();
}
void loop() {
  if (Serial.available() > 0) {
    char cmd = (char)Serial.read();
    procesarComando(cmd);
  }
  if (modoActual == MODO_SEQ1) {
    ejecutarSecuencia1();
  } else if (modoActual == MODO_SEQ2) {
    ejecutarSecuencia2();
  }
}

void procesarComando(char cmd) {
  Serial.print("[CMD] Recibido: ");
  Serial.println(cmd);
  switch (cmd) {
    case 'A':
      modoActual = MODO_PWM;
      apagarTodos();
      ledcWrite(PIN_LED_AMARILLO, DUTY_30);
      Serial.println("  => LED Amarillo ON  30%");
      break;
    case 'B':
      modoActual = MODO_PWM;
      apagarTodos();
      ledcWrite(PIN_LED_AZUL, DUTY_70);
      Serial.println("  => LED Azul ON  70%");
      break;
    case 'C':
      modoActual = MODO_PWM;
      apagarTodos();
      ledcWrite(PIN_LED_ROJO, DUTY_100);
      Serial.println("  => LED Rojo ON  100%");
      break;
    case 'D':
      modoActual    = MODO_SEQ1;
      seqPaso       = 0;
      seqTimestamp  = millis();
      apagarTodos();
      Serial.println("  => MODO Secuencia 1 activado");
      break;
    case 'E':
      modoActual    = MODO_SEQ2;
      seqPaso       = 0;
      seqTimestamp  = millis();
      apagarTodos();
      Serial.println("  => MODO Secuencia 2 activado");
      break;
    case 'F':
      modoActual = MODO_PWM;
      apagarTodos();
      ledcWrite(PIN_LED_AMARILLO, DUTY_100);
      ledcWrite(PIN_LED_AZUL,     DUTY_100);
      ledcWrite(PIN_LED_ROJO,     DUTY_100);
      Serial.println("  => Los tres LEDs ON  100% (dedo del medio)");
      break;
    default:
      Serial.println("  => Comando desconocido, ignorado.");
      break;
  }
}
void ejecutarSecuencia1() {
  const uint32_t DURACION_PASO = 400;
  uint32_t ahora = millis();
  if ((ahora - seqTimestamp) >= DURACION_PASO) {
    seqTimestamp = ahora; 

    switch (seqPaso) {
      case 0:
        apagarTodos();
        ledcWrite(PIN_LED_AMARILLO, DUTY_100);
        seqPaso = 1;
        break;

      case 1:
        apagarTodos();
        ledcWrite(PIN_LED_AZUL, DUTY_100);
        seqPaso = 2;
        break;
      case 2:
        apagarTodos();
        ledcWrite(PIN_LED_ROJO, DUTY_100);
        seqPaso = 3;
        break;
      case 3:
        apagarTodos();
        ledcWrite(PIN_LED_AMARILLO, DUTY_100);
        ledcWrite(PIN_LED_ROJO,     DUTY_100);
        seqPaso = 4;
        break;
      case 4:
        apagarTodos();
        seqPaso = 0;
        break;

      default:
        seqPaso = 0;
        break;
    }
  }
}

void ejecutarSecuencia2() {
  const uint32_t DURACION_PASO = 300;
  uint32_t ahora = millis();

  if ((ahora - seqTimestamp) >= DURACION_PASO) {
    seqTimestamp = ahora;
    switch (seqPaso) {
      case 0:
        apagarTodos();
        ledcWrite(PIN_LED_AMARILLO, DUTY_30);
        seqPaso = 1;
        break;
      case 1:
        ledcWrite(PIN_LED_AMARILLO, DUTY_100);
        seqPaso = 2;
        break;
      case 2:
        apagarTodos();
        ledcWrite(PIN_LED_AZUL, DUTY_30);
        seqPaso = 3;
        break;
      case 3:
        ledcWrite(PIN_LED_AZUL, DUTY_100);
        seqPaso = 4;
        break;

      case 4:
        apagarTodos();
        ledcWrite(PIN_LED_ROJO, DUTY_30);
        seqPaso = 5;
        break;
      case 5:
        ledcWrite(PIN_LED_ROJO, DUTY_100);
        seqPaso = 6;
        break;

      case 6:
        ledcWrite(PIN_LED_AMARILLO, DUTY_70);
        ledcWrite(PIN_LED_AZUL,     DUTY_70);
        ledcWrite(PIN_LED_ROJO,     DUTY_70);
        seqPaso = 7;
        break;
      case 7:
        apagarTodos();
        seqPaso = 0;
        break;
      default:
        seqPaso = 0;
        break;
    }
  }
}
void apagarTodos() {
  ledcWrite(PIN_LED_AMARILLO, 0);
  ledcWrite(PIN_LED_AZUL,     0);
  ledcWrite(PIN_LED_ROJO,     0);
}
