import asyncio, ssl, logging, os, aiomysql, json, traceback
import aiomqtt, json


logging.basicConfig(format='%(asctime)s - cliente mqtt - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')

async def main():

    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    async with aiomqtt.Client(
    os.environ["SERVIDOR"],
    username=os.environ["MQTT_USR"],
    password=os.environ["MQTT_PASS"],
    port=int(os.environ["PUERTO_MQTTS"]),
    tls_context=tls_context,
    ) as client:
        await client.subscribe(os.environ['TOPICO'])
        async for message in client.messages:
            try:
                payload = message.payload.decode("utf-8")
                datos = json.loads(payload)

                temperatura = int(datos.get("temperatura", 0))
                humedad = int(datos.get("humedad", 0))

                logging.info(f"{message.topic}: temperatura={temperatura}, humedad={humedad}")

                dispositivo = os.environ['TOPICO']

                sql = "INSERT INTO `mediciones` (`sensor_id`, `temperatura`, `humedad`) VALUES (%s, %s, %s)"

                try:
                    conn = await aiomysql.connect(
                        host=os.environ["MARIADB_SERVER"],
                        port=3306,
                        user=os.environ["MARIADB_USER"],
                        password=os.environ["MARIADB_USER_PASS"],
                        db=os.environ["MARIADB_DB"]
                    )
                except Exception as e:
                    logging.error("Error de conexión a la base de datos")
                    logging.error(traceback.format_exc())
                    continue

                async with conn.cursor() as cur:
                    try:
                        await cur.execute(sql, (dispositivo, temperatura, humedad))
                        await conn.commit()
                    except Exception as e:
                        logging.error("Error al ejecutar SQL")
                        logging.error(traceback.format_exc())
                    finally:
                        await cur.close()
                        await conn.ensure_closed()

            except Exception as e:
                logging.error("Error procesando mensaje MQTT")
                logging.error(traceback.format_exc())
            
        
if __name__ == "__main__":
    asyncio.run(main())