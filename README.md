# Bot de Telegram para Monitoreo de Sensores

Este bot está diseñado para interactuar con sensores conectados a través de MQTT y almacenar/recolectar datos desde una base de datos MariaDB. A través de Telegram, los usuarios autorizados pueden consultar datos de temperatura y humedad, controlar dispositivos, enviar comandos y generar gráficos automáticos.

---

## Funcionalidades principales

### Monitoreo de variables ambientales
- Consulta de la **última temperatura** o **humedad** registrada.
- Generación de **gráficos de temperatura o humedad** de las últimas 24h.

### Control de dispositivos
- Encendido/apagado de un relé.
- Cambio entre modo **manual** y **automático**.
- Comando de **destello visual** (animación de luces).

### Configuración de parámetros
- Definición del valor **setpoint** de temperatura.
- Configuración del **período de muestreo** del sensor.

---

## Tecnologías utilizadas

- **Python 3.11+**
- **Telegram Bot API** (`python-telegram-bot v20+`)
- **MQTT (seguro con TLS)** (`aiomqtt`)
- **MariaDB** (`aiomysql`)
- **Matplotlib**: para la generación de gráficos.
- **Asyncio**: ejecución concurrente de tareas asíncronas.

---

## Seguridad

- Solo usuarios autorizados (definidos por ID en la variable de entorno `TB_AUTORIZADOS`) pueden interactuar con el bot.
- La comunicación MQTT utiliza TLS para cifrado de extremo a extremo.

---

## Variables de entorno requeridas


| Variable                | Descripción                        |
|------------------------|------------------------------------|
| `TB_TOKEN`             | Token del bot de Telegram          |
| `TB_AUTORIZADOS`       | Lista de IDs de usuarios permitidos (ej. `123456789,987654321`) |
| `DOMINIO`              | Dirección del broker MQTT          |
| `PUERTO_MQTTS`         | Puerto del broker (TLS)            |
| `MQTT_USR`             | Usuario MQTT                       |
| `MQTT_PASS`            | Contraseña MQTT                    |
| `MARIADB_SERVER`       | Host del servidor MariaDB          |
| `MARIADB_USER`         | Usuario de la base de datos        |
| `MARIADB_USER_PASS`    | Contraseña de la base de datos     |
| `MARIADB_DB`           | Nombre de la base de datos         |

---

## Comandos disponibles

| Comando / Mensaje        | Acción                                                        |
|--------------------------|---------------------------------------------------------------|
| `/start`                 | Inicia la conversación y muestra opciones                     |
| `/acercade`              | Muestra información sobre el bot                              |
| `/rele`                  | Muestra botones para encender o apagar el relé                |
| `/modo`                  | Cambia entre modo manual y automático                         |
| `/setpoint`              | Configura el valor de referencia de temperatura               |
| `/periodo`               | Configura el período de medición del sensor (en segundos)     |
| `/cancelar`              | Cancela una operación interactiva en curso                    |
| `temperatura` / `humedad`| Muestra la última medición                                    |
| `gráfico temperatura` / `gráfico humedad` | Genera y envía un gráfico de las últimas 24h    |
| `/destello`              | Envía un comando visual y un GIF animado                      |

---

